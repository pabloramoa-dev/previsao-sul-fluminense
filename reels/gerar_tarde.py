#!/usr/bin/env python3
"""
gerar_tarde.py — o Reel das 18h com a DONA MARIA.

Contraponto do Ranzinza no TEMPO, não só no humor: ele fala do dia de HOJE às
06:10, ela fala do dia de AMANHÃ às 18:00. Nenhum dos dois comenta o dia do
outro — é o que impede os dois vídeos de se contradizerem no mesmo perfil.

Ela cita ele de propósito — quem viu um vídeo quer ver o outro, e isso é a
mecânica de retenção mais barata do projeto todo.

Cinco blocos, todos da MESMA chamada ao Open-Meteo, só que no índice de AMANHÃ
(`coletar_tempo.py --quando amanha`):
    1. gancho          — o número mais forte de amanhã
    2. mínima e máxima — da cidade principal
    3. o que separar   — casaco, guarda-chuva ou protetor, pra deixar pronto hoje
    4. sensação térmica— por que o termômetro vai "mentir"
    5. índice UV       — protetor solar

REGRA DE COERÊNCIA COM O VELHO (não quebre isto):
  - ela nunca fala do tempo de hoje;
  - ela usa os MESMOS limiares dele (LIMIAR_CHUVA_MM, chove_de_verdade), então
    "chove" quer dizer a mesma coisa nos dois vídeos;
  - ela fecha passando o bastão: previsão muda de um dia pro outro, e quem dá a
    palavra final na manhã seguinte é ele.

Uso:
    python gerar_tarde.py --dados amanha.json --saida TARDE.mp4
    python gerar_tarde.py --demo
"""
import argparse, json, os, random, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from gerar_dia import (produzir, num_extenso, maiusculizar, LIMIAR_CHUVA_MM,
                       chove_de_verdade)


UV_AVISO = [
    (2, "tranquilo"), (5, "passa protetor"), (7, "protetor e chapéu"),
    (10, "evite o sol do meio-dia"), (99, "sol forte demais, fique na sombra"),
]


def aviso_uv(uv):
    for lim, txt in UV_AVISO:
        if uv <= lim:
            return txt
    return "sol forte"


# =====================================================================
#  O QUE SEPARAR HOJE À NOITE — o bloco útil dela agora
# =====================================================================
#  Substituiu o índice de varal. O varal respondia "dá pra estender AGORA?",
#  uma pergunta do dia de hoje — não cabe mais num vídeo que fala de amanhã.
#  A pergunta que cabe às 18h é "o que eu deixo pronto pra amanhã?".
def o_que_separar(cidades, uv, umidade):
    """Devolve (cartaz, fala) do preparo de amanhã. Prioridade pelo que dói
    mais esquecer: chuva > frio > sol forte > ar seco > nada.

    Olha TODAS as cidades, não só a principal: quem mora em Resende passa frio
    numa manhã em que Volta Redonda está amena, e o conselho é o mesmo pros dois
    ("separa o casaco") — errar pra mais aqui custa pouco, errar pra menos deixa
    alguém no ponto de ônibus sem agasalho.
    """
    mais_frio = min(cidades, key=lambda c: c["min"])
    if any(chove_de_verdade(c) for c in cidades):
        return ("LEVE GUARDA-CHUVA",
                "Deixa o guarda-chuva na porta hoje à noite. Amanhã você não "
                "lembra.")
    if mais_frio["min"] <= 13:
        return ("SEPARE O CASACO",
                "Separa o casaco antes de dormir. Amanhã cedo você agradece.")
    if uv and uv >= 8:
        return ("PROTETOR SOLAR",
                "Deixa o protetor solar na bolsa. O sol de amanhã não perdoa.")
    if umidade and umidade <= 30:
        return ("GARRAFA DE ÁGUA",
                "Enche a garrafa de água hoje. O ar de amanhã vem seco demais.")
    return ("DIA TRANQUILO",
            "Amanhã não precisa de nada especial. Só de disposição.")


# =====================================================================
#  FALAS — voz dela: acolhedora, prática, e sempre alfinetando o velho
# =====================================================================
ABERTURAS = [
    "Boa noite, meus queridos.",
    "Oi, gente. Já jantaram?",
    "Boa noite. Senta aqui que eu já te conto como vai ser amanhã.",
    "Cheguei. Vim adiantar o seu dia de amanhã.",
]

