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

# GANCHO do vídeo — qual número abre o Reel nos primeiros 1,5s. É uma pergunta
# DIFERENTE das duas de cima ("o dia é de alerta?", "o que a manchete diz?"):
# aqui a resposta é só "qual dos quatro números choca mais quem mora aqui".
# Subiram pra cá em 2026-09-04 porque estavam escritos QUATRO vezes — uma no
# escolher_gancho() do gerar_dia.py, outra no do gerar_tarde.py, e o docstring
# do segundo prometia que os dois consideravam "extremo" a mesma coisa sem
# nada no código garantir isso. Bastava alguém mexer num pra o Ranzinza das
# 06h abrir com o frio e a Dona Maria das 18h abrir com a chuva do mesmo dado.
GANCHO_FRIO_C = 11.0
GANCHO_CALOR_C = 32.0
GANCHO_CHUVA_MM = 10.0
GANCHO_SECO_PCT = 30.0

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
#  É DIA DE CHUVA? — a pergunta que o vídeo E a legenda fazem
# =====================================================================
def chove_de_verdade(cidade):
    """O dia é de chuva NESTA cidade? Código WMO e acumulado têm que concordar.

    Morava no `gerar_dia.py`, com uma cópia própria do `LIMIAR_CHUVA_MM`, até
    2026-09-04. Subiu pra cá junto com o número que ela lê: enquanto os dois
    viviam lá embaixo, este arquivo era a fonte única só pro `src/alertas.py`
    — o caminho dos Reels (`gerar_dia` -> `gerar_tarde` -> `postar_reel`)
    tinha o seu próprio 1.0, e mudar a régua aqui em cima não mudava nem o
    vídeo nem a legenda. Era a mesma divergência de agosto montada de novo,
    só que armada e ainda não disparada.

    Quem importava do `gerar_dia` continua importando de lá: o nome segue
    exportado por ele. O que mudou é de ONDE ele vem.
    """
    return (cidade.get("cond") in ("chuva", "tempestade")
            and _num(cidade.get("chuva_mm")) >= LIMIAR_CHUVA_MM)


def conferir_gancho(cidades, cor):
    """Aborta se o GANCHO do vídeo promete chuva e o dado não sustenta.

    Irmã da `validar_coerencia()` do `postar_reel.py`, do lado do roteiro. A
    legenda ganhou a trava dela no PR #18; o vídeo ficou sem nenhuma — e o
    gancho é a única batida que decide por acumulado PURO (>= GANCHO_CHUVA_MM)
    sem olhar o código WMO.

    Basta uma previsão de 12 mm codificada como neve ou granizo (WMO 71-77,
    que `condicao()` traduz como "frio", não como "chuva") pra que o Reel abra
    com "Vem chuva, doze milímetros" e feche, seis batidas depois, com "Chuva
    nenhuma" — porque a batida final lê `chove_de_verdade()` e o gancho não
    lia. É a contradição de 07/08 e 12/08 outra vez, agora dentro do MP4, onde
    a trava da legenda não alcança.
    """
    if cor != "chuva":
        return
    if not any(chove_de_verdade(c) for c in (cidades or [])):
        pico = max([_num(c.get("chuva_mm")) for c in (cidades or [])] or [0.0])
        raise SystemExit(
            f"INCOERÊNCIA: o gancho do vídeo promete chuva e nenhuma cidade "
            f"tem código de chuva com {LIMIAR_CHUVA_MM}mm ou mais "
            f"(pico: {pico}mm). Renderização abortada.")


# =====================================================================
#  MODO DO REEL — seção 3
# =====================================================================
def alerta_do_dia(dia):
    """(chave, texto, cidade) do alerta, ou (None, None, None).

    A CASCATA MORA SÓ AQUI. A ordem é por gravidade: o que manda alguém mudar
    o dia vem antes do desconforto.

    Devolve a `chave` além do texto porque quem monta o Reel precisa saber QUE
    TIPO de alerta é pra escolher o cartaz e a instrução ("feche as janelas" não
    serve pra onda de calor). Sem isso o roteiro teria que reavaliar os mesmos
    cinco limiares por conta própria — e uma segunda cascata, escrita à mão em
    outro arquivo, é exatamente a doença que este arquivo existe pra curar.
    """
    e = extremos(dia)
    if e["chuva"] >= ALERTA_CHUVA_MM:
        return "chuva", f"CHUVA DE {round(e['chuva'])}MM", e["cidade_chuva"]
    if e["rajada"] >= ALERTA_RAJADA_KMH:
        return "rajada", f"VENTO DE {round(e['rajada'])}KM/H", None
    if e["max"] >= ALERTA_TEMP_MAX_C:
        return "calor", f"CALOR DE {round(e['max'])} GRAUS", e["cidade_max"]
    if e["min"] <= ALERTA_TEMP_MIN_C:
        return "frio", f"FRIO DE {round(e['min'])} GRAUS", e["cidade_min"]
    if e["umidade"] is not None and e["umidade"] <= ALERTA_UMIDADE_PCT:
        return "umidade", f"AR A {round(e['umidade'])}% DE UMIDADE", None
    return None, None, None


def motivo_do_alerta(dia):
    """Só o texto do alerta, ou None. É o que entra na manchete depois de
    "ALERTA — ". Fina por cima de `alerta_do_dia()`, que tem a cascata."""
    return alerta_do_dia(dia)[1]


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
