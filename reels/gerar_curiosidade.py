#!/usr/bin/env python3
"""
gerar_curiosidade.py — o Reel "Mito ou Verdade" de domingo, com os personagens.

Substituiu o carrossel de domingo em 2026-08-23. O motivo está medido no
engajamento.py: carrossel com alcance mediano 4, Reel com alcance mediano 106.
O banco de curiosidades continua o mesmo (src/curiosidades.py, 52 itens) — só
mudou quem conta: os personagens que o público já conhece.

RODÍZIO DE APRESENTADOR
-----------------------
Semana ISO par  -> Seu Ranzinza (varanda, voz pm_alex)
Semana ISO ímpar-> Dona Maria  (quintal ao entardecer, voz pf_dora)
Determinístico pela data, como tudo no projeto: rodar duas vezes no mesmo
domingo dá o mesmo vídeo.

ESCOLHA DA CURIOSIDADE
----------------------
Índice = (dias desde a era // 7) % 52 — avança um item por semana, sem estado
em disco (o workflow dos Reels não commita nada; ver a nota longa no
engajamento.py sobre por que rotação por DATA e não por estado.json).

ESTRUTURA DO VÍDEO (~35s)
-------------------------
1. gancho   — "MITO OU VERDADE?" estala na tela
2. a afirmação, em legenda karaokê (65% assiste sem som)
3. provocação do personagem ("pensa bem...")
4. veredito — faixa vermelha "É MITO!" / "É VERDADE!"
5. explicação
6. o dado regional (Sul Fluminense / RJ)
7. CTA duplo — seguir o perfil E mandar o bairro na DM (hoje + amanhã)

Uso:
    python gerar_curiosidade.py --saida CURIOSIDADE.mp4
    python gerar_curiosidade.py --so-roteiro            # só imprime as batidas
    python gerar_curiosidade.py --personagem maria --indice 3 --so-roteiro
"""
import argparse
import datetime
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, RAIZ)

from gerar_dia import produzir
from src.curiosidades import CURIOSIDADES
import engajamento


# =====================================================================
#  FALAS — cada personagem apresenta do seu jeito
# =====================================================================
ABERTURAS = {
    "ranzinza": [
        "Todo mundo repete isso por aí. Mas será que é verdade?",
        "Aposto que você acredita nisso. Vamos ver se acerta.",
        "Minha avó já dizia isso. E nem tudo que a avó diz é verdade.",
        "Pensa bem antes de responder. A maioria erra, como sempre.",
    ],
    "maria": [
        "Todo mundo fala isso, meu bem. Mas será que é verdade?",
        "O que você acha, meu amor? Pensa comigo antes de responder.",
        "A tia ouviu isso a vida inteira. Hoje a gente tira a dúvida.",
        "Responde aí nos comentários antes de ver o final, viu?",
    ],
}

REVELACAO = {
    "ranzinza": {"MITO": "É mito. Pode parar de repetir isso.",
                 "VERDADE": "É verdade. Dessa vez o povo tem razão."},
    "maria": {"MITO": "É mito, meu bem. Pode contar pra todo mundo.",
              "VERDADE": "É verdade, meu amor. Essa o povo acertou."},
}

FECHOS = {
    "ranzinza": [
        "Acertou? Duvido. Conta nos comentários.",
        "Se você errou, compartilha, que tem mais gente errada por aí.",
        "Domingo que vem tem outra. Infelizmente eu volto.",
        "Manda pra aquele teimoso que vive repetindo isso.",
    ],
    "maria": [
        "Acertou, meu bem? Me conta nos comentários.",
        "Compartilha com quem vive repetindo isso, viu?",
        "Domingo que vem a gente aprende mais uma juntos.",
        "Manda pra família, que essa dúvida é de todo mundo.",
    ],
}

# CTA duplo do fim: SEGUIR + BAIRRO NA DM, sempre os dois — é a regra do
# perfil desde 2026-08-23. A fala diz "mensagem", nunca "DM" (o Kokoro
# soletra sigla; ver gerar_dia.py). O robô responde hoje E amanhã.
CTA_DUPLO = {
    "ranzinza": [
        "Segue o perfil e manda o nome do teu bairro na mensagem. Eu digo como fica hoje e amanhã.",
        "Toca no seguir e escreve o teu bairro na mensagem. Devolvo a previsão de hoje e a de amanhã.",
        "Segue aí e manda o teu bairro por mensagem. Respondo hoje e amanhã, contrariado.",
        "Segue o perfil e manda o bairro na mensagem. Aí o amanhã não te pega de surpresa.",
    ],
    "maria": [
        "Segue o perfil, meu bem, e manda o nome do teu bairro na mensagem. Te digo como fica hoje e amanhã.",
        "Aperta o seguir e me escreve o teu bairro, meu amor. Vai a previsão de hoje e a de amanhã.",
        "Segue a gente e manda o bairro numa mensagem. A tia responde hoje e amanhã, rapidinho.",
        "Toca no seguir, meu bem, e manda o teu bairro na mensagem. Volta a de hoje e a de amanhã.",
    ],
}


