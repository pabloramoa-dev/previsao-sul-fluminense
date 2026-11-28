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
import argparse, json, sys, urllib.parse, urllib.request, urllib.error, datetime, time
from zoneinfo import ZoneInfo

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

# Angra dos Reis entra como cidade convidada nos boletins PUBLICADOS na sexta
# e no domingo, sem alterar o rodízio das dez cidades regulares. As mesmas
# coordenadas já são usadas para Angra no serviço de previsão por DM.
ANGRA_DOS_REIS = ("Angra dos Reis", -23.0067, -44.3181)
DIAS_ANGRA = frozenset((4, 6))  # date.weekday(): sexta=4, domingo=6

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


def cidades_para_publicacao(data=None, desloca=0, sem_rodizio=False):
    """Seleciona as cidades conforme a data LOCAL de publicação do boletim.

    Em sextas e domingos Angra entra como destaque, à frente das dez cidades
    regulares. Nos demais dias não entra na coleta nem no resumo. Isto vale
    tanto para o Reel de hoje quanto para o card de amanhã: os dois são
    publicados no dia de execução, não na data prevista no card.
    """
    d = data or datetime.datetime.now(ZoneInfo(TZ)).date()
    base = list(CIDADES) if sem_rodizio else ordem_do_dia(CIDADES, data=d, desloca=desloca)
    if d.weekday() in DIAS_ANGRA:
        return [ANGRA_DOS_REIS] + base
    return base


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


# ------------------------------------------------------------------ coleta
# Run 46084225814: SSL do Open-Meteo caiu nas três tentativas e o Reel não saiu.
# Agora: retentativas com espera exponencial + variação aleatória, lotes menores
# quando a chamada única falha, e MET Norway como fonte alternativa. Nada é
# inventado: campo que a fonte não tem fica de fora (o roteiro pula a fala).
import random, ssl

MET_API = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
MET_UA = "previsao-sul-fluminense/1.0 github.com/pabloramoa-dev/previsao-sul-fluminense"
TENTATIVAS = 4
ESPERA_MAX = 45
TRANSITORIOS = (urllib.error.URLError, TimeoutError, ConnectionError, ssl.SSLError,
                OSError, ValueError, UnicodeError)


class FonteIndisponivel(RuntimeError):
    pass


def _espera(tentativa, retry_after=None):
    base = min(ESPERA_MAX, 2 * 2 ** tentativa)
    if retry_after:
        base = max(base, min(ESPERA_MAX, retry_after))
    return base + random.uniform(0, base / 2)


def _get_json(url, timeout=30, headers=None, tentativas=TENTATIVAS, rotulo="fonte"):
    ultimo = None
    for tentativa in range(tentativas):
        espera_ra = None
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # 4xx permanente (menos 408/429) é erro da chamada: não insistir.
            if exc.code not in (408, 429) and exc.code < 500:
                raise
            ultimo = exc
            try:
                espera_ra = int((exc.headers or {}).get("Retry-After", "0")) or None
            except (ValueError, TypeError, AttributeError):
                espera_ra = None
        except TRANSITORIOS as exc:
            ultimo = exc
        if tentativa < tentativas - 1:
            t = _espera(tentativa, espera_ra)
            print(f"{rotulo} instavel (tentativa {tentativa + 1}/{tentativas}): {ultimo}; "
                  f"repetindo em {t:.1f}s", file=sys.stderr)
            time.sleep(t)
    raise FonteIndisponivel(f"{rotulo} falhou apos {tentativas} tentativas: {ultimo}") from ultimo


def _url_openmeteo(cidades, dias):
    return f"{API}?" + urllib.parse.urlencode({
        "latitude": ",".join(f"{c[1]:.4f}" for c in cidades),
        "longitude": ",".join(f"{c[2]:.4f}" for c in cidades),
        # wind_gusts_10m_max: o gatilho de alerta é RAJADA >= 50 km/h.
        "daily": ("temperature_2m_max,temperature_2m_min,precipitation_sum,"
                  "weather_code,uv_index_max,sunshine_duration,"
                  "wind_speed_10m_max,wind_gusts_10m_max,"
                  "apparent_temperature_max"),
        "hourly": "relative_humidity_2m,precipitation",
        "timezone": TZ,
        "forecast_days": dias,
    })


def _openmeteo(cidades, dias, timeout):
    dados = _get_json(_url_openmeteo(cidades, dias), timeout, rotulo="Open-Meteo")
    respostas = dados if isinstance(dados, list) else [dados]
    # Nunca zip() com resposta parcial: associaria previsão à cidade errada.
    if (len(respostas) != len(cidades) or
            any(not isinstance(r, dict) or not isinstance(r.get("daily"), dict) for r in respostas)):
        raise FonteIndisponivel(f"Open-Meteo incompleto: {len(respostas)} respostas "
                                f"para {len(cidades)} cidades")
    for r in respostas:
        r["fonte"] = "open-meteo"
    return respostas


