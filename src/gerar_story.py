# -*- coding: utf-8 -*-
"""
gerar_story.py - Gera a imagem 1080x1920 do Story diario com a
pergunta do dia em layout de enquete visual.

NOTA: a Graph API publica a imagem do Story, mas o sticker interativo
de enquete NAO e suportado via API. O layout simula a enquete e
direciona o usuario para os comentarios do post do feed.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent.parent
FONTES = BASE / "assets" / "fontes"
OUTPUT = BASE / "assets" / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920


def _fonte(tam: int, bold: bool = False):
    nome = "bold.ttf" if bold else "regular.ttf"
    try:
        return ImageFont.truetype(str(FONTES / nome), tam)
    except OSError:
        try:
            return ImageFont.truetype(
                "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", tam)
        except OSError:
            return ImageFont.load_default()


def _gradiente(tipo: str) -> Image.Image:
    top, bot = ((56, 142, 220), (18, 24, 56)) if tipo == "noite" else ((56, 142, 220), (135, 206, 250))
    img = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t),
        ))
    return img


def _centralizar(d, y, texto, fonte, cor, max_w=W - 140):
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if d.textlength(teste, font=fonte) <= max_w:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    for l in linhas:
        w = d.textlength(l, font=fonte)
        d.text(((W - w) / 2, y), l, font=fonte, fill=cor)
        y += fonte.size + 18
    return y


def _opcao(d, y, texto, cor_caixa):
    """Desenha uma 'opcao' de enquete simulada."""
    x0, x1 = 120, W - 120
    d.rounded_rectangle([x0, y, x1, y + 130], radius=30, fill=cor_caixa)
    w = d.textlength(texto, font=_fonte(48, bold=True))
    d.text(((W - w) / 2, y + 38), texto, font=_fonte(48, bold=True), fill=(30, 30, 30))
    return y + 170


def gerar_story(pergunta: str, opcao_a: str, opcao_b: str,
                tipo: str = "manha") -> str:
    img = _gradiente(tipo)
    d = ImageDraw.Draw(img)
    y = 360
    y = _centralizar(d, y, "ENQUETE DO DIA", _fonte(52, bold=True), (255, 214, 10))
    y += 40
    y = _centralizar(d, y, pergunta, _fonte(64, bold=True), (255, 255, 255))
    y += 80
    y = _opcao(d, y, opcao_a, (255, 255, 255))
    y = _opcao(d, y, opcao_b, (255, 235, 180))
    y += 60
    _centralizar(d, y, "Responde no post do feed! Arrasta pra cima",
                 _fonte(40), (255, 255, 255))
    _centralizar(d, H - 180, "@previsaosulfluminense", _fonte(44, bold=True), (255, 255, 255))
    caminho = OUTPUT / f"story_{tipo}.png"
    img.save(caminho, "PNG")
    return str(caminho)


def dividir_opcoes(pergunta: str) -> tuple[str, str]:
    """
    Extrai 2 opcoes de uma pergunta fechada quando possivel.
    Ex: 'Cafe ou chocolate quente?' -> ('Cafe', 'Chocolate quente')
    Fallback: ('Opcao A', 'Opcao B').
    """
    base = pergunta.split("?")[0]
    if " ou " in base:
        partes = base.rsplit(":", 1)[-1].split(" ou ")
        if len(partes) == 2:
            a = partes[0].strip().strip(",.").capitalize()
            b = partes[1].strip().strip(",.").capitalize()
            # remove emojis simples do fim
            return a, b
    return "Sim", "Nao"


if __name__ == "__main__":
    p = "Frio de manha pede: cafe ou chocolate quente?"
    a, b = dividir_opcoes(p)
    print(gerar_story(p, a, b, "manha"))
