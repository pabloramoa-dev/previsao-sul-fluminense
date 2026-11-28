"""Coleta do Sul Fluminense: falha do Open-Meteo não pode derrubar o Reel nem inventar dado."""
import datetime as dt
import io
import ssl
import sys
import urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reels"))
import coletar_tempo as C  # noqa: E402

HOJE = dt.date(2026, 11, 27)
CID = C.CIDADES[:4]


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(C.time, "sleep", lambda s: None)


def om_resposta(n, dias=2):
    d = {"time": [(HOJE + dt.timedelta(days=i)).isoformat() for i in range(dias)],
         "temperature_2m_max": [30.4] * dias, "temperature_2m_min": [18.2] * dias,
         "precipitation_sum": [12.0] * dias, "weather_code": [61] * dias,
         "uv_index_max": [9.0] * dias, "sunshine_duration": [20000] * dias,
         "wind_speed_10m_max": [14] * dias, "wind_gusts_10m_max": [30] * dias,
         "apparent_temperature_max": [33] * dias}
    return [{"daily": d, "hourly": {"relative_humidity_2m": [60] * 24 * dias,
                                    "precipitation": [0] * 24 * dias}} for _ in range(n)]


def met_json(dias=2, updated="2026-11-27T20:00:00Z"):
    tz = ZoneInfo(C.TZ)
    serie = []
    ini = dt.datetime.combine(HOJE, dt.time(0), tz)
    for h in range(24 * dias):
        t = (ini + dt.timedelta(hours=h)).astimezone(dt.timezone.utc)
        serie.append({"time": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "data": {
            "instant": {"details": {"air_temperature": 15 + (h % 24) / 2, "relative_humidity": 70,
                                    "wind_speed": 3, "wind_speed_of_gust": 9}},
            "next_1_hours": {"summary": {"symbol_code": "rain" if h % 24 in (15, 16) else "cloudy"},
                             "details": {"precipitation_amount": 2.0 if h % 24 in (15, 16) else 0}}}})
    return {"properties": {"meta": {"updated_at": updated}, "timeseries": serie}}


def test_ssl_some_vez_e_retentativa_com_variacao_aleatoria(monkeypatch):
    chamadas, esperas = [], []
    monkeypatch.setattr(C.time, "sleep", esperas.append)

    def get(url, timeout=30, headers=None, **k):
        chamadas.append(url)
        if len(chamadas) < 3:
            raise ssl.SSLError("EOF occurred in violation of protocol")
        return om_resposta(len(CID))
    monkeypatch.setattr(C.urllib.request, "urlopen", lambda req, timeout: _Resp(get(req.full_url)))
    r = C.buscar(CID, hoje=HOJE)
    assert len(r) == len(CID) and r[0]["fonte"] == "open-meteo"
    assert len(esperas) == 2 and esperas[1] > esperas[0] > 0


class _Resp(io.BytesIO):
    def __init__(self, obj):
        import json
        super().__init__(json.dumps(obj).encode())

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http(code, retry_after=None):
    hdr = {"Retry-After": str(retry_after)} if retry_after else {}
    return urllib.error.HTTPError("u", code, "x", hdr, None)


def test_429_respeita_retry_after_e_5xx_tenta_de_novo(monkeypatch):
    seq = [_http(429, 20), _http(503), om_resposta(len(CID))]
    esperas = []
    monkeypatch.setattr(C.time, "sleep", esperas.append)

    def urlopen(req, timeout):
        x = seq.pop(0)
        if isinstance(x, Exception):
            raise x
        return _Resp(x)
    monkeypatch.setattr(C.urllib.request, "urlopen", urlopen)
    assert len(C.buscar(CID, hoje=HOJE)) == len(CID)
    assert esperas[0] >= 20


def test_4xx_permanente_nao_insiste(monkeypatch):
    n = []

    def urlopen(req, timeout):
        n.append(1)
        raise _http(400)
    monkeypatch.setattr(C.urllib.request, "urlopen", urlopen)
    with pytest.raises(urllib.error.HTTPError):
        C._get_json("https://x", rotulo="t")
    assert len(n) == 1


