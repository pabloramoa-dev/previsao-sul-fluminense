# -*- coding: utf-8 -*-
"""
gerar_hf.py — o Reel do Juarez Plantão feito com HyperFrames (HTML -> vídeo).

É um motor PARALELO ao Manim (reels/gerar_juarez.py). Não substitui nada: usa
o MESMO roteiro (montar_roteiro), a MESMA voz do Bira (Kokoro pm_alex 1.04 +
FILTRO_BIRA) e o MESMO lip sync por amplitude do repositório. Muda só a
camada visual, que aqui é HTML + GSAP renderizado pelo HyperFrames.

Recursos do HyperFrames usados:
  - hyperframes tts            narração Kokoro local (voz pm_alex, pt-br)
  - composição HTML + GSAP     timeline pausada e determinística
  - sub-composição             compositions/instagram-follow.html (registry)
  - @hyperframes/shader-transitions  glitch / whip-pan / flash-through-white
  - componentes do registry    count-up, headline-slam, camera-shake,
                               caption-highlight (karaokê), grain, vignette,
                               beat-accent, news-ticker, lower-third-bild,
                               split-flap-board (adaptados pro vertical)
  - áudio multifaixa           narração + trilha + whooshes, mixados pelo motor
  - hyperframes lint/check     trava de qualidade antes do render
  - hyperframes render         MP4 1080x1920

Uso:
    python gerar_hf.py --demo                         # dados de exemplo
    python gerar_hf.py --dados ../reels/dia.json      # previsão real
    python gerar_hf.py --demo --render REEL_HF.mp4    # já renderiza
"""
import argparse
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import wave

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
REELS = os.path.join(RAIZ, "reels")
sys.path.insert(0, REELS)
sys.path.insert(0, RAIZ)

from gerar_juarez import (DEMO, FILTRO_BIRA, GAP_ENTRE_BATIDAS, SPEED_BIRA,  # noqa: E402
                          VOZ_BIRA, cenario_telao, montar_roteiro)
from lipsync_amplitude import gerar_cues  # noqa: E402
from limiares import modo_do_dia  # noqa: E402

SR = 24000
LEAD_IN = 0.12          # a primeira palavra sai quase no frame 1 (gancho)
CAUDA = 0.9             # respiro depois do "siga o canal"
TRANS_DUR = 0.45
BUILD = os.path.join(AQUI, "build")
AUDIO = os.path.join(AQUI, "assets", "audio")
HF = "node " + os.path.join(RAIZ, "video/node_modules/hyperframes/bin/hyperframes.mjs")

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"]


# ---------------------------------------------------------------- áudio ---
def sh(cmd, **kw):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"falhou: {cmd}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r.stdout


def ler_wav(caminho):
    w = wave.open(caminho, "rb")
    n, sr, ch, larg = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
    x = np.frombuffer(w.readframes(n), dtype={2: np.int16, 4: np.int32}[larg]).astype(np.float32)
    w.close()
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x / (32768.0 if larg == 2 else 2147483648.0), sr


def gravar_wav(caminho, x, sr=SR, estereo=False):
    x = np.clip(x, -1, 1)
    if estereo and x.ndim == 1:
        x = np.stack([x, x], axis=1)
    pcm = (x * 32767).astype(np.int16)
    w = wave.open(caminho, "wb")
    w.setnchannels(2 if pcm.ndim == 2 else 1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(pcm.tobytes())
    w.close()


def falar(i, texto):
    """Uma batida -> wav filtrado com a cadeia do Bira, 24 kHz mono."""
    cru = os.path.join(BUILD, f"b{i}_cru.wav")
    fil = os.path.join(BUILD, f"b{i}.wav")
    with open(os.path.join(BUILD, f"b{i}.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    subprocess.run([sys.executable, os.path.join(REELS, 'gerar_voz_kokoro.py'),
                    os.path.join(BUILD, f'b{i}.txt'), '--voz', VOZ_BIRA,
                    '--speed', str(SPEED_BIRA), '--gap', '0', '--out', cru], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', cru, '-af', FILTRO_BIRA,
                    '-ar', str(SR), '-ac', '1', fil], check=True)
    x, _ = ler_wav(fil)
    # apara silêncio das pontas (Kokoro deixa ~80 ms de cada lado)
    env = np.abs(x) > 0.01
    if env.any():
        a, b = np.argmax(env), len(x) - np.argmax(env[::-1])
        x = x[max(0, a - int(0.02 * SR)): min(len(x), b + int(0.04 * SR))]
    return x


def tempos_das_palavras(texto, ini, fim):
    """Distribui as palavras da batida no tempo real dela. Peso = sílabas
    aproximadas (vogais) + pausa extra na pontuação, que o Kokoro respeita."""
    palavras = texto.split()
    pesos = []
    for p in palavras:
        v = len(re.findall(r"[aeiouáéíóúâêôãõà]", p.lower())) or 1
        pausa = 1.6 if p[-1] in ".!?" else (0.9 if p[-1] in ",:;" else 0.0)
        pesos.append((v, pausa))
    total = sum(v + pa for v, pa in pesos) or 1
    t, out = ini, []
    for p, (v, pa) in zip(palavras, pesos):
        d_fala = (fim - ini) * v / total
        out.append({"w": p, "s": round(t, 3), "e": round(t + d_fala, 3)})
        t += d_fala + (fim - ini) * pa / total
    return out


