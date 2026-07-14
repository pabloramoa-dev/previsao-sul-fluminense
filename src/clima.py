# -*- coding: utf-8 -*-
"""
clima.py - Coleta de dados meteorologicos do Open-Meteo para o
@previsaosulfluminense. Cobre 5 cidades do Sul Fluminense.

Endpoints usados (todos gratuitos, sem chave):
- /v1/forecast    : previsao diaria + horaria + sol/UV
- /v1/air-quality : qualidade do ar (AQI europeu)

Retorna estruturas prontas para os modulos gerar_carrossel.py,
captions.py, indices.py, alertas.py e historico.py.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo
from dataclasses import dataclass, field, asdict
from typing import Any

import time

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
TIMEZONE = "America/Sao_Paulo"
_TZ = ZoneInfo(TIMEZONE)
TIMEOUT = 30

# Cidades cobertas (nome -> coordenadas)
CIDADES = [
    {"nome": "Volta Redonda", "lat": -22.5231, "lon": -44.1042},
    {"nome": "Barra Mansa", "lat": -22.5446, "lon": -44.1719},
    {"nome": "Resende", "lat": -22.4705, "lon": -44.4509},
    {"nome": "Porto Real", "lat": -22.4175, "lon": -44.2952},
    {"nome": "Angra dos Reis", "lat": -23.0067, "lon": -44.3181},
]

# Dias e meses em portugues (runner do Actions nao tem locale pt_BR)
DIAS_SEMANA = [
    "Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sabado", "Domingo",
]
MESES = [
    "", "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def data_por_extenso(d: dt.date | None = None) -> str:
    """Retorna algo como 'Segunda-feira, 6 de julho de 2026'."""
    d = d or dt.datetime.now(_TZ).date()
    return f"{DIAS_SEMANA[d.weekday()]}, {d.day} de {MESES[d.month]} de {d.year}"


@dataclass
class CidadeClima:
    nome: str
    lat: float
    lon: float
    # Previsao diaria (hoje)
    tmin: float = 0.0
    tmax: float = 0.0
    prob_chuva: float = 0.0
    precipitacao_mm: float = 0.0
    weathercode: int = 0
    vento_max: float = 0.0
    umidade: float = 0.0
    uv_max: float = 0.0
    nascer_sol: str = ""
    por_sol: str = ""
    # Noite / madrugada
    temp_21h: float = 0.0
    tmin_madrugada: float = 0.0
    prob_chuva_noite: float = 0.0
    sensacao_noite: float = 0.0
    # Qualidade do ar
    aqi: int = 0
    # Series horarias brutas (para alertas)
    horarias: dict[str, Any] = field(default_factory=dict)

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    # Retry com backoff para tolerar instabilidades transitorias (5xx/timeout)
    # da API Open-Meteo, que ocasionalmente responde 503 Service Unavailable.
    ultimo_erro: Exception | None = None
    for tentativa in range(1, 4):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            ultimo_erro = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            # So faz retry em erros transitorios (5xx/timeout/conexao).
            transitorio = (
                status is None or status >= 500
            )
            if not transitorio or tentativa == 3:
                break
            time.sleep(2 * tentativa)
    raise ultimo_erro if ultimo_erro else RuntimeError("Falha desconhecida em _get_json")


def _hora_local(iso_str: str) -> str:
    """Converte '2026-07-06T06:12' em '06:12'."""
    if not iso_str:
        return ""
    try:
        return iso_str.split("T")[1][:5]
    except (IndexError, AttributeError):
        return ""


def coletar_forecast(cidade: dict[str, Any]) -> dict[str, Any]:
    params = {
        "latitude": cidade["lat"],
        "longitude": cidade["lon"],
        "timezone": TIMEZONE,
        "forecast_days": 2,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "precipitation_sum",
            "weathercode",
            "windspeed_10m_max",
            "uv_index_max",
            "sunrise",
            "sunset",
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "apparent_temperature",
            "windspeed_10m",
            "weathercode",
        ]),
    }
    return _get_json(FORECAST_URL, params)


def coletar_qualidade_ar(cidade: dict[str, Any]) -> int:
    params = {
        "latitude": cidade["lat"],
        "longitude": cidade["lon"],
        "timezone": TIMEZONE,
        "hourly": "european_aqi",
        "forecast_days": 1,
    }
    try:
        data = _get_json(AIR_QUALITY_URL, params)
        valores = [v for v in data.get("hourly", {}).get("european_aqi", []) if v is not None]
        return int(max(valores)) if valores else 0
    except (requests.RequestException, ValueError, KeyError):
        return 0


def _indice_hora(horas: list[str], alvo_hora: int, dia_offset: int = 0) -> int | None:
    """Encontra o indice da lista horaria para uma hora do dia (0-23)."""
    hoje = dt.datetime.now(_TZ).date() + dt.timedelta(days=dia_offset)
    alvo = f"{hoje.isoformat()}T{alvo_hora:02d}:00"
    for i, h in enumerate(horas):
        if h == alvo:
            return i
    return None


def processar_cidade(cidade: dict[str, Any]) -> CidadeClima:
    fc = coletar_forecast(cidade)
    daily = fc.get("daily", {})
    hourly = fc.get("hourly", {})

    c = CidadeClima(nome=cidade["nome"], lat=cidade["lat"], lon=cidade["lon"])

    # Diaria (indice 0 = hoje)
    c.tmin = float(daily.get("temperature_2m_min", [0])[0])
    c.tmax = float(daily.get("temperature_2m_max", [0])[0])
    c.prob_chuva = float(daily.get("precipitation_probability_max", [0])[0] or 0)
    c.precipitacao_mm = float(daily.get("precipitation_sum", [0])[0] or 0)
    c.weathercode = int(daily.get("weathercode", [0])[0])
    c.vento_max = float(daily.get("windspeed_10m_max", [0])[0] or 0)
    c.uv_max = float(daily.get("uv_index_max", [0])[0] or 0)
    c.nascer_sol = _hora_local(daily.get("sunrise", [""])[0])
    c.por_sol = _hora_local(daily.get("sunset", [""])[0])

    horas = hourly.get("time", [])

    # Umidade: media do periodo diurno (aproximada pela hora 12h de hoje)
    idx_12 = _indice_hora(horas, 12, 0)
    if idx_12 is not None:
        c.umidade = float(hourly.get("relative_humidity_2m", [0])[idx_12] or 0)

    # Noite: temperatura as 21h de hoje
    idx_21 = _indice_hora(horas, 21, 0)
    if idx_21 is not None:
        c.temp_21h = float(hourly.get("temperature_2m", [0])[idx_21] or 0)
        c.sensacao_noite = float(hourly.get("apparent_temperature", [0])[idx_21] or 0)

    # Madrugada: minima entre 00h e 06h de amanha
    idx_00 = _indice_hora(horas, 0, 1)
    idx_06 = _indice_hora(horas, 6, 1)
    temps = hourly.get("temperature_2m", [])
    if idx_00 is not None and idx_06 is not None and temps:
        janela = temps[idx_00:idx_06 + 1]
        janela = [t for t in janela if t is not None]
        c.tmin_madrugada = float(min(janela)) if janela else c.tmin

    # Chuva noturna: maior prob entre 18h de hoje e 06h de amanha
    idx_18 = _indice_hora(horas, 18, 0)
    probs = hourly.get("precipitation_probability", [])
    if idx_18 is not None and idx_06 is not None and probs:
        janela_p = [p for p in probs[idx_18:idx_06 + 1] if p is not None]
        c.prob_chuva_noite = float(max(janela_p)) if janela_p else 0.0

    # Qualidade do ar
    c.aqi = coletar_qualidade_ar(cidade)

    # Series horarias brutas para alertas (proximas horas)
    c.horarias = {
        "time": horas,
        "temperature_2m": hourly.get("temperature_2m", []),
        "precipitation_probability": hourly.get("precipitation_probability", []),
        "precipitation": hourly.get("precipitation", []),
        "windspeed_10m": hourly.get("windspeed_10m", []),
        "weathercode": hourly.get("weathercode", []),
    }
    return c


def coletar_todas() -> list[CidadeClima]:
    """Coleta clima de todas as 5 cidades. Retorna lista de CidadeClima."""
    resultado: list[CidadeClima] = []
    for cidade in CIDADES:
        try:
            resultado.append(processar_cidade(cidade))
        except requests.RequestException as e:
            print(f"[clima] ERRO ao coletar {cidade['nome']}: {e}")
            raise
    return resultado


def resumo_regional(cidades: list[CidadeClima]) -> dict[str, Any]:
    """Agrega dados regionais para a capa dos carrosseis."""
    return {
        "tmin": min(c.tmin for c in cidades),
        "tmax": max(c.tmax for c in cidades),
        "prob_chuva": max(c.prob_chuva for c in cidades),
        "weathercode_pred": max(c.weathercode for c in cidades),
        "uv_max": max(c.uv_max for c in cidades),
        "data_extenso": data_por_extenso(),
    }


if __name__ == "__main__":
    dados = coletar_todas()
    print(f"Data: {data_por_extenso()}")
    for c in dados:
        print(
            f"{c.nome}: {c.tmin:.0f}/{c.tmax:.0f}C | chuva {c.prob_chuva:.0f}% "
            f"| {c.precipitacao_mm:.1f}mm | vento {c.vento_max:.0f}km/h "
            f"| UV {c.uv_max:.0f} | AQI {c.aqi} | sol {c.nascer_sol}-{c.por_sol}"
        )
    print("Resumo:", resumo_regional(dados))
