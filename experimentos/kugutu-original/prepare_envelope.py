#!/usr/bin/env python3
"""Curva RMS real do áudio original, determinística para animação offline Kugutu."""
import json,subprocess,math
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
public=root/"public"
timeline=json.loads((public/"timeline.json").read_text())
fps=15
raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(public/"source.mp4"),"-f","f32le","-ar","16000","-ac","1","pipe:1"])
snd=np.frombuffer(raw,dtype=np.float32)
n=int(math.ceil(timeline["duration"]*fps))
opens=[]
for i in range(n):
    mid=int((i+0.5)*16000/fps)
    seg=snd[max(0,mid-400):min(len(snd),mid+400)]
    loud=math.sqrt(float(np.mean(seg*seg))) if len(seg) else 0.
    opens.append(min(1, max(0, (loud-0.009)*15)))
# Amplitude por quadro, específica de cada fala; evita abrir bocas simultaneamente.
for t,open_value in enumerate(opens):
    tm=t/fps
    if not any(x["ini"]<=tm<x["fim"] for x in timeline["timeline"]):
        opens[t]=0
(public/"envelope.json").write_text(json.dumps({"fps":fps,"values":[round(float(x),3) for x in opens],
  "timeline":timeline["timeline"],"duration":timeline["duration"]},separators=(",",":"),ensure_ascii=False))
print("Kugutu RMS frames:",len(opens),"duration",timeline["duration"])