# Ela cita o velho SEM repetir o conteúdo dele: ele reclamou de hoje cedo,
# ela fala do dia seguinte. É a linha que mantém os dois vídeos coerentes.
CITA_VELHO = [
    "O velho já resmungou o dia de hoje lá de manhã. Eu vim falar do de amanhã.",
    "De manhã o ranzinza reclamou de hoje. Agora eu adianto o amanhã.",
    "Hoje já foi, e ele já reclamou. Vamos ao que vem por aí.",
    "Ele cuida do dia de hoje. O de amanhã fica comigo.",
]

# Fecho: hedge + passagem de bastão. Previsão muda de um dia pro outro; dizer
# isso na voz dela é mais barato (e mais honesto) que tentar travar os dois
# vídeos no mesmo número.
FECHOS = [
    "É o que está previsto até agora. Amanhã cedo o velho confere e reclama.",
    "Deixa tudo pronto hoje. Se mudar alguma coisa, o ranzinza avisa de manhã.",
    "Assim está a previsão. De manhã ele confirma, do jeito mal-humorado dele.",
    "Já organiza a sua noite. Amanhã cedo tem o resmungo dele pra confirmar.",
]

# Mesmo CTA, outra voz: ela pede com jeito, ele pede contrariado.
CTA = [
    "E segue a gente, viu? Assim você sabe do amanhã todo dia.",
    "Aperta o seguir, meu bem. É rapidinho.",
    "Segue o perfil pra não ser pego de surpresa amanhã.",
    "Se ainda não segue, segue agora. Eu agradeço.",
]


# =====================================================================
#  GANCHO — o número mais forte de AMANHÃ
# =====================================================================
def escolher_gancho(cid, umidade):
    """(fala, numero, subtitulo, cor). Mesma prioridade do velho — frio
    extremo > calor extremo > chuva forte > ar seco — pra que os dois vídeos
    considerem "extremo" a mesma coisa."""
    mais_frio = min(cid, key=lambda c: c["min"])
    mais_quente = max(cid, key=lambda c: c["max"])
    mais_chuva = max(cid, key=lambda c: c.get("chuva_mm", 0) or 0)

    if mais_frio["min"] <= 11:
        t = mais_frio["min"]
        return (f"Amanhã, {num_extenso(t)} graus em {mais_frio['nome']}.",
                f"{t}°", "AMANHÃ", "frio")
    if mais_quente["max"] >= 32:
        t = mais_quente["max"]
        return (f"Amanhã, {num_extenso(t)} graus em {mais_quente['nome']}.",
                f"{t}°", "AMANHÃ", "calor")
    if (mais_chuva.get("chuva_mm", 0) or 0) >= 10:
        v = round(mais_chuva["chuva_mm"])
        return (f"Amanhã vem chuva. {num_extenso(v)} milímetros em "
                f"{mais_chuva['nome']}.",
                f"{v}mm", "AMANHÃ", "chuva")
    if umidade and umidade <= 30:
        return (f"Amanhã o ar seca. Umidade em {num_extenso(umidade)} por cento.",
                f"{umidade}%", "AMANHÃ", "seco")
    c = cid[0]
    return (f"Amanhã, {num_extenso(c['max'])} graus em {c['nome']}.",
            f"{c['max']}°", "AMANHÃ", "normal")


