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
  - o fecho SEMPRE termina passando o bastão: previsão muda de um dia pro outro,
    e quem dá a palavra final na manhã seguinte é ele.

Uso:
    python gerar_tarde.py --dados amanha.json --saida TARDE.mp4
    python gerar_tarde.py --demo
"""
import argparse, json, os, random, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from gerar_dia import (produzir, num_extenso, LIMIAR_CHUVA_MM,
                       chove_de_verdade, fala_do_resumo)
from coletar_tempo import resumo_cinco

# Entradas do resumo na voz DELA. O velho manda anotar; ela oferece.
INTRO_RESUMO_MARIA = [
    "Olha as cinco principais pra amanhã, meu bem.",
    "Anota aí as cinco principais de amanhã.",
    "As cinco maiores, pra você já se programar.",
    "Vamos às cinco principais de amanhã.",
    "Separei as cinco principais pra você.",
    "As cinco de sempre, pra amanhã.",
    "Repara nas cinco principais.",
    "Olha aqui como fica amanhã nas cinco principais.",
]


UV_AVISO = [
    (2, "tranquilo"), (5, "passa protetor"), (7, "protetor e chapéu"),
    (10, "evite o sol do meio-dia"), (99, "sol forte demais, fique na sombra"),
]


def aviso_uv(uv):
    for lim, txt in UV_AVISO:
        if uv <= lim:
            return txt
    return "sol forte"


def maiusculizar(t):
    """Primeira letra da frase E depois de cada ponto."""
    if not t:
        return t
    saida, novo = [], True
    for ch in t:
        saida.append(ch.upper() if novo and ch.isalpha() else ch)
        if ch.isalpha():
            novo = False
        elif ch in ".!?":
            novo = True
    return "".join(saida)


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
#  Os quatro bancos abaixo são os mesmos de sempre, com uma adaptação: ela
#  gravava ao meio-dia e agora grava às 18h, então "boa tarde" virou "boa
#  noite", "já almoçaram" virou "já jantaram", e as duas falas que prometiam
#  cuidar do "resto do dia" agora falam do dia de amanhã.

ABERTURAS = [
    "Boa noite, meus queridos.",
    "Oi, gente. Já jantaram?",
    "Boa noite. Senta aqui que eu já te conto.",
    "Cheguei. Trouxe as informações que importam.",
    "Boa noite, meus amores.",
    "Oi, meus queridos. Tudo em ordem por aí?",
    "Cheguei, cheguei. Senta que a tia te explica.",
    "Boa noite. Vim resolver o dia de vocês.",
    "Oi, gente linda. Bora ao que interessa?",
    "Boa noite. Preparei tudo com carinho pra você.",
    "Oi, meus bem. Vamos organizar essa noite juntos?",
    "Boa noite. Chegou a hora da parte útil do dia.",
    "Cheguei com as dicas que salvam a sua noite.",
    "Oi, meus queridos. Senta e relaxa que eu cuido do resto.",
    "Boa noite. Já pus a água pra ferver e vim te avisar.",
    "Oi, gente. Jantaram bem? Então vem cá.",
    "Boa noite, meus amores. Trago notícia e conselho.",
    "Cheguei pra deixar sua noite mais tranquila.",
    "Oi, meus queridos. A tia passou pra ajudar.",
    "Boa noite. Vamos aproveitar bem o dia de amanhã?",
    "Oi, gente linda. Preparei um resuminho pra vocês.",
    "Boa noite. Se ajeita aí que eu já começo.",
    "Cheguei com tudo anotado, pode confiar.",
    "Oi, meus queridos. Dia bom começa sabendo o que vem.",
    "Boa noite, meus amores. Como estão as forças?",
    "Oi, gente. Vim com as dicas de sempre, com carinho.",
    "Boa noite. A parte chata passou, agora é comigo.",
    "Cheguei pra deixar você por dentro de tudo.",
    "Oi, meus queridos. Bora deixar o amanhã pronto?",
    "Boa noite. Senta, respira, e me deixa te ajudar.",
]

# Ela cita o velho SEM repetir o conteúdo dele: ele reclamou de hoje cedo,
# ela fala do dia seguinte.
CITA_VELHO = [
    "O velho já reclamou do tempo hoje cedo. Mas ele exagera.",
    "Não liga pro que aquele ranzinza falou de manhã.",
    "Ele reclamou. Ele sempre reclama. Vamos ao que interessa.",
    "De manhã teve resmungo. Agora tem solução.",
    "O ranzinza resmungou cedo, coitado. É o feitio dele.",
    "De manhã teve reclamação; agora tem solução, viu?",
    "Ignora o mau humor do velho. Eu cuido de vocês.",
    "Ele já encheu o saco cedo. Minha vez de ajudar.",
    "O velho reclama, eu resolvo. Sempre foi assim.",
    "Aquele rabugento já falou. Agora escuta quem acalma.",
    "O ranzinza fez a parte dele: resmungou. Eu faço a minha.",
    "De manhã foi bronca; de noite é conselho. Combinado?",
    "Ele reclamou do tempo, como sempre. Nada de novo nisso.",
    "O velho está de mau humor, coitado. Deixa ele lá.",
    "Já ouviram o resmungo dele hoje cedo? Pois é. Vamos em frente.",
    "O ranzinza tem razão no tempo, só erra no humor.",
    "Ele não mente na previsão, só reclama demais dela.",
    "De manhã o velho avisou, à sua maneira. Eu explico melhor.",
    "O rabugento cumpriu o dever de resmungar. Agora sou eu.",
    "Ele até acerta o tempo. Só falta acertar o sorriso.",
    "O velho já deu o recado cedo, do jeito azedo dele.",
    "Aquele resmungão falou tudo com cara feia. Eu falo com jeito.",
    "O ranzinza acordou reclamando. Milagre seria acordar contente.",
    "Deixa o velho lá com o mau humor. Aqui a gente se cuida.",
    "Ele reclamou bonito hoje cedo. Agora vem a parte boa.",
    "O rabugento avisou de manhã. Eu venho confirmar com carinho.",
    "O velho e o tempo combinam: os dois teimosos. Mas ele acerta.",
    "De manhã bronca, de noite afago. É a nossa dupla.",
    "O ranzinza resmungou cedinho. Eu vim descomplicar pra você.",
    "Ele falou do tempo do jeito dele. Eu falo do jeito que ajuda.",
]

FECHOS = [
    "É isso, meus queridos. Amanhã eu volto.",
    "Qualquer coisa, me chama nos comentários.",
    "Cuidem-se. E bebam água.",
    "Até amanhã, viu? Um beijo.",
    "É isso, meus amores. Amanhã tem mais.",
    "Se cuidam, bebam água e um beijo grande.",
    "Qualquer dúvida, comentários abertos, viu?",
    "Até amanhã, meus amores. A tia volta.",
    "Fica com Deus e se cuida, meu bem.",
    "Descansem bem, que amanhã tem mais cuidado.",
    "Me conta nos comentários como foi seu dia.",
    "É isso por hoje. Um abraço apertado de tia.",
    "Cuidem de vocês e de quem tá por perto.",
    "Até amanhã. Não esquece de beber água, viu?",
    "Vai com calma no dia de amanhã, meu amor.",
    "É isso, gente linda. Amanhã a gente se vê.",
    "Boa noite, meus queridos.",
    "Se precisar, é só chamar. Tô sempre por aqui.",
    "Aproveita a noite com quem você gosta.",
    "Um beijo no coração de cada um de vocês.",
    "Cuida da saúde e do sorriso, tá bom?",
    "É isso, meu bem. Até o próximo aviso da tia.",
    "Descansa, hidrata e respira fundo. Até amanhã.",
    "Qualquer novidade no tempo, eu apareço aqui.",
    "Fica bem, meu amor. A tia te espera amanhã.",
    "É tudo por hoje. Manda um oi pra família.",
    "Se cuida bastante, que você merece.",
    "Até amanhã, meus queridos. Durmam bem.",
    "Um beijo grande e até a próxima, viu?",
    "Cuidem-se com carinho. A tia se despede por hoje.",
]

# Mesmo CTA do bairro, outra voz: ela pede com jeito, ele pede contrariado.
# Ver a nota longa em gerar_dia.py sobre por que a fala diz "mensagem" e
# nunca "DM" — o Kokoro soletra sigla.
CTA = [
    "Manda o nome do teu bairro na mensagem, meu bem. Eu respondo na hora.",
    "Me escreve o teu bairro numa mensagem, meu amor. A tia diz o tempo daí.",
    "Manda mensagem com o nome do teu bairro. Aí a previsão é sua, viu?",
    "Quer saber do teu bairro? Me manda o nome numa mensagem, meu bem.",
    "Escreve o teu bairro na mensagem, meu amor. Eu já te devolvo certinho.",
    "Manda o bairro numa mensagem pra tia. Respondo rapidinho, prometo.",
    "Me diz onde você mora numa mensagem. É só o nome do bairro, meu bem.",
    "Manda mensagem com o teu bairro e recebe a previsão do teu canto.",
    "Teu bairro numa mensagem, meu amor. A tia cuida do resto.",
    "Escreve o nome do bairro na mensagem. Assim eu falo direto com você.",
    "Manda o teu bairro pra mim numa mensagem. Nem precisa dizer oi.",
    "Me manda o bairro numa mensagem, viu? Eu respondo até tarde.",
    "Manda o nome do teu bairro. Uma mensagem só, meu bem, e pronto.",
    "Escreve o teu bairro numa mensagem e compartilha com a vizinhança.",
    "Manda mensagem com o bairro, meu amor. A tia não te deixa na chuva.",
    "Teu bairro, numa mensagem. Aí a previsão sai sob medida pra você.",
]


# PASSAGEM DE BASTÃO — entra colada no fecho, SEMPRE.
# Previsão de D+1 muda de madrugada. Em vez de fingir certeza, ela avisa que o
# número é o de agora e devolve a palavra final pro velho, que fala 12h depois
# com dados mais novos. É isso que transforma uma eventual divergência entre os
# dois vídeos em continuidade, não em contradição.
PASSAGEM = [
    "É o que está previsto até agora. Amanhã cedo o velho confere.",
    "Se mudar alguma coisa de madrugada, o ranzinza avisa de manhã.",
    "De manhã ele confirma, do jeito mal-humorado dele.",
    "Amanhã cedo tem o resmungo dele pra confirmar.",
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

    # --- 2. AS CINCO PRINCIPAIS: mínima e máxima de amanhã ---
    # A batida que faltava. Até 2026-08-22 este roteiro lia só `cid[0]` do
    # começo ao fim: com Volta Redonda fixa na primeira posição ninguém notou,
    # mas no dia em que o rodízio pôs Piraí ali, o vídeo inteiro falou de Piraí
    # e de mais nenhuma.
    #
    # Ficou no lugar do cartão solto da cidade principal, que dizia os mesmos
    # dois números que o quadro repetiria logo em seguida. A cidade da vez não
    # perdeu nada: continua com o selo no alto e é a primeira linha do quadro.
    resumo = resumo_cinco(cid)
    if len(resumo) > 1:
        fala_r, leg_r = fala_do_resumo(resumo, rnd, intros=INTRO_RESUMO_MARIA)
        # sem `acao`: ela sai do quadro nesta batida (P.sair_de_cena), e não
        # dá pra apontar pra um cartaz de dentro dos bastidores
        add(fala_r, leg_r, tipo="resumo", cidades=resumo,
            titulo="AMANHÃ NAS CINCO PRINCIPAIS")
    else:
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

    # --- fecho: despedida dela + passagem de bastão pro velho ---
    add(f"{rnd.choice(FECHOS)} {rnd.choice(PASSAGEM)}",
        "Amanhã cedo o velho confirma.",
        tipo="fecho", texto="AMANHÃ VOCÊ JÁ SABE")
    add(rnd.choice(CTA), tipo="cta", chamada="TEU BAIRRO NA DM",
        sub="manda o nome e eu respondo a previsão daí")
    return batidas


DEMO = {
    "data": "2026-07-30",
    # cinco cidades: sem isso a batida do resumo não entra e o --demo deixa de
    # testar justamente a parte nova
    "cidades": [
        {"nome": "Porto Real", "min": 13, "max": 28, "cond": "sol", "chuva_mm": 0},
        {"nome": "Volta Redonda", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0},
        {"nome": "Barra Mansa", "min": 11, "max": 28, "cond": "sol", "chuva_mm": 0},
        {"nome": "Resende", "min": 9, "max": 25, "cond": "frio", "chuva_mm": 0},
        {"nome": "Barra do Piraí", "min": 14, "max": 30, "cond": "sol", "chuva_mm": 0},
    ],
    "umidade_min": 34, "vento_kmh": 14, "sol_h": 9,
    "sensacao_max": 30, "uv_max": 8,
}


DEMO_CHUVA = {
    "data": "2026-11-13",
    "cidades": [
        {"nome": "Quatis", "min": 18, "max": 27, "cond": "chuva", "chuva_mm": 9.0},
        {"nome": "Volta Redonda", "min": 19, "max": 28, "cond": "chuva", "chuva_mm": 12.0},
        {"nome": "Barra Mansa", "min": 19, "max": 27, "cond": "chuva", "chuva_mm": 11.0},
        {"nome": "Resende", "min": 17, "max": 25, "cond": "chuva", "chuva_mm": 14.0},
        {"nome": "Barra do Piraí", "min": 20, "max": 29, "cond": "chuva", "chuva_mm": 8.0},
    ],
    "umidade_min": 72, "vento_kmh": 9, "sol_h": 3,
    "sensacao_max": 31, "uv_max": 6,
}


DEMO_FRIO = {
    "data": "2026-06-18",
    "cidades": [
        {"nome": "Itatiaia", "min": 6, "max": 19, "cond": "frio", "chuva_mm": 0},
        {"nome": "Volta Redonda", "min": 9, "max": 21, "cond": "frio", "chuva_mm": 0},
        {"nome": "Barra Mansa", "min": 8, "max": 21, "cond": "frio", "chuva_mm": 0},
        {"nome": "Resende", "min": 5, "max": 18, "cond": "frio", "chuva_mm": 0},
        {"nome": "Barra do Piraí", "min": 10, "max": 22, "cond": "frio", "chuva_mm": 0},
    ],
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
                    "vento_visual": 0.7,
                    # a cidade da vez. O coletar_tempo roda o vídeo dela com
                    # DESLOCA_TARDE, então nunca é a mesma que o Ranzinza
                    # destacou de manhã — duas cidades citadas por dia.
                    "destaque": d.get("destaque") or d["cidades"][0]["nome"],
                    # ela fala do dia seguinte; o rótulo tem que dizer isso,
                    # senão o selo desmente o cartão logo abaixo
                    "destaque_rotulo": "AMANHÃ EM"})


if __name__ == "__main__":
    main()
