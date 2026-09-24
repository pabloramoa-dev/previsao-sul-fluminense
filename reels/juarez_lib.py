"""
juarez_lib — Juarez Plantão, o repórter de plantão do @previsaosulflu.

Mesmo mundo dos outros dois (traço grosso, cabeça grande, tudo desenhado por
código) e a mesma regra de ouro: NADA congela, todo personagem em cena leva
respirar(). O que muda é a função. O Ranzinza comenta o tempo de hoje e a Dona
Maria prepara o de amanhã; o Juarez ANUNCIA — gravidade de plantão de última
hora aplicada, na maioria dos dias, a notícia nenhuma. É essa distância entre o
tom e o fato que faz a graça, e é ela que sustenta o mesmo personagem servindo
tanto ao dia comum quanto ao dia de alerta de verdade.

VEIO DA SKILL, NAO NASCEU AQUI
------------------------------
O personagem foi desenhado e validado na skill `juarez-plantao`, que produz os
comunicados avulsos (alerta extraordinario e publicidade). Ate 2026-09-04 ele
existia SO la: o repositorio tinha o Juarez em documentacao — o
`docs/reels_spec_fase7.md` e um comentario no `monitor_alertas.yml` que fala do
"Reel do Juarez (Modo Alerta)" como se ele existisse — e nenhuma linha de
codigo. Era por isso que o `ranzinza.yml` nao podia ser desligado: desligar
deixaria o perfil com ZERO Reels por dia, nao com um.

O rosto e o figurino continuam os da skill (o experimento de 14 dias acabou
em 22/09/2026). Em 23/09/2026 entrou o visual v2: o estudio virou um
telejornal com telao da paisagem regional que reage ao tempo, bancada com
AO VIVO, e o microfone ganhou canopla legivel. A voz passou a ser a do Bira
do Tempo (@previsaorj) — ver `gerar_juarez.py`.

Uma diferenca de escopo vale registrar: a skill descreve o Juarez para
comunicados AVULSOS (vendaval, publicidade). Aqui ele e o Reel DIARIO, unico,
das 06h, nos dois modos do plano v3 — rotina e alerta. Mesmo personagem, papel
maior. O `painel_publi()` veio junto porque e do personagem, mas o gerador
diario nao o usa: publicidade continua saindo pela skill, avulsa.
"""
import os
import sys

from manim import *
import numpy as np

# dvh_lib.py mora na mesma pasta que este arquivo — mesma solução do
# previsao_lib.py, que também já teve um caminho absoluto de /mnt/skills aqui.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dvh_lib as L

PT = L.PT
FONTE = L.FONTE
respirar = L.respirar

PELE_J = "#e8b48f"
CABELO_J = "#2b2118"
TERNO_J = "#2c3e50"
TERNO_ESC = "#1c2b38"
CAMISA_J = "#f2f0e6"
GRAVATA_J = "#8a2f28"


