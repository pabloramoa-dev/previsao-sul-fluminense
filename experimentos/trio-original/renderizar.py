#!/usr/bin/env python3
"""Piloto isolado com os modelos originais Nina, Seu Ranzinza e Dona Maria."""
from __future__ import annotations
import json
import math
import os
import subprocess
import sys
import textwrap
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
NINA = ROOT / "nina_source" / "motor"
REELS = ROOT / "reels"
sys.path.insert(0, str(REELS))
import previsao_lib as PREV
import dvh_lip as LIP
sys.path.insert(0, str(NINA))
import nina_lib as NL
from manim import *

# Geometria original para tela vertical: três segmentos no formato 9:16.
config.frame_width = 8.0
config.frame_height = 14.222
config.pixel_width = 720
config.pixel_height = 1280

ROTEIRO = [
    ("nina", "Gente, chegou uma mensagem sobre o quarto doze.", "MENSAGEM MISTERIOSA"),
    ("ranzinza", "Quarto doze? Eu mandei trancar aquela porta!", "PORTA TRANCADA"),
    ("maria", "Pois eu encontrei uma chave dentro da minha bolsa.", "UMA CHAVE ANTIGA"),
    ("nina", "Dona Maria, essa chave tem o número doze?", "NÚMERO DOZE"),
    ("ranzinza", "Se tiver, ninguém abre essa porta!", "SEGREDO GUARDADO"),
    ("maria", "Tarde demais. Alguém deixou uma mala lá dentro!", "MALA NO QUARTO"),
]
VOICES = {"nina": ("pf_dora", 1.02, 1.0),
          "ranzinza": ("pm_alex", 0.95, 0.88),
          "maria": ("pf_dora", 0.95, 0.94)}
SR = 44100


def run(*cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True)


def wav_read(path):
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0


def wav_write(path, samples):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())


def preparar():
    BUILD.mkdir(parents=True, exist_ok=True)
    por_pessoa = {}
    for pessoa in VOICES:
        frases = [fala for nome, fala, _ in ROTEIRO if nome == pessoa]
        rot = BUILD / (pessoa + ".txt")
        rot.write_text(chr(10).join(frases) + chr(10), encoding="utf-8")
        voz, velocidade, pitch = VOICES[pessoa]
        origem = NINA if pessoa == "nina" else REELS
        run(sys.executable, origem / "gerar_voz_kokoro.py", rot, "--voz", voz,
            "--speed", velocidade, "--gap", "0.22",
            "--out", BUILD / (pessoa + "_base.wav"),
            "--seg-json", BUILD / (pessoa + "_segs.json"))
        src = BUILD / (pessoa + "_base.wav")
        if pitch != 1:
            # Filtro original FILTRO_VELHO, em reels/gerar_dia.py.
            flt = (f"asetrate=44100*{pitch},aresample=44100,atempo={1/pitch:.5f},"
                   "vibrato=f=5.5:d=0.09,highpass=f=90,"
                   "acompressor=threshold=-18dB:ratio=3:attack=8:release=180,"
                   "volume=1.15")
            dst = BUILD / (pessoa + ".wav")
            run("ffmpeg", "-y", "-loglevel", "error", "-i", src,
                "-af", flt, "-ar", SR, "-ac", "1", dst)
            src = dst
        samples = wav_read(src)
        segs = json.loads((BUILD / (pessoa + "_segs.json")).read_text())
        fatias = []
        for seg in segs:
            ini = int(seg["ini"] * SR)
            fim = int(seg.get("fim_fala", seg["fim"] - 0.22) * SR)
            fatias.append(samples[ini:fim].copy())
        por_pessoa[pessoa] = fatias

    ordem = {"nina": 0, "ranzinza": 0, "maria": 0}
    parte_audio = []
    timeline = []
    cursor = 0
    for pessoa, fala, ilustracao in ROTEIRO:
        pedaco = por_pessoa[pessoa][ordem[pessoa]]
        ordem[pessoa] += 1
        ini = cursor / SR
        parte_audio.append(pedaco)
        cursor += len(pedaco)
        fim = cursor / SR
        timeline.append({"personagem": pessoa, "fala": fala,
                         "ilustracao": ilustracao, "ini": ini, "fim": fim})
        parte_audio.append(np.zeros(round(0.22 * SR), dtype=np.float32))
        cursor += round(0.22 * SR)
    audio = np.concatenate(parte_audio)
    wav_write(BUILD / "trio_original.wav", audio)
    # Executa diretamente a implementação ORIGINAL do Sul Fluminense,
    # evitando o arquivo homônimo do projeto Nina.
    run(sys.executable, REELS / "lipsync_amplitude.py",
        BUILD / "trio_original.wav", BUILD / "lip_original.json", "--fps", 24)
    cues = json.loads((BUILD / "lip_original.json").read_text())["mouthCues"]
    info = {"timeline": timeline, "mouthCues": cues, "duration": len(audio) / SR,
            "source": {"nina": "nina_source/motor/nina_lib.py",
                       "ranzinza_maria": "reels/previsao_lib.py",
                       "voice": "scripts originais Kokoro com filtros originais"}}
    (BUILD / "timeline.json").write_text(json.dumps(info, ensure_ascii=False, indent=2))
    print("Áudio real concluído; duração:", info["duration"], flush=True)


