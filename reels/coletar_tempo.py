#!/usr/bin/env python3
"""
coletar_tempo.py — busca a previsão do Sul Fluminense no Open-Meteo e grava o
`dia.json` que o `gerar_dia.py` consome.

Open-Meteo é grátis e não pede chave. Uma única chamada traz todas as cidades
(a API aceita listas de latitude/longitude e devolve um array na mesma ordem).

Uso:
    python coletar_tempo.py --saida dia.json                     # hoje  (Ranzinza)
    python coletar_tempo.py --quando amanha --saida amanha.json  # amanhã (Dona Maria)
    python coletar_tempo.py --saida dia.json --cidades "Volta Redonda,Resende"

A ORDEM das cidades importa pro roteiro: a primeira é a "cidade principal"
(ganha a fala com mínima e máxima por extenso, e é ela que define o cenário do
vídeo), a 2ª e a 3ª entram juntas na fala do "mesma bagunça", e a 4ª ganha o
destaque de amanhecer.

RODÍZIO DIÁRIO (desde 2026-08-22)
---------------------------------
Volta Redonda era fixa na primeira posição, porque é a maior audiência do
perfil. O efeito colateral apareceu na grade: todo vídeo abria pela mesma
cidade, e quem mora nas outras nove nunca via o nome do seu município. A lista
agora GIRA por data — a cidade principal muda todo dia e cada uma volta a cada
dez dias, sem repetir na sequência.

O giro é determinístico (função da data), então rodar duas vezes no mesmo dia
dá exatamente o mesmo vídeo — a mesma garantia que a semente do roteiro já dava.

`--desloca N` gira mais N posições. É o que separa os dois vídeos do mesmo dia:
o Ranzinza (06h10) roda com deslocamento 0 e a Dona Maria (18h) com 5, então
eles nunca destacam a mesma cidade no mesmo dia.
"""
import argparse, json, sys, urllib.parse, urllib.request, datetime

API = "https://api.open-meteo.com/v1/forecast"
TZ = "America/Sao_Paulo"

# ordem BASE do rodízio. Não é mais a ordem de aparição no vídeo: `ordem_do_dia`
# gira esta lista pela data. A sequência abaixo é a ordem em que as cidades se
# revezam — vizinhas de audiência ficam separadas de propósito, pra que dois
# dias seguidos não abram os dois em municípios pequenos.
CIDADES = [
    ("Volta Redonda", -22.5231, -44.1041),
    ("Quatis",        -22.4064, -44.2578),
    ("Barra Mansa",   -22.5441, -44.1712),
    ("Pinheiral",     -22.5136, -44.0022),
    ("Resende",       -22.4686, -44.4468),
    ("Piraí",         -22.6289, -43.8981),
    ("Porto Real",    -22.4189, -44.2947),
    ("Rio Claro",     -22.7203, -44.1400),
    ("Barra do Piraí", -22.4711, -43.8256),
    ("Itatiaia",      -22.4906, -44.5636),
]

# Deslocamento do vídeo da tarde. Com 10 cidades, 5 é a metade exata da volta:
# a Dona Maria fica sempre no lado oposto do rodízio, então nunca cai na mesma
# cidade que o Ranzinza destacou de manhã.
DESLOCA_TARDE = 5


def ordem_do_dia(cidades, data=None, desloca=0):
    """Gira a lista de cidades pela data — a principal muda todo dia.

    `data` é a data de PUBLICAÇÃO, não a da previsão. Os dois vídeos do mesmo
    dia (o do Ranzinza fala de hoje, o da Dona Maria fala de amanhã) precisam
    girar pelo mesmo referencial, senão o de 18h repetiria a cidade que o de
    06h já usou. Quem separa os dois é `desloca`, não a data.

    Determinístico: mesma data, mesma ordem. Rodar de novo hoje refaz o mesmo
    vídeo, igual à semente do roteiro em gerar_dia.py.
    """
    if not cidades:
        return cidades
    d = data or datetime.date.today()
    n = (d.toordinal() + int(desloca)) % len(cidades)
    return cidades[n:] + cidades[:n]


# As maiores audiências do perfil, em ordem. Entram no RESUMO de todo vídeo,
# independentemente do rodízio: o rodízio existe pra dar palco às pequenas, não
# pra tirar o palco das grandes. Um vídeo que não diz a temperatura de Volta
# Redonda perde a maior parte de quem assiste.
MAIORES = ["Volta Redonda", "Barra Mansa", "Resende", "Barra do Piraí", "Itatiaia"]

# Quantas cidades o resumo mostra. Cinco é o teto do cartão: acima disso as
# linhas encolhem a ponto de não se ler no celular.
N_RESUMO = 5


