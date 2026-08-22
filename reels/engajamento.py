# -*- coding: utf-8 -*-
"""
engajamento.py — hashtags rotativas e pergunta fechada para as legendas dos Reels.

POR QUE ISTO EXISTE
-------------------
A máquina de engajamento do projeto (rotação de hashtags, banco de perguntas
fechadas, ganchos) foi construída em `src/` para os carrosséis de feed — o
formato que, medido de 25/07 a 13/08/2026, entregou alcance mediano 4 e zero
interação em 35 de 37 posts. Enquanto isso os Reels, que entregam alcance
mediano 106, saíam com a MESMA string de 10 hashtags todo dia e um CTA aberto
("comenta aí"), e 20 dos 33 ficaram em zero interação.

Este módulo leva as duas técnicas para o lado que tem distribuição.

SEM ESTADO, DE PROPÓSITO
------------------------
O `src/perguntas.py` roda a rotação gravando em `estado.json` e o workflow dos
carrosséis commita o arquivo de volta. O workflow dos Reels não commita nada —
um estado em disco seria descartado a cada job e a rotação repetiria sempre o
primeiro item. Aqui a escolha é derivada da DATA: sem arquivo, sem commit, e
ainda reproduzível (rodar de novo no mesmo dia dá a mesma legenda).

A regra manhã≠noite do mesmo dia é mantida — é o motivo de o slot entrar no
cálculo do índice.
"""
from __future__ import annotations

import datetime as _dt
import unicodedata as _unicodedata

SLOTS = ("manha", "noite")

# 5 conjuntos: 3 cidade + 3 tema + 2 região. As cidades são as 6 do rodapé do
# perfil — Angra dos Reis, que aparecia nos carrosséis, ficou de fora: não está
# na bio, não está nos Reels e não é Sul Fluminense.
CONJUNTOS = [
    ["#voltaredonda", "#barramansa", "#resende",
     "#previsaodotempo", "#climatempo", "#tempoagora",
     "#sulfluminense", "#interiordorj"],
    ["#portoreal", "#barradopirai", "#pirai",
     "#meteorologia", "#chuva", "#calor",
     "#regiaodovale", "#riodejaneiro"],
    ["#voltaredonda", "#resende", "#pirai",
     "#previsao", "#temperatura", "#frio",
     "#sulfluminense", "#valedoparaiba"],
    ["#barramansa", "#portoreal", "#itatiaia",
     "#climarj", "#previsaodotempo", "#sol",
     "#interiordorj", "#regiaodovale"],
    ["#resende", "#voltaredonda", "#barradopirai",
     "#tempoagora", "#meteorologia", "#chuvahoje",
     "#valedoparaiba", "#riodejaneiro"],
]

CONTEXTO = {
    "chuva": ["#chuvahoje", "#guardachuva"],
    "tempestade": ["#temporal", "#chuvaforte"],
    "calor": ["#calorao", "#verao"],
    "frio": ["#friozinho", "#casaco"],
    "sol": ["#diadesol", "#ceuazul"],
    "nublado": ["#temponublado", "#ceufechado"],
}


def _ordinal(data=None) -> int:
    return (data or _dt.date.today()).toordinal()


def _indice(slot: str, data=None) -> int:
    """Índice do conjunto. Manhã e noite do mesmo dia nunca coincidem."""
    if slot not in SLOTS:
        raise ValueError(f"slot deve ser um de {SLOTS}, veio {slot!r}")
    o = _ordinal(data)
    i_manha = o % len(CONJUNTOS)
    if slot == "manha":
        return i_manha
    i_noite = (o + 2) % len(CONJUNTOS)
    return i_noite if i_noite != i_manha else (i_noite + 1) % len(CONJUNTOS)


def tag_cidade(nome: str) -> str:
    """#nomedacidade — minúsculas, sem espaço e sem acento."""
    base = _unicodedata.normalize("NFKD", nome or "")
    base = "".join(c for c in base if not _unicodedata.combining(c))
    return "#" + "".join(c for c in base.lower() if c.isalnum())


def hashtags(slot: str, condicao: str = "nublado", data=None,
             destaque: str = None) -> str:
    """Conjunto do dia + a cidade da vez + as tags de contexto, sem repetir.

    O dedup importa: #chuvahoje está no conjunto 5 E no contexto de chuva, e a
    mesma tag duas vezes na legenda é sinal de spam pro Instagram.

    `destaque` entra na FRENTE e nunca falta: desde que a lista de cidades gira
    por data (ver coletar_tempo.ordem_do_dia), o vídeo pode ser inteiro sobre
    Quatis enquanto o conjunto do dia só cita Volta Redonda e Barra Mansa. A
    tag do município de que o vídeo fala é a única que não pode estar ausente —
    é por ela que quem mora lá encontra o vídeo.
    """
    tags = []
    if destaque:
        tags.append(tag_cidade(destaque))
    for t in CONJUNTOS[_indice(slot, data)]:
        if t not in tags:
            tags.append(t)
    for t in CONTEXTO.get(condicao, []):
        if t not in tags:
            tags.append(t)
    return " ".join(tags)


