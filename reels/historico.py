#!/usr/bin/env python3
"""
historico.py — constrói (uma vez) a tabela de recordes "neste dia" e consulta
ela depois, sem tocar na rede.

A API de arquivo do Open-Meteo tem dados desde 1940. Baixar isso todo dia seria
desperdício: o passado não muda. Então o fluxo é:

    python historico.py --construir            # 1x, gera historico.json (~60 KB)
    python historico.py --consultar 07-29      # confere o que saiu

E o gerar_tarde.py só faz `carregar()` + `recorde_do_dia()`, offline.

A tabela tem 366 entradas (uma por dia do calendário), cada uma com o recorde
de frio e o de calor daquele dia ao longo de todas as décadas.
"""
import argparse, json, os, sys, urllib.parse, urllib.request, datetime

ARQUIVO_API = "https://archive-api.open-meteo.com/v1/archive"
TZ = "America/Sao_Paulo"
PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico.json")

# uma cidade só: é a referência do canal e evita baixar 10x o mesmo período
CIDADE = ("Volta Redonda", -22.5231, -44.1041)
ANO_INICIO = 1960


def baixar(lat, lon, inicio, fim, timeout=180):
    q = urllib.parse.urlencode({
        "latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}",
        "start_date": inicio, "end_date": fim,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": TZ,
    })
    with urllib.request.urlopen(f"{ARQUIVO_API}?{q}", timeout=timeout) as r:
        return json.loads(r.read().decode())


def construir(dados, cidade):
    """Reduz a série diária a 366 recordes. Devolve o dict pronto pra gravar."""
    d = dados["daily"]
    tabela = {}
    for data, tmax, tmin in zip(d["time"], d["temperature_2m_max"],
                                d["temperature_2m_min"]):
        if tmax is None or tmin is None:
            continue
        chave = data[5:]                       # "MM-DD"
        ano = int(data[:4])
        e = tabela.setdefault(chave, {"frio": None, "calor": None})
        if e["frio"] is None or tmin < e["frio"]["v"]:
            e["frio"] = {"v": round(tmin, 1), "ano": ano}
        if e["calor"] is None or tmax > e["calor"]["v"]:
            e["calor"] = {"v": round(tmax, 1), "ano": ano}
    return {"cidade": cidade, "desde": d["time"][0], "ate": d["time"][-1],
            "dias": tabela,
            "gerado_em": datetime.datetime.now().isoformat(timespec="seconds")}


def carregar(caminho=PADRAO):
    try:
        return json.load(open(caminho))
    except Exception:
        return None


def recorde_do_dia(tabela, data_iso, min_hoje=None, max_hoje=None):
    """Escolhe QUAL recorde contar hoje e devolve no formato que o roteiro usa.

    Comparar "distância até cada recorde" não funciona: num dia de 12°/27° o
    número diz que estamos mais perto do recorde de calor (35°) do que do de
    frio (2°) — mas quem mora aqui viveu uma manhã fria, e é o recorde de frio
    que conversa com o resto do vídeo. Mínima e máxima não são grandezas
    comparáveis desse jeito.

    Então a regra é a mesma que uma pessoa usaria:
      manhã fria  -> conta o frio
      tarde quente-> conta o calor
      dia morno   -> segue a estação (maio a setembro é a seca fria daqui)
    """
    if not tabela:
        return None
    e = tabela.get("dias", {}).get(data_iso[5:])
    if not e:
        return None

    if min_hoje is not None and min_hoje <= 14:
        lado = "frio"
    elif max_hoje is not None and max_hoje >= 31:
        lado = "calor"
    else:
        mes = int(data_iso[5:7])
        lado = "frio" if 5 <= mes <= 9 else "calor"

    alvo = e.get(lado) or e.get("frio") or e.get("calor")
    if not alvo:
        return None
    return {"ano": alvo["ano"], "valor": f"{round(alvo['v'])}°",
            "valor_num": round(alvo["v"]), "lado": lado}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--construir", action="store_true")
    ap.add_argument("--consultar", help='dia no formato MM-DD, ex: 07-29')
    ap.add_argument("--saida", default=PADRAO)
    ap.add_argument("--desde", type=int, default=ANO_INICIO)
    a = ap.parse_args()

    if a.construir:
        nome, lat, lon = CIDADE
        fim = (datetime.date.today() - datetime.timedelta(days=6)).isoformat()
        print(f"baixando {nome} de {a.desde} até {fim} (só 1x; o passado não muda)")
        dados = baixar(lat, lon, f"{a.desde}-01-01", fim)
        tab = construir(dados, nome)
        json.dump(tab, open(a.saida, "w"), ensure_ascii=False)
        print(f"ok: {a.saida} — {len(tab['dias'])} dias do calendário, "
              f"série de {tab['desde']} a {tab['ate']}, "
              f"{os.path.getsize(a.saida)//1024} KB")
        return

    tab = carregar(a.saida)
    if not tab:
        sys.exit(f"{a.saida} não existe. Rode com --construir primeiro.")
    dia = a.consultar or datetime.date.today().strftime("%m-%d")
    e = tab["dias"].get(dia)
    if not e:
        sys.exit(f"sem dados para {dia}")
    print(f"{tab['cidade']} — dia {dia} (série {tab['desde']}..{tab['ate']})")
    print(f"  recorde de frio : {e['frio']['v']}° em {e['frio']['ano']}")
    print(f"  recorde de calor: {e['calor']['v']}° em {e['calor']['ano']}")


if __name__ == "__main__":
    main()