def personagem_da_semana(data=None):
    """Semana ISO par = Ranzinza, ímpar = Dona Maria. Determinístico."""
    d = data or datetime.date.today()
    return "ranzinza" if d.isocalendar()[1] % 2 == 0 else "maria"


def curiosidade_da_semana(data=None, indice=None):
    """Um item por semana, rodando o banco inteiro em 52 semanas, sem estado."""
    if indice is not None:
        return CURIOSIDADES[indice % len(CURIOSIDADES)], indice % len(CURIOSIDADES)
    d = data or datetime.date.today()
    i = (d.toordinal() // 7) % len(CURIOSIDADES)
    return CURIOSIDADES[i], i


def montar_roteiro(item, personagem, data=None):
    d = data or datetime.date.today()
    rnd = random.Random(d.toordinal())
    veredito = item["veredito"].strip().upper()
    batidas = []

    def add(fala, legenda=None, tipo="nenhum", **dd):
        batidas.append({"fala": fala,
                        "legenda": legenda if legenda is not None else fala,
                        "tipo": tipo, "dados": dd})

    # 1. gancho — o cartaz estala; a afirmação vem NA PRÓXIMA batida, em
    # legenda karaokê (o gancho não leva legenda, e afirmação encolhida
    # dentro do cartaz não se lê no celular)
    add("Mito ou verdade?", "MITO OU VERDADE?", tipo="gancho",
        numero="MITO OU VERDADE?", sub="responde aí embaixo", cor="normal")

    # 2. a afirmação
    add(item["titulo"])

    # 3. provocação
    add(rnd.choice(ABERTURAS[personagem]))

    # 4. veredito — faixa vermelha no topo + fala curta
    add(REVELACAO[personagem][veredito], f"É {veredito}!",
        tipo="fecho", texto=f"É {veredito}!")

    # 5. explicação
    add(item["explicacao"])

    # 6. o dado regional, quando existir
    if item.get("regional"):
        add(item["regional"])

    # 7. fecho + CTA duplo (seguir + bairro)
    add(rnd.choice(FECHOS[personagem]))
    add(rnd.choice(CTA_DUPLO[personagem]), tipo="cta",
        chamada="SEGUE + BAIRRO NA DM",
        sub="manda o nome e recebe hoje + amanhã")
    return batidas


def montar_legenda(item, data=None):
    """A legenda do post NÃO entrega o veredito — quem quer saber assiste."""
    d = data or datetime.date.today()
    linhas = [
        "🧠 MITO ou VERDADE?",
        "",
        f"“{item['titulo']}”",
        "",
        "Responde nos comentários ANTES de ver o final do vídeo 👇",
        "",
        engajamento.chamada_bairro("manha", d),
        "",
        engajamento.hashtags("manha", "sol"),
    ]
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="CURIOSIDADE.mp4")
    ap.add_argument("--personagem", choices=["auto", "ranzinza", "maria"],
                    default="auto")
    ap.add_argument("--indice", type=int, default=None,
                    help="força um item do banco (0-51); padrão: o da semana")
    ap.add_argument("--quality", default="m")
    ap.add_argument("--so-roteiro", action="store_true",
                    help="imprime as batidas e a legenda e sai, sem renderizar")
    a = ap.parse_args()

    hoje = datetime.date.today()
    personagem = (personagem_da_semana(hoje) if a.personagem == "auto"
                  else a.personagem)
    item, indice = curiosidade_da_semana(hoje, a.indice)

    print(f"[curiosidade] item {indice}: {item['titulo']!r} "
          f"({item['veredito']}) — apresenta: {personagem}")
    batidas = montar_roteiro(item, personagem, hoje)
    for b in batidas:
        print(f'   [{b["tipo"]:8s}] {b["fala"]}')

    legenda = montar_legenda(item, hoje)
    open(os.path.join(AQUI, "LEGENDA.txt"), "w", encoding="utf-8").write(
        legenda + "\n")
    print("--- LEGENDA.txt ---")
    print(legenda)
    if a.so_roteiro:
        return

    if personagem == "maria":
        produzir(batidas, a.saida, cenario="entardecer", personagem="maria",
                 cenario_tipo="quintal", quality=a.quality,
                 voz="pf_dora", pitch=0.94,
                 extra={"data": hoje.isoformat(), "vento_visual": 0.7})
    else:
        produzir(batidas, a.saida, cenario="sol", personagem="ranzinza",
                 cenario_tipo="varanda", quality=a.quality,
                 voz="pm_alex", pitch=0.88,
                 extra={"data": hoje.isoformat()})


if __name__ == "__main__":
    main()
