# -*- coding: utf-8 -*-
"""
gerar_juarez.py — o Reel ÚNICO das 06h, com o Juarez Plantão.

O QUE ESTE ARQUIVO SUBSTITUI
----------------------------
Até 2026-09-04 o perfil publicava dois Reels por dia: o Seu Ranzinza às 06h10 e
a Dona Maria às 18h00, os dois pelo `ranzinza.yml`. O plano v3 troca isso por um
só, às 06h, na voz do Juarez, em dois modos — e é este arquivo que faltava pra
que o desligamento dos outros dois não deixasse o perfil com ZERO Reels por dia.

O `gerar_dia.py` e o `gerar_tarde.py` continuam inteiros e funcionando: o
experimento é de 14 dias e pode dar errado. Voltar atrás é descomentar dois
crons, não recuperar código apagado.

OS DOIS MODOS
-------------
Quem decide não é este arquivo: é o `modo_do_dia()` do `limiares.py`, na raiz.

  ROTINA — o dia comum, que é a esmagadora maioria deles. Abre pelo número mais
           extremo do dia, lê as três maiores e diz se chove.
  ALERTA  — só quando um dos cinco limiares diários foi cruzado. Abre pelo
           cartaz vermelho, diz onde, e traz uma instrução do que fazer.

Os dois terminam igual: o CTA do dia (alternado por paridade) e, depois dele, o
FECHO_CANAL — "Siga o canal para não ser pego de surpresa" —, que é a última
fala de todo Reel e nunca muda.

A meta declarada no plano é no máximo 2 alertas em 14 dias
(`ALERTAS_ESPERADOS_EM_14_DIAS`). Se sair mais que isso, o problema são os
limiares, não o dia — e eles se mexem num arquivo só.

POR QUE 18-22 SEGUNDOS
----------------------
A métrica do experimento é skip rate, e o vídeo do Ranzinza era longo demais
pro que ele entrega. O resumo aqui lê TRÊS cidades, não cinco — é o corte que
paga os segundos. `estimar_segundos()` calcula a duração antes de gastar dois
minutos de Kokoro e render; o teste do repositório trava a faixa.

VOZ
---
`pm_santa`, speed 1.05, SEM pitch pra baixo — ele não é idoso como os outros
dois, é locutor. No lugar do pitch, a cadeia de masterização de locutor
(`FILTRO_LOCUTOR` no gerar_dia.py). Tudo isso vem da skill `juarez-plantao`,
onde a voz dele já foi ao ar.

CUIDADO COM SIGLA: o espeak-ng (fonetizador do Kokoro) soletra letra por letra
qualquer palavra toda em maiúscula — "PIX" vira "p-i-xis". Nas FALAS, escreva
"Pix", "Med". Nas LEGENDAS pode ser caixa alta à vontade: elas não são faladas.

Uso:
    python gerar_juarez.py --dados dia.json --saida REEL.mp4
    python gerar_juarez.py --demo --so-roteiro     # imprime e não renderiza
"""
import argparse
import json
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, RAIZ)

from coletar_tempo import resumo_cinco
from gerar_dia import (produzir, num_extenso, FILTRO_LOCUTOR,
                       escolher_gancho, maiusculizar_frase)
from limiares import (alerta_do_dia, chove_de_verdade, conferir_gancho,
                      conferir_manchete, extremos, manchete, modo_do_dia)

# Três, não cinco. Ver "POR QUE 18-22 SEGUNDOS" no topo.
N_RESUMO_JUAREZ = 3

# Faixa-alvo do plano v3. `estimar_segundos()` avisa quando o roteiro sai fora;
# não aborta, porque um dia com nome de cidade comprido não é um bug.
DUR_MIN, DUR_MAX = 18.0, 22.0

# Ritmo do Kokoro com pm_santa a --speed 1.05. Começou em 2,9 (medido pelos
# vídeos da skill) e desceu pra 2,82 em 2026-09-05, depois do primeiro render
# de verdade: o `ffprobe` do workflow mediu 19,2s num roteiro que a conta dizia
# 18,6s — a narração real gasta ~3% a mais que a estimativa.
#
# Baixar o número faz a conta ERRAR PRA CIMA, e é assim que ela tem que errar:
# o teste do repositório trava a faixa de 18-22s, e é melhor ele reclamar de um
# roteiro que caberia do que deixar passar um que estoura no ar.
PALAVRAS_POR_SEGUNDO = 2.82
GAP_ENTRE_BATIDAS = 0.25