# =====================================================================
#  JUAREZ PLANTÃO
# =====================================================================
def juarez(humor="dramatico"):
    cab = Circle(radius=0.9, stroke_color=PT, stroke_width=15,
                fill_color=PELE_J, fill_opacity=1).shift(UP * 1.4)
    c = cab.get_center()

    # cabelo despenteado — tufos irregulares em vários ângulos (plantão = sem tempo de pentear)
    cabelo = VGroup(*[
        Polygon(c + UP * 0.75 + RIGHT * dx,
               c + UP * (1.15 + h) + RIGHT * (dx - 0.05),
               c + UP * (1.05 + h) + RIGHT * (dx + 0.16),
               fill_color=CABELO_J, fill_opacity=1, stroke_color=PT, stroke_width=7)
        for dx, h in [(-0.55, 0.15), (-0.30, 0.30), (-0.02, 0.20), (0.26, 0.32), (0.52, 0.12)]
    ])
    topete = Polygon(c + UP * 0.80 + LEFT * 0.15, c + UP * 1.45 + LEFT * 0.30,
                     c + UP * 1.30 + RIGHT * 0.10, fill_color=CABELO_J, fill_opacity=1,
                     stroke_color=PT, stroke_width=7)

    orE = Ellipse(width=0.20, height=0.32, fill_color=PELE_J, fill_opacity=1,
                 stroke_color=PT, stroke_width=7).move_to(c + LEFT * 0.90 + DOWN * 0.10)
    orD = Ellipse(width=0.20, height=0.32, fill_color=PELE_J, fill_opacity=1,
                 stroke_color=PT, stroke_width=7).move_to(c + RIGHT * 0.90 + DOWN * 0.10)

    # sobrancelhas ASSIMÉTRICAS — uma erguida, drama automático
    sobE = Line(c + LEFT * 0.54 + UP * 0.50, c + LEFT * 0.14 + UP * 0.30, stroke_color=CABELO_J, stroke_width=12)
    sobD = Line(c + RIGHT * 0.14 + UP * 0.26, c + RIGHT * 0.54 + UP * 0.30, stroke_color=CABELO_J, stroke_width=12)

    # olhos arregalados — branco visível atrás da pupila, maior que os outros dois
    olhoE_branco = Circle(radius=0.19, fill_color=WHITE, fill_opacity=1, stroke_color=PT, stroke_width=6).move_to(c + LEFT * 0.32 + UP * 0.04)
    olhoD_branco = Circle(radius=0.19, fill_color=WHITE, fill_opacity=1, stroke_color=PT, stroke_width=6).move_to(c + RIGHT * 0.32 + UP * 0.04)
    oe = Dot(c + LEFT * 0.32 + UP * 0.02, radius=0.10, color=PT)
    od = Dot(c + RIGHT * 0.32 + UP * 0.02, radius=0.10, color=PT)

    # barba por fazer — tracinhos na mandíbula (plantão = madrugada sem barbear)
    rng = np.random.default_rng(3)
    barba = VGroup(*[
        Line(p, p + np.array([rng.uniform(-0.02, 0.02), -0.035, 0]), stroke_color=CABELO_J, stroke_width=2.5)
        for p in [c + RIGHT * dx + DOWN * dy for dx in np.arange(-0.5, 0.51, 0.09)
                 for dy in [0.56 + abs(dx) * 0.25]]
    ])

    nariz = Ellipse(width=0.20, height=0.22, fill_color="#d99b73", fill_opacity=1,
                    stroke_color=PT, stroke_width=5).move_to(c + DOWN * 0.16)

    # boca sempre tensa/aberta — ele está sempre "no ar"
    boca = ArcBetweenPoints(c + DOWN * 0.54 + LEFT * 0.20, c + DOWN * 0.54 + RIGHT * 0.20,
                            angle=-PI / 4).set_stroke(PT, 8)

    pesc = Line(cab.get_bottom(), cab.get_bottom() + DOWN * 0.20, stroke_color=PT, stroke_width=15)
    t = pesc.get_end()

    camisa = Polygon(t + LEFT * 0.55, t + RIGHT * 0.55, t + DOWN * 1.55 + RIGHT * 0.85,
                     t + DOWN * 1.55 + LEFT * 0.85, fill_color=CAMISA_J, fill_opacity=1,
                     stroke_color=PT, stroke_width=9)

    # gravata torta — o detalhe que resume o personagem
    gravata = Polygon(t + DOWN * 0.05 + LEFT * 0.08, t + DOWN * 0.05 + RIGHT * 0.14,
                      t + DOWN * 0.30 + RIGHT * 0.20, t + DOWN * 1.15 + RIGHT * 0.02,
                      t + DOWN * 0.30 + LEFT * 0.02, fill_color=GRAVATA_J, fill_opacity=1,
                      stroke_color=PT, stroke_width=6)

    # blazer por cima, com lapela
    blazerE = Polygon(t + LEFT * 0.62 + UP * 0.05, t + LEFT * 0.10 + DOWN * 0.10,
                      t + LEFT * 0.30 + DOWN * 0.55, t + DOWN * 1.58 + LEFT * 0.90,
                      t + DOWN * 1.58 + LEFT * 0.40, t + DOWN * 0.20 + LEFT * 0.50,
                      fill_color=TERNO_J, fill_opacity=1, stroke_color=PT, stroke_width=9)
    blazerD = Polygon(t + RIGHT * 0.62 + UP * 0.05, t + RIGHT * 0.10 + DOWN * 0.10,
                      t + RIGHT * 0.30 + DOWN * 0.55, t + DOWN * 1.58 + RIGHT * 0.90,
                      t + DOWN * 1.58 + RIGHT * 0.40, t + DOWN * 0.20 + RIGHT * 0.50,
                      fill_color=TERNO_J, fill_opacity=1, stroke_color=PT, stroke_width=9)
    lapelaE = Line(t + LEFT * 0.10 + DOWN * 0.10, t + LEFT * 0.30 + DOWN * 0.55, stroke_color=TERNO_ESC, stroke_width=5)
    lapelaD = Line(t + RIGHT * 0.10 + DOWN * 0.10, t + RIGHT * 0.30 + DOWN * 0.55, stroke_color=TERNO_ESC, stroke_width=5)

    omb = t + DOWN * 0.20
    be = Line(omb + LEFT * 0.58, omb + DOWN * 0.55 + LEFT * 0.85, stroke_color=TERNO_J, stroke_width=22)
    cotoveloD = omb + RIGHT * 0.60 + DOWN * 0.45
    maoD_pos = cotoveloD + UP * 0.15 + RIGHT * 0.55
    bd1 = Line(omb + RIGHT * 0.58, cotoveloD, stroke_color=TERNO_J, stroke_width=22)
    bd2 = Line(cotoveloD, maoD_pos, stroke_color=TERNO_J, stroke_width=19)
    maoE = Dot(be.get_end(), radius=0.13, color=PELE_J).set_stroke(PT, 5)
    maoD = Dot(maoD_pos, radius=0.13, color=PELE_J).set_stroke(PT, 5)

    # microfone erguido na mão direita — o prop que define a silhueta
    mic_corpo = Line(maoD_pos, maoD_pos + UP * 0.55 + RIGHT * 0.08, stroke_color="#3a3a3c", stroke_width=13)
    mic_espuma = Circle(radius=0.20, fill_color="#1c1c1e", fill_opacity=1,
                        stroke_color=PT, stroke_width=6).move_to(mic_corpo.get_end())
    # canopla do microfone com a marca do plantão (antes: "@psf" deitado na
    # espuma, ilegível no celular). Cubo vermelho, "SF" branco, de pé.
    canopla = Square(0.34, fill_color="#d63a2f", fill_opacity=1, stroke_color=PT,
                     stroke_width=5).move_to(mic_corpo.point_from_proportion(0.45))
    mic_logo = Text("SF", font=FONTE, weight=BOLD, font_size=16, color=WHITE).move_to(canopla)
    microfone = VGroup(mic_corpo, mic_espuma, canopla, mic_logo)

    q = t + DOWN * 1.55
    calca = Polygon(q + LEFT * 0.85, q + RIGHT * 0.85, q + DOWN * 0.55 + RIGHT * 0.70,
                    q + DOWN * 0.55 + LEFT * 0.70, fill_color=TERNO_ESC, fill_opacity=1,
                    stroke_color=PT, stroke_width=8)

    grupo = VGroup(pesc, calca, camisa, gravata, be, bd1, bd2, maoE,
                   blazerE, blazerD, lapelaE, lapelaD, microfone, maoD,
                   orE, orD, cabelo, topete, cab,
                   barba, olhoE_branco, olhoD_branco, sobE, sobD, oe, od, nariz, boca)
    return dict(grupo=grupo, cab=cab, oe=oe, od=od, boca=boca,
               maoE=maoE, maoD=maoD, sobE=sobE, sobD=sobD, microfone=microfone)


