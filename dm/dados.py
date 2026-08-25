# -*- coding: utf-8 -*-
"""
dados.py - Fonte de previsao do robo de DM.

O webhook_ig.py chama previsao_hoje() a cada mensagem recebida. Por isso este
modulo NAO reaproveita src/clima.py: aquele modulo faz 20 requisicoes em serie
com pausa de 1,5s entre cidades (~20s por chamada), o que e certo para o post
diario e errado para responder uma DM.

Aqui a coleta e uma unica requisicao ao Open-Meteo com as 10 cidades de uma vez,
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

import threading
import time

import requests

from dm_bairro import CIDADES as CIDADES_BAIRRO

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
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
    """Uma requisicao, as 10 cidades, DOIS dias. Devolve {cidade: {...}}."""
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
        }
    return saida


def previsao_hoje() -> dict[str, dict]:
    """Previsao de hoje E de amanha das 10 cidades, com cache.

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