# =====================================================================
#  FALAS — voz dele: locutor de plantão, gravidade sem motivo
# =====================================================================
# Curtíssimas de propósito: o gancho é a batida mais cara do vídeo em atenção
# e a mais barata em segundos. Cada palavra de cerimônia aqui sai de algum
# lugar que informa — e o orçamento inteiro é de 18 a 22 segundos.
ABERTURAS = [
    "Plantão das seis.",
    "Boletim das seis.",
    "Plantão da previsão.",
]

# O que ele diz DEPOIS do gancho, em dia comum. Curtas: o gancho já gastou o
# tempo da abertura, e o resumo é a batida longa.
CONFIRMACOES = [
    "É o quadro do dia.",
    "Números confirmados.",
    "É o que está previsto.",
    "Anotem.",
]

INTRO_RESUMO_JUAREZ = [
    "Nas três maiores:",
    "Situação nas três maiores:",
    "Acompanhem:",
]

SEM_CHUVA = [
    "Chuva, nenhuma. Varal liberado.",
    "Sem chuva prevista. Repito, nenhuma.",
    "Nada de chuva hoje.",
]

# Instrução do modo alerta, por tipo. É a única batida do Reel que pede uma
# AÇÃO — em dia comum ela não existe, e é essa diferença que faz o modo alerta
# valer alguma coisa quando aparece.
#
# Encurtadas em 2026-09-05, quando o FECHO_CANAL entrou: com seis batidas o
# orçamento ficou apertado, e a instrução é onde cabia cortar sem perder o que
# a pessoa precisa FAZER. "Fundo de vale alaga" continua lá; o que saiu foi a
# explicação de por que alaga.
INSTRUCAO = {
    "chuva": "Saiam mais cedo. Fundo de vale alaga.",
    "rajada": "Recolham o que está solto no quintal.",
    "calor": "Bebam água antes de ter sede. Evitem o sol.",
    "frio": "Separem agasalho para quem sai cedo.",
    "umidade": "Bebam água. Evitem exercício ao ar livre.",
}

CARTAZ = {
    "chuva": "ALERTA DE CHUVA",
    "rajada": "ALERTA DE VENTO",
    "calor": "ALERTA DE CALOR",
    "frio": "ALERTA DE FRIO",
    "umidade": "ALERTA DE AR SECO",
}

# CTA ALTERNADO POR PARIDADE DO DIA (plano v3). Não é sorteio: alternar por
# paridade garante que os dois CTAs saem o mesmo número de vezes nos 14 dias do
# experimento. Com sorteio, uma sequência azarada mediria um CTA só.
CTA_PAR = ("Teu bairro, na mensagem.",
           "TEU BAIRRO NA DM", "manda o nome e recebe a previsão do teu canto")
CTA_IMPAR = ("Salva aí, pra conferir depois.",
             "SALVA PRA CONFERIR", "o dia inteiro cabe em vinte segundos")

# O FECHO FIXO — a última fala de TODO Reel, nos dois modos.
#
# É a única linha do roteiro que não muda nunca: o CTA de cima alterna por
# paridade porque é a variável que o experimento mede, e este aqui é constante
# justamente pra não ser variável nenhuma. Pedir pra seguir uma vez, no fim de
# um vídeo, todo dia, é o que constrói o hábito — alternar isso mediria ruído.
#
# "não ser pego de surpresa" fecha o argumento do canal inteiro: o Juarez é um
# plantão, e a razão de seguir um plantão é não ser pego de surpresa. Por isso
# ele vem DEPOIS do pedido do dia, e não no lugar dele.
FECHO_CANAL = ("Siga o canal para não ser pego de surpresa.",
               "SEGUE O CANAL", "pra não ser pego de surpresa")


def estimar_segundos(batidas):
    """Duração aproximada do vídeo, antes de gastar Kokoro e render.

    Conta palavras porque é o que a narração gasta tempo dizendo. Não é exata —
    nome de cidade comprido e número por extenso pesam mais que a média — mas
    erra por pouco e erra sempre para o mesmo lado, que é o que basta pra saber
    se o roteiro está perto da faixa antes de rodar dois minutos de pipeline.
    """
    palavras = sum(len(b["fala"].split()) for b in batidas)
    return palavras / PALAVRAS_POR_SEGUNDO + GAP_ENTRE_BATIDAS * max(0, len(batidas) - 1)


