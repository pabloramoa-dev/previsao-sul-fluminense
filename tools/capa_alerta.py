"""Capa 1080x1920 de alertas reais, com texto seguro no recorte da grade."""
import argparse
import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
EVENTOS = {
    "temporal": ("RISCO DE", "TEMPORAL", (255, 174, 69)),
    "chuva": ("CHUVA", "INTENSA", (80, 210, 255)),
    "granizo": ("RISCO DE", "GRANIZO", (166, 204, 255)),
    "vento": ("VENTOS", "FORTES", (105, 226, 198)),
}


def fonte(tamanho, negrito=True):
    return ImageFont.truetype(FONT_BOLD if negrito else FONT_REG, tamanho)


def ajustar(draw, texto, max_largura, tamanho=70, minimo=36):
    while tamanho > minimo and draw.textbbox((0, 0), texto, font=fonte(tamanho))[2] > max_largura:
        tamanho -= 2
    return fonte(tamanho)


def detalhes(rel):
    """Não transformar previsão em aviso oficial nem inventar cidade/horário."""
    if not rel.get("publicar"):
        raise ValueError("Sem alerta confirmado para criar capa")
    if rel.get("modo") == "aviso_oficial_inmet":
        av = rel.get("aviso_oficial") or {}
        if av.get("fonte") != "INMET" or av.get("evento") != "Tempestade":
            raise ValueError("Aviso INMET inválido")
        fim = datetime.fromisoformat(av["fim"])
        return ("ALERTA", "AMARELO", (255, 195, 77),
                "SUL FLUMINENSE", fim, "AVISO OFICIAL DO INMET")
    eventos = rel.get("eventos") or []
    if not eventos:
        raise ValueError("Nenhum evento meteorológico corroborado")
    evento = eventos[0]
    if evento["tipo"] not in EVENTOS:
        raise ValueError(f"Tipo desconhecido: {evento['tipo']}")
    a, b, cor = EVENTOS[evento["tipo"]]
    return a, b, cor, evento["local"].upper(), datetime.fromisoformat(evento["fim"]), "PREVISÃO • 2 MODELOS"


def gerar_capa(rel, destino):
    a, b, cor, local, fim, base = detalhes(rel)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), (11, 26, 46))
    pixels = img.load()
    # Gradiente discreto e contraste alto para leitura em miniaturas.
    for y in range(H):
        k = y / H
        rgb = (int(9 + 11 * k), int(24 + 10 * k), int(45 + 13 * k))
        for x in range(W):
            pixels[x, y] = rgb
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 22), fill=cor)
    d.text((76, 120), "PREVISÃO SULFLU", font=fonte(55), fill=(245, 248, 255))
    d.text((78, 199), "PLANTÃO METEOROLÓGICO", font=fonte(32, False), fill=(173, 192, 214))
    # A grade do Instagram pode cortar 1:1 ou 3:4: manter o conteúdo entre y=410 e 1480.
    d.rounded_rectangle((55, 365, 1025, 1525), radius=58, fill=(19, 42, 67),
                        outline=(65, 87, 111), width=4)
    d.rounded_rectangle((94, 420, 725, 525), radius=27, fill=cor)
    d.text((124, 445), "ALERTA METEOROLÓGICO", font=ajustar(d, "ALERTA METEOROLÓGICO", 565, 39),
           fill=(13, 30, 47))
    # Pictograma próprio: raio e gotículas, sem usar símbolo ambíguo 0!.
    d.polygon([(850, 440), (793, 527), (846, 527), (820, 611),
               (936, 494), (874, 494), (916, 440)], fill=cor)
    d.text((92, 650), a, font=ajustar(d, a, 875, 106, 70), fill=(245, 248, 255))
    d.text((92, 780), b, font=ajustar(d, b, 875, 109, 66), fill=cor)
    d.line((95, 948, 985, 948), fill=(70, 101, 131), width=3)
    d.text((96, 1004), "REGIÃO / MUNICÍPIO", font=fonte(34), fill=(183, 201, 220))
    d.text((94, 1066), local, font=ajustar(d, local, 890, 63, 38), fill=(255, 255, 255))
    # Mostrar a data real do término: não usar 'hoje' se o risco termina amanhã.
    vencimento = f"ATÉ {fim:%d/%m} ÀS {fim:%H:%M}"
    d.text((95, 1191), vencimento, font=ajustar(d, vencimento, 890, 56, 42), fill=cor)
    d.rounded_rectangle((94, 1303, 984, 1420), radius=24, fill=(32, 65, 94))
    d.text((116, 1338), base, font=ajustar(d, base, 840, 42, 33), fill=(235, 242, 250))
    d.text((78, 1652), "ACOMPANHE A DEFESA CIVIL", font=fonte(44), fill=(240, 245, 250))
    d.text((80, 1733), "@previsaosulflu", font=fonte(38, False), fill=(187, 211, 229))
    img.save(destino, format="JPEG", quality=93, subsampling=0, optimize=True)
    with Image.open(destino) as check:
        if check.size != (W, H) or check.format != "JPEG":
            raise ValueError("Capa inválida: tamanho ou formato incorretos")
    if destino.stat().st_size < 18000:
        raise ValueError("Capa suspeita: arquivo pequeno demais")
    return destino


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--consulta", required=True)
    ap.add_argument("--saida", default="saida/alertas/CAPA_ALERTA.jpg")
    a = ap.parse_args()
    rel = json.loads(Path(a.consulta).read_text(encoding="utf-8"))
    print(gerar_capa(rel, a.saida))


if __name__ == "__main__":
    main()
