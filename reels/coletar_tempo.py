#!/usr/bin/env python3
"""
coletar_tempo.py — busca a previsão do Sul Fluminense no Open-Meteo e grava o
`dia.json` que o `gerar_dia.py` consome.

Open-Meteo é grátis e não pede chave. Uma única chamada traz todas as cidades
(a API aceita listas de latitude/longitude e devolve um array na mesma ordem).

Uso:
    python coletar_tempo.py --saida dia.json
    python coletar_tempo.py --saida dia.json --quando hoje
    python coletar_tempo.py --saida dia.json --cidades "Volta Redonda,Resende"

A ORDEM das cidades importa pro roteiro: a primeira é a "cidade principal"
(ganha a fala com mínima e máxima por extenso), a 2ª e a 3ª entram juntas na
fala do "mesma bagunça", e a 4ª ganha o destaque de amanhecer. Por isso Volta
Redonda vem primeiro — é a maior audiência do perfil.
"""
import argparse, json, sys, urllib.parse, urllib.request, datetime

API = "https://api.open-meteo.com/v1/forecast"
TZ = "America/Sao_Paulo"

# ordem = ordem de aparição no vídeo
CIDADES = [
    ("Volta Redonda", -22.5231, -44.1041),
    ("Barra Mansa",   -22.5441, -44.1712),
    ("Porto Real",    -22.4189, -44.2947),
    ("Resende",       -22.4686, -44.4468),
    ("Barra do Piraí", -22.4711, -43.8256),
    ("Piraí",         -22.6289, -43.8981),
    ("Itatiaia",      -22.4906, -44.5636),
    ("Quatis",        -22.4064, -44.2578),
    ("Pinheiral",     -22.5136, -44.0022),
    ("Rio Claro",     -22.7203, -44.1400),
]


# --- WMO weather code -> a condição que a lib de desenho entende -------------
def condicao(code, tmin):
    """Traduz o código WMO do Open-Meteo pras 5 condições do cenário.

    `frio` tem prioridade: no inverno do Sul Fluminense o que define o dia (e o
    que o público sente) é a mínima, não a nebulosidade. Abaixo de 10°C o vídeo
    vira o cenário frio mesmo com céu limpo.
    """
    if code in (95, 96, 99):
        return "tempestade"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 85, 86):
        return "chuva"
    if tmin is not None and tmin < 10:
        return "frio"
    if code in (2, 3, 45, 48):
        return "nublado"
    return "sol"


def buscar(cidades, dias=2, timeout=30):
    lats = ",".join(f"{c[1]:.4f}" for c in cidades)
    lons = ",".join(f"{c[2]:.4f}" for c in cidades)
    q = urllib.parse.urlencode({
        "latitude": lats,
        "longitude": lons,
        # os quatro últimos campos diários existem só pro bloco da Dona Maria:
        # UV, horas de sol, vento e sensação térmica alimentam o índice de varal
        "daily": ("temperature_2m_max,temperature_2m_min,precipitation_sum,"
                  "weather_code,uv_index_max,sunshine_duration,"
                  "wind_speed_10m_max,apparent_temperature_max"),
        # precipitation por HORA é o que revela a virada do tempo à tarde —
        # o caso traiçoeiro do varal (manhã seca, chuva às 15h)
        "hourly": "relative_humidity_2m,precipitation",
        "timezone": TZ,
        "forecast_days": dias,
    })
    url = f"{API}?{q}"
    with urllib.request.urlopen(url, timeout=timeout) as r:
        dados = json.loads(r.read().decode())
    # com 1 cidade a API devolve objeto; com várias, lista. Normaliza.
    return dados if isinstance(dados, list) else [dados]


def primeira_chuva_da_tarde(precip_horaria, indice_dia, limiar=0.2,
                            inicio=12, fim=20):
    """Primeira hora da tarde com chuva prevista, ou None.

    É o dado que separa "pode estender" de "estende e recolhe às 15h". Sem ele
    o índice de varal olharia só o total do dia e mandaria estender a roupa numa
    manhã seca que vira temporal à tarde.
    """
    if not precip_horaria:
        return None
    fatia = precip_horaria[indice_dia * 24:(indice_dia + 1) * 24]
    for h in range(inicio, min(fim + 1, len(fatia))):
        v = fatia[h]
        if v is not None and v >= limiar:
            return h
    return None