def cta_do_dia(data):
    """(fala, chamada, sub) alternando por paridade do dia do mês."""
    dia_do_mes = int((data or "2026-01-01")[-2:])
    return CTA_PAR if dia_do_mes % 2 == 0 else CTA_IMPAR


def montar_roteiro(dados):
    """As batidas do Reel do Juarez, no modo que o dado autorizar.

    Mesma forma de batida dos outros dois geradores ({fala, legenda, tipo,
    dados}), porque o `piloto.py` é o mesmo — o que muda é o personagem, o
    cenário e quais painéis entram.
    """
    cid = dados["cidades"]
    rnd = random.Random(int(dados["data"].replace("-", "")))
    batidas = []

    def add(fala, legenda=None, tipo="nenhum", **dd):
        fala = maiusculizar_frase(fala)
        batidas.append({"fala": fala,
                        "legenda": legenda if legenda is not None else fala,
                        "tipo": tipo, "dados": dd})

    # --- QUE DIA É HOJE: a única porta é o limiares.py ------------------
    modo = modo_do_dia(dados)
    texto_manchete, _ = manchete(dados)
    conferir_manchete(dados, texto_manchete)
    chave, motivo, cidade_alerta = alerta_do_dia(dados)

    if modo == "alerta":
        # 1. O CARTAZ. É ele o gancho: em dia de alerta o número não precisa
        #    competir com nada, e o vermelho na tela é mais rápido de ler que
        #    qualquer algarismo.
        add(f"Atenção. {CARTAZ[chave].capitalize()}.",
            CARTAZ[chave], tipo="alerta",
            titulo=CARTAZ[chave], detalhe=motivo.lower(),
            modo=modo, manchete=texto_manchete)
        # 2. ONDE e QUANTO — o dado que sustenta o cartaz
        add(_fala_do_motivo(chave, dados, cidade_alerta),
            motivo, tipo="gancho", numero=_numero_do_motivo(chave, dados),
            sub=(cidade_alerta or "NA REGIÃO").upper(), cor="alerta")
    else:
        # 1. GANCHO: o número mais extremo do dia, estalando na tela. A régua
        #    é a mesma dos outros dois vídeos (GANCHO_* do limiares.py).
        fala_g, num_g, sub_g, cor_g = escolher_gancho(cid, dados.get("umidade_min"), rnd)
        conferir_gancho(cid, cor_g)
        add(f"{rnd.choice(ABERTURAS)} {fala_g}", num_g, tipo="gancho",
            numero=num_g, sub=sub_g, cor=cor_g,
            modo=modo, manchete=texto_manchete)
        # 2. a confirmação de plantão — o tom do personagem, em uma linha
        add(rnd.choice(CONFIRMACOES))

    # --- 3. AS TRÊS MAIORES: o corpo do vídeo --------------------------
    resumo = resumo_cinco(cid, n=N_RESUMO_JUAREZ)
    if len(resumo) > 1:
        corpo = " ".join(f"{c['nome']}, {num_extenso(c['min'])} a "
                         f"{num_extenso(c['max'])}." for c in resumo)
        legenda = " · ".join(f"{c['nome']} {c['min']}/{c['max']}°" for c in resumo)
        add(f"{rnd.choice(INTRO_RESUMO_JUAREZ)} {corpo}", legenda,
            tipo="resumo", cidades=resumo, titulo="AS TRÊS MAIORES")

    # --- 4. A LINHA DO DIA ---------------------------------------------
    if modo == "alerta":
        # em dia de alerta, a batida útil é o que fazer — não o acumulado, que
        # o cartaz já disse
        add(INSTRUCAO[chave], tipo="nenhum")
    elif not any(chove_de_verdade(c) for c in cid):
        add(rnd.choice(SEM_CHUVA), tipo="sem_chuva")
    else:
        pico = max(cid, key=lambda c: c.get("chuva_mm", 0) or 0)
        add(f"Chuva prevista: até {num_extenso(round(pico['chuva_mm']))} "
            f"milímetros em {pico['nome']}.",
            f"Chuva: até {pico['chuva_mm']}mm em {pico['nome']}.",
            tipo="chuva", cidade=pico)

    # --- 5. CTA, alternado por paridade --------------------------------
    fala_cta, chamada, sub = cta_do_dia(dados.get("data"))
    add(fala_cta, chamada, tipo="cta", chamada=chamada, sub=sub)

    # --- 6. O FECHO: a última coisa dita, todo dia, nos dois modos --------
    fala_f, chamada_f, sub_f = FECHO_CANAL
    add(fala_f, chamada_f, tipo="cta", chamada=chamada_f, sub=sub_f)
    return batidas


