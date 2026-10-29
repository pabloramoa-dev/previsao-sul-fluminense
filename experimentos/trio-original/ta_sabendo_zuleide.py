#!/usr/bin/env python3
"""Tá Sabendo, Zuleide? EP 01, Bebel e Zuleide originais com gancho e final."""
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
    ("nina", "Zuleide, o prédio inteiro descobriu que eu levei um homem para casa. E quando você entrou no meu apartamento, quase caiu para trás!", "O HOMEM MISTERIOSO"),
    ("nina", "Só que ninguém imaginava quem ele era. Vou contar como essa confusão começou!", "VOLTA AO COMEÇO"),
    ("maria", "Bebel, minha filha, por que tem quarenta mensagens no grupo dos moradores sobre você?", "GRUPO AGITADO"),
    ("nina", "Quarenta? Eu só mandei um áudio para você contando uma novidade!", "AUDIO NO CELULAR"),
    ("maria", "Pois mandou para o grupo inteiro! Inclusive para dona Cida do décimo segundo andar.", "GRUPO ERRADO"),
    ("nina", "Não acredito! Minha reputação levou elevador expresso para o último andar!", "ELEVADOR SUBINDO"),
    ("maria", "E que história é essa de um homem alto, elegante, que passou a noite na sua sala?", "UM HOMEM NA SALA"),
    ("nina", "Ah, Zuleide, você sabe como eu sou. Sempre aberta a novas oportunidades!", "BEBEL SORRINDO"),
    ("maria", "Oportunidades? Você escreveu que ele não fala, não reclama e nunca discute!", "AUDIO MISTERIOSO"),
    ("nina", "Uma raridade! No meu histórico, isso é praticamente uma descoberta científica.", "DESCOBERTA"),
    ("maria", "E ainda disse que ele é lindo e combina com qualquer roupa!", "ROUPAS"),
    ("nina", "Tudo verdade. Inclusive, ele ficou parado no mesmo lugar a noite toda.", "HOMEM PARADO"),
    ("maria", "Minha filha, isso não é namorado. Isso é decoração!", "SALA DECORADA"),
    ("nina", "Zuleide, por favor! Algumas histórias merecem um pouco de suspense!", "SEGREDO"),
    ("maria", "Suspense é o que tem no grupo. Já perguntaram se vamos marcar o casamento no salão de festas.", "SALAO DE FESTAS"),
    ("nina", "E o pessoal aceitou? Porque eu nem escolhi o vestido!", "VESTIDO"),
    ("maria", "Bebel, seja séria. Quem é esse homem?", "QUEM É ELE"),
    ("nina", "Promete não rir?", "PROMESSA"),
    ("maria", "Eu prometo tentar. Não é a mesma coisa, mas é o máximo que posso oferecer.", "RISADA"),
    ("nina", "É um manequim. Um manequim de vitrine, desses de loja!", "MANEQUIM"),
    ("maria", "Um manequim? E você chamou o coitado de homem dos seus sonhos?", "REVELACAO"),
    ("nina", "Claro! É educado, usa qualquer roupa e nunca pede a senha do meu celular!", "MANEQUIM E CELULAR"),
    ("maria", "Meu Deus, Bebel! E por que você levou um manequim para o apartamento?", "CURIOSIDADE"),
    ("nina", "Vou montar um bazar beneficente para ajudar a reformar a brinquedoteca do prédio.", "BAZAR BENEFICENTE"),
    ("maria", "Ah! Então a ideia é boa. Mas por que não me contou antes? Sou a síndica!", "SINDICA"),
    ("nina", "Porque era surpresa para você. Eu queria anunciar na reunião e ver sua cara!", "SURPRESA"),
    ("maria", "A minha cara agora é a de alguém que precisa explicar tudo para mil moradores.", "MIL MORADORES"),
    ("nina", "Podemos mandar outro áudio! Dessa vez, no grupo certo.", "NOVO AUDIO"),
    ("maria", "Você não vai mandar mais nada! Eu mesma vou escrever um comunicado.", "COMUNICADO OFICIAL"),
    ("nina", "Capricha no título: esclarecimentos sobre o homem da Bebel!", "TITULO ENGRAÇADO"),
    ("maria", "Nem pensar. Vou escrever: bazar solidário, sábado, às três da tarde.", "CONVITE BAZAR"),
    ("nina", "Muito sem graça. Não chama atenção de ninguém!", "BEBEL DESANIMADA"),
    ("maria", "Então coloca uma foto do manequim com uma camisa bonita. Assim acaba o mistério.", "FOTO DO MANEQUIM"),
    ("nina", "Boa! Mas primeiro preciso tirar a camisa dele. É a única que tenho para vender.", "CAMISA NO CABIDE"),
    ("maria", "Pelo amor! Eu vou até aí ajudar antes que você invente outra manchete!", "ZULEIDE VISITA"),
    ("nina", "Entra, amiga. Só não estranha. Ele está perto da janela olhando a cidade.", "JANELA DO APARTAMENTO"),
    ("maria", "Nossa Senhora! De costas parece mesmo uma pessoa! Quase pedi licença!", "SUSTO"),
    ("nina", "Tá vendo? Ele causa uma ótima primeira impressão!", "MANEQUIM NA JANELA"),
    ("maria", "E esse chapéu?", "CHAPEU"),
    ("nina", "Para deixar mais charmoso. Se o bazar não vender roupa, pelo menos vende elegância!", "ROUPAS DO BAZAR"),
    ("maria", "Bebel, você precisa parar de transformar tudo em novela!", "NOVELA"),
    ("nina", "E perder a melhor parte da vida? Nunca!", "BEBEL FELIZ"),
    ("maria", "Olha só, chegaram respostas ao comunicado. Estão oferecendo roupas para doar!", "DOACOES"),
    ("nina", "Sério? Então o homem misterioso fez alguma coisa boa pelo prédio!", "SOLIDARIEDADE"),
    ("maria", "Fez. E você também. A brinquedoteca vai ficar linda!", "BRINQUEDOTECA"),
    ("nina", "Tá vendo? Toda boa fofoca pode terminar em boa ação!", "FINAL FELIZ"),
    ("maria", "Só que a dona Cida perguntou se o manequim está solteiro.", "MENSAGEM CIDA"),
    ("nina", "Diz para ela que está disponível... por um preço especial no bazar!", "OFERTA"),
    ("maria", "Bebel! Você vai vender o namorado?", "ZULEIDE CHOCADA"),
    ("nina", "Amiga, se ele comprar uma cadeira na brinquedoteca, eu deixo até levar o chapéu!", "PIADA FINAL"),
]
VOICES = {"nina": ("pf_dora", 1.02, 1.0),
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



class PortariaSabe(Scene):
    """Cena com DUAS faixas grandes; todos os personagens vêm dos motores originais."""
    def construct(self):
        cfg = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
        timeline = cfg["timeline"]
        cues = cfg["mouthCues"]
        self.camera.background_color = "#101725"
        nomes = {"nina": "BEBEL", "maria": "DONA ZULEIDE"}
        cores = {"nina": "#4A304C", "ranzinza": "#354150", "maria": "#405447"}
        personagens = {
            "nina": NL.nina(expr="ironica", cenario="tarde"),
            "maria": PREV.dona_maria(humor="simpatica"),
        }
        Y = [3.28, -3.28]
        duo_fases = [(0, len(timeline), ("nina", "maria"))]
        def dupla(i):
            for ini, fim, par in duo_fases:
                if ini <= i < fim:
                    return par
            return ("nina", "ranzinza")

        panes = []
        for slot, y in enumerate(Y):
            fundo = RoundedRectangle(
                corner_radius=0.12, width=7.80, height=6.26,
                fill_color="#223040" if slot == 0 else "#2C3442",
                fill_opacity=1, stroke_color="#0B1220", stroke_width=5
            ).move_to([0, y, 0])
            accent = Line([-3.86, y+3.05, 0], [3.86, y+3.05, 0],
                          color="#DBB972", stroke_width=6)
            nome = Text("BEBEL", font="DejaVu Sans", font_size=34,
                        weight="BOLD", color="#FFE4A5").move_to([-2.0, y+2.66, 0])
            suporte = RoundedRectangle(corner_radius=0.20, width=3.42, height=4.16,
                                      fill_color="#121E2E", fill_opacity=1,
                                      stroke_color="#9F8A63", stroke_width=3).move_to([1.91,y+0.06,0])
            glow = Circle(radius=0.82, fill_color="#C19752", fill_opacity=0.17,
                          stroke_color="#E9C87F", stroke_width=3).move_to([1.91,y+0.45,0])
            icon = Text("?", font="DejaVu Sans", font_size=90,
                        color="#F4D59D").move_to([1.91, y+0.42,0])
            label = Text("CENA", font="DejaVu Sans", font_size=24,
                         weight="BOLD", color="#F4D59D").move_to([1.91,y-1.41,0])
            self.add(fundo,accent,suporte,glow,icon,label,nome)
            panes.append({"nome":nome,"suporte":suporte,"icone":icon,"label":label,"glow":glow})

        for pessoa,p in personagens.items():
            g=p["grupo"]
            esc=min(4.30/g.width, 4.35/g.height)
            g.scale(esc)
            p["_escala"]=esc
            g.move_to([14.0,0.0,0.0])
            self.add(g)

        subtitles=[]
        visuals=[]
        for item in timeline:
            legend = Text(textwrap.fill(item["fala"], width=48), font="DejaVu Sans",
                          font_size=28, weight="MEDIUM", color="#FFFFFF")
            if legend.width > 7.16: legend.scale_to_fit_width(7.16)
            if legend.height > 0.90: legend.scale_to_fit_height(0.90)
            subtitles.append(legend)
            v = Text(item["ilustracao"], font="DejaVu Sans", font_size=25,
                     weight="BOLD", color="#F4D59D")
            if v.width > 3.20: v.scale_to_fit_width(3.20)
            visuals.append(v)
        subtitle = Text("TA SABENDO, ZULEIDE?", font="DejaVu Sans", font_size=26,
                        weight="BOLD", color=WHITE)
        illus = Text("MISTERIO NA TORRE", font="DejaVu Sans", font_size=22,
                     weight="BOLD", color="#F4D59D")
        self.add(subtitle,illus)
        mouths={}
        for pessoa,p in personagens.items():
            original = p["rosto"][3] if pessoa=="nina" else p["boca"]
            lip = VGroup()
            self.add(lip)
            mouths[pessoa]={"original":original,"lip":lip,"prev":"X"}

        clock_state={"t":0.0, "idx":-1, "duo":None, "gesture":{p:0.0 for p in personagens},
                     "iris":{p:0.0 for p in personagens}, "cue":0}
        starts=[c["start"] for c in cues]
        from bisect import bisect_right
        beginnings=[it["ini"] for it in timeline]

        def actualizar(mob,alpha):
            t=min(cfg["duration"]-0.001,alpha*cfg["duration"])
            clock_state["t"]=t
            idx=max(0,min(len(timeline)-1,bisect_right(beginnings,t)-1))
            it=timeline[idx]
            quem=it["personagem"] if t < it["fim"] else None
            par=dupla(idx)
            if idx!=clock_state["idx"]:
                clock_state["idx"]=idx
                sub_idx=0 if quem is None or quem==par[0] else 1
                subtitle.become(subtitles[idx].copy())
                subtitle.move_to([0,Y[sub_idx]-2.52,0])
                illus.become(visuals[idx].copy())
                illus.move_to([1.91,Y[sub_idx]-1.38,0])
                key = it["ilustracao"].upper()
                sym = ("3" if "VISITA" in key or "APARTAMENT" in key else
                       "18" if "1801" in key else
                       "!" if "SURPRESA" in key or "SEGREDO" in key else
                       "@" if "GRUPO" in key or "INTERFONE" in key else
                       "01" if "SHOW" in key or "PALCO" in key or "ENSAIO" in key else
                       "?" if "MISTERIO" in key else
                       "✓" if "FIM" in key or "ACEITO" in key else
                       "•")
                for slot,pane in enumerate(panes):
                    pane["icone"].become(Text(sym, font="DejaVu Sans",
                                              font_size=90, color="#F4D59D"))
                    pane["icone"].move_to([1.91,Y[slot]+0.42,0])
                clock_state["duo"]=par
                for slot,who in enumerate(par):
                    pane=panes[slot]
                    pane["nome"].become(Text(nomes[who],font="DejaVu Sans",
                                             font_size=34,weight="BOLD",color="#FFE4A5"))
                    pane["nome"].move_to([-2,Y[slot]+2.66,0])
                for person,p in personagens.items():
                    if person in par:
                        slot=par.index(person)
                        p["grupo"].move_to([-2.07,Y[slot]+0.05,0])
                    else:
                        p["grupo"].move_to([14,0,0])
                    clock_state["gesture"][person]=0.0
            ci=max(0,min(len(cues)-1,bisect_right(starts,t)-1))
            cue=cues[ci]["value"] if cues and cues[ci]["start"]<=t<cues[ci]["end"] else "X"
            for person,p in personagens.items():
                lip=mouths[person]
                falando=person==quem and cue!="X"
                target=cue if falando else "X"
                if target!=lip["prev"]:
                    lip["original"].set_stroke(opacity=0 if falando else 1)
                    if falando:
                        if person=="nina":
                            form=NL.boca_fala("aberta" if cue in ("C","D") else "meia")
                        else:
                            form=LIP.boca_visema(cue)
                        form.scale(p["_escala"])
                        lip["lip"].become(form)
                        lip["lip"].move_to(lip["original"].get_center())
                    else:
                        lip["lip"].become(VGroup())
                    lip["prev"]=target
                if person not in par: continue
                phase=0 if person=="nina" else 1 if person=="ranzinza" else 2
                dy=0.038*math.sin(t*2.2+phase)
                p["grupo"].shift(UP*(dy-clock_state["gesture"][person]))
                clock_state["gesture"][person]=dy
                delta_x=0.044*math.sin(t*0.93+phase)-clock_state["iris"][person]
                if person=="nina":
                    for eye in p["rosto"][0]:
                        for part in (eye[1],eye[2],eye[3]):
                            part.shift(RIGHT*delta_x)
                    blink=(t+0.3)%3.6 < 0.12
                    for lid in p["rosto"][1]:
                        lid[0].set_fill(opacity=1 if blink else 0)
                        lid[1].set_stroke(opacity=1 if blink else 0)
                else:
                    for eye in [p["oe"],p["od"]]:
                        eye.shift(RIGHT*delta_x)
                        eye.set_opacity(0.06 if (t+0.4*phase)%3.6<0.1 else 1)
                clock_state["iris"][person]+=delta_x
            active_slot=0 if quem is None or quem==par[0] else 1
            for slot,pane in enumerate(panes):
                pane["suporte"].set_stroke(color="#F4D59D" if slot==active_slot else "#9F8A63",
                                          width=5 if slot==active_slot else 2)
                pane["glow"].set_opacity(0.22+0.09*math.sin(t*2.5)
                                         if slot==active_slot else 0.08)
            for slot,pane in enumerate(panes):
                pane["icone"].set_opacity(1 if slot==active_slot else 0.35)
            illus.set_opacity(1 if quem is not None else 0.45)
            subtitle.set_opacity(1 if quem is not None else 0.45)

        clock=Dot(point=ORIGIN,radius=0.001,fill_opacity=0,stroke_opacity=0)
        self.add(clock)
        all_scene=Group(*list(self.mobjects))
        self.play(UpdateFromAlphaFunc(all_scene,actualizar),
                  run_time=cfg["duration"],rate_func=linear)

if __name__=="__main__":
    if "--prepare" in sys.argv:
        preparar()
