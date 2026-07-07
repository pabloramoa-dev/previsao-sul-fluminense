# -*- coding: utf-8 -*-
"""
historico.py - Acumula leituras diarias por cidade para detectar
recordes e comparacoes ("3C a menos que ontem", "manha mais fria do ano").

Persistencia em historico.json (commitado de volta pelo Action).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

HISTORICO_PATH = Path(__file__).parent / "historico.json"


def carregar() -> dict[str, Any]:
    if HISTORICO_PATH.exists():
        return json.loads(HISTORICO_PATH.read_text(encoding="utf-8"))
    return {"cidades": {}}


def salvar(dados: dict[str, Any]) -> None:
    HISTORICO_PATH.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def registrar_dia(cidades: list) -> None:
    """
    Registra tmin/tmax do dia por cidade. 'cidades' e a lista de
    CidadeClima do clima.py (usa atributos .nome, .tmin, .tmax).
    """
    dados = carregar()
    hoje = dt.date.today().isoformat()
    for c in cidades:
        registro = dados["cidades"].setdefault(c.nome, {})
        registro[hoje] = {"tmin": round(c.tmin, 1), "tmax": round(c.tmax, 1)}
    salvar(dados)


def _leituras_do_ano(dados: dict[str, Any], nome: str, ano: int) -> dict[str, Any]:
    registro = dados["cidades"].get(nome, {})
    return {d: v for d, v in registro.items() if d.startswith(str(ano))}


def checar_recorde(nome: str, tmin: float, tmax: float) -> str | None:
    """
    Retorna texto de recorde se a leitura de hoje for a mais fria ou
    mais quente do ano ate agora para a cidade. None caso contrario.
    Deve ser chamado ANTES de registrar_dia (para nao comparar com o proprio dia).
    """
    dados = carregar()
    hoje = dt.date.today()
    leituras = _leituras_do_ano(dados, nome, hoje.year)
    # Remove hoje se ja registrado
    leituras.pop(hoje.isoformat(), None)
    if len(leituras) < 5:
        return None  # amostra pequena, evita "recorde" precoce

    mins = [v["tmin"] for v in leituras.values()]
    maxs = [v["tmax"] for v in leituras.values()]

    if tmin < min(mins):
        return f"manha mais fria de {hoje.year} em {nome} ({tmin:.0f}C)"
    if tmax > max(maxs):
        return f"dia mais quente de {hoje.year} em {nome} ({tmax:.0f}C)"
    return None


def comparar_com_ontem(nome: str, tmax: float) -> str | None:
    """
    Retorna 'XC a mais/menos que ontem' se houver leitura de ontem
    e a diferenca for >= 3C.
    """
    dados = carregar()
    ontem = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    registro = dados["cidades"].get(nome, {})
    if ontem not in registro:
        return None
    tmax_ontem = registro[ontem]["tmax"]
    delta = tmax - tmax_ontem
    if abs(delta) < 3:
        return None
    if delta < 0:
        return f"{abs(delta):.0f}C a menos que ontem"
    return f"{delta:.0f}C a mais que ontem"


if __name__ == "__main__":
    d = carregar()
    print("Cidades no historico:", list(d["cidades"].keys()))