class TrioPiloto(Scene):
    def construct(self):
        cfg = json.loads((BUILD / "timeline.json").read_text())
        timeline = cfg["timeline"]
        mouth_cues = cfg["mouthCues"]
        frame_w = config.frame_width
        frame_h = config.frame_height
        self.camera.background_color = "#11141E"
        centers = {"nina": 4.46, "ranzinza": 0.0, "maria": -4.46}
        cores = {"nina": "#342D40", "ranzinza": "#323846", "maria": "#354138"}
        exibicao = {"nina": "NINA", "ranzinza": "SEU RANZINZA", "maria": "DONA MARIA"}
        icons = {"nina": "?", "ranzinza": "12", "maria": "!"}
        personagens = {
            "nina": NL.nina(expr="desconfiada", cenario="tarde"),
            "ranzinza": PREV.ranzinza(humor="bravo"),
            "maria": PREV.dona_maria(humor="conspirando"),
        }

        # Cada personagem é desenhado EXATAMENTE com o gerador do próprio projeto.
        # Somente a escala e a posição são alteradas para dividir a tela em 3.
        panels = {}
        all_subs = []
        all_visuals = []
        for pessoa, y in centers.items():
            fundo = Rectangle(width=frame_w, height=4.40,
                              fill_color=cores[pessoa], fill_opacity=1,
                              stroke_color="#10131E", stroke_width=6)
            fundo.move_to([0, y, 0])
            self.add(fundo)
            nome = Text(exibicao[pessoa], font="DejaVu Sans", font_size=27,
                        weight="BOLD", color="#FFE1A6").move_to([-1.8, y + 1.90, 0])
            self.add(nome)
            cartao = RoundedRectangle(corner_radius=0.12, width=3.47, height=2.70,
                                      fill_color="#151E2B", fill_opacity=1,
                                      stroke_color="#C3A56A", stroke_width=2)
            cartao.move_to([1.78, y + 0.08, 0])
            self.add(cartao)
            hint = Text("CENA ILUSTRADA", font_size=19,
                        font="DejaVu Sans", color="#A9BCD3").move_to([1.78, y - 0.98, 0])
            hint.set_opacity(0)
            self.add(hint)
            glyph = Text(icons[pessoa], font_size=78,
                         font="DejaVu Sans", color="#F2D7A0").move_to([1.78, y + 0.40, 0])
            self.add(glyph)
            panels[pessoa] = {"card": cartao, "glyph": glyph}

            p = personagens[pessoa]
            g = p["grupo"]
            escala = min(3.20 / g.width, 3.20 / g.height)
            g.scale(escala)
            g.move_to([-2.0, y - 0.05, 0])
            p["_escala"] = escala
            self.add(g)

        for item in timeline:
            pessoa = item["personagem"]
            y = centers[pessoa]
            legenda = Text(textwrap.fill(item["fala"], 46), font="DejaVu Sans",
                           font_size=27, color=WHITE, weight="MEDIUM")
            if legenda.width > 7.35:
                legenda.scale_to_fit_width(7.35)
            legenda.move_to([0, y - 1.77, 0])
            legenda.set_opacity(0)
            self.add(legenda)
            all_subs.append(legenda)
            ilustracao = Text(item["ilustracao"], font="DejaVu Sans",
                              font_size=22, color="#F2D7A0", weight="BOLD")
            if ilustracao.width > 3.1:
                ilustracao.scale_to_fit_width(3.1)
            ilustracao.move_to([1.78, y - 1.01, 0])
            ilustracao.set_opacity(0)
            self.add(ilustracao)
            all_visuals.append(ilustracao)

        # Reaproveita as bocas originais: Nina por nina_lib.boca_fala,
        # e casal por dvh_lip.boca_visema do Sul Fluminense.
        mouths = {}
        for pessoa, p in personagens.items():
            if pessoa == "nina":
                original = p["rosto"][3]
            else:
                original = p["boca"]
            mouths[pessoa] = {"original": original, "center": original.get_center().copy(),
                             "object": VGroup(), "status": None}
            self.add(mouths[pessoa]["object"])

        # Atualização independente de cena e fala, sincronizada ao áudio real.
        estado = {"gesture": {}, "iris": {}}
        for pessoa in personagens:
            estado["gesture"][pessoa] = 0.0
            estado["iris"][pessoa] = 0.0
        def updater(clock, dt):
            t = estado["tempo"]
            ativo = next((i for i, it in enumerate(timeline)
                          if it["ini"] <= t < it["fim"]), -1)
            falante = timeline[ativo]["personagem"] if ativo >= 0 else None
            for i, (item, sub) in enumerate(zip(timeline, all_subs)):
                sub.set_opacity(1 if i == ativo else 0)
                all_visuals[i].set_opacity(1 if i == ativo else 0)

            cue = next((c["value"] for c in mouth_cues
                        if c["start"] <= t < c["end"]), "X")
            for pessoa, p in personagens.items():
                mouth = mouths[pessoa]
                speaking = pessoa == falante and cue != "X"
                mouth["original"].set_stroke(opacity=0 if speaking else 1)
                if speaking:
                    if pessoa == "nina":
                        shape = NL.boca_fala("aberta" if cue in ("C", "D") else "meia")
                    else:
                        shape = LIP.boca_visema(cue)
                    shape.scale(p["_escala"])
                    mouth["object"].become(shape)
                    mouth["object"].move_to(mouth["original"].get_center())
                elif mouth["status"] != "quiet":
                    mouth["object"].become(VGroup())
                mouth["status"] = "talk" if speaking else "quiet"

                # Respiração; deslocamentos suaves sem deformar os modelos.
                g = p["grupo"]
                previous = estado["gesture"][pessoa]
                dy = 0.032 * math.sin(t * 2.3 + list(centers).index(pessoa))
                g.shift(UP * (dy - previous))
                estado["gesture"][pessoa] = dy

                # Olhar lateral: desloca somente olhos originais, não o rosto inteiro.
                look = 0.045 * math.sin(t * 0.95 + list(centers).index(pessoa))
                delta = look - estado["iris"][pessoa]
                if pessoa == "nina":
                    for olho in p["rosto"][0]:
                        for parte in (olho[1], olho[2], olho[3]):
                            parte.shift(RIGHT * delta)
                    piscada = (t + 0.4) % 3.2 < 0.11
                    for palpebra in p["rosto"][1]:
                        palpebra[0].set_fill(opacity=1 if piscada else 0)
                        palpebra[1].set_stroke(opacity=1 if piscada else 0)
                else:
                    for eye in (p["oe"], p["od"]):
                        eye.shift(RIGHT * delta)
                        eye.set_opacity(0.05 if (t + (0.7 if pessoa == "maria" else 0)) % 3.6 < 0.10 else 1)
                estado["iris"][pessoa] = look

            for pessoa, pane in panels.items():
                ativo_pessoa = pessoa == falante
                pane["card"].set_stroke(color="#FFE28B" if ativo_pessoa else "#C3A56A",
                                        width=5 if ativo_pessoa else 2)

        # A animação é conduzida explicitamente por alpha do Manim.
        # Scene.wait pode congelar updaters em frames sem mobjects mutáveis.
        # UpdateFromAlphaFunc força atualização de boca, olhos e respiração em CADA quadro.
        estado["tempo"] = 0.0
        clock = Dot(point=ORIGIN, radius=0.001, fill_opacity=0, stroke_opacity=0)
        self.add(clock)
        def atualizar_quadro(obj, alpha):
            estado["tempo"] = min(cfg["duration"] - 0.00001, max(0.0, alpha * cfg["duration"]))
            updater(obj, 0.0)
        self.play(UpdateFromAlphaFunc(clock, atualizar_quadro),
                  run_time=cfg["duration"], rate_func=linear)


if __name__ == "__main__":
    if "--prepare" in sys.argv:
        preparar()