# =====================================================================
#  ESTÚDIO DO PLANTÃO — telejornal de bairro (visual v2, 23/09/2026)
#
#  Antes era um lençol pendurado com um mapa desenhado à mão: interior,
#  cinza, o mesmo em todo dia. O Reel perdia o que o perfil tem de mais
#  reconhecível — o LUGAR. Agora o fundo é um TELÃO com a paisagem do Sul
#  Fluminense (a Serra da Mantiqueira ao fundo, o Rio Paraíba do Sul
#  cortando o vale e as chaminés da usina de Volta Redonda), e o céu desse
#  telão É o tempo do dia: sol, nublado, chuva, tempestade ou frio.
#
#  Na frente, uma bancada de telejornal com o selo "AO VIVO" piscando e o
#  relógio do plantão. O Juarez fica atrás dela, do peito pra cima — o que
#  libera a parte de cima da tela pros cartões sem cobrir o rosto dele (no
#  visual antigo o número do gancho tampava a cara do personagem).
#
#  Tudo que se mexe aqui (nuvem, fumaça, chuva, luz do AO VIVO) tem período
#  que divide a duração do vídeo: o último frame continua igual ao primeiro,
#  e o loop do Reel não emenda.
# =====================================================================
CEU_TELAO = {
    # (topo, horizonte, cor da serra ao fundo, cor da serra da frente)
    "sol":        ("#3f95d6", "#bfe6f7", "#6f9fb5", "#4f7f62"),
    "nublado":    ("#7f8e9c", "#cfd6dc", "#8a9aa6", "#5b7566"),
    "chuva":      ("#4c5a6b", "#8e9aa6", "#6a7784", "#465c52"),
    "tempestade": ("#262d3a", "#5c6474", "#4a5362", "#34463f"),
    "frio":       ("#8fb1c9", "#e7eef3", "#a7bccb", "#6e8a80"),
}