def resumo_cinco(cidades, n=N_RESUMO):
    """As cidades do resumo: a cidade da vez primeiro, depois as maiores.

    Sem isto o vídeo fala de UMA cidade só. Foi o que aconteceu no Reel da Dona
    Maria de 2026-08-22: o rodízio pôs Piraí na primeira posição e o roteiro,
    que só lia `cidades[0]`, falou de Piraí do começo ao fim — as outras nove
    sumiram. O rodízio não era o problema; ele só revelou que o roteiro nunca
    tinha olhado além da primeira.

    A regra tem duas metades, e as duas importam:
      - a cidade da VEZ abre, porque é dela o selo e a chamada do dia;
      - as MAIORES vêm logo atrás, sempre, porque são a maior parte do público.
    Quando a cidade da vez já é uma das maiores, a lista simplesmente desce mais
    um degrau (entra a seguinte de MAIORES) — o resumo tem sempre `n` cidades.

    `cidades` é a lista de dicts do dia.json, já na ordem do rodízio.
    """
    if not cidades:
        return []
    por_nome = {c["nome"]: c for c in cidades}
    saida, vistos = [], set()

    def juntar(c):
        if c is not None and c["nome"] not in vistos:
            vistos.add(c["nome"])
            saida.append(c)

    juntar(cidades[0])                      # a cidade da vez abre o resumo
    for nome in MAIORES:                    # depois as maiores audiências
        if len(saida) >= n:
            break
        juntar(por_nome.get(nome))
    for c in cidades:                       # rede de segurança: completa na ordem
        if len(saida) >= n:
            break
        juntar(c)
    return saida[:n]


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
        # os quatro últimos campos diários existem pro bloco da Dona Maria:
        # UV e sensação térmica viram batida no roteiro dela, vento e horas de
        # sol entram na leitura do dia
        # wind_gusts_10m_max entrou em 2026-09-04: o gatilho de alerta do plano
        # v3 é RAJADA >= 50 km/h, e wind_speed_10m_max é a velocidade média
        # máxima — numa frente de vento a média fica em 30 e a rajada passa de
        # 60. Sem este campo o alerta de vento simplesmente nunca dispararia.
        "daily": ("temperature_2m_max,temperature_2m_min,precipitation_sum,"
                  "weather_code,uv_index_max,sunshine_duration,"
                  "wind_speed_10m_max,wind_gusts_10m_max,"
                  "apparent_temperature_max"),
        # precipitation por HORA revela a virada do tempo à tarde; continua
        # sendo coletada porque diz A QUE HORAS o tempo vira
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

    Nasceu pro aviso de recolher o varal, que saiu do roteiro. Continua sendo
    coletado (custa zero: vem na mesma resposta) porque é o dado que diz A QUE
    HORAS o tempo vira — o candidato natural pra um alerta futuro.
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
        # rajada POR CIDADE: o alerta de vento é regional (basta uma cidade
        # cruzar), e o campo do dia só trazia a cidade principal
        rajadas = d.get("wind_gusts_10m_max") or []
        rajada = rajadas[indice_dia] if indice_dia < len(rajadas) else None
        saida.append({
            "nome": nome,
            "min": round(tmin),
            "max": round(tmax),
            "cond": condicao(code, tmin),
            "chuva_mm": round(float(chuva), 1),
            "rajada_kmh": round(float(rajada)) if rajada is not None else None,
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
        # a cidade da vez: é ela que dá o nome ao selo na tela e, por
        # consequência, o que a miniatura da grade mostra
        "destaque": saida[0]["nome"] if saida else None,
        "cidades": saida,
        "umidade_min": round(min(umidades)) if umidades else None,
        # --- usados pelo bloco da Dona Maria ---
        "vento_kmh": round(diario("wind_speed_10m_max") or 0),
        # a maior rajada da região — é ela que o limiar de alerta lê
        "rajada_max": max([c["rajada_kmh"] for c in saida
                           if c.get("rajada_kmh") is not None] or [0]),
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
    ap.add_argument("--cidades", help="lista separada por vírgula pra sobrescrever a padrão "
                                      "(desliga o rodízio: a ordem passa a ser a sua)")
    ap.add_argument("--desloca", type=int, default=None,
                    help="posições extras no rodízio. Padrão: 0 pra hoje (Ranzinza) "
                         f"e {DESLOCA_TARDE} pra amanhã (Dona Maria)")
    ap.add_argument("--sem-rodizio", action="store_true",
                    help="mantém a ordem fixa da lista (Volta Redonda sempre primeiro)")
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
    elif not a.sem_rodizio:
        desloca = a.desloca
        if desloca is None:
            desloca = 0 if a.quando == "hoje" else DESLOCA_TARDE
        cidades = ordem_do_dia(cidades, desloca=desloca)

    idx = 0 if a.quando == "hoje" else 1
    respostas = buscar(cidades, dias=idx + 1 + 1)
    dia = montar(cidades, respostas, idx)

    json.dump(dia, open(a.saida, "w"), ensure_ascii=False, indent=2)
    print(f"ok: {a.saida} — {dia['data']}, {len(dia['cidades'])} cidades")
    print(f"  cidade da vez: {dia['destaque']}")
    print(f"  umidade mín {dia['umidade_min']}%  |  vento {dia['vento_kmh']} km/h  |  "
          f"sol {dia['sol_h']}h  |  UV {dia['uv_max']}  |  sensação {dia['sensacao_max']}°")
    if dia["chuva_hora"] is not None:
        print(f"  chuva prevista a partir das {dia['chuva_hora']}h")
    for c in dia["cidades"][:4]:
        print(f"  {c['nome']:16s} {c['min']:3d}° / {c['max']:3d}°  {c['cond']:11s} "
              f"chuva {c['chuva_mm']}mm")


if __name__ == "__main__":
    main()