# =====================================================================
#  PERGUNTA FECHADA — o CTA que substitui o "comenta aí"
# =====================================================================
#  Três regras, e as três vieram do que os números mostraram:
#
#  1. FECHADA, de uma palavra. "E aí, vai precisar de casaco na sua cidade?"
#     obriga o leitor a formular uma frase. "Casaco ou não?" custa um toque.
#  2. COM CIDADE NO TEXTO. Quem mora em Resende responde a uma pergunta sobre
#     Resende; "na sua cidade" não é pergunta de ninguém.
#  3. SOBRE AMANHÃ (ou hoje), nunca sobre o passado — o leitor sabe a resposta
#     antes de pensar, e é isso que faz o dedo parar.
#
#  A pergunta cita a cidade que torna a pergunta interessante: a mais fria
#  quando o assunto é casaco, a mais chuvosa quando é guarda-chuva.
PERGUNTAS = {
    "frio": [
        "Vai de casaco em {cidade} {quando}? Responde sim ou não 👇",
        "{cidade} {quando}: casaco ou aguenta na camiseta? 👇",
        "Quem aí em {cidade} já separou o casaco pra {quando}? 👇",
    ],
    "chuva": [
        "Você leva guarda-chuva em {cidade} {quando} ou arrisca? 👇",
        "{cidade} {quando}: guarda-chuva na bolsa ou fé? 👇",
        "Dá pra estender roupa em {cidade} {quando}? Sim ou não 👇",
    ],
    "tempestade": [
        "{cidade} {quando}: você muda o programa por causa do temporal? 👇",
        "Já guardou o que voa aí em {cidade}? Responde sim ou não 👇",
    ],
    "calor": [
        "{cidade} {quando}: ventilador ou ar-condicionado? 👇",
        "Aguenta esse calor em {cidade} {quando}? Sim ou não 👇",
        "{cidade} {quando}: piscina, praia ou sombra? 👇",
    ],
    "sol": [
        "Dá pra estender roupa em {cidade} {quando}? Sim ou não 👇",
        "{cidade} {quando}: dia de sair ou de ficar? 👇",
        "Você põe protetor solar em {cidade} {quando}? Responde aí 👇",
    ],
    "nublado": [
        "{cidade} {quando}: casaco ou camiseta? 👇",
        "Você confia nesse céu fechado em {cidade} {quando}? Sim ou não 👇",
        "{cidade} {quando}: dá praia ou não dá? 👇",
    ],
}


def _cidade_do_assunto(cidades, condicao: str) -> str:
    """A cidade que torna a pergunta interessante para quem mora lá."""
    if not cidades:
        return "Volta Redonda"
    if condicao in ("chuva", "tempestade"):
        return max(cidades, key=lambda c: c.get("chuva_mm", 0) or 0)["nome"]
    if condicao == "frio":
        return min(cidades, key=lambda c: c.get("min", 99))["nome"]
    if condicao == "calor":
        return max(cidades, key=lambda c: c.get("max", -99))["nome"]
    return cidades[0]["nome"]


# =====================================================================
#  CHAMADA DO BAIRRO — a última linha da legenda, antes das hashtags
# =====================================================================
#  Substituiu a pergunta fechada em 2026-08-22. A pergunta pedia um comentário
#  de uma palavra; esta pede uma mensagem direta, que vale mais no ranqueamento
#  e ainda entrega alguma coisa de volta pra quem responde — a previsão do
#  bairro dela, que nenhum outro perfil da região dá.
#
#  O robô que atende está em dm/ (325 bairros, 10 cidades). Se ele sair do ar,
#  esta linha vira promessa falsa: veja o runbook antes de deixar quebrado.
CHAMADA_BAIRRO = [
    "📩 Manda o nome do teu bairro aqui na DM. Eu respondo a previsão só dele.",
    "📩 Quer a previsão do TEU bairro? Manda o nome numa DM e recebe na hora.",
    "📩 Teu bairro na DM. São 325 bairros das 10 cidades — o teu está aí.",
    "📩 Manda uma DM com o nome do bairro. A previsão volta pronta, do teu canto.",
]


def chamada_bairro(slot: str, data=None) -> str:
    """A chamada do dia. Roda o banco por data e alterna manhã/noite, do mesmo
    jeito que as hashtags — pra quem vê os dois Reels não ler a mesma frase."""
    i = (_ordinal(data) + (0 if slot == "manha" else 1)) % len(CHAMADA_BAIRRO)
    return CHAMADA_BAIRRO[i]


def pergunta(slot: str, condicao: str, cidades=None, quando: str = "hoje",
             data=None) -> str:
    banco = PERGUNTAS.get(condicao) or PERGUNTAS["nublado"]
    i = (_ordinal(data) + (0 if slot == "manha" else 1)) % len(banco)
    return banco[i].format(cidade=_cidade_do_assunto(cidades or [], condicao),
                           quando=quando)


def _sanity() -> None:
    for c in CONJUNTOS:
        assert len(c) == 8, "cada conjunto base deve ter 8 tags (3+3+2)"
    for dia in range(400):
        d = _dt.date(2026, 1, 1) + _dt.timedelta(days=dia)
        assert _indice("manha", d) != _indice("noite", d), f"manhã == noite em {d}"
    for slot in SLOTS:
        for cond in list(CONTEXTO) + ["nublado"]:
            t = hashtags(slot, cond).split()
            assert len(t) == len(set(t)), f"tag repetida em {slot}/{cond}"
    cid = [{"nome": "Volta Redonda", "min": 18, "max": 30, "chuva_mm": 1.0},
           {"nome": "Resende", "min": 11, "max": 27, "chuva_mm": 9.0}]
    assert "Resende" in pergunta("manha", "frio", cid)
    assert "Resende" in pergunta("noite", "chuva", cid, quando="amanhã")


_sanity()