# Geometria do telão (unidades do Manim, quadro 8 x 14.222).
TELAO_W, TELAO_H = 7.2, 8.6
TELAO_Y = 1.35             # centro: vai de -2.95 a 5.65
BANCADA_TOPO = -3.05       # o Juarez aparece do peito pra cima
Y_LEGENDA_BANCADA = -3.62  # a legenda karaokê corre na frente da bancada


def _serra(pontos_y, x0, x1, base, cor):
    n = len(pontos_y)
    xs = np.linspace(x0, x1, n)
    topo = [[x, y, 0] for x, y in zip(xs, pontos_y)]
    return VMobject(fill_color=cor, fill_opacity=1, stroke_width=0).set_points_as_corners(
        topo + [[x1, base, 0], [x0, base, 0], topo[0]])


def _chamine(x, base, alt, larg=0.26):
    corpo = Polygon([x - larg / 2, base, 0], [x + larg / 2, base, 0],
                    [x + larg * 0.36, base + alt, 0], [x - larg * 0.36, base + alt, 0],
                    fill_color="#5b4f4a", fill_opacity=1, stroke_color=PT, stroke_width=3)
    faixas = VGroup(*[Rectangle(width=larg * (0.86 - 0.12 * k), height=0.11,
                                fill_color="#c0392b", fill_opacity=1, stroke_width=0)
                      .move_to([x, base + alt * (0.62 + 0.16 * k), 0]) for k in range(2)])
    return VGroup(corpo, faixas)


def _nuvem_telao(escala, cor, op):
    n = VGroup(*[Circle(radius=r, fill_color=cor, fill_opacity=op, stroke_width=0)
                 for r in (0.34, 0.5, 0.4)])
    n[0].shift(LEFT * 0.48 + DOWN * 0.06)
    n[2].shift(RIGHT * 0.5 + DOWN * 0.04)
    base = RoundedRectangle(width=1.7, height=0.42, corner_radius=0.2, fill_color=cor,
                            fill_opacity=op, stroke_width=0).shift(DOWN * 0.22)
    return VGroup(n, base).scale(escala)


