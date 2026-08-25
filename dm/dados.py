# -*- coding: utf-8 -*-
"""
dados.py - Fonte de previsao do robo de DM.

O webhook_ig.py chama previsao_hoje() a cada mensagem recebida. Por isso este
modulo NAO reaproveita src/clima.py: aquele modulo faz 20 requisicoes em serie
com pausa de 1,5s entre cidades (~20s por chamada), o que e certo para o post
diario e errado para responder uma DM.

Aqui a coleta e uma unica requisicao ao Open-Meteo com as 14 cidades de uma vez,
guardada em memoria por TTL_SEGUNDOS. Em um dia normal o robo bate na API poucas
vezes por hora, nao uma vez por seguidor.

Desde 2026-08-23 a mesma requisicao traz DOIS dias (forecast_days=2): a
resposta da DM passou a entregar hoje E amanha, porque os Reels ja contam um
dia cada (Ranzinza fala de hoje as 06h10, Dona Maria de amanha as 18h) e a DM
que repetisse um dia so seria redundante com o video que a pessoa acabou de
ver. Os campos de amanha chegam com o sufixo _amanha.

Fonte das coordenadas: src/clima.py (CIDADES). Os nomes precisam bater com
dm_bairro.CIDADES -- se alguem editar um lado so, este modulo se recusa a
carregar, na mesma logica da trava do dm_bairro.py.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import threading
from zoneinfo import ZoneInfo
import time

import requests

from dm_bairro import CIDADES as CIDADES_BAIRRO

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MET_NO_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
MET_NO_UA = "previsaosulflu/1.0 github.com/pabloramoa-dev/previsao-sul-fluminense"
TIMEZONE = "America/Sao_Paulo"
TIMEOUT = 20
TENTATIVAS_429 = 3
ESPERA_429_PADRAO = 2
COOLDOWN_429 = 60

# Quanto tempo a previsao serve sem ir buscar de novo.
TTL_SEGUNDOS = 20 * 60
# Ate quando vale servir dado velho se a API cair. Previsao de 3h atras ainda
# ajuda o seguidor; silencio nao ajuda em nada.
TTL_EMERGENCIA = 3 * 60 * 60

COORDENADAS = {
    "Volta Redonda": (-22.5231, -44.1041),
    "Barra Mansa": (-22.5441, -44.1712),
    "Porto Real": (-22.4189, -44.2947),
    "Resende": (-22.4686, -44.4468),
    "Barra do Piraí": (-22.4711, -43.8256),
    "Piraí": (-22.6289, -43.8981),
    "Itatiaia": (-22.4906, -44.5636),
    "Quatis": (-22.4064, -44.2578),
    "Pinheiral": (-22.5136, -44.0022),
    "Rio Claro": (-22.7203, -44.1400),
    "Angra dos Reis": (-23.0067, -44.3181),
    "Paraty": (-23.2178, -44.7131),
    "Valença": (-22.2456, -43.7003),
    "Rio das Flores": (-22.1692, -43.5856),
}

if set(COORDENADAS) != set(CIDADES_BAIRRO):
    faltam = set(CIDADES_BAIRRO) - set(COORDENADAS)
    sobram = set(COORDENADAS) - set(CIDADES_BAIRRO)
    raise RuntimeError(
        "dados.py: as cidades daqui nao batem com as de dm_bairro.py. "
        f"Sem coordenada: {sorted(faltam)}. Sem bairros: {sorted(sobram)}.")

_NOMES = list(COORDENADAS)

_cache: dict[str, dict] | None = None
_cache_em: float = 0.0
_bloqueado_ate: float = 0.0
_trava = threading.Lock()


def _numero(valor, padrao: float = 0.0) -> float:
    """O Open-Meteo devolve null em campo sem dado; nao deixa isso virar erro."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _coletar() -> dict[str, dict]:
    """Uma requisicao, as 14 cidades, DOIS dias. Devolve {cidade: {...}}."""
    parametros = {
        "latitude": ",".join(str(COORDENADAS[n][0]) for n in _NOMES),
        "longitude": ",".join(str(COORDENADAS[n][1]) for n in _NOMES),
        "daily": ("temperature_2m_min,temperature_2m_max,"
                  "precipitation_probability_max,wind_gusts_10m_max"),
        "timezone": TIMEZONE,
        "forecast_days": 2,
    }
    for tentativa in range(1, TENTATIVAS_429 + 1):
        resposta = requests.get(
            FORECAST_URL, params=parametros, timeout=TIMEOUT)
        if resposta.status_code != 429 or tentativa == TENTATIVAS_429:
            break
        cabecalho = resposta.headers.get("Retry-After")
        try:
            espera = float(cabecalho) if cabecalho else (
                ESPERA_429_PADRAO * tentativa)
        except ValueError:
            espera = ESPERA_429_PADRAO * tentativa
        espera = min(max(espera, 1), 15)
        print(f"[dados] Open-Meteo limitou a chamada (429); "
              f"nova tentativa em {espera:.0f}s.")
        time.sleep(espera)
    resposta.raise_for_status()
    bruto = resposta.json()
    # Com varias coordenadas a API devolve uma lista; com uma so, um objeto.
    blocos = bruto if isinstance(bruto, list) else [bruto]
    if len(blocos) != len(_NOMES):
        raise RuntimeError(
            f"dados.py: pedi {len(_NOMES)} cidades e o Open-Meteo devolveu "
            f"{len(blocos)}.")

    def _dia(d: dict, chave: str, indice: int) -> float:
        serie = d.get(chave) or []
        return _numero(serie[indice] if indice < len(serie) else None)

    saida: dict[str, dict] = {}
    for nome, bloco in zip(_NOMES, blocos):
        d = bloco.get("daily") or {}
        saida[nome] = {
            # hoje (indice 0) — mesmos nomes de sempre, nada quebra
            "tmin": _dia(d, "temperature_2m_min", 0),
            "tmax": _dia(d, "temperature_2m_max", 0),
            "prob_chuva": _dia(d, "precipitation_probability_max", 0),
            "rajada_kmh": _dia(d, "wind_gusts_10m_max", 0),
            # amanha (indice 1)
            "tmin_amanha": _dia(d, "temperature_2m_min", 1),
            "tmax_amanha": _dia(d, "temperature_2m_max", 1),
            "prob_chuva_amanha": _dia(d, "precipitation_probability_max", 1),
            "rajada_kmh_amanha": _dia(d, "wind_gusts_10m_max", 1),
            "_fonte": "open_meteo",
        }
    return saida


