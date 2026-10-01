#!/usr/bin/env python3
"""
gerar_voz_kokoro.py — motor de narração do pipeline de Reels.

O backend histórico continua sendo o Kokoro local. Quando a variável de ambiente
PREVISAO_TTS=edge está definida, o mesmo contrato de entrada/saída passa a usar
Microsoft Edge TTS, preservando o WAV mono 44,1 kHz e o segs.json que alimentam
legendas, timeline e lip sync.

Uso Kokoro:
  python gerar_voz_kokoro.py roteiro.txt --voz pm_alex --out narracao.wav \
         --seg-json segs.json [--gap 0.35] [--speed 1.0]

Uso Edge (configurado pelo ambiente do workflow):
  PREVISAO_TTS=edge \
  PREVISAO_EDGE_VOICE=pt-BR-AntonioNeural \
  PREVISAO_EDGE_RATE='+10%' \
  PREVISAO_EDGE_PITCH='+6Hz' \
  PREVISAO_EDGE_VOLUME='+6%' \
  python gerar_voz_kokoro.py roteiro.txt --out narracao.wav --seg-json segs.json

roteiro.txt = UMA batida por linha. O script grava:
  - narracao.wav (mono 44100 Hz)
  - segs.json [{"i":0,"texto":...,"ini":0.0,"fim":...}, ...]
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

SR = 44100
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
ARQS = {
    "kokoro-v1.0.onnx": f"{BASE}/kokoro-v1.0.onnx",
    "voices-v1.0.bin": f"{BASE}/voices-v1.0.bin",
}


def cache_dir():
    d = os.environ.get("DVH_KOKORO_DIR", os.path.expanduser("~/.cache/dvh_kokoro"))
    os.makedirs(d, exist_ok=True)
    return d


def garantir_modelo():
    d = cache_dir()
    for nome, url in ARQS.items():
        alvo = os.path.join(d, nome)
        if os.path.exists(alvo) and os.path.getsize(alvo) > 1_000_000:
            continue
        print(f"[kokoro] baixando {nome} ...", file=sys.stderr)
        subprocess.run(
            ["curl", "-fsSL", "--retry", "3", "--retry-delay", "2", "-o", alvo, url],
            check=True,
        )
        if os.path.getsize(alvo) < 1_000_000:
            raise SystemExit(
                f"[kokoro] download de {nome} veio truncado "
                f"({os.path.getsize(alvo)} bytes). Abortando."
            )
    return (
        os.path.join(d, "kokoro-v1.0.onnx"),
        os.path.join(d, "voices-v1.0.bin"),
    )


def resample_44100(s, sr):
    if sr == SR:
        return s.astype(np.float32)
    n = int(round(len(s) * SR / sr))
    xp = np.linspace(0, 1, len(s), endpoint=False)
    x = np.linspace(0, 1, n, endpoint=False)
    return np.interp(x, xp, s).astype(np.float32)


def _edge_params():
    return {
        "voice": os.environ.get("PREVISAO_EDGE_VOICE", "pt-BR-AntonioNeural"),
        "rate": os.environ.get("PREVISAO_EDGE_RATE", "+10%"),
        "pitch": os.environ.get("PREVISAO_EDGE_PITCH", "+6Hz"),
        "volume": os.environ.get("PREVISAO_EDGE_VOLUME", "+6%"),
    }


async def _baixar_edge(linhas, pasta, params):
    try:
        import edge_tts
    except ImportError:
        raise SystemExit(
            "edge-tts não instalado. Rode: pip install edge-tts==7.2.8"
        )

    wavs = []
    for i, texto in enumerate(linhas):
        mp3 = os.path.join(pasta, f"{i:03d}.mp3")
        wavp = os.path.join(pasta, f"{i:03d}.wav")
        await edge_tts.Communicate(
            texto,
            voice=params["voice"],
            rate=params["rate"],
            pitch=params["pitch"],
            volume=params["volume"],
        ).save(mp3)
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error", "-i", mp3,
                "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", wavp,
            ],
            check=True,
        )
        wavs.append(wavp)
    return wavs


def gerar_edge(linhas, a):
    params = _edge_params()
    print(
        "[edge] "
        f"voice={params['voice']} rate={params['rate']} "
        f"pitch={params['pitch']} volume={params['volume']}",
        file=sys.stderr,
    )

    with tempfile.TemporaryDirectory(prefix="previsao_edge_") as td:
        wavs = asyncio.run(_baixar_edge(linhas, td, params))
        gap_n = int(round(a.gap * SR))
        gap_bytes = b"\x00\x00" * gap_n
        segs = []
        t = 0.0

        with wave.open(a.out, "wb") as destino:
            destino.setnchannels(1)
            destino.setsampwidth(2)
            destino.setframerate(SR)

            for i, (texto, wavp) in enumerate(zip(linhas, wavs)):
                with wave.open(wavp, "rb") as origem:
                    if (
                        origem.getnchannels() != 1
                        or origem.getsampwidth() != 2
                        or origem.getframerate() != SR
                    ):
                        raise SystemExit(f"[edge] WAV inesperado em {wavp}")
                    nframes = origem.getnframes()
                    frames = origem.readframes(nframes)

                ini = t
                destino.writeframes(frames)
                destino.writeframes(gap_bytes)
                dur = nframes / SR
                t += dur + a.gap
                segs.append(
                    {
                        "i": i,
                        "texto": texto,
                        "ini": round(ini, 3),
                        "fim": round(t, 3),
                    }
                )
                print(f"[edge] linha {i}: {dur:.2f}s", file=sys.stderr)

    if a.seg_json:
        with open(a.seg_json, "w", encoding="utf-8") as f:
            json.dump(segs, f, ensure_ascii=False, indent=2)
    print(
        f"ok: {a.out} ({t:.1f}s, {len(linhas)} batidas, voz={params['voice']})",
        file=sys.stderr,
    )


def gerar_kokoro(linhas, a):
    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        sys.exit(
            "kokoro-onnx não instalado. Rode: bash scripts/setup_ambiente.sh "
            "(ou pip install --break-system-packages kokoro-onnx soundfile)"
        )

    onnx, vozes = garantir_modelo()
    k = Kokoro(onnx, vozes)
    gap = np.zeros(int(a.gap * SR), dtype=np.float32)
    buf = []
    segs = []
    t = 0.0

    for i, txt in enumerate(linhas):
        s, sr = k.create(txt, voice=a.voz, speed=a.speed, lang="pt-br")
        s = resample_44100(np.asarray(s, dtype=np.float32), sr)
        ini = t
        buf.append(s)
        buf.append(gap)
        t += (len(s) + len(gap)) / SR
        segs.append({"i": i, "texto": txt, "ini": round(ini, 3), "fim": round(t, 3)})
        print(f"[kokoro] linha {i}: {(len(s) / SR):.2f}s", file=sys.stderr)

    voz = np.concatenate(buf) if buf else np.zeros(1, dtype=np.float32)
    pk = float(np.abs(voz).max()) or 1.0
    voz = voz / pk * 0.97
    with wave.open(a.out, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(voz, -1, 1) * 32767).astype(np.int16).tobytes())

    if a.seg_json:
        with open(a.seg_json, "w", encoding="utf-8") as f:
            json.dump(segs, f, ensure_ascii=False, indent=2)
    print(
        f"ok: {a.out} ({t:.1f}s, {len(linhas)} batidas, voz={a.voz})",
        file=sys.stderr,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roteiro", help="txt: uma batida de narração por linha")
    ap.add_argument("--voz", default="pm_alex")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--gap", type=float, default=0.35, help="silêncio entre batidas (s)")
    ap.add_argument("--out", default="narracao.wav")
    ap.add_argument("--seg-json", default=None, help="grava boundaries p/ a timeline")
    a = ap.parse_args()

    linhas = [l.strip() for l in open(a.roteiro, encoding="utf-8") if l.strip()]
    backend = os.environ.get("PREVISAO_TTS", "kokoro").strip().lower()
    if backend == "edge":
        gerar_edge(linhas, a)
    elif backend == "kokoro":
        gerar_kokoro(linhas, a)
    else:
        raise SystemExit(f"PREVISAO_TTS inválido: {backend!r}. Use 'kokoro' ou 'edge'.")


if __name__ == "__main__":
    main()
