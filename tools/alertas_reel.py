#!/usr/bin/env python3
"""Converte gatilhos reais do SulFlu em Reels de 14s; mantém antispam existente."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src import alertas, captions
from src.cards_html import motor as gc
from src.main import _coletar

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TZ = ZoneInfo("America/Sao_Paulo")

def executar(*args):
    subprocess.run(args, check=True)

def criar_video(capa, arquivo, cidade, hora, titulo):
    arquivo = Path(arquivo)
    cidade_txt = arquivo.with_suffix(".cidade.txt")
    hora_txt = arquivo.with_suffix(".hora.txt")
    titulo_txt = arquivo.with_suffix(".titulo.txt")
    audio = arquivo.with_suffix(".wav")
    cidade_txt.write_text(cidade.upper(), encoding="utf-8")
    hora_txt.write_text(f"BOLETIM {hora}  •  SUL FLUMINENSE", encoding="utf-8")
    titulo_txt.write_text(titulo.replace("ALERTA:", "").strip(), encoding="utf-8")
    fala = f"Atenção, {cidade}! {titulo.replace('ALERTA:', '')}. Boletim das {hora.replace(':', ' e ')}. Acompanhe novas atualizações."
    executar("espeak-ng", "-v", "pt-br", "-s", "150", "-w", str(audio), fala)
    vf = ",".join([
        "scale=1080:1920",
        "zoompan=z='min(zoom+0.0003,1.035)':d=1:s=1080x1920:fps=25",
        "drawbox=x=58:y=315:w=965:h=370:color=0x0B2039@0.91:t=fill",
        f"drawtext=fontfile={FONTE}:textfile={cidade_txt}:fontsize=56:fontcolor=white:x=80:y=345",
        f"drawtext=fontfile={FONTE}:textfile={hora_txt}:fontsize=36:fontcolor=0xFFD166:x=80:y=442",
        f"drawtext=fontfile={FONTE}:textfile={titulo_txt}:fontsize=42:fontcolor=white:x=80:y=517",
    ])
    executar("ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "25",
             "-i", str(capa), "-i", str(audio), "-filter_complex",
             f"[0:v]{vf}[v];[1:a]apad=pad_dur=20,atrim=duration=14[a]",
             "-map", "[v]", "-map", "[a]", "-t", "14", "-r", "25",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", str(arquivo))
    thumb = arquivo.with_suffix(".jpg")
    executar("ffmpeg", "-y", "-loglevel", "error", "-ss", "0.3", "-i", str(arquivo),
             "-frames:v", "1", "-q:v", "3", str(thumb))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(arquivo)], text=True))
    if not (12 <= dur <= 15):
        raise ValueError(f"Alerta fora de 12–15 segundos: {dur}")
    return thumb

def gerar(saida=Path("saida/alertas"), dry_run=False):
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    cidades, _ = _coletar()
    encontrados = alertas.detectar_alertas(cidades)
    agora = datetime.now(TZ)
    hora = agora.strftime("%H:%M")
    dados = []
    for i, evento in enumerate(encontrados[:2], 1):
        cidade = evento["cidades"][0] if evento["cidades"] else "Sul Fluminense"
        codigo = f"alerta_{i:02d}"
        base = saida / codigo
        carta = gc.gerar_card_alerta(evento["tipo"], evento["titulo"],
                                     evento["detalhe"], evento["cidades"])
        # O horário é da EMISSÃO do boletim, não uma hora de início de chuva inferida.
        legenda = (f"{cidade}: alerta no boletim das {hora}! #{''.join(cidade.split())}\n"
                   + captions.caption_alerta(evento["tipo"], evento["detalhe"], evento["cidades"])
                   + "\nManda para quem está nessa região.")
        base.with_suffix(".txt").write_text(legenda+"\n", encoding="utf-8")
        gancho = f"{cidade}: {evento['titulo']} — boletim das {hora}."
        meta = {"formato": "alerta_reel_14s", "gancho": gancho,
                "cidade_destaque": cidade, "horario_brt": hora,
                "tipo_alerta": evento["tipo"], "emitido_em_brt": agora.isoformat(),
                "cidades": evento["cidades"], "horario_tipo": "emissao_do_boletim"}
        base.with_suffix(".json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        criar_video(carta, base.with_suffix(".mp4"), cidade, hora, evento["titulo"])
        dados.append(meta)
    (saida/"manifest.json").write_text(json.dumps(
        {"dry_run": bool(dry_run), "quantidade": len(dados), "alertas": dados},
        ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"alertas_gerados": len(dados), "dry_run": bool(dry_run)}))
    return dados

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, default=Path("saida/alertas"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    gerar(saida=args.saida, dry_run=args.dry_run)