def _fala_do_motivo(chave, dados, cidade):
    """A batida que diz ONDE e QUANTO, na voz dele."""
    e = extremos(dados)
    onde = f" em {cidade}" if cidade else " na região"
    if chave == "chuva":
        return f"{num_extenso(round(e['chuva']))} milímetros{onde}, num dia só."
    if chave == "rajada":
        return (f"Rajadas de {num_extenso(round(e['rajada']))} "
                f"quilômetros por hora.")
    # sem "máxima de" / "mínima de": o cartaz na tela ja diz CALOR ou FRIO e o
    # numero grande esta do lado dele. A fala repetiria o que os olhos leem.
    if chave == "calor":
        return f"{num_extenso(round(e['max']))} graus{onde}."
    if chave == "frio":
        return f"{num_extenso(round(e['min']))} graus{onde}."
    return f"Umidade em {num_extenso(round(e['umidade']))} por cento."


def _numero_do_motivo(chave, dados):
    """O número grande que vai na tela junto do cartaz."""
    e = extremos(dados)
    return {"chuva": f"{round(e['chuva'])}mm",
            "rajada": f"{round(e['rajada'])}km/h",
            "calor": f"{round(e['max'])}°",
            "frio": f"{round(e['min'])}°",
            "umidade": f"{round(e['umidade'])}%"}[chave]


def gerar(dados, saida, quality="m"):
    """Do dia.json ao MP4."""
    batidas = montar_roteiro(dados)
    dur = estimar_segundos(batidas)
    for b in batidas:
        print(f'     [{b["tipo"]:9s}] {b["fala"]}')
    aviso = "" if DUR_MIN <= dur <= DUR_MAX else "   <-- FORA DA FAIXA 18-22s"
    print(f"     duração estimada: {dur:.1f}s{aviso}")
    return produzir(
        batidas, saida,
        # o Juarez fala de dentro do estúdio: o cenário não muda com o tempo lá
        # fora, e é isso que o `cenario_tipo` diz ao piloto.py
        cenario="sol", calor=False,
        personagem="juarez", cenario_tipo="estudio",
        quality=quality, voz="pm_santa",
        speed=1.05, gap=GAP_ENTRE_BATIDAS, filtro=FILTRO_LOCUTOR,
        extra={"data": dados["data"],
               "destaque": dados.get("destaque") or dados["cidades"][0]["nome"],
               "destaque_rotulo": "HOJE EM"})


DEMO = {
    "data": "2026-09-08",
    "cidades": [
        {"nome": "Quatis", "min": 15, "max": 27, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Volta Redonda", "min": 16, "max": 28, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Barra Mansa", "min": 16, "max": 28, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Resende", "min": 14, "max": 26, "cond": "nublado", "chuva_mm": 0.4},
    ],
    "umidade_min": 55,
    "destaque": "Quatis",
}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados")
    ap.add_argument("--saida", default="REEL.mp4")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--quality", default="m")
    ap.add_argument("--so-roteiro", action="store_true",
                    help="imprime o roteiro e a duração estimada, sem renderizar")
    a = ap.parse_args()
    d = DEMO if a.demo or not a.dados else json.load(open(a.dados))
    if a.so_roteiro:
        bat = montar_roteiro(d)
        for b in bat:
            print(f'[{b["tipo"]:9s}] {b["fala"]}')
            if b["legenda"] != b["fala"]:
                print(f'{"":11s} tela: {b["legenda"]}')
        print(f'\nmodo: {modo_do_dia(d)} | batidas: {len(bat)} | '
              f'duração estimada: {estimar_segundos(bat):.1f}s')
    else:
        gerar(d, a.saida, a.quality)