def _coletar_met_no() -> dict[str, dict]:
    """Fallback gratuito do MET Norway, agregado em hoje e amanha."""

    fuso = ZoneInfo(TIMEZONE)
    hoje = datetime.now(fuso).date()
    datas = [hoje, hoje + timedelta(days=1)]

    def _cidade(item):
        nome, (lat, lon) = item
        resposta = requests.get(
            MET_NO_URL,
            params={"lat": f"{lat:.4f}", "lon": f"{lon:.4f}"},
            headers={"User-Agent": MET_NO_UA},
            timeout=TIMEOUT,
        )
        resposta.raise_for_status()
        series = resposta.json().get("properties", {}).get("timeseries", [])
        por_dia = {d: {"temp": [], "chuva": [], "vento": []} for d in datas}
        for ponto in series:
            instante = datetime.fromisoformat(
                ponto["time"].replace("Z", "+00:00")).astimezone(fuso)
            if instante.date() not in por_dia:
                continue
            dados_ponto = ponto.get("data", {})
            detalhes = dados_ponto.get("instant", {}).get("details", {})
            bucket = por_dia[instante.date()]
            if detalhes.get("air_temperature") is not None:
                bucket["temp"].append(_numero(detalhes["air_temperature"]))
            vento = detalhes.get("wind_speed_of_gust",
                                  detalhes.get("wind_speed"))
            if vento is not None:
                bucket["vento"].append(_numero(vento) * 3.6)
            periodo = (dados_ponto.get("next_1_hours")
                       or dados_ponto.get("next_6_hours") or {})
            pdet = periodo.get("details", {})
            prob = pdet.get("probability_of_precipitation")
            if prob is None and pdet.get("precipitation_amount") is not None:
                prob = 100.0 if _numero(pdet["precipitation_amount"]) > 0.1 else 0.0
            if prob is not None:
                bucket["chuva"].append(_numero(prob))

        if any(not por_dia[d]["temp"] for d in datas):
            raise RuntimeError(f"MET Norway sem dois dias completos para {nome}")

        def resumo(d):
            b = por_dia[d]
            return (min(b["temp"]), max(b["temp"]),
                    max(b["chuva"] or [0.0]), max(b["vento"] or [0.0]))

        h = resumo(datas[0])
        a = resumo(datas[1])
        return nome, {
            "tmin": h[0], "tmax": h[1], "prob_chuva": h[2],
            "rajada_kmh": h[3], "tmin_amanha": a[0],
            "tmax_amanha": a[1], "prob_chuva_amanha": a[2],
            "rajada_kmh_amanha": a[3],
            "_fonte": "met_no",
        }

    with ThreadPoolExecutor(max_workers=4) as executor:
        return dict(executor.map(_cidade, COORDENADAS.items()))


