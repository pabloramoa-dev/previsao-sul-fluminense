# -*- coding: utf-8 -*-
"""
limiares.py — fonte única dos limiares que decidem O QUE o perfil publica.

Existe porque a mesma pergunta ("hoje é dia de alerta?", "isso é chuva?")
estava respondida em três lugares com números diferentes: `gerar_dia.py`,
`src/alertas.py` e a legenda do `postar_reel.py`. Divergiram, e o resultado
foi post prometendo chuva com 0,2 mm no dado (07/08 e 12/08 de 2026).

Mora na RAIZ do repositório de propósito: é importado tanto pelo bot de
imagens (`src/`) quanto pelos Reels (`reels/`), que rodam de diretórios
diferentes. Quem está em `reels/` insere a raiz no `sys.path` antes de
importar — ver o topo do `gerar_dia.py`.

DOIS RELÓGIOS, NÃO UM
---------------------
Os limiares aqui embaixo respondem a duas perguntas que parecem a mesma e
não são:

  DIÁRIOS     — leem a previsão fechada do dia (máx, mín, acumulado). É o que
                decide o MODO do Reel das 06h: rotina ou alerta. Um dia inteiro
                cabe num número.
  INTRADIÁRIOS— leem a série horária das próximas 3h. É o que o monitor de
                alertas usa pra avisar de coisa que ninguém viu de manhã.

Um não substitui o outro: 12 mm em três horas é temporal e não chega perto dos
20 mm/dia; 20 mm espalhados em vinte e quatro horas é um dia chuvoso sem
nenhuma hora dramática. Os dois blocos ficam no mesmo arquivo pra que mudar a
régua do perfil seja mexer num lugar só — não porque sejam o mesmo número.
"""

# =====================================================================
#  DIÁRIOS — decidem o modo do Reel (seção 3 do plano v3)
# =====================================================================
# Nenhum destes é discricionário. Se nenhum for cruzado, o painel de alerta
# NÃO pode ser usado, por mais tentador que o dia pareça — é essa a trava.
ALERTA_CHUVA_MM = 20.0        # acumulado do dia
ALERTA_RAJADA_KMH = 50.0      # rajada máxima (wind_gusts_10m_max, não a média)
ALERTA_TEMP_MAX_C = 37.0
ALERTA_TEMP_MIN_C = 8.0
ALERTA_UMIDADE_PCT = 20.0     # umidade relativa MÍNIMA do dia

# Meta declarada no plano: no máximo 2 alertas em 14 dias. Não é uma trava —
# é a régua pra saber se os limiares acima estão frouxos. Se o experimento
# fechar com mais que isso, o problema são os números, não o dia.
ALERTAS_ESPERADOS_EM_14_DIAS = 2

# Um dia só é "de chuva" acima disto. O código WMO marca "chuva" numa garoa de
# 0,2 mm; foi daí que veio a contradição entre o roteiro e a legenda.
LIMIAR_CHUVA_MM = 1.0

# Cascata da manchete (seção 5). Avaliada de cima para baixo.
MANCHETE_CALOR_C = 33.0
MANCHETE_FRIO_C = 14.0
MANCHETE_SECO_PCT = 30.0

# =====================================================================
#  INTRADIÁRIOS — monitor de alertas, janela de 3h (src/alertas.py)
# =====================================================================
DELTA_TEMP = 6.0              # variação contra a leitura anterior
PROB_CHUVA_FORTE = 70.0       # % de probabilidade
MM_CHUVA_FORTE = 10.0         # acumulado em 3h
VENTO_FORTE = 50.0            # velocidade nas próximas 3h
MM_ACUMULADO_24H = 30.0       # gatilho do "choveu quanto"


# =====================================================================
#  LEITURA DO DIA
# =====================================================================
def _num(v, padrao=0.0):
    """Número ou o padrão. A API devolve None em campo indisponível."""
    try:
        return float(v) if v is not None else padrao
    except (TypeError, ValueError):
        return padrao


