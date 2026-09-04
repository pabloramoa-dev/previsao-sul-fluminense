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

O desenho abaixo e o da skill, sem retoque, de proposito: o personagem ja foi ao
ar e mexer no traco agora misturaria duas variaveis no experimento de 14 dias. O
que mudou foram so os imports — o `dvh_lib` mora aqui do lado, e o
`ranzinza_lib` que a skill importava nunca chegou a ser usado por este arquivo.

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
    mic_logo = Text("@psf", font=FONTE, weight=BOLD, font_size=11, color=WHITE).move_to(mic_espuma).rotate(PI/2)
    microfone = VGroup(mic_corpo, mic_espuma, mic_logo)

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
#  ESTÚDIO IMPROVISADO — lençol de fundo, luminária como refletor,
#  mapa do tempo desenhado à mão. Interior, à noite — o único dos três
#  cenários que não é do lado de fora.
# =====================================================================
def estudio_juarez():
    W = config.frame_width
    H = config.frame_height
    g = VGroup()
    g.add(Rectangle(width=W + 2, height=H + 2, fill_opacity=1, stroke_width=0)
         .set_color(["#2a2620", "#100e0c"]).set_sheen_direction(UP))

    # lençol pendurado como fundo (com dobras)
    lencol = Rectangle(width=W - 0.6, height=H * 0.78, fill_color="#e8e2d4",
                       fill_opacity=1, stroke_width=0).move_to([0, H * 0.13, 0])
    dobras = VGroup(*[
        VMobject(stroke_color="#c9c2b0", stroke_width=3, stroke_opacity=0.6).set_points_smoothly([
            [x, lencol.get_top()[1], 0], [x + 0.15, lencol.get_center()[1], 0],
            [x - 0.05, lencol.get_bottom()[1], 0]])
        for x in np.arange(-W / 2 + 1.0, W / 2 - 0.5, 0.85)
    ])
    g.add(lencol, dobras)

    # mapa do tempo desenhado à mão, colado na parede (canto superior esquerdo)
    mapa_fundo = Rectangle(width=1.9, height=1.5, fill_color="#f5f1e6", fill_opacity=1,
                           stroke_color=PT, stroke_width=5).move_to([-W / 2 + 1.7, H / 2 - 3.1, 0])
    sol_desenho = VGroup(
        Circle(radius=0.18, stroke_color="#c98f2e", stroke_width=5, fill_opacity=0).move_to(mapa_fundo.get_center() + UP * 0.3 + LEFT * 0.35),
        *[Line(ORIGIN, RIGHT * 0.1, stroke_color="#c98f2e", stroke_width=4).rotate(a).shift(
            mapa_fundo.get_center() + UP * 0.3 + LEFT * 0.35 + np.array([np.cos(a), np.sin(a), 0]) * 0.2)
          for a in np.arange(0, TAU, TAU / 6)])
    nuvem_desenho = VGroup(*[
        Circle(radius=rr, stroke_color="#5a6a78", stroke_width=4, fill_opacity=0)
        for rr in [0.14, 0.18, 0.14]
    ])
    nuvem_desenho[0].shift(LEFT * 0.18); nuvem_desenho[2].shift(RIGHT * 0.18)
    nuvem_desenho.move_to(mapa_fundo.get_center() + DOWN * 0.15 + RIGHT * 0.3)
    seta_desenho = Line(mapa_fundo.get_center() + LEFT * 0.55 + DOWN * 0.5,
                        mapa_fundo.get_center() + RIGHT * 0.4 + DOWN * 0.35,
                        stroke_color="#8a2f28", stroke_width=5)
    fita = lambda p: Rectangle(width=0.22, height=0.12, fill_color="#e8e2d4", fill_opacity=0.75,
                               stroke_width=0).rotate(PI / 4).move_to(p)
    fitas = VGroup(fita(mapa_fundo.get_corner(UL)), fita(mapa_fundo.get_corner(UR)))
    g.add(mapa_fundo, sol_desenho, nuvem_desenho, seta_desenho, fitas)

    # luminária de mesa como refletor — luz dura, não ambiente
    base_luz = [W / 2 - 1.3, -H / 2 + 2.0, 0]
    haste = Line(base_luz, [base_luz[0] - 0.3, base_luz[1] + 1.8, 0], stroke_color="#3a3a3c", stroke_width=9)
    cupula = Polygon(haste.get_end() + LEFT * 0.35, haste.get_end() + RIGHT * 0.35,
                     haste.get_end() + DOWN * 0.35 + RIGHT * 0.18, haste.get_end() + DOWN * 0.35 + LEFT * 0.18,
                     fill_color="#4a4a4c", fill_opacity=1, stroke_color=PT, stroke_width=6)
    cone = Polygon(cupula.get_bottom() + LEFT * 0.15, cupula.get_bottom() + RIGHT * 0.15,
                   cupula.get_bottom() + DOWN * 3.5 + RIGHT * 1.6, cupula.get_bottom() + DOWN * 3.5 + LEFT * 1.6,
                   fill_color="#fff3c4", fill_opacity=0.22, stroke_width=0)
    base = Rectangle(width=0.4, height=0.12, fill_color="#3a3a3c", fill_opacity=1, stroke_width=0).move_to(base_luz)
    g.add(cone, haste, cupula, base)

    piso_y = -H / 2 + 2.0
    g.add(Rectangle(width=W + 2, height=2.0, fill_color="#4a4038", fill_opacity=1,
                    stroke_width=0).move_to([0, piso_y - 1.0, 0]))

    return dict(grupo=g, piso_y=piso_y)


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
