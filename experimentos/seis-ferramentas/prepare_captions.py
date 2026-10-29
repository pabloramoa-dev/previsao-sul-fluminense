#!/usr/bin/env python3
"""Usa efetivamente o gerador de legendas ASS do repositório auto-caption.

Como o piloto já tem roteiro e tempos de fala reais, aproveita esses dados
para não baixar modelo Whisper nem gastar CPU re-transcrevendo voz gerada.
"""
from pathlib import Path
import json, sys, re
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
sys.path.insert(0, str(ROOT/"third_party"/"auto-caption"))
from autocaption.ass_builder import build_ass
from autocaption.grouping import group_words
from autocaption.transcribe import Word
from autocaption.styles import StylePreset
timeline=json.loads((BASE/"public"/"timeline.json").read_text())["timeline"]
# Legendas karaoke em pequenas intervenções, pois a composição original já contém falas.
selected=[2,5,9,12,17,24,31,36,40,44]
words=[]
for i in selected:
    b=timeline[i]
    frase=re.findall(r"\S+", b["fala"])
    duration=float(b["fim"]-b["ini"])
    weights=[max(1,len(w)) for w in frase]
    total=sum(weights)
    t=float(b["ini"])
    for w,k in zip(frase,weights):
        delta=duration*k/total
        words.append(Word(w,t,t+delta))
        t+=delta
grouped=group_words(words,max_words=4,max_chars=22,gap_break=0.7)
style=StylePreset(name="karaoke",mode="karaoke",font="DejaVu Sans",font_size=49,
                  pos_y=0.50,highlight_color="#FFDA71",
                  text_color="#F8F4ED",outline=3.0,shadow=1,caps=True)
ass=build_ass(grouped,style,540,960)
out=BASE/"out"/"real_auto_caption.ass"
out.parent.mkdir(exist_ok=True,parents=True)
out.write_text(ass,encoding="utf-8")
print("Auto Caption real:",len(grouped),"linhas,",len(words),"palavras:",out)