def estudio_juarez(cenario="sol", hora="06:00", rotulo="PLANTÃO SUL FLU", vivo="AO VIVO"):
    """Cenário do Juarez. Devolve dict com:
        grupo    -> fundo (telão + paisagem), atrás do personagem
        bancada  -> a bancada, que vai NA FRENTE do personagem
        piso_y   -> onde os pés dele ficam (escondidos atrás da bancada)
        vivos    -> alças do que se mexe, pra animar_estudio()
    """
    W = config.frame_width
    H = config.frame_height
    topo_ceu, horiz, serra_fundo, serra_frente = CEU_TELAO.get(cenario, CEU_TELAO["sol"])
    g = VGroup()
    vivos = {"nuvens": [], "fumaca": [], "chuva": None, "luz": None, "sol": None}

    # parede do estúdio: azul-marinho de telejornal, com um brilho no centro
    g.add(Rectangle(width=W + 2, height=H + 2, fill_opacity=1, stroke_width=0)
          .set_color(["#0e1a2b", "#1d3552"]).set_sheen_direction(UP))

    # ---- o telão ---------------------------------------------------------
    x0, x1 = -TELAO_W / 2, TELAO_W / 2
    y0, y1 = TELAO_Y - TELAO_H / 2, TELAO_Y + TELAO_H / 2
    ceu = Rectangle(width=TELAO_W, height=TELAO_H, fill_opacity=1, stroke_width=0) \
        .set_color([topo_ceu, horiz]).set_sheen_direction(DOWN).move_to([0, TELAO_Y, 0])
    g.add(ceu)

    if cenario in ("sol", "frio"):
        cor_sol = "#ffd34e" if cenario == "sol" else "#fff4c8"
        halo = Circle(radius=0.95, fill_color=cor_sol, fill_opacity=0.22, stroke_width=0)
        disco = Circle(radius=0.62, fill_color=cor_sol, fill_opacity=1,
                       stroke_color="#e8a93a", stroke_width=5)
        raios = VGroup(*[Line(RIGHT * 0.78, RIGHT * 1.08, stroke_color=cor_sol, stroke_width=7)
                         .rotate(a, about_point=ORIGIN) for a in np.arange(0, TAU, TAU / 12)])
        sol = VGroup(halo, raios, disco).move_to([2.05, y1 - 1.9, 0])
        g.add(sol)
        vivos["sol"] = raios

    cor_nuvem = {"sol": "#ffffff", "frio": "#f4f7fa", "nublado": "#eef1f4",
                 "chuva": "#b7c1cb", "tempestade": "#6d7686"}[cenario] \
        if cenario in ("sol", "frio", "nublado", "chuva", "tempestade") else "#ffffff"
    n_nuvens = {"sol": 2, "frio": 2, "nublado": 4, "chuva": 5, "tempestade": 5}.get(cenario, 2)
    posic = [(-2.2, y1 - 1.5, 0.95), (0.9, y1 - 2.6, 0.75), (-0.6, y1 - 0.9, 1.1),
             (2.3, y1 - 1.2, 0.9), (-2.6, y1 - 3.0, 0.8)]
    for k in range(n_nuvens):
        x, y, e = posic[k]
        n = _nuvem_telao(e, cor_nuvem, 0.95).move_to([x, y, 0])
        g.add(n)
        vivos["nuvens"].append((n, x, 0.18 + 0.07 * k, k))

    # a serra ao fundo (Mantiqueira) e os morros da frente
    horizonte = y0 + 3.05
    g.add(_serra([horizonte + v for v in (0.9, 1.6, 1.25, 2.05, 1.5, 1.85, 1.05, 1.55, 0.8)],
                 x0, x1, y0, serra_fundo))
    g.add(_serra([horizonte + v for v in (0.35, 0.75, 0.3, 0.55, 0.95, 0.45, 0.2, 0.6)],
                 x0, x1, y0, serra_frente))

    # o Rio Paraíba do Sul atravessando o vale
    rio = VMobject(fill_color="#6fb3d6" if cenario in ("sol", "frio") else "#7f98aa",
                   fill_opacity=1, stroke_width=0)
    ry = horizonte - 0.55
    rio.set_points_smoothly([[x0, ry + 0.05, 0], [-1.6, ry - 0.22, 0], [0.4, ry + 0.12, 0],
                             [2.2, ry - 0.15, 0], [x1, ry, 0], [x1, ry - 0.42, 0],
                             [2.2, ry - 0.55, 0], [0.4, ry - 0.3, 0], [-1.6, ry - 0.62, 0],
                             [x0, ry - 0.38, 0], [x0, ry + 0.05, 0]])
    g.add(rio)
    g.add(Rectangle(width=TELAO_W, height=ry - 0.45 - y0, fill_color="#3e5c4a", fill_opacity=1,
                    stroke_width=0).move_to([0, (ry - 0.45 + y0) / 2, 0]))

    # a usina: galpões e as chaminés listradas que o Sul Fluminense conhece
    base_u = horizonte + 0.05
    galpoes = VGroup(*[Rectangle(width=w, height=h, fill_color=c, fill_opacity=1,
                                 stroke_color=PT, stroke_width=3)
                       .move_to([x, base_u + h / 2, 0])
                       for x, w, h, c in [(-2.55, 1.1, 0.55, "#7c6f69"), (-1.6, 0.8, 0.8, "#8b7d75"),
                                          (-0.85, 0.7, 0.45, "#74685f")]])
    chamines = VGroup(_chamine(-2.3, base_u, 2.0), _chamine(-1.85, base_u, 2.45),
                      _chamine(-1.35, base_u, 1.75))
    g.add(galpoes, chamines)
    for k, ch in enumerate(chamines):
        topo = ch[0].get_top()
        for j in range(3):
            p = Circle(radius=0.13 + 0.05 * j, fill_color="#e9e6e1", fill_opacity=0.75,
                       stroke_width=0).move_to(topo + UP * (0.25 + 0.3 * j))
            g.add(p)
            vivos["fumaca"].append((p, topo.copy(), j, k))

    # prédios da cidade, à direita do rio
    for x, w, h in [(0.9, 0.5, 0.9), (1.45, 0.45, 1.35), (1.95, 0.55, 1.05),
                    (2.5, 0.42, 1.6), (3.0, 0.5, 1.1)]:
        pr = Rectangle(width=w, height=h, fill_color="#3a4a5c", fill_opacity=1,
                       stroke_color=PT, stroke_width=3).move_to([x, base_u + h / 2 - 0.1, 0])
        luzes = VGroup(*[Square(0.07, fill_color="#ffe08a", fill_opacity=0.9, stroke_width=0)
                         .move_to([x + dx, base_u + dy, 0])
                         for dx in (-w / 4, w / 4) for dy in np.arange(0.2, h - 0.2, 0.28)])
        g.add(pr, luzes)

    # tempo caindo DENTRO do telão
    if cenario in ("chuva", "tempestade"):
        rng = np.random.default_rng(11)
        gotas = VGroup(*[Line(ORIGIN, DOWN * 0.34 + LEFT * 0.08, stroke_color="#dbe9f5",
                              stroke_width=3, stroke_opacity=0.8)
                         .move_to([rng.uniform(x0 + 0.2, x1 - 0.2), rng.uniform(y0 + 0.5, y1 - 0.4), 0])
                         for _ in range(46)])
        g.add(gotas)
        vivos["chuva"] = (gotas, y0 + 0.5, y1 - 0.4)
    if cenario == "frio":
        g.add(*[Rectangle(width=TELAO_W, height=0.5, fill_color=WHITE, fill_opacity=0.18,
                          stroke_width=0).move_to([0, horizonte + dy, 0]) for dy in (-0.2, 0.35)])

    # moldura do telão e o "reflexo" de vidro
    g.add(Rectangle(width=TELAO_W, height=TELAO_H, fill_opacity=0, stroke_color="#0a121d",
                    stroke_width=14).move_to([0, TELAO_Y, 0]))
    g.add(Polygon([x0 + 0.3, y1, 0], [x0 + 1.3, y1, 0], [x0 + 0.1, y1 - 2.2, 0], [x0, y1 - 2.2, 0],
                  fill_color=WHITE, fill_opacity=0.07, stroke_width=0))

    # ---- a bancada (vai NA FRENTE do personagem) ---------------------------
    bancada = VGroup()
    tampo = RoundedRectangle(width=W + 0.4, height=0.34, corner_radius=0.08,
                             fill_color="#c9d3de", fill_opacity=1, stroke_color=PT,
                             stroke_width=6).move_to([0, BANCADA_TOPO, 0])
    frente = Polygon([-W / 2 - 0.2, BANCADA_TOPO - 0.15, 0], [W / 2 + 0.2, BANCADA_TOPO - 0.15, 0],
                     [W / 2 + 0.2, -H / 2 - 1, 0], [-W / 2 - 0.2, -H / 2 - 1, 0],
                     fill_color="#13243a", fill_opacity=1, stroke_width=0)
    faixa = Rectangle(width=W + 0.4, height=0.16, fill_color="#d63a2f", fill_opacity=1,
                      stroke_width=0).move_to([0, BANCADA_TOPO - 0.26, 0])
    bancada.add(frente, faixa, tampo)

    # AO VIVO + relógio, no canto da bancada (acima da área da interface do IG)
    ponto = Dot(radius=0.075, color="#ff4d3d")
    ao_vivo_txt = Text(vivo, font=FONTE, weight=BOLD, font_size=20, color=WHITE)
    pilula_ao_vivo = VGroup(ponto, ao_vivo_txt).arrange(RIGHT, buff=0.1)
    fundo_av = RoundedRectangle(width=pilula_ao_vivo.width + 0.3, height=0.36, corner_radius=0.18,
                                fill_color="#d63a2f", fill_opacity=1, stroke_width=0)
    pilula_ao_vivo.move_to(fundo_av)
    relogio = Text(hora, font=FONTE, weight=BOLD, font_size=20, color="#13243a")
    fundo_rel = RoundedRectangle(width=relogio.width + 0.3, height=0.36, corner_radius=0.18,
                                 fill_color="#ffd34e", fill_opacity=1, stroke_width=0)
    relogio.move_to(fundo_rel)
    nome = Text(rotulo, font=FONTE, weight=BOLD, font_size=20, color=WHITE)
    fundo_nome = RoundedRectangle(width=nome.width + 0.3, height=0.36, corner_radius=0.06,
                                  fill_color="#13243a", fill_opacity=1, stroke_color=WHITE,
                                  stroke_width=2)
    nome.move_to(fundo_nome)
    tarja = VGroup(VGroup(fundo_av, pilula_ao_vivo), VGroup(fundo_nome, nome),
                   VGroup(fundo_rel, relogio)).arrange(RIGHT, buff=0.12)
    vivos["luz"] = ponto

    return dict(grupo=g, bancada=bancada, tarja=tarja, piso_y=BANCADA_TOPO - 1.2,
                vivos=vivos, telao=(x0, x1, y0, y1))


