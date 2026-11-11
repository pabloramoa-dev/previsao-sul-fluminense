#!/usr/bin/env python3
"""Acabamento/QA de Reels SulFlu: gancho visual seguro, capa e duração 20–25s."""
import argparse
import json
import subprocess
from pathlib import Path

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LARGURA, ALTURA = 1080, 1920
# Faixa segura: x=70..1010, y=315..630; fora do topo/rodapé do Instagram.
CAIXA = (64, 320, 952, 338)

def cmd(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def duracao(path):
    return float(cmd("ffprobe", "-v", "error", "-show_entries",
                     "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                     str(path)).strip())

def finalizar(video, metadata):
    video, metadata = Path(video), Path(metadata)
    info = json.loads(metadata.read_text(encoding="utf-8"))
    fonte = Path(FONTE)
    if not fonte.exists():
        raise RuntimeError("Fonte para títulos não encontrada; instalar fonts-dejavu-core")
    if any([CAIXA[0] < 60, CAIXA[1] < 250, CAIXA[0]+CAIXA[2] > 1020,
            CAIXA[1]+CAIXA[3] > 1550]):
        raise ValueError("Texto fora da área segura do Reel")
    antiga = duracao(video)
    if antiga <= 0:
        raise ValueError("MP4 sem duração")
    # Não acelerar demais a fala: erros de roteiro exigem revisão, não truncamento.
    fator = max(1.0, antiga / 23.5) if antiga > 25 else 1.0
    if fator > 1.4:
        raise ValueError(f"Roteiro longo demais ({antiga:.1f}s); não acelerar >40%")
    alvo = antiga / fator
    extensao = max(0.0, 20.5 - alvo)
    titulo = video.parent / "cidade_destaque.txt"
    numero = video.parent / "temperatura_destaque.txt"
    titulo.write_text(info["cidade_destaque"].upper(), encoding="utf-8")
    numero.write_text(f'{info["temperatura_destaque"]}° {info["quando"].upper()}', encoding="utf-8")
    bairro = (info.get("bairro_destaque") or "").strip()
    bairro_txt = video.parent / "bairro_destaque.txt"
    bairro_txt.write_text(f"BAIRRO: {bairro.upper()}" if bairro else "", encoding="utf-8")
    # Textfile elimina escapamento de acentos, dois-pontos e símbolos.
    def visual():
        fx = [f"setpts=(PTS-STARTPTS)/{fator:.5f}", "fps=25"]
        if extensao > 0:
            fx.append(f"tpad=stop_mode=clone:stop_duration={extensao:.3f}")
        fx += [
            "drawbox=x=64:y=320:w=952:h=338:color=0x0B2039@0.92:t=fill:enable='lt(t,3.6)'",
            f"drawtext=fontfile={fonte}:textfile={titulo}:fontcolor=white:fontsize=57:x=90:y=365:enable='lt(t,3.6)'",
            f"drawtext=fontfile={fonte}:textfile={numero}:fontcolor=0xFFD166:fontsize=95:x=90:y=462:enable='lt(t,3.6)'",
        ]
        if bairro:
            fx.append(
                f"drawtext=fontfile={fonte}:textfile={bairro_txt}:fontcolor=white:fontsize=37:x=90:y=585:enable='lt(t,3.6)'"
            )
        fx += [
        ]
        return ",".join(fx)
    tmp = video.with_name("REEL.final.mp4")
    limite = max(20.5, alvo)
    filtros = f"[0:v]{visual()}[v];[0:a]atempo={fator:.5f},apad=pad_dur={extensao+1:.3f}[a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
                    "-filter_complex", filtros, "-map", "[v]", "-map", "[a]",
                    "-t", f"{limite:.3f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "24", "-pix_fmt", "yuv420p", "-r", "25",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                    str(tmp)], check=True)
    tmp.replace(video)
    final = duracao(video)
    if not 20 <= final <= 25.05:
        raise ValueError(f"Reel fora de 20–25 segundos: {final:.2f}s")
    cap = video.with_name("CAPA.jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.35",
                    "-i", str(video), "-frames:v", "1", "-q:v", "3", str(cap)], check=True)
    resolucao = cmd("ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=width,height", "-of", "csv=p=0",
                    str(video)).strip()
    if resolucao != "1080,1920":
        raise ValueError(f"Resolução inválida: {resolucao}")
    qa = {"validado": True, "duracao_original_s": round(antiga, 2),
          "duracao_final_s": round(final, 2), "resolucao": resolucao,
          "capa": cap.name, "area_segura_px": CAIXA,
          "gancho": info["gancho"], "formato": info["formato"]}
    video.with_name("REEL.sulflu_quality.json").write_text(
        json.dumps(qa, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return qa

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--video", type=Path, required=True)
    a.add_argument("--meta", type=Path, required=True)
    args = a.parse_args()
    print(json.dumps(finalizar(args.video, args.meta), ensure_ascii=False))