def previsao_hoje() -> dict[str, dict]:
    """Previsao de hoje E de amanha das 14 cidades, com cache.

    {"Resende": {"tmin": 14.2, "tmax": 27.9, "prob_chuva": 10.0,
                 "rajada_kmh": 23.4, "tmin_amanha": 15.0, ...}, ...}

    Se a API falhar mas houver cache recente, devolve o cache e segue. So
    levanta excecao quando nao ha nada util para responder.
    """
    global _cache, _cache_em, _bloqueado_ate
    agora = time.time()
    if _cache is not None and agora - _cache_em < TTL_SEGUNDOS:
        return _cache

    with _trava:
        # Outra thread pode ter atualizado enquanto esperavamos a trava.
        agora = time.time()
        if _cache is not None and agora - _cache_em < TTL_SEGUNDOS:
            return _cache
        if agora < _bloqueado_ate:
            espera = int(_bloqueado_ate - agora)
            raise RuntimeError(
                f"Open-Meteo em cooldown por limite de chamadas ({espera}s)")
        try:
            _cache = _coletar()
            _cache_em = time.time()
        except Exception as exc:
            if (isinstance(exc, requests.HTTPError)
                    and exc.response is not None
                    and exc.response.status_code == 429):
                _bloqueado_ate = time.time() + COOLDOWN_429
                try:
                    print("[dados] Open-Meteo em 429; usando fallback MET Norway.")
                    _cache = _coletar_met_no()
                    _cache_em = time.time()
                    return _cache
                except Exception as fallback_exc:
                    print(f"[dados] fallback MET Norway falhou: {fallback_exc}")
            if _cache is not None and agora - _cache_em < TTL_EMERGENCIA:
                idade = int((agora - _cache_em) / 60)
                print(f"[dados] Open-Meteo falhou ({exc}); "
                      f"servindo cache de {idade} min atras.")
                return _cache
            raise
        return _cache


if __name__ == "__main__":
    for cidade, p in previsao_hoje().items():
        print(f"{cidade:<16} {p['tmin']:.0f}/{p['tmax']:.0f}  "
              f"chuva {p['prob_chuva']:.0f}%  rajada {p['rajada_kmh']:.0f} km/h  "
              f"| amanha {p['tmin_amanha']:.0f}/{p['tmax_amanha']:.0f}  "
              f"chuva {p['prob_chuva_amanha']:.0f}%")