def _met_wmo(simbolos, chuva_mm):
    s = " ".join(simbolos)
    if "thunder" in s:
        return 95
    if chuva_mm is not None and chuva_mm >= 0.5 and any(k in s for k in ("rain", "sleet", "showers")):
        return 65 if "heavy" in s else 61 if chuva_mm < 2.5 else 63
    if "fog" in s:
        return 45
    nub = sum(1 for x in simbolos if x.startswith(("cloudy", "partlycloudy")))
    if simbolos and nub / len(simbolos) >= 0.6:
        return 3 if sum(1 for x in simbolos if x.startswith("cloudy")) >= nub / 2 else 2
    return 0


def met_para_openmeteo(dados, dias, hoje):
    """Converte o Locationforecast do MET Norway no formato que montar() lê.

    Só entram dias com cobertura horária (>= 18 h). Sem sensação térmica, horas
    de sol e UV real: esses campos ficam ausentes, nunca zerados.
    """
    tz = ZoneInfo(TZ)
    if not isinstance(dados, dict):
        raise FonteIndisponivel("MET Norway devolveu formato inesperado")
    serie = (dados.get("properties") or {}).get("timeseries") or []
    datas = [(hoje + datetime.timedelta(days=i)).isoformat() for i in range(dias)]
    por_dia = {d: [] for d in datas}
    for ponto in serie:
        t = datetime.datetime.fromisoformat(ponto["time"].replace("Z", "+00:00")).astimezone(tz)
        if t.date().isoformat() in por_dia and "next_1_hours" in ponto.get("data", {}):
            por_dia[t.date().isoformat()].append((t.hour, ponto["data"]))
    daily = {k: [] for k in ("time", "temperature_2m_max", "temperature_2m_min",
                             "precipitation_sum", "weather_code",
                             "wind_speed_10m_max", "wind_gusts_10m_max")}
    umid, prec = [None] * (24 * dias), [None] * (24 * dias)
    for i, d in enumerate(datas):
        horas = por_dia[d]
        if len(horas) < 18:
            raise FonteIndisponivel(f"MET Norway sem cobertura horária para {d} ({len(horas)} h)")
        inst = [h[1]["instant"]["details"] for h in horas]
        n1 = [h[1]["next_1_hours"] for h in horas]
        temps = [x["air_temperature"] for x in inst if x.get("air_temperature") is not None]
        chuva = round(sum((x.get("details") or {}).get("precipitation_amount") or 0 for x in n1), 1)
        rajadas = [x["wind_speed_of_gust"] * 3.6 for x in inst if x.get("wind_speed_of_gust") is not None]
        ventos = [x["wind_speed"] * 3.6 for x in inst if x.get("wind_speed") is not None]
        daily["time"].append(d)
        daily["temperature_2m_max"].append(max(temps))
        daily["temperature_2m_min"].append(min(temps))
        daily["precipitation_sum"].append(chuva)
        daily["weather_code"].append(_met_wmo([(x.get("summary") or {}).get("symbol_code", "") for x in n1], chuva))
        daily["wind_speed_10m_max"].append(max(ventos) if ventos else None)
        daily["wind_gusts_10m_max"].append(max(rajadas) if rajadas else None)
        for hora_local, dado in horas:
            umid[i * 24 + hora_local] = dado["instant"]["details"].get("relative_humidity")
            prec[i * 24 + hora_local] = (dado["next_1_hours"].get("details") or {}).get("precipitation_amount")
    atualizado = (dados.get("properties") or {}).get("meta", {}).get("updated_at")
    return {"daily": daily, "hourly": {"relative_humidity_2m": umid, "precipitation": prec},
            "fonte": "met.no", "atualizado_em": atualizado}


def _met(cidades, dias, timeout, hoje):
    respostas = []
    for nome, la, lo in cidades:
        url = f"{MET_API}?lat={la:.4f}&lon={lo:.4f}"
        dados = _get_json(url, timeout, headers={"User-Agent": MET_UA}, rotulo=f"MET Norway ({nome})")
        respostas.append(met_para_openmeteo(dados, dias, hoje))
    return respostas