def trilha(dur, cortes):
    """Cama de plantão sintetizada (sem licença de terceiros): pulso grave em
    110 BPM + acorde suspenso + um 'ding' de telejornal no início. Whooshes
    de ruído filtrado nos cortes de cena."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    bpm = 110
    beat = 60 / bpm
    x = np.zeros(n, dtype=np.float32)
    # pulso (kick suave) em todo tempo
    for k in range(int(dur / beat) + 1):
        a = int(k * beat * SR)
        m = min(n - a, int(0.25 * SR))
        if m <= 0:
            continue
        tt = np.arange(m) / SR
        f = 55 + 60 * np.exp(-tt * 30)
        x[a:a + m] += 0.55 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 14)
    # pad: Dsus2 bem baixo, com trêmulo lento
    for fr in (146.83, 220.0, 329.63):
        x += 0.05 * np.sin(2 * np.pi * fr * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t))
    # hi-hat em colcheia (ruído com envelope curto), só depois do gancho
    rng = np.random.default_rng(6)
    for k in range(int(dur / (beat / 2)) + 1):
        a = int(k * beat / 2 * SR)
        if a / SR < 1.8:
            continue
        m = min(n - a, int(0.04 * SR))
        if m <= 0:
            continue
        ruido = rng.standard_normal(m).astype(np.float32)
        ruido = np.diff(ruido, prepend=0)          # "high-pass" barato
        x[a:a + m] += 0.05 * ruido * np.exp(-np.arange(m) / SR * 90)
    # ding de plantão (duas notas) no começo
    for ini, fr in ((0.0, 987.77), (0.16, 1318.5)):
        a = int(ini * SR)
        m = int(0.9 * SR)
        tt = np.arange(m) / SR
        x[a:a + m] += 0.28 * np.sin(2 * np.pi * fr * tt) * np.exp(-tt * 5)
    # fade in/out
    fade = int(0.4 * SR)
    x[-fade:] *= np.linspace(1, 0, fade)
    trilha_x = x / (np.abs(x).max() or 1) * 0.9

    sfx = np.zeros(n, dtype=np.float32)
    for c in cortes:
        a = int(max(0, c - 0.18) * SR)
        m = min(n - a, int(0.55 * SR))
        tt = np.arange(m) / SR
        ruido = rng.standard_normal(m).astype(np.float32)
        # varredura: passa-baixa móvel via média exponencial
        y = np.zeros(m, dtype=np.float32)
        alpha = np.linspace(0.02, 0.5, m)
        acc = 0.0
        for j in range(m):
            acc += alpha[j] * (ruido[j] - acc)
            y[j] = acc
        env = np.sin(np.pi * np.clip(tt / 0.55, 0, 1)) ** 2
        sfx[a:a + m] += y * env
    sfx = sfx / (np.abs(sfx).max() or 1) * 0.8
    return trilha_x, sfx


# ---------------------------------------------------------------- cenas ---
def agrupar_cenas(batidas):
    """Batida -> cena. 'nenhum' junta com a próxima quando a próxima é o
    quadro (a confirmação vira o cabeçalho do quadro); senão vira frase."""
    chave = {"alerta": "abertura", "gancho": "abertura", "resumo": "quadro",
             "sem_chuva": "chuva", "chuva": "chuva", "cta": "cta"}
    cenas = []
    for i, b in enumerate(batidas):
        k = chave.get(b["tipo"])
        if k is None:
            prox = batidas[i + 1]["tipo"] if i + 1 < len(batidas) else None
            k = "quadro" if prox == "resumo" else "frase"
        if cenas and cenas[-1]["tipo"] == k:
            cenas[-1]["batidas"].append(i)
        else:
            cenas.append({"tipo": k, "batidas": [i]})
    for j, c in enumerate(cenas):
        c["id"] = f"s{j}-{c['tipo']}"
    return cenas


def momento_da_capa(cenas, cortes, dur):
    """Segundo do vídeo que vira a miniatura da GRADE do perfil.

    No Manim o frame 0 já trazia o selo da cidade. No HyperFrames o frame 0 é
    só o cenário de chuva, e a grade passou a mostrar quadros vazios (desde
    01/10/2026). A capa agora é o QUADRO das cidades já montado: pegamos
    2,2 s depois do início da cena, sem passar do corte seguinte.
    """
    for j, c in enumerate(cenas):
        if c["tipo"] != "quadro":
            continue
        fim = cortes[j] - 0.15 if j < len(cortes) else dur - 0.2
        return round(max(c["ini"] + 0.6, min(c["ini"] + 2.2, fim)), 2)
    return round(min(1.5, dur / 2), 2)   # sem quadro: abertura já montada


def extrair_capa(mp4, capa_s):
    """Salva CAPA.jpg (mesma pasta do MP4) e capa_ms.txt para o workflow."""
    pasta = os.path.dirname(mp4)
    jpg = os.path.join(pasta, "CAPA.jpg")
    sh(f'ffmpeg -y -loglevel error -ss {capa_s:.2f} -i "{mp4}" -frames:v 1 -q:v 2 "{jpg}"')
    if not os.path.exists(jpg) or os.path.getsize(jpg) < 10_000:
        raise RuntimeError("capa da grade não foi gerada")
    with open(os.path.join(pasta, "capa_ms.txt"), "w") as f:
        f.write(str(int(capa_s * 1000)))
    print(f"capa: {jpg} ({capa_s:.2f}s)")


def data_extenso(iso):
    import datetime as dt
    d = dt.date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]}, {d.day} DE {MESES[d.month - 1].upper()}"


# ---------------------------------------------------------------- main ---
def preparar(dados, render=None, qualidade="standard"):
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(AUDIO, exist_ok=True)
    vendor = os.path.join(AQUI, 'assets', 'vendor')
    os.makedirs(vendor, exist_ok=True)
    shutil.copy(os.path.join(RAIZ, 'video/node_modules/gsap/dist/gsap.min.js'), vendor)

    batidas = montar_roteiro(dados)
    modo = modo_do_dia(dados)
    print(f"modo: {modo} | batidas: {len(batidas)}")

    # 1) voz por batida -> linha do tempo real
    trechos, t, tempos = [], LEAD_IN, []
    for i, b in enumerate(batidas):
        x = falar(i, b["fala"])
        ini, fim = t, t + len(x) / SR
        tempos.append((round(ini, 3), round(fim, 3)))
        trechos.append((ini, x))
        t = fim + GAP_ENTRE_BATIDAS
        print(f"  [{b['tipo']:9s}] {ini:5.2f}-{fim:5.2f}s  {b['fala']}")
    fala_fim = tempos[-1][1]
    dur = round(fala_fim + CAUDA, 2)

    narr = np.zeros(int(dur * SR), dtype=np.float32)
    for ini, x in trechos:
        a = int(ini * SR)
        narr[a:a + len(x)] += x[: len(narr) - a]
    narr_path = os.path.join(AUDIO, "narracao.wav")
    gravar_wav(narr_path, narr)

    # 2) lip sync pela energia (mesmo algoritmo do reels/)
    xn, srn = ler_wav(narr_path)
    cues = gerar_cues(xn / (np.abs(xn).max() or 1), srn, fps=30)

    # 3) cenas e cortes
    cenas = agrupar_cenas(batidas)
    for c in cenas:
        c["ini"] = tempos[c["batidas"][0]][0]
    cortes = [round(c["ini"] - TRANS_DUR * 0.55, 3) for c in cenas[1:]]
    trans_nomes = []
    for c in cenas[1:]:
        trans_nomes.append({"quadro": "glitch", "chuva": "whip-pan",
                            "cta": "flash-through-white"}.get(c["tipo"], "whip-pan"))

    capa_s = momento_da_capa(cenas, cortes, dur)
    print(f"capa da grade: {capa_s:.2f}s (quadro com as cidades na tela)")

    tr, sfx = trilha(dur, cortes)
    gravar_wav(os.path.join(AUDIO, "trilha.wav"), tr, estereo=True)
    gravar_wav(os.path.join(AUDIO, "whoosh.wav"), sfx, estereo=True)

    # 4) palavras (karaokê) e pacote de dados pra composição
    palavras = []
    for i, b in enumerate(batidas):
        for p in tempos_das_palavras(b["fala"], *tempos[i]):
            p["b"] = i
            palavras.append(p)

    pacote = {
        "dur": dur, "modo": modo, "data": dados["data"],
        "data_ext": data_extenso(dados["data"]),
        "ceu": cenario_telao(dados),
        "cidades": dados["cidades"],
        "batidas": [dict(b, ini=tempos[i][0], fim=tempos[i][1])
                    for i, b in enumerate(batidas)],
        "cenas": cenas, "cortes": cortes, "transicoes": trans_nomes,
        "palavras": palavras,
        "capa_s": capa_s,
        "boca": [[c["start"], c["value"]] for c in cues],
    }
    with open(os.path.join(BUILD, "pacote.json"), "w", encoding="utf-8") as f:
        json.dump(pacote, f, ensure_ascii=False, indent=1)

    from compor import compor
    html_final = compor(pacote)
    with open(os.path.join(AQUI, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_final)
    print(f"index.html pronto — {dur:.1f}s, {len(cenas)} cenas, "
          f"transições: {', '.join(trans_nomes)}")

    if render:
        saida = os.path.abspath(render)
        print(sh(f"{HF} render --output \"{saida}\" --quality {qualidade}",
                 cwd=AQUI)[-800:])
        from hyperframes import conferir
        conferir(saida, dur)
        extrair_capa(saida, capa_s)
    return pacote


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--render", help="caminho do MP4 (sem isso só gera o index.html)")
    ap.add_argument("--qualidade", default="standard", choices=["draft", "standard", "high"])
    a = ap.parse_args()
    d = DEMO if a.demo or not a.dados else json.load(open(a.dados, encoding="utf-8"))
    preparar(d, a.render, a.qualidade)