def animar_estudio(cen, duracao):
    """Liga o movimento do telão. Todo período divide `duracao`: loop limpo."""
    vivos = cen["vivos"]
    def ciclos(periodo_desejado):
        return max(1, round(duracao / periodo_desejado))

    relog = {"t": 0.0}

    def tique(mo, dt):
        relog["t"] += dt
    cen["grupo"].add_updater(tique)

    for n, x, amp, k in vivos["nuvens"]:
        c = ciclos(duracao)                # uma ida e volta por vídeo
        base = n.get_center().copy()
        def upd(mo, dt, base=base, amp=amp, k=k, c=c):
            t = relog["t"]
            mo.move_to(base + RIGHT * amp * 1.6 * np.sin(TAU * c * t / duracao + k))
        n.add_updater(upd)

    per_f = duracao / ciclos(2.4)
    for p, topo, j, k in vivos["fumaca"]:
        r0 = p.width / 2
        def upd(mo, dt, topo=topo, j=j, k=k, r0=r0):
            f = ((relog["t"] / per_f) + j / 3 + k * 0.21) % 1.0
            mo.move_to(topo + UP * (0.2 + 1.0 * f) + RIGHT * 0.35 * f)
            mo.set_fill(opacity=0.75 * (1 - f))
            mo.scale_to_fit_width(2 * r0 * (1 + 0.9 * f))
        p.add_updater(upd)

    if vivos["chuva"] is not None:
        gotas, ylo, yhi = vivos["chuva"]
        alt = yhi - ylo
        c = ciclos(0.9)
        base = [m.get_center().copy() for m in gotas]
        def upd(mo, dt):
            desl = (relog["t"] * c / duracao) % 1.0 * alt
            for m, b in zip(mo, base):
                y = b[1] - desl
                if y < ylo:
                    y += alt
                m.move_to([b[0] + (b[1] - y) * 0.235, y, 0])
        gotas.add_updater(upd)

    if vivos["sol"] is not None:
        raios = vivos["sol"]
        centro = raios.get_center().copy()
        st = {"a": 0.0}
        def upd(mo, dt):
            alvo = TAU / 12 * (relog["t"] / duracao)   # gira um "dente" por vídeo
            mo.rotate(alvo - st["a"], about_point=centro)
            st["a"] = alvo
        raios.add_updater(upd)

    if vivos["luz"] is not None:
        c = ciclos(1.1)
        def upd(mo, dt):
            on = np.cos(TAU * c * relog["t"] / duracao) > -0.2
            mo.set_fill(opacity=1.0 if on else 0.15)
        vivos["luz"].add_updater(upd)