def montar(cidades, respostas, indice_dia):
    """indice_dia: 0 = hoje, 1 = amanhã."""
    saida, umidades = [], []
    for (nome, _la, _lo), r in zip(cidades, respostas):
        d = r["daily"]
        tmax = d["temperature_2m_max"][indice_dia]
        tmin = d["temperature_2m_min"][indice_dia]
        chuva = d["precipitation_sum"][indice_dia] or 0.0
        code = d["weather_code"][indice_dia]
        saida.append({
            "nome": nome,
            "min": round(tmin),
            "max": round(tmax),
            "cond": condicao(code, tmin),
            "chuva_mm": round(float(chuva), 1),
            "wmo": code,
        })
        # umidade mínima do dia: 24 horas a partir do dia escolhido
        h = r.get("hourly", {}).get("relative_humidity_2m") or []
        fatia = h[indice_dia * 24:(indice_dia + 1) * 24]
        if fatia:
            umidades.append(min(x for x in fatia if x is not None))

    # --- campos do dia, tirados da cidade principal (a primeira da lista) ---
    r0 = respostas[0]
    d0 = r0["daily"]

    def diario(chave, pad=None):
        v = d0.get(chave)
        return v[indice_dia] if v and indice_dia < len(v) else pad

    sol_seg = diario("sunshine_duration")
    data = d0["time"][indice_dia]

    return {
        "data": data,
        "cidades": saida,
        "umidade_min": round(min(umidades)) if umidades else None,
        # --- usados pelo bloco da Dona Maria ---
        "vento_kmh": round(diario("wind_speed_10m_max") or 0),
        "sol_h": round((sol_seg or 0) / 3600, 1),
        "uv_max": round(diario("uv_index_max") or 0, 1),
        "sensacao_max": round(diario("apparent_temperature_max")
                              or d0["temperature_2m_max"][indice_dia]),
        "chuva_hora": primeira_chuva_da_tarde(
            r0.get("hourly", {}).get("precipitation"), indice_dia),
        "gerado_em": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="dia.json")
    ap.add_argument("--quando", choices=["hoje", "amanha"], default="hoje")
    ap.add_argument("--cidades", help="lista separada por vírgula pra sobrescrever a padrão")
    a = ap.parse_args()

    cidades = CIDADES
    if a.cidades:
        querido = [x.strip().lower() for x in a.cidades.split(",")]
        por_nome = {c[0].lower(): c for c in CIDADES}
        faltando = [n for n in querido if n not in por_nome]
        if faltando:
            sys.exit(f"cidade desconhecida: {', '.join(faltando)}\n"
                     f"disponíveis: {', '.join(c[0] for c in CIDADES)}")
        cidades = [por_nome[n] for n in querido]

    idx = 0 if a.quando == "hoje" else 1
    respostas = buscar(cidades, dias=idx + 1 + 1)
    dia = montar(cidades, respostas, idx)

    json.dump(dia, open(a.saida, "w"), ensure_ascii=False, indent=2)
    print(f"ok: {a.saida} — {dia['data']}, {len(dia['cidades'])} cidades")
    print(f"  umidade mín {dia['umidade_min']}%  |  vento {dia['vento_kmh']} km/h  |  "
          f"sol {dia['sol_h']}h  |  UV {dia['uv_max']}  |  sensação {dia['sensacao_max']}°")
    if dia["chuva_hora"] is not None:
        print(f"  ATENÇÃO: chuva prevista a partir das {dia['chuva_hora']}h "
              f"-> a Dona Maria vai avisar pra recolher o varal")
    for c in dia["cidades"][:4]:
        print(f"  {c['nome']:16s} {c['min']:3d}° / {c['max']:3d}°  {c['cond']:11s} "
              f"chuva {c['chuva_mm']}mm")


if __name__ == "__main__":
    main()
