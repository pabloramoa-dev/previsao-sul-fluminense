#!/usr/bin/env python3
"""Juarez HyperFrames -> Remotion aprovado, com QA e saída atômica.

Não publica. Usa o áudio do vídeo original para preservar integralmente a voz.
Qualquer falha ocorre antes do passo de publicação do workflow.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def sh(*args, cwd=None):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run([str(x) for x in args], cwd=cwd, check=True)


def info(path):
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True))


def check(path, dur):
    p = info(path)
    v = [s for s in p["streams"] if s["codec_type"] == "video"]
    a = [s for s in p["streams"] if s["codec_type"] == "audio"]
    if len(v) != 1 or not a or (v[0]["width"], v[0]["height"]) != (1080, 1920):
        raise ValueError("Remotion: vídeo ou áudio inválido (1080x1920 obrigatório)")
    if v[0]["avg_frame_rate"] != "30/1" or abs(float(p["format"]["duration"])-dur) > .18:
        raise ValueError("Remotion: fps e sincronização divergentes")
    if path.stat().st_size < 100000:
        raise ValueError("Remotion: arquivo incompleto")
    return p


def finalize(video, pacote, dados=None, production=False):
    video = Path(video).resolve()
    pacote = Path(pacote).resolve()
    if not video.is_file() or not pacote.is_file():
        raise FileNotFoundError("Faltou MP4 HyperFrames ou pacote de dados")
    p = json.loads(pacote.read_text(encoding="utf-8"))
    if dados:
        dados_json = json.loads(Path(dados).resolve().read_text(encoding="utf-8"))
        if dados_json["data"] != p["data"]:
            raise ValueError("Dados meteorológicos inconsistentes com vídeo")
    public = ROOT / "public"
    out = ROOT / "out"
    public.mkdir(exist_ok=True, parents=True)
    out.mkdir(exist_ok=True, parents=True)
    original = public / "juarez-original.mp4"
    shutil.copy2(video, original)
    sh("ffmpeg", "-v", "error", "-y", "-i", original, "-vn", "-ar", "44100",
       "-ac", "1", public / "voz-original.wav")
    sh("python", "prepare_props.py", cwd=ROOT)
    props = ROOT / "props.json"
    data = json.loads(props.read_text(encoding="utf-8"))
    data["demo"] = not production
    props.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    expected = data["durationFrames"] / 30
    if not (ROOT / "node_modules/@remotion/cli").exists():
        sh("npm", "install", "--no-audit", "--no-fund", cwd=ROOT)
    sh("npx", "--no-install", "remotion", "browser", "ensure", cwd=ROOT)
    rendered = out / "boletim-sulflu-remotion.mp4"
    sh("npx", "--no-install", "remotion", "render", "src/index.ts", "BoletimSulFlu",
       rendered, f"--props={props}", "--codec=h264", "--crf=21", "--concurrency=2", cwd=ROOT)
    check(rendered, expected)
    preview = out / "preview-remotion.mp4"
    cover = out / "CAPA-remotion.jpg"
    sh("ffmpeg", "-v", "error", "-y", "-i", rendered, "-vf", "scale=720:-2",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
       "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", preview)
    at = max(.0, min(float(p["capa_s"]), expected-.1))
    sh("ffmpeg", "-v", "error", "-y", "-ss", f"{at:.2f}", "-i", rendered,
       "-frames:v", "1", "-q:v", "2", cover)
    if preview.stat().st_size < 100000 or cover.stat().st_size < 10000:
        raise ValueError("Remotion: prévia ou capa inválida")
    # Os três arquivos só mudam depois de toda a validação.
    tmp = video.with_name(video.stem + ".remotion-ready.mp4")
    shutil.copy2(rendered, tmp)
    os.replace(tmp, video)
    os.replace(preview, video.with_name(video.stem + "_preview_720p.mp4"))
    os.replace(cover, video.parent / "CAPA.jpg")
    if dados:
        import sys
        sys.path.insert(0, str(REPO))
        from tools.channel_ops import record_render
        record_render(video, dados_json, REPO)
    (out / "qa-probe.json").write_text(
        json.dumps(check(video, expected), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REMOTION OK: {video.name}, {len(data['cidades'])} cidades, "
          f"voz original, pronto para produção={production}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--pacote", required=True)
    parser.add_argument("--dados")
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    finalize(args.video, args.pacote, args.dados, args.production)