def extremos(dia):
    """Os números do dia que interessam às duas decisões abaixo.

    Regionais, não da cidade em destaque: o perfil cobre dez municípios e
    fala deles como uma região — é assim que `escolher_gancho()` já se comporta
    desde sempre. Um alerta que valesse só pra cidade sorteada do dia deixaria
    o temporal de Resende de fora porque hoje calhou de ser a vez de Quatis.
    """
    cidades = (dia or {}).get("cidades") or []
    if not cidades:
        # min = 99 e não 0: sem dado nenhum, o dia não pode disparar o alerta
        # de frio. Zero aqui faria "sem cidades" virar alerta de 0 grau.
        return {"max": 0.0, "min": 99.0, "chuva": 0.0, "rajada": 0.0,
                "umidade": None, "cidade_max": None, "cidade_min": None,
                "cidade_chuva": None}
    q = max(cidades, key=lambda c: _num(c.get("max")))
    f = min(cidades, key=lambda c: _num(c.get("min"), 99))
    ch = max(cidades, key=lambda c: _num(c.get("chuva_mm")))
    rajadas = [_num(c.get("rajada_kmh")) for c in cidades]
    return {
        "max": _num(q.get("max")),
        "min": _num(f.get("min"), 99),
        "chuva": _num(ch.get("chuva_mm")),
        # rajada por cidade é campo novo; o `rajada_max` do dia cobre os
        # dia.json gerados antes dele existir
        "rajada": max(rajadas + [_num((dia or {}).get("rajada_max"))]),
        "umidade": (None if (dia or {}).get("umidade_min") is None
                    else _num(dia.get("umidade_min"))),
        "cidade_max": q.get("nome"),
        "cidade_min": f.get("nome"),
        "cidade_chuva": ch.get("nome"),
    }


# =====================================================================
#  MODO DO REEL — seção 3
# =====================================================================
def motivo_do_alerta(dia):
    """O motivo do alerta, ou None se nenhum limiar foi cruzado.

    Devolve o texto curto que vai na manchete depois de "ALERTA — ". A ordem
    é por gravidade: o que manda alguém mudar o dia vem antes do desconforto.
    """
    e = extremos(dia)
    if e["chuva"] >= ALERTA_CHUVA_MM:
        return f"CHUVA DE {round(e['chuva'])}MM"
    if e["rajada"] >= ALERTA_RAJADA_KMH:
        return f"VENTO DE {round(e['rajada'])}KM/H"
    if e["max"] >= ALERTA_TEMP_MAX_C:
        return f"CALOR DE {round(e['max'])} GRAUS"
    if e["min"] <= ALERTA_TEMP_MIN_C:
        return f"FRIO DE {round(e['min'])} GRAUS"
    if e["umidade"] is not None and e["umidade"] <= ALERTA_UMIDADE_PCT:
        return f"AR A {round(e['umidade'])}% DE UMIDADE"
    return None


def modo_do_dia(dia):
    """"alerta" ou "rotina". É esta função que autoriza o painel_alerta().

    Nenhum caminho discricionário: quem quiser publicar em modo alerta num dia
    comum tem que mexer nos limiares lá em cima, onde a mudança fica registrada
    no diff — e não na hora de montar o vídeo.
    """
    return "alerta" if motivo_do_alerta(dia) else "rotina"


# =====================================================================
#  MANCHETE DO PRIMEIRO FRAME — seção 5
# =====================================================================
def manchete(dia):
    """(texto, modo) da manchete. Primeira condição verdadeira vence."""
    motivo = motivo_do_alerta(dia)
    if motivo:
        return f"ALERTA — {motivo}", "alerta"
    e = extremos(dia)
    if e["chuva"] >= LIMIAR_CHUVA_MM:
        return "HOJE CHOVE", "rotina"
    if e["max"] >= MANCHETE_CALOR_C:
        return f"HOJE FAZ {round(e['max'])}°", "rotina"
    if e["min"] <= MANCHETE_FRIO_C:
        return "HOJE ESFRIA", "rotina"
    if e["umidade"] is not None and e["umidade"] <= MANCHETE_SECO_PCT:
        return "AR SECO HOJE", "rotina"
    return "HOJE NÃO CHOVE", "rotina"


def conferir_manchete(dia, texto):
    """Aborta se a manchete e o dado se contradizem.

    A trava que faltava em agosto: dizer CHOVE com acumulado zero. Roda antes
    de renderizar e antes de publicar — nas duas pontas, porque a manchete
    aparece no primeiro frame do vídeo E na primeira linha da legenda.
    """
    e = extremos(dia)
    t = (texto or "").upper()
    if "CHOVE" in t and "NÃO CHOVE" not in t and e["chuva"] < LIMIAR_CHUVA_MM:
        raise SystemExit(
            f"INCOERÊNCIA: manchete {texto!r} com acumulado máximo de "
            f"{e['chuva']}mm (limiar: {LIMIAR_CHUVA_MM}mm). Publicação bloqueada.")
    if "NÃO CHOVE" in t and e["chuva"] >= ALERTA_CHUVA_MM:
        raise SystemExit(
            f"INCOERÊNCIA: manchete {texto!r} com {e['chuva']}mm previstos. "
            f"Publicação bloqueada.")
    if t.startswith("ALERTA") and modo_do_dia(dia) != "alerta":
        raise SystemExit(
            "INCOERÊNCIA: manchete de alerta sem nenhum limiar cruzado. "
            "Publicação bloqueada.")
