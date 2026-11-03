#!/usr/bin/env python3
"""Piloto isolado inspirado nas gramaticas Data Storytelling e Broadcast News Package
do projeto lemomo-ai/lemo-opuscar. Nao importa o motor nem modifica a producao.
Exige Pillow e ffmpeg; fontes do sistema. Os exemplos sao ficticios e rotulados.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SEGUNDOS = 540, 960, 15, 14
DEMO = {
    "data": "2026-11-03",
    "cidades": [
        {"nome": "Volta Redonda", "min": 19, "max": 28, "cond": "nublado", "chuva_mm": 2.0},
        {"nome": "Barra Mansa", "min": 18, "max": 27, "cond": "chuva", "chuva_mm": 8.0},
        {"nome": "Resende", "min": 17, "max": 26, "cond": "chuva", "chuva_mm": 12.0},
        {"nome": "Porto Real", "min": 18, "max": 29, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Angra dos Reis", "min": 21, "max": 30, "cond": "chuva", "chuva_mm": 15.0},
        {"nome": "Piraí", "min": 18, "max": 27, "cond": "nublado", "chuva_mm": 1.0},
        {"nome": "Quatis", "min": 16, "max": 27, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Rio Claro", "min": 17, "max": 26, "cond": "nublado", "chuva_mm": 3.0},
        {"nome": "Pinheiral", "min": 19, "max": 28, "cond": "sol", "chuva_mm": 0.0},
        {"nome": "Itatiaia", "min": 15, "max": 24, "cond": "chuva", "chuva_mm": 10.0}
    ]
}
CORES = {"sol": "#ffd266", "calor": "#ffc44d", "chuva": "#78c9ea",
         "tempestade": "#ec7b7b", "nublado": "#b5c8d5",
         "frio": "#91ccff", "ameno": "#cde9c3", "abafado": "#ffd082"}
TITULOS = {"sol":"SOL","calor":"CALOR","chuva":"CHUVA","tempestade":"TEMPORAL",
           "nublado":"NUBLADO","frio":"FRIO","ameno":"AMENO","abafado":"ABAFADO"}

def normalizar(dados):
    if not isinstance(dados, dict) or not isinstance(dados.get("cidades"), list):
        raise ValueError("Arquivo sem lista de cidades")
    cidades = []
    for c in dados["cidades"]:
        nome = str(c.get("nome", "")).strip()
        minimo, maximo = float(c["min"]), float(c["max"])
        chuva = float(c.get("chuva_mm") or 0)
        if not nome or not all(math.isfinite(v) for v in (minimo, maximo, chuva)):
            raise ValueError("Cidade ou numero invalido")
        if minimo > maximo or chuva < 0:
            raise ValueError("Minima, maxima ou chuva incoerentes")
        cidades.append(dict(nome=nome, min=minimo, max=maximo,
                            cond=str(c.get("cond", "nublado")), chuva_mm=chuva))
    if not 1 <= len(cidades) <= 20:
        raise ValueError("O piloto aceita de 1 a 20 cidades")
    return cidades

def paginas(cidades):
    return [cidades[i:i+5] for i in range(0, len(cidades), 5)]

@lru_cache(maxsize=32)
def fonte(tamanho, bold=False):
    nome = "/usr/share/fonts/truetype/dejavu/DejaVuSans" + ("-Bold" if bold else "") + ".ttf"
    return ImageFont.truetype(nome, tamanho)

def texto(d, xy, msg, tamanho, cor="#ffffff", bold=False):
    d.text(xy, msg, font=fonte(tamanho, bold), fill=cor)

def pill(d, caixa, cor):
    d.rounded_rectangle(caixa, radius=18, fill=cor)

def compor(t, cidades, estilo, dados_ficticios=True):
    im = Image.new("RGB", (W, H), "#10283f")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 12), fill="#f6c94e")
    texto(d, (31, 38), "PREVISÃO SULFLU", 34, bold=True)
    texto(d, (32, 94), "EXPERIMENTO VISUAL • LEMO OPUSCAR", 16, "#afd1e4")
    d.rectangle((30, 137, W-30, 140), fill="#ffce49")
    if t < 1.35:
        texto(d, (35, 274), "O TEMPO", 54, "#ffe080", True)
        texto(d, (35, 344), "EM MOVIMENTO", 38, "#ffffff", True)
        texto(d, (35, 430), "Boletim visual orientado a dados", 20, "#c0d8e8")
        pill(d, (36, 521, 501, 589), "#203e57")
        texto(d, (52, 538), f"{len(cidades)} CIDADES • 2 ESTILOS", 25, "#ffffff", True)
    elif t >= 12.4:
        texto(d, (36, 305), "QUAL É O SEU BAIRRO?", 32, "#ffe080", True)
        texto(d, (36, 390), "Mande o nome por mensagem", 25, "#ffffff")
        texto(d, (36, 432), "para receber sua previsão local.", 22, "#bfdbe9")
        d.rounded_rectangle((35, 570, 505, 655), radius=18, fill="#ee654f")
        texto(d, (54, 591), "@PREVISAOSULFLU", 31, "#ffffff", True)
    else:
        lista = paginas(cidades)
        duracao_pagina = 11.05 / len(lista)
        page_index = min(int((t-1.35)//duracao_pagina), len(lista)-1)
        page_index = max(0, page_index)
        grupo = lista[page_index]
        elapsed = (t-1.35) - page_index*duracao_pagina
        tag = "GIRO DA REGIÃO" if estilo == "noticiario" else "CHUVA PREVISTA • mm"
        texto(d, (33, 175), tag, 30, "#ffe080", True)
        texto(d, (34, 220), f"Painel {page_index+1}/{len(lista)}", 19, "#bdd2df")
        escala = max(1.0, max(x["chuva_mm"] for x in cidades))
        for i, c in enumerate(grupo):
            progress = min(1.0, max(0.0, (elapsed-i*.18)/.55))
            if progress <= 0:
                continue
            x = int(30+(1-progress)*45)
            y = 286+i*111
            pill(d, (x, y, 507, y+96), "#1d3c54")
            cor = CORES.get(c["cond"], "#b5c8d5")
            d.rectangle((x, y, x+7, y+96), fill=cor)
            texto(d, (x+18, y+10), c["nome"][:23], 23, "#ffffff", True)
            if estilo == "noticiario":
                texto(d, (x+18, y+56), TITULOS.get(c["cond"], "TEMPO"), 17, cor, True)
                texto(d, (x+322, y+45), f'{c["min"]:g}° / {c["max"]:g}°', 21, "#ffe080", True)
            else:
                valor = c["chuva_mm"]
                largura = 288 * (valor/escala) * progress
                d.rounded_rectangle((x+18, y+58, x+307, y+76), radius=9, fill="#38566a")
                if largura > 0:
                    d.rounded_rectangle((x+18, y+58, x+18+largura, y+76), radius=9, fill=cor)
                texto(d, (x+325, y+55), f"{valor:g} mm", 20, "#ffe080", True)
        texto(d, (32, 866), "Mín/max: °C  •  Chuva: acumulado previsto", 17, "#bfd5e1")
    # Marca permanente: nunca tratar o fixture como previsão real.
    d.rounded_rectangle((18, 895, 522, 948), radius=11, fill="#e45d4a")
    rotulo = "DEMONSTRAÇÃO • DADOS FICTÍCIOS • NÃO PUBLICAR" if dados_ficticios else "TESTE COM DADOS REAIS • NÃO PUBLICAR"
    texto(d, (30, 910), rotulo, 16, "#ffffff", True)
    return im

def renderizar(destino, cidades, estilo, dados_ficticios=True):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}",
           "-framerate", str(FPS), "-i", "-", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(destino)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for frame in range(FPS*SEGUNDOS):
            proc.stdin.write(compor(frame/FPS, cidades, estilo, dados_ficticios).tobytes())
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg falhou")
    if destino.stat().st_size < 10000:
        raise ValueError("Arquivo MP4 incompleto")
    return destino

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dados", help="JSON real do pipeline com cidades (ainda permanece DEMO)")
    p.add_argument("--estilo", choices=["noticiario", "dados"], required=True)
    p.add_argument("--saida", required=True)
    args = p.parse_args()
    payload = json.loads(Path(args.dados).read_text(encoding="utf-8")) if args.dados else DEMO
    cidades = normalizar(payload)
    video = renderizar(args.saida, cidades, args.estilo, dados_ficticios=not bool(args.dados))
    print(json.dumps({"video":str(video), "estilo":args.estilo,
                      "cidades":len(cidades),"duracao_s":SEGUNDOS,
                      "fonte":"arquivo externo" if args.dados else "EXEMPLO FICTICIO",
                      "publicacao":False}, ensure_ascii=False))

if __name__ == "__main__":
    main()
