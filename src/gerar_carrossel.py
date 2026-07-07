# -*- coding: utf-8 -*-
"""
gerar_carrossel.py - Renderiza os slides dos carrosseis com Pillow.
Templates: manha, noite, alerta, fim_de_semana, curiosidade, chuva_acumulada.

Todas as imagens sao 1080x1350 (feed). Stories ficam em gerar_story.py.
Salva PNGs em assets/output/ e retorna a lista de caminhos gerados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent.parent
ASSETS = BASE / "assets"
FONTES = ASSETS / "fontes"
FUNDOS = ASSETS / "fundos"
OUTPUT = ASSETS / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350

# Paletas por tipo de post
PALETAS = {
    "manha": {"bg": (56, 142, 220), "bg2": (135, 206, 250), "texto": (255, 255, 255), "destaque": (255, 214, 10)},
    "noite": {"bg": (18, 24, 56), "bg2": (44, 52, 100), "texto": (235, 238, 255), "destaque": (140, 170, 255)},
    "alerta": {"bg": (200, 40, 30), "bg2": (240, 120, 30), "texto": (255, 255, 255), "destaque": (255, 230, 120)},
    "fim_de_semana": {"bg": (0, 150, 136), "bg2": (77, 208, 195), "texto": (255, 255, 255), "destaque": (255, 235, 59)},
    "curiosidade": {"bg": (94, 53, 177), "bg2": (149, 117, 205), "texto": (255, 255, 255), "destaque": (255, 213, 79)},
    "chuva": {"bg": (38, 50, 78), "bg2": (63, 81, 120), "texto": (235, 240, 255), "destaque": (100, 181, 246)},
}

ICONES_TEMPO = {
    0: "SOL", 1: "SOL", 2: "SOL/NUVENS", 3: "NUBLADO",
    45: "NEBLINA", 48: "NEBLINA", 51: "GAROA", 53: "GAROA", 55: "GAROA",
    61: "CHUVA", 63: "CHUVA", 65: "CHUVA FORTE",
    80: "PANCADAS", 81: "PANCADAS", 82: "PANCADAS FORTES",
    95: "TEMPESTADE", 96: "TEMPESTADE", 99: "TEMPESTADE",
}


def _fonte(tam: int, bold: bool = False):
    """Carrega fonte do repo; cai para default se ausente (dry-run local)."""
    nome = "bold.ttf" if bold else "regular.ttf"
    caminho = FONTES / nome
    try:
        return ImageFont.truetype(str(caminho), tam)
    except OSError:
        try:
            return ImageFont.truetype(
                "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", tam)
        except OSError:
            return ImageFont.load_default()


def _fundo(tipo: str) -> Image.Image:
    """Gera fundo com gradiente vertical usando a paleta do tipo."""
    pal = PALETAS[tipo]
    img = Image.new("RGB", (W, H), pal["bg"])
    top, bot = pal["bg"], pal["bg2"]
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def _texto_centralizado(draw, y, texto, fonte, cor, max_w=W - 120):
    """Desenha texto centralizado horizontalmente; quebra se necessario."""
    linhas = _quebrar(draw, texto, fonte, max_w)
    for linha in linhas:
        bbox = draw.textbbox((0, 0), linha, font=fonte)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((W - w) / 2, y), linha, font=fonte, fill=cor)
        y += h + 14
    return y


def _quebrar(draw, texto, fonte, max_w):
    palavras = texto.split()
    linhas, atual = [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if draw.textlength(teste, font=fonte) <= max_w:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def _salvar(img: Image.Image, nome: str) -> str:
    caminho = OUTPUT / nome
    img.save(caminho, "PNG")
    return str(caminho)


# ----------------------- SLIDES -----------------------

def slide_capa(tipo: str, titulo: str, subtitulo: str, destaque: str) -> str:
    pal = PALETAS[tipo]
    img = _fundo(tipo)
    d = ImageDraw.Draw(img)
    y = 320
    y = _texto_centralizado(d, y, titulo, _fonte(72, bold=True), pal["texto"])
    y += 30
    y = _texto_centralizado(d, y, subtitulo, _fonte(40), pal["texto"])
    y += 60
    if destaque:
        _texto_centralizado(d, y, destaque, _fonte(52, bold=True), pal["destaque"])
    return _salvar(img, f"{tipo}_capa.png")


def slide_cidade(tipo: str, cidade, indice: int, extra: str = "") -> str:
    pal = PALETAS[tipo]
    img = _fundo(tipo)
    d = ImageDraw.Draw(img)
    d.text((60, 120), cidade.nome, font=_fonte(64, bold=True), fill=pal["texto"])
    cond = ICONES_TEMPO.get(cidade.weathercode, "TEMPO VARIAVEL")
    d.text((60, 220), cond, font=_fonte(40), fill=pal["destaque"])
    d.text((60, 380), f"{cidade.tmin:.0f}C / {cidade.tmax:.0f}C",
           font=_fonte(110, bold=True), fill=pal["texto"])
    linhas = [
        f"Chance de chuva: {cidade.prob_chuva:.0f}%",
        f"Volume esperado: {cidade.precipitacao_mm:.1f} mm",
        f"Vento ate: {cidade.vento_max:.0f} km/h",
        f"Umidade: {cidade.umidade:.0f}%",
    ]
    y = 560
    for l in linhas:
        d.text((60, y), l, font=_fonte(44), fill=pal["texto"])
        y += 70
    if extra:
        d.text((60, y + 20), extra, font=_fonte(40, bold=True), fill=pal["destaque"])
    return _salvar(img, f"{tipo}_cidade_{indice}.png")


def slide_indices(itens: list[dict[str, Any]]) -> str:
    pal = PALETAS["manha"]
    img = _fundo("manha")
    d = ImageDraw.Draw(img)
    d.text((60, 120), "RESUMO DO DIA", font=_fonte(60, bold=True), fill=pal["texto"])
    y = 280
    for item in itens:
        marca = "[X]" if item["ativo"] else "[ ]"
        d.text((60, y), f"{marca} {item['texto']}", font=_fonte(42), fill=pal["texto"])
        y += 100
    return _salvar(img, "manha_indices.png")


def slide_sol_lua(tipo: str, resumo: dict[str, Any], nascer: str, por: str,
                  fase_lua: str) -> str:
    pal = PALETAS[tipo]
    img = _fundo(tipo)
    d = ImageDraw.Draw(img)
    d.text((60, 120), "SOL E LUA", font=_fonte(60, bold=True), fill=pal["texto"])
    linhas = [
        f"Nascer do sol: {nascer}",
        f"Por do sol: {por}",
        f"Fase da lua: {fase_lua}",
        f"Indice UV maximo: {resumo.get('uv_max', 0):.0f}",
    ]
    y = 300
    for l in linhas:
        d.text((60, y), l, font=_fonte(46), fill=pal["texto"])
        y += 90
    return _salvar(img, f"{tipo}_sol_lua.png")


def slide_pergunta(tipo: str, pergunta: str, perfil: str = "@previsaosulfluminense") -> str:
    pal = PALETAS[tipo]
    img = _fundo(tipo)
    d = ImageDraw.Draw(img)
    y = 380
    y = _texto_centralizado(d, y, pergunta, _fonte(58, bold=True), pal["texto"])
    y += 60
    y = _texto_centralizado(d, y, "Responde nos comentarios!", _fonte(44), pal["destaque"])
    _texto_centralizado(d, H - 200, perfil, _fonte(40), pal["texto"])
    return _salvar(img, f"{tipo}_pergunta.png")


def slide_texto_livre(tipo: str, titulo: str, corpo: str, nome: str) -> str:
    pal = PALETAS[tipo]
    img = _fundo(tipo)
    d = ImageDraw.Draw(img)
    y = 160
    y = _texto_centralizado(d, y, titulo, _fonte(58, bold=True), pal["destaque"])
    y += 40
    _texto_centralizado(d, y, corpo, _fonte(44), pal["texto"])
    return _salvar(img, f"{tipo}_{nome}.png")


# ----------------------- CARROSSEIS -----------------------

def gerar_carrossel_manha(cidades, resumo, indices_itens, pergunta,
                          fase_lua, recorde=None) -> list[str]:
    slides = []
    destaque = recorde.upper() if recorde else f"{resumo['tmin']:.0f}C a {resumo['tmax']:.0f}C"
    slides.append(slide_capa("manha", "PREVISAO DO TEMPO",
                             resumo["data_extenso"], destaque))
    slides.append(slide_indices(indices_itens))
    for i, c in enumerate(cidades, start=1):
        slides.append(slide_cidade("manha", c, i))
    slides.append(slide_sol_lua("manha", resumo,
                                cidades[0].nascer_sol, cidades[0].por_sol, fase_lua))
    slides.append(slide_pergunta("manha", pergunta))
    return slides


def gerar_carrossel_noite(cidades, resumo, pergunta, fase_lua) -> list[str]:
    slides = []
    slides.append(slide_capa("noite", "COMO SERA A NOITE",
                             resumo["data_extenso"], "SUL FLUMINENSE"))
    for i, c in enumerate(cidades, start=1):
        extra = f"Madrugada: min {c.tmin_madrugada:.0f}C"
        slides.append(slide_cidade("noite", c, i, extra=extra))
    slides.append(slide_texto_livre("noite", "LUA E AMANHA",
                                    f"Fase: {fase_lua}. Amanha o sol nasce as "
                                    f"{cidades[0].nascer_sol}.", "lua_amanha"))
    slides.append(slide_pergunta("noite", pergunta))
    return slides


def gerar_alerta(tipo_alerta: str, titulo: str, detalhe: str, cidades_afetadas) -> str:
    img = _fundo("alerta")
    pal = PALETAS["alerta"]
    d = ImageDraw.Draw(img)
    y = 240
    y = _texto_centralizado(d, y, titulo, _fonte(64, bold=True), pal["texto"])
    y += 60
    y = _texto_centralizado(d, y, detalhe, _fonte(48), pal["destaque"])
    y += 60
    _texto_centralizado(d, y, "Cidades: " + ", ".join(cidades_afetadas),
                        _fonte(40), pal["texto"])
    return _salvar(img, f"alerta_{tipo_alerta}.png")


if __name__ == "__main__":
    # Amostra minima para aprovacao visual (dry-run sem dados reais)
    class _C:
        nome = "Volta Redonda"; tmin = 14; tmax = 19; prob_chuva = 70
        precipitacao_mm = 12.0; weathercode = 63; vento_max = 22; umidade = 82
        tmin_madrugada = 12; temp_21h = 16; nascer_sol = "06:34"; por_sol = "17:28"
    resumo = {"tmin": 14, "tmax": 19, "prob_chuva": 70, "uv_max": 4,
              "data_extenso": "Segunda-feira, 6 de julho de 2026"}
    print(slide_capa("manha", "PREVISAO DO TEMPO", resumo["data_extenso"], "14C a 19C"))
    print(slide_cidade("manha", _C(), 1))
    print(gerar_alerta("chuva_forte", "ALERTA: CHUVA FORTE",
                       "Ate 30mm nas proximas 3h", ["Volta Redonda", "Resende"]))
