# -*- coding: utf-8 -*-
"""
alertas.py - Deteccao de variacao brusca do tempo + gatilho "choveu quanto".

Thresholds:
- Queda ou subida >= 6C em relacao a leitura anterior (estado.json)
- Chuva forte: prob > 70% e > 10mm nas proximas 3h, ausente na previsao da manha
- Rajadas de vento >= 50 km/h previstas
- Weathercode de tempestade (95-99) nas proximas horas

Anti-spam:
- Maximo 2 alertas por dia
- Nao repetir o mesmo tipo de alerta em menos de 6h

"Choveu quanto": acumulado 24h >= 30mm em qualquer cidade (max 1/dia).
Estado persistido em estado.json (commitado pelo Action).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

ESTADO_PATH = Path(__file__).parent / "estado.json"

LIMITE_ALERTAS_DIA = 2
INTERVALO_MIN_MESMO_TIPO_H = 6
DELTA_TEMP = 6.0
PROB_CHUVA_FORTE = 70.0
MM_CHUVA_FORTE = 10.0
VENTO_FORTE = 50.0
MM_ACUMULADO_24H = 30.0


def _carregar() -> dict[str, Any]:
    if ESTADO_PATH.exists():
        return json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
    return {}


def _salvar(estado: dict[str, Any]) -> None:
    ESTADO_PATH.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def _agora() -> dt.datetime:
    return dt.datetime.now()


def _proximas_horas(cidade, n: int = 3) -> dict[str, list]:
    """Recorta as proximas n horas das series horarias a partir de agora."""
    horas = cidade.horarias.get("time", [])
    agora = _agora().replace(minute=0, second=0, microsecond=0)
    alvo = agora.strftime("%Y-%m-%dT%H:00")
    try:
        i0 = horas.index(alvo)
    except ValueError:
        i0 = 0
    fatia = slice(i0, i0 + n)
    return {
        "prob": cidade.horarias.get("precipitation_probability", [])[fatia],
        "mm": cidade.horarias.get("precipitation", [])[fatia],
        "vento": cidade.horarias.get("windspeed_10m", [])[fatia],
        "code": cidade.horarias.get("weathercode", [])[fatia],
        "temp": cidade.horarias.get("temperature_2m", [])[fatia],
    }


def _pode_disparar(estado: dict[str, Any], tipo: str) -> bool:
    hoje = dt.date.today().isoformat()
    log = estado.get("alertas_log", {})
    do_dia = [a for a in log.get(hoje, [])]
    if len(do_dia) >= LIMITE_ALERTAS_DIA:
        return False
    # mesmo tipo em menos de 6h?
    for a in do_dia:
        if a["tipo"] == tipo:
            t = dt.datetime.fromisoformat(a["hora"])
            if (_agora() - t).total_seconds() < INTERVALO_MIN_MESMO_TIPO_H * 3600:
                return False
    return True


def _registrar(estado: dict[str, Any], tipo: str) -> None:
    hoje = dt.date.today().isoformat()
    log = estado.setdefault("alertas_log", {})
    log.setdefault(hoje, []).append({"tipo": tipo, "hora": _agora().isoformat()})
    _salvar(estado)


def detectar_alertas(cidades) -> list[dict[str, Any]]:
    """
    Retorna lista de alertas prontos para publicar. Ja aplica anti-spam
    e registra no estado.json. Cada alerta: {tipo, titulo, detalhe, cidades}.
    """
    estado = _carregar()
    leitura_anterior = estado.get("ultima_leitura", {})
    alertas: list[dict[str, Any]] = []

    afetadas: dict[str, list[str]] = {}

    for c in cidades:
        prox = _proximas_horas(c, 3)
        temps = [t for t in prox["temp"] if t is not None]
        probs = [p for p in prox["prob"] if p is not None]
        mms = [m for m in prox["mm"] if m is not None]
        ventos = [v for v in prox["vento"] if v is not None]
        codes = [x for x in prox["code"] if x is not None]

        # 1. Variacao de temperatura vs leitura anterior
        anterior = leitura_anterior.get(c.nome)
        if anterior is not None and temps:
            delta = temps[0] - anterior
            if delta <= -DELTA_TEMP:
                afetadas.setdefault("queda_temperatura", []).append(c.nome)
            elif delta >= DELTA_TEMP:
                afetadas.setdefault("subida_temperatura", []).append(c.nome)

        # 2. Chuva forte proximas 3h
        if probs and mms and max(probs) > PROB_CHUVA_FORTE and sum(mms) > MM_CHUVA_FORTE:
            afetadas.setdefault("chuva_forte", []).append(c.nome)

        # 3. Vento
        if ventos and max(ventos) >= VENTO_FORTE:
            afetadas.setdefault("vento", []).append(c.nome)

        # 4. Tempestade
        if codes and any(95 <= x <= 99 for x in codes):
            afetadas.setdefault("tempestade", []).append(c.nome)

    detalhes = {
        "queda_temperatura": "Queda brusca de temperatura nas proximas horas",
        "subida_temperatura": "Elevacao brusca de temperatura nas proximas horas",
        "chuva_forte": "Chuva forte prevista para as proximas 3h",
        "vento": "Rajadas de vento acima de 50 km/h previstas",
        "tempestade": "Risco de tempestade nas proximas horas",
    }
    titulos = {
        "queda_temperatura": "ALERTA: QUEDA BRUSCA DE TEMPERATURA",
        "subida_temperatura": "ALERTA: CALOR CHEGANDO COM FORCA",
        "chuva_forte": "ALERTA: CHUVA FORTE A CAMINHO",
        "vento": "ALERTA: RAJADAS DE VENTO",
        "tempestade": "ALERTA: RISCO DE TEMPESTADE",
    }

    for tipo, cidades_afetadas in afetadas.items():
        if _pode_disparar(estado, tipo):
            alertas.append({
                "tipo": tipo,
                "titulo": titulos[tipo],
                "detalhe": detalhes[tipo],
                "cidades": cidades_afetadas,
            })
            _registrar(estado, tipo)
            estado = _carregar()  # recarrega apos registrar

    # Atualiza ultima leitura para a proxima comparacao
    estado["ultima_leitura"] = {
        c.nome: (c.horarias.get("temperature_2m", [None])[0]
                 if c.horarias.get("temperature_2m") else c.tmax)
        for c in cidades
    }
    _salvar(estado)
    return alertas


def checar_chuva_acumulada(cidades) -> dict[str, Any] | None:
    """
    Gatilho "Choveu quanto?": se acumulado das ultimas 24h >= 30mm em
    qualquer cidade. Max 1 por dia. Retorna ranking ou None.
    """
    estado = _carregar()
    hoje = dt.date.today().isoformat()
    if estado.get("chuva_acumulada_publicada") == hoje:
        return None

    ranking = []
    for c in cidades:
        mm_series = [m for m in c.horarias.get("precipitation", [])[:24] if m is not None]
        total = sum(mm_series)
        ranking.append({"nome": c.nome, "mm": round(total, 1)})

    ranking.sort(key=lambda x: x["mm"], reverse=True)
    if ranking and ranking[0]["mm"] >= MM_ACUMULADO_24H:
        estado["chuva_acumulada_publicada"] = hoje
        _salvar(estado)
        return {"ranking": ranking}
    return None


if __name__ == "__main__":
    print("Modulo de alertas - rode via monitor_alertas.yml")