# =====================================================================
#  BOCA POR AMPLITUDE
# =====================================================================
def boca_amp_juarez(estado, largura_base=0.28):
    if estado == "fechada":
        return ArcBetweenPoints(LEFT * 0.20, RIGHT * 0.20, angle=-PI / 4).set_stroke(PT, 8)
    elif estado == "meia":
        return Ellipse(width=largura_base, height=0.13, fill_color="#7a1f2a",
                       fill_opacity=1, stroke_color=PT, stroke_width=6)
    else:
        return Ellipse(width=largura_base * 1.2, height=0.26, fill_color="#7a1f2a",
                       fill_opacity=1, stroke_color=PT, stroke_width=6)


def anexar_lipsync_amp_juarez(scene, ref, cues, escala=1.0):
    relogio = {'t': 0.0}
    estado_atual = {'v': None}
    boca = boca_amp_juarez("fechada").scale(escala).move_to(ref.get_center())

    def upd(mo, dt):
        relogio['t'] += dt
        t = relogio['t']
        v = "fechada"
        for c in cues:
            if c['start'] <= t < c['end']:
                v = c['estado']; break
            if c['start'] > t:
                break
        if v != estado_atual['v']:
            mo.become(boca_amp_juarez(v).scale(escala).move_to(ref.get_center()))
            estado_atual['v'] = v
        else:
            mo.move_to(ref.get_center())

    boca.add_updater(upd)
    scene.add(boca)
    return boca