def montar_roteiro(d):
    """`d` = amanha.json (mesmo formato do dia.json, só que do dia seguinte)."""
    rnd = random.Random(int(d["data"].replace("-", "")))
    cid = d["cidades"]
    principal = cid[0]
    batidas = []

    def add(fala, legenda=None, tipo="nenhum", **dd):
        f = maiusculizar(fala)
        batidas.append({"fala": f, "legenda": legenda if legenda is not None else f,
                        "tipo": tipo, "dados": dd})

    # --- 1. GANCHO: o número mais forte de amanhã, nos primeiros 1,5s ---
    fala_g, num_g, sub_g, cor_g = escolher_gancho(cid, d.get("umidade_min"))
    add(fala_g, num_g, tipo="gancho", numero=num_g, sub=sub_g, cor=cor_g)

    add(rnd.choice(ABERTURAS))
    add(rnd.choice(CITA_VELHO))

    # --- 2. mínima e máxima de amanhã na cidade principal ---
    add(f"Em {principal['nome']}, amanhã: mínima de "
        f"{num_extenso(principal['min'])} graus, máxima de "
        f"{num_extenso(principal['max'])}.",
        f"Amanhã: {principal['min']}° / {principal['max']}°",
        tipo="cidade", cidade=principal)

    # --- 3. o que separar hoje à noite (o bloco útil, no lugar do varal) ---
    cartaz, fala = o_que_separar(cid, d.get("uv_max"), d.get("umidade_min"))
    add(fala, fala, tipo="preparar", cartaz=cartaz, acao="apontar")

    # --- 4. sensação térmica ---
    real, sente = principal["max"], d.get("sensacao_max", principal["max"])
    if abs(real - sente) >= 2:
        add(f"O termômetro vai marcar {num_extenso(real)} graus, mas o corpo "
            f"vai sentir {num_extenso(sente)}.",
            f"Termômetro {real}°, você sente {sente}°.",
            tipo="sensacao", real=real, sente=sente)

    # --- 5. UV ---
    # Não entra em dia de chuva: "leve guarda-chuva" seguido de "passe protetor
    # e chapéu" no mesmo vídeo é a contradição mais fácil de cometer aqui. E
    # abaixo de 3 o índice não pede nada de ninguém, só ocupa uma batida.
    uv = d.get("uv_max")
    if uv and uv >= 3 and not any(chove_de_verdade(c) for c in cid):
        add(f"O sol de amanhã vem no índice {num_extenso(round(uv))}. "
            f"{aviso_uv(uv).capitalize()}.",
            f"UV {round(uv)} — {aviso_uv(uv)}",
            tipo="uv", uv=round(uv), aviso=aviso_uv(uv))

    # --- fecho com passagem de bastão pro velho, e CTA ---
    add(rnd.choice(FECHOS), tipo="fecho", texto="AMANHÃ VOCÊ JÁ SABE")
    add(rnd.choice(CTA), tipo="cta", chamada="TOCA NO SEGUIR")
    return batidas


DEMO = {
    "data": "2026-07-30",
    "cidades": [{"nome": "Volta Redonda", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0}],
    "umidade_min": 34, "vento_kmh": 14, "sol_h": 9,
    "sensacao_max": 30, "uv_max": 8,
}


DEMO_CHUVA = {
    "data": "2026-11-13",
    "cidades": [{"nome": "Volta Redonda", "min": 19, "max": 28, "cond": "chuva",
                 "chuva_mm": 12.0}],
    "umidade_min": 72, "vento_kmh": 9, "sol_h": 3,
    "sensacao_max": 31, "uv_max": 6,
}


DEMO_FRIO = {
    "data": "2026-06-18",
    "cidades": [{"nome": "Volta Redonda", "min": 9, "max": 21, "cond": "frio",
                 "chuva_mm": 0}],
    "umidade_min": 48, "vento_kmh": 7, "sol_h": 6,
    "sensacao_max": 19, "uv_max": 4,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados", help="amanha.json (coletar_tempo.py --quando amanha)")
    ap.add_argument("--saida", default="TARDE.mp4")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--demo-chuva", action="store_true",
                    help="cenário de chuva amanhã, pro cartaz do guarda-chuva")
    ap.add_argument("--demo-frio", action="store_true",
                    help="cenário de frio amanhã, pro cartaz do casaco")
    ap.add_argument("--quality", default="m")
    ap.add_argument("--so-roteiro", action="store_true",
                    help="imprime as batidas e sai, sem renderizar")
    a = ap.parse_args()

    if getattr(a, "demo_chuva", False):
        d = DEMO_CHUVA
    elif getattr(a, "demo_frio", False):
        d = DEMO_FRIO
    elif a.demo or not a.dados:
        d = DEMO
    else:
        d = json.load(open(a.dados))

    batidas = montar_roteiro(d)
    for b in batidas:
        print(f"   [{b['tipo']:10s}] {b['fala']}")
    if a.so_roteiro:
        return

    # O cenário dela é sempre o QUINTAL AO ENTARDECER — é o momento em que ela
    # está falando (18h), não o tempo de amanhã. Isso resolve três coisas de uma
    # vez: nunca chove em cima dela (logo, nada de guarda-chuva), o fundo não
    # desmente o card quando a previsão de amanhã muda, e o horário do post fica
    # legível no primeiro frame.
    produzir(batidas, a.saida,
             cenario="entardecer", personagem="maria", cenario_tipo="quintal",
             quality=a.quality, voz="pf_dora", pitch=0.94,
             extra={"data": d["data"],
                    # brisa do fim de tarde: constante e suave, sem significar
                    # nota nenhuma (o índice de varal não existe mais)
                    "vento_visual": 0.7})


if __name__ == "__main__":
    main()