def test_lote_menor_quando_chamada_unica_falha(monkeypatch):
    from urllib.parse import parse_qs, urlparse

    def urlopen(req, timeout):
        assert "open-meteo" in req.full_url, "não deveria cair no MET"
        n = len(parse_qs(urlparse(req.full_url).query)["latitude"][0].split(","))
        if n > 3:
            raise ssl.SSLError("payload grande")
        return _Resp(om_resposta(n))
    monkeypatch.setattr(C.urllib.request, "urlopen", urlopen)
    r = C.buscar(CID, hoje=HOJE)
    assert len(r) == len(CID) and all(x["fonte"] == "open-meteo" for x in r)


def test_met_norway_como_fonte_alternativa_sem_inventar(monkeypatch):
    def urlopen(req, timeout):
        if "open-meteo" in req.full_url:
            raise ssl.SSLError("down")
        assert "User-Agent" in dict(req.header_items()) or "User-agent" in dict(req.header_items())
        return _Resp(met_json())
    monkeypatch.setattr(C.urllib.request, "urlopen", urlopen)
    r = C.buscar(CID, hoje=HOJE)
    assert all(x["fonte"] == "met.no" for x in r)
    dia = C.montar(CID, r, 1)
    assert dia["data"] == "2026-11-28" and dia["fonte"] == "met.no"
    c = dia["cidades"][0]
    assert c["chuva_mm"] == 4.0 and c["cond"] == "chuva" and c["rajada_kmh"] == 32
    assert c["min"] == 15 and c["max"] == round(15 + 23 / 2)
    # MET não tem sol, UV real nem sensação: ausentes, não zero.
    for chave in ("sol_h", "uv_max", "sensacao_max"):
        assert chave not in dia
    assert dia["vento_kmh"] == round(3 * 3.6)


def test_todas_as_fontes_falham_sem_inventar(monkeypatch):
    def urlopen(req, timeout):
        raise ssl.SSLError("down")
    monkeypatch.setattr(C.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError, match="nada será inventado"):
        C.buscar(CID, hoje=HOJE)


def test_met_sem_cobertura_horaria_e_recusado():
    dados = met_json(dias=1)
    with pytest.raises(C.FonteIndisponivel):
        C.met_para_openmeteo(dados, 2, HOJE)


def _dia(data="2026-11-28", **kw):
    base = {"data": data, "cidades": [{"nome": c[0], "min": 18, "max": 30, "chuva_mm": 3.0} for c in CID]}
    base.update(kw)
    return base


def test_validacao_barra_data_vencida_localidade_e_valor_impossivel():
    C.validar(_dia(), CID, dt.date(2026, 11, 28))
    with pytest.raises(SystemExit, match="data"):
        C.validar(_dia("2026-11-27"), CID, dt.date(2026, 11, 28))
    with pytest.raises(SystemExit, match="localidades"):
        C.validar(_dia(), CID[:3], dt.date(2026, 11, 28))
    ruim = _dia()
    ruim["cidades"][0]["max"] = 61
    with pytest.raises(SystemExit, match="temperatura"):
        C.validar(ruim, CID, dt.date(2026, 11, 28))
    with pytest.raises(SystemExit, match="desatualizada"):
        C.validar(_dia(atualizado_em="2026-11-01T00:00:00Z"), CID, dt.date(2026, 11, 28))


def test_open_meteo_mantem_campos_completos(monkeypatch):
    monkeypatch.setattr(C.urllib.request, "urlopen", lambda req, timeout: _Resp(om_resposta(len(CID))))
    dia = C.montar(CID, C.buscar(CID, hoje=HOJE), 0)
    assert dia["sol_h"] == round(20000 / 3600, 1) and dia["uv_max"] == 9.0 and dia["sensacao_max"] == 33