# =====================================================================
#  PAINEL DE COMPARAÇÃO — hoje vs amanhã, o gimmick visual do personagem
# =====================================================================
def painel_comparacao(hoje, amanha, rotulo="", y=-1.0):
    hoje_g = VGroup(
        Text("HOJE", font=FONTE, weight=BOLD, font_size=22, color="#b0aca4"),
        Text(hoje, font=FONTE, weight=BOLD, font_size=52, color="#b0aca4"),
    ).arrange(DOWN, buff=0.06)
    seta = VGroup(
        Line(LEFT * 0.35, RIGHT * 0.35, stroke_color=WHITE, stroke_width=8),
        Triangle(fill_color=WHITE, fill_opacity=1, stroke_width=0).scale(0.16).rotate(-PI / 2).move_to(RIGHT * 0.35),
    )
    amanha_g = VGroup(
        Text("AMANHÃ", font=FONTE, weight=BOLD, font_size=22, color="#ffd23f"),
        Text(amanha, font=FONTE, weight=BOLD, font_size=64, color="#ffd23f"),
    ).arrange(DOWN, buff=0.06)
    linha = VGroup(hoje_g, seta, amanha_g).arrange(RIGHT, buff=0.35)
    conteudo = VGroup(linha)
    if rotulo:
        rot_txt = Text(rotulo, font=FONTE, weight=BOLD, font_size=24, color=WHITE)
        conteudo = VGroup(linha, rot_txt).arrange(DOWN, buff=0.22)
    fundo = RoundedRectangle(width=conteudo.width + 0.7, height=conteudo.height + 0.5,
                             corner_radius=0.2, fill_color="#1c1c1e", fill_opacity=0.88,
                             stroke_color=WHITE, stroke_width=3)
    fundo.move_to(conteudo)
    return VGroup(fundo, conteudo).move_to([0, y, 0])


# =====================================================================
#  PAINEL DE ALERTA — evento extraordinário (vendaval, temporal, etc.)
#  Visualmente mais urgente que painel_comparacao: vermelho, não escuro.
# =====================================================================
def painel_alerta(titulo, detalhe="", y=-1.0):
    tri = Triangle(fill_color="#f5b400", fill_opacity=1, stroke_color=PT,
                  stroke_width=6).scale(0.42).rotate(0)
    exclam = VGroup(
        Line(UP * 0.14, UP * 0.02, stroke_color=PT, stroke_width=7),
        Dot(DOWN * 0.06, radius=0.028, color=PT),
    ).move_to(tri.get_center() + UP * 0.02)
    icone = VGroup(tri, exclam)

    titulo_g = VGroup(*[Text(l, font=FONTE, weight=BOLD, font_size=40, color=WHITE)
                        for l in titulo.split("\n")]).arrange(DOWN, buff=0.06)
    conteudo = VGroup(icone, titulo_g).arrange(RIGHT, buff=0.25)
    if detalhe:
        det_txt = Text(detalhe, font=FONTE, weight=BOLD, font_size=22, color="#ffd9c4")
        conteudo = VGroup(conteudo, det_txt).arrange(DOWN, buff=0.18)
    if conteudo.width > 6.6:
        conteudo.scale(6.6 / conteudo.width)

    fundo = RoundedRectangle(width=conteudo.width + 0.7, height=conteudo.height + 0.5,
                             corner_radius=0.2, fill_color="#a52a1f", fill_opacity=1,
                             stroke_color="#f5b400", stroke_width=5)
    conteudo.move_to(fundo)
    return VGroup(fundo, conteudo).move_to([0, y, 0])


# =====================================================================
#  PAINEL DE PUBLICIDADE — conteúdo patrocinado/promocional.
#  A tag "PUBLICIDADE" é fixa e sempre visível — não é opcional. O CONAR
#  (autorregulamentação publicitária no Brasil) exige identificação clara
#  de conteúdo pago; tirar essa tag não é uma opção de estilo.
# =====================================================================
def painel_publi(produto, oferta="", y=-1.0):
    tag = Text("PUBLICIDADE", font=FONTE, weight=BOLD, font_size=18, color="#2a1a00")
    tag_fundo = RoundedRectangle(width=tag.width + 0.3, height=tag.height + 0.16,
                                 corner_radius=0.06, fill_color="#ffd23f", fill_opacity=1,
                                 stroke_width=0)
    tag_g = VGroup(tag_fundo, tag)

    produto_g = VGroup(*[Text(l, font=FONTE, weight=BOLD, font_size=42, color=WHITE)
                         for l in produto.split("\n")]).arrange(DOWN, buff=0.06)
    conteudo = VGroup(tag_g, produto_g).arrange(DOWN, buff=0.22)
    if oferta:
        of_txt = Text(oferta, font=FONTE, weight=BOLD, font_size=26, color="#ffd23f")
        conteudo = VGroup(conteudo, of_txt).arrange(DOWN, buff=0.18)
    if conteudo.width > 6.6:
        conteudo.scale(6.6 / conteudo.width)

    fundo = RoundedRectangle(width=conteudo.width + 0.8, height=conteudo.height + 0.55,
                             corner_radius=0.22, fill_color="#4a2f7a", fill_opacity=1,
                             stroke_color="#ffd23f", stroke_width=5)
    conteudo.move_to(fundo)
    return VGroup(fundo, conteudo).move_to([0, y, 0])
