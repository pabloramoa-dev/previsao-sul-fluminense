# -*- coding: utf-8 -*-
"""
gerar_card_amanha.py — o CARD das 18h: a previsão de AMANHÃ, com o Juarez.

POR QUE EXISTE (23/09/2026)
---------------------------
Desde o plano v3 o perfil publica um Reel só, às 06h. Quem abre o Instagram à
noite querendo saber o dia seguinte não encontrava nada — e é à noite que se
decide a roupa, o guarda-chuva e a hora de sair. Este card antecipa amanhã e
cria o hábito de voltar às 06h pro plantão completo.

É IMAGEM (post de foto), não Reel, de propósito: o teste_juarez.py trava que
só o juarez.yml publica Reel por agendamento, e o skip rate que ele mede
continua respondendo por um formato só.

O visual é o mesmo do Reel v2 — telão com a paisagem do Sul Fluminense no céu
de AMANHÃ, bancada de telejornal, Juarez de microfone — pra que a grade do
perfil leia como uma série só.

Uso:
    python gerar_card_amanha.py --dados amanha.json --saida CARD.jpg
    python gerar_card_amanha.py --demo --saida CARD.jpg
    python gerar_card_amanha.py --dados amanha.json --so-legenda
    python gerar_card_amanha.py --dados amanha.json --publicar --url <URL do JPG>

Formato: 1080 x 1350 (4:5), JPEG — a API de conteúdo do Instagram só aceita
JPEG em post de imagem.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, RAIZ)

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
N_CIDADES = 6


def dia_semana(data_iso):
    d = datetime.date.fromisoformat(data_iso)
    return DIAS[d.weekday()], d.strftime("%d/%m")


def _chove(c):
    from gerar_dia import chove_de_verdade
    return chove_de_verdade(c)


def cond_card(c):
    """Mesma regra do vídeo e da legenda: garoa não vira chuva."""
    cond = c.get("cond", "sol")
    if cond in ("chuva", "tempestade") and not _chove(c):
        return "nublado"
    return cond


def linha_chuva(cid):
    chuvosas = [c for c in cid if _chove(c)]
    if not chuvosas:
        return "Amanhã: sem chuva prevista."
    pico = max(chuvosas, key=lambda c: c.get("chuva_mm", 0) or 0)
    mm = f"{pico['chuva_mm']:.1f}".replace(".", ",").replace(",0", "")
    return f"Amanhã, chuva: até {mm} mm em {pico['nome']}."


def legenda(dia):
    """Legenda do card. Diz AMANHÃ na primeira linha (validar_legenda exige)."""
    import engajamento
    import postar_reel as PR
    cid = dia["cidades"]
    sem, dm = dia_semana(dia["data"])
    linhas = [f"🎙️ Plantão antecipado: amanhã, {sem} ({dm}), no Sul Fluminense.", ""]
    for c in cid[:N_CIDADES]:
        linhas.append(f"{PR.EMOJI.get(cond_card(c), '🌡️')} {c['nome']}: "
                      f"{c['min']}° / {c['max']}°")
    linhas += ["", "☔ " + linha_chuva(cid)]
    u = dia.get("umidade_min")
    if u and u <= 40:
        linhas += ["💧 Ar seco amanhã: umidade mínima de " + f"{u}%. Deixa a garrafa de água pronta."]
    linhas += ["", "📌 Salva este card e confere amanhã cedo.",
               "⏰ O plantão completo sai às 6h, em vídeo.", "",
               engajamento.hashtags("noite", cond_card(cid[0]),
                                    destaque=dia.get("destaque") or cid[0]["nome"])]
    cap = "\n".join(linhas)
    PR.validar_legenda(cap, quando="amanha")
    PR.validar_coerencia(dia, cap)
    return cap


def cenario_amanha(dia):
    cid = dia["cidades"]
    chuvosas = [c for c in cid if _chove(c)]
    if chuvosas:
        pico = max(chuvosas, key=lambda c: c.get("chuva_mm", 0) or 0)
        return "tempestade" if pico.get("cond") == "tempestade" else "chuva"
    return cond_card(cid[0])


# =====================================================================
#  RENDER — cena Manim de um frame só (manim -s salva a imagem final)
# =====================================================================
CENA = r'''
import json, os, sys
sys.path.insert(0, os.environ["CARD_AQUI"])
from manim import *
import numpy as np
config.pixel_width = 1080
config.pixel_height = 1350
config.frame_width = 8.0
config.frame_height = 10.0
import juarez_lib as J
import vox_papel as VX

D = json.load(open(os.environ["CARD_JSON"], encoding="utf-8"))
PT = J.PT


def icone(cond, s=0.32):
    """Ícone de tempo desenhado (sem emoji: fonte de emoji não é garantida
    no runner do GitHub)."""
    def nuvem(cor="#eef1f4"):
        n = VGroup(*[Circle(radius=r, fill_color=cor, fill_opacity=1, stroke_color=PT,
                            stroke_width=3).shift(d)
                     for r, d in [(0.36, LEFT*0.38+DOWN*0.08), (0.5, UP*0.08), (0.38, RIGHT*0.42+DOWN*0.08)]])
        return VGroup(n, Rectangle(width=1.5, height=0.36, fill_color=cor, fill_opacity=1,
                                   stroke_width=0).shift(DOWN*0.28))
    if cond == "sol":
        g = VGroup(*[Line(RIGHT*0.62, RIGHT*0.9, stroke_color="#f2a900", stroke_width=6)
                     .rotate(a, about_point=ORIGIN) for a in np.arange(0, TAU, TAU/10)],
                   Circle(radius=0.48, fill_color="#ffd34e", fill_opacity=1,
                          stroke_color=PT, stroke_width=3))
    elif cond == "frio":
        g = VGroup(*[Line(UP*0.7, DOWN*0.7, stroke_color="#5aa9e6", stroke_width=8)
                     .rotate(a) for a in (0, PI/3, 2*PI/3)])
    elif cond in ("chuva", "tempestade"):
        g = VGroup(nuvem("#b7c1cb"), *[Line(ORIGIN, DOWN*0.3+LEFT*0.08, stroke_color="#3f95d6",
                                            stroke_width=7).move_to([x, -0.75, 0])
                                       for x in (-0.4, 0.05, 0.5)])
        if cond == "tempestade":
            g.add(Polygon([0.1,-0.45,0],[-0.15,-0.9,0],[0.05,-0.9,0],[-0.1,-1.25,0],[0.3,-0.75,0],
                          [0.1,-0.75,0], fill_color="#ffd34e", fill_opacity=1, stroke_width=0))
    else:
        g = VGroup(Circle(radius=0.4, fill_color="#ffd34e", fill_opacity=1, stroke_width=0)
                   .shift(UP*0.3+RIGHT*0.35), nuvem())
    return g.scale(s)


class Card(Scene):
    def construct(self):
        cen = J.estudio_juarez(D["cenario"], hora="18:00", rotulo="PLANTÃO SUL FLU",
                               vivo="PREVISÃO")
        fundo = cen["grupo"]
        fundo.shift(DOWN * 1.3)
        self.add(fundo)

        v = J.juarez()
        G = v["grupo"]
        G.scale(0.95)
        G.shift(np.array([2.45, -1.55, 0]) - v["cab"].get_center())
        self.add(VX.adesivo_personagem(v, espessura=12), G)

        banc = cen["bancada"]
        banc.shift(UP * (-3.25 - (-3.05)))
        self.add(banc)

        # título: data em tira teal + manchete amarela
        rot = VX.manchete(D["rotulo"], cor_papel="teal", cor_texto="tinta", tam=20,
                          semente=11, juntar=True, desalinho=False, girar=0.02)
        tit = VX.manchete("AMANHÃ NO SUL FLU", cor_papel="amarelo", tam=40, semente=17,
                          juntar=True, largura_max=7.0)
        cab = VGroup(rot, tit).arrange(DOWN, buff=0.04)
        rot.align_to(tit, LEFT).shift(RIGHT * 0.15)
        cab.move_to([0, 3.98, 0])
        self.add(cab)

        # quadro das cidades
        linhas = VGroup()
        for c in D["cidades"]:
            nome = Text(c["nome"], font="Poppins", weight=BOLD, font_size=26, color=WHITE)
            temp = Text(f"{c['min']}° / {c['max']}°", font="Poppins", weight=BOLD,
                        font_size=28, color="#ffd34e")
            linhas.add(VGroup(icone(c["cond"]), nome, temp))
        larg_nome = max(l[1].width for l in linhas)
        util = 0.75 + larg_nome + 0.35 + max(l[2].width for l in linhas)
        for l in linhas:
            l[0].move_to(LEFT * (util/2 - 0.3))
            l[1].move_to(LEFT * (util/2 - 0.7), aligned_edge=LEFT)
            l[2].move_to(RIGHT * (util/2), aligned_edge=RIGHT)
        linhas.arrange(DOWN, buff=0.22)
        if linhas.width > 4.7:
            linhas.scale_to_fit_width(4.7)
        if linhas.height > 3.6:
            linhas.scale_to_fit_height(3.6)
        quadro = VX.colar_painel(VGroup(
            RoundedRectangle(width=linhas.width + 0.6, height=linhas.height + 0.55,
                             corner_radius=0.2, fill_color=BLACK, fill_opacity=0.78,
                             stroke_color=WHITE, stroke_width=3), linhas.copy()), semente=5)
        quadro.move_to([-1.2, 0.8, 0])
        self.add(quadro)

        # na bancada: a linha da chuva e a assinatura
        chuva = Text(D["linha_chuva"], font="Poppins", weight=BOLD, font_size=26,
                     color=WHITE)
        if chuva.width > 7.2:
            chuva.scale_to_fit_width(7.2)
        chuva.move_to([0, -3.85, 0])
        tarja = cen["tarja"].move_to([0, -4.5, 0])
        self.add(chuva, tarja)
        self.add(VX.marca().scale(0.75).move_to([-2.3, -2.72, 0]))
'''


def render(dia, saida, trab=None):
    trab = trab or os.path.join(AQUI, "_trab_card")
    os.makedirs(trab, exist_ok=True)
    cid = dia["cidades"][:N_CIDADES]
    sem, dm = dia_semana(dia["data"])
    dados = {
        "cenario": cenario_amanha(dia),
        "rotulo": f"{sem.upper()} · {dm}",
        "cidades": [{"nome": c["nome"], "min": c["min"], "max": c["max"],
                     "cond": cond_card(c)} for c in cid],
        "linha_chuva": linha_chuva(dia["cidades"]),
    }
    jj = os.path.join(trab, "card.json")
    json.dump(dados, open(jj, "w", encoding="utf-8"), ensure_ascii=False)
    cena = os.path.join(trab, "card_cena.py")
    open(cena, "w", encoding="utf-8").write(CENA)
    env = dict(os.environ, CARD_AQUI=AQUI, CARD_JSON=jj)
    subprocess.run(["manim", "-s", "-qh", "--disable_caching", "--format", "png",
                    "--media_dir", os.path.join(trab, "media"), cena, "Card"],
                   check=True, env=env)
    pngs = []
    for raiz, _, arqs in os.walk(os.path.join(trab, "media", "images")):
        pngs += [os.path.join(raiz, a) for a in arqs if a.endswith(".png")]
    if not pngs:
        raise SystemExit("o Manim não gerou a imagem do card")
    png = max(pngs, key=os.path.getmtime)
    # grão de papel, como no Reel, e JPEG (a API só aceita JPEG em foto)
    try:
        import vox_papel as VX
        tex = VX.textura_png(1080, 1350)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", png, "-i", tex,
                        "-filter_complex", "[0][1]overlay", "-q:v", "2", saida], check=True)
    except Exception as e:                      # textura é enfeite, não trava
        print(f"  (sem textura: {e})")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", png, "-q:v", "2", saida],
                       check=True)
    print(f"pronto: {saida}")
    return saida


# =====================================================================
#  PUBLICAÇÃO — post de imagem via graph.instagram.com (mesmo token do Reel)
# =====================================================================
def publicar(url, cap):
    import postar_reel as PR
    ig_user = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_TOKEN") or os.environ.get("IG_ACCESS_TOKEN")
    if not ig_user or not token:
        sys.exit("faltam as variáveis IG_USER_ID e IG_TOKEN")
    PR.cota(ig_user, token)
    if PR.ja_publicado(ig_user, token, cap):
        raise SystemExit("publicação cancelada: esta legenda já existe entre as 25 mídias recentes")
    print("[1/3] criando o container da imagem")
    r = PR._post(f"{ig_user}/media", {"image_url": url, "caption": cap, "access_token": token})
    cid = r["id"]
    print("[2/3] aguardando a Meta processar")
    PR.esperar_container(cid, token, limite=300)
    print("[3/3] publicando")
    pub = PR.publicar_com_retentativa(ig_user, cid, token)
    print(f"publicado: media id {pub.get('id')}")
    PR.publicar_primeiro_comentario(
        pub.get("id"), token, "🌙 Amanhã você sai cedo? Conta aqui de qual cidade.")
    return pub


DEMO = {
    "data": "2026-09-24",
    "cidades": [
        {"nome": "Volta Redonda", "min": 17, "max": 29, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Barra Mansa", "min": 17, "max": 30, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Resende", "min": 15, "max": 27, "cond": "nublado", "chuva_mm": 0.2},
        {"nome": "Porto Real", "min": 16, "max": 29, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Barra do Piraí", "min": 18, "max": 30, "cond": "chuva", "chuva_mm": 6.4},
        {"nome": "Itatiaia", "min": 13, "max": 24, "cond": "nublado", "chuva_mm": 0.0},
    ],
    "umidade_min": 45,
    "destaque": "Volta Redonda",
}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--saida", default="CARD.jpg")
    ap.add_argument("--so-legenda", action="store_true")
    ap.add_argument("--legenda-saida", default=None, help="grava a legenda num .txt")
    ap.add_argument("--publicar", action="store_true")
    ap.add_argument("--url", help="URL pública do JPG (obrigatória com --publicar)")
    a = ap.parse_args()
    d = DEMO if a.demo or not a.dados else json.load(open(a.dados, encoding="utf-8"))
    cap = legenda(d)
    if a.legenda_saida:
        open(a.legenda_saida, "w", encoding="utf-8").write(cap)
    if a.so_legenda:
        print(cap)
    elif a.publicar:
        if not a.url:
            sys.exit("--publicar exige --url")
        publicar(a.url, cap)
    else:
        render(d, a.saida)