def buscar(cidades, dias=2, timeout=30, hoje=None):
    """Open-Meteo em uma chamada → Open-Meteo em lotes de 3 → MET Norway."""
    hoje = hoje or datetime.datetime.now(ZoneInfo(TZ)).date()
    erros = []
    try:
        return _openmeteo(cidades, dias, timeout)
    except FonteIndisponivel as exc:
        erros.append(str(exc))
    try:
        respostas = []
        for i in range(0, len(cidades), 3):
            respostas += _openmeteo(cidades[i:i + 3], dias, timeout)
        print("Open-Meteo recuperado em lotes menores", file=sys.stderr)
        return respostas
    except FonteIndisponivel as exc:
        erros.append(str(exc))
    try:
        respostas = _met(cidades, dias, timeout, hoje)
        print("Open-Meteo indisponivel; usando MET Norway (fonte alternativa)", file=sys.stderr)
        return respostas
    except (FonteIndisponivel, KeyError, TypeError) as exc:
        erros.append(f"MET Norway: {exc}")
    raise RuntimeError("Nenhuma fonte meteorológica válida — nada será inventado:\n  "
                       + "\n  ".join(erros))


def validar(dia, cidades, esperado):
    """Barra previsão vencida, cidade faltando ou número impossível."""
    problemas = []
    if dia.get("data") != esperado.isoformat():
        problemas.append(f"data {dia.get('data')} != esperada {esperado.isoformat()}")
    nomes = [c["nome"] for c in dia.get("cidades", [])]
    if nomes != [c[0] for c in cidades]:
        problemas.append(f"localidades divergentes: {nomes}")
    for c in dia.get("cidades", []):
        if not (-10 <= c["min"] <= c["max"] <= 48):
            problemas.append(f"temperatura inválida em {c['nome']}: {c['min']}/{c['max']}")
        if not (0 <= c["chuva_mm"] <= 500):
            problemas.append(f"chuva inválida em {c['nome']}: {c['chuva_mm']}")
    if dia.get("atualizado_em"):
        upd = datetime.datetime.fromisoformat(dia["atualizado_em"].replace("Z", "+00:00"))
        if datetime.datetime.now(datetime.timezone.utc) - upd > datetime.timedelta(hours=12):
            problemas.append(f"previsão desatualizada (atualizada em {dia['atualizado_em']})")
    if problemas:
        raise SystemExit("validação da previsão falhou:\n  " + "\n  ".join(problemas))


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

    dia = {
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
        "gerado_em": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "fonte": r0.get("fonte", "open-meteo"),
    }
    if r0.get("atualizado_em"):
        dia["atualizado_em"] = r0["atualizado_em"]
    # Campo que a fonte não tem (MET: sol, UV real, sensação) sai do JSON em vez
    # de virar 0 — "zero horas de sol" seria informação inventada.
    for chave, bruto in (("sol_h", sol_seg), ("uv_max", diario("uv_index_max")),
                         ("sensacao_max", diario("apparent_temperature_max")),
                         ("vento_kmh", diario("wind_speed_10m_max"))):
        if bruto is None:
            dia.pop(chave, None)
    return dia


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
                    help="mantém a ordem das dez cidades regulares; Angra abre sextas e domingos")
    a = ap.parse_args()

    if a.cidades:
        querido = [x.strip().lower() for x in a.cidades.split(",")]
        por_nome = {c[0].lower(): c for c in CIDADES + [ANGRA_DOS_REIS]}
        faltando = [n for n in querido if n not in por_nome]
        if faltando:
            sys.exit(f"cidade desconhecida: {', '.join(faltando)}\n"
                     f"disponíveis: {', '.join(c[0] for c in CIDADES + [ANGRA_DOS_REIS])}")
        cidades = [por_nome[n] for n in querido]
    else:
        desloca = a.desloca
        if desloca is None:
            desloca = 0 if a.quando == "hoje" else DESLOCA_TARDE
        cidades = cidades_para_publicacao(desloca=desloca, sem_rodizio=a.sem_rodizio)

    idx = 0 if a.quando == "hoje" else 1
    hoje = datetime.datetime.now(ZoneInfo(TZ)).date()
    respostas = buscar(cidades, dias=idx + 1 + 1, hoje=hoje)
    dia = montar(cidades, respostas, idx)
    validar(dia, cidades, hoje + datetime.timedelta(days=idx))

    json.dump(dia, open(a.saida, "w"), ensure_ascii=False, indent=2)
    print(f"ok: {a.saida} — {dia['data']}, {len(dia['cidades'])} cidades, fonte {dia['fonte']}")
    print(f"  cidade da vez: {dia['destaque']}")
    print(f"  umidade mín {dia['umidade_min']}%  |  vento {dia.get('vento_kmh')} km/h  |  "
          f"sol {dia.get('sol_h')}h  |  UV {dia.get('uv_max')}  |  sensação {dia.get('sensacao_max')}°")
    if dia["chuva_hora"] is not None:
        print(f"  chuva prevista a partir das {dia['chuva_hora']}h")
    for c in dia["cidades"][:4]:
        print(f"  {c['nome']:16s} {c['min']:3d}° / {c['max']:3d}°  {c['cond']:11s} "
              f"chuva {c['chuva_mm']}mm")


if __name__ == "__main__":
    main()
