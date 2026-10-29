#!/usr/bin/env python3
"""Converte objetos VGroup ORIGINAIS de nina_lib.py / previsao_lib.py em SVG Kugutu.
Não redesenha nem substitui as personagens: serializa as curvas Bézier Manim reais.
"""
import sys,json,html
from pathlib import Path
import numpy as np
from manim import VMobject
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"nina_source"/"motor"))
sys.path.insert(0,str(ROOT/"reels"))
import nina_lib as NL
import previsao_lib as PREV

HERE=Path(__file__).resolve().parent
OUT=HERE/"source"
OUT.mkdir(parents=True,exist_ok=True)

def svg_color(c,op):
    try:
        col=c.to_hex()
    except Exception:
        col=str(c)
    if col in ("None","none",""):
        col="#000000"
    return col

def leaf_svg(m):
    if not isinstance(m,VMobject):return ""
    try:
        tuples=np.asarray(m.get_cubic_bezier_tuples())
    except Exception:return ""
    if len(tuples)==0:return ""
    # Extrai os pontos do próprio desenho original no espaço Manim.
    def p(q):
        return f"{(q[0]+2.16)*96:.2f},{(2.82-q[1])*96:.2f}"
    d=[]
    for c in tuples:
        if len(c)!=4:continue
        if not d or np.linalg.norm(last-c[0])>0.002:
            d.append("M"+p(c[0]))
        d.append("C"+" ".join(p(q) for q in c[1:4]))
        last=c[3]
    if not d:return ""
    try:
        fo=float(m.get_fill_opacity())
        sc=float(m.get_stroke_opacity())
        sw=float(m.get_stroke_width())
        fc=svg_color(m.get_fill_color(),fo)
        stroke=svg_color(m.get_stroke_color(),sc)
    except Exception:
        fo=0;sc=1;sw=5;fc="#000";stroke="#121212"
    return f'<path d="{html.escape(" ".join(d))}" fill="{fc if fo>0.003 else "none"}" fill-opacity="{fo:.3f}" stroke="{stroke if sc>0.003 and sw>0 else "none"}" stroke-opacity="{sc:.3f}" stroke-width="{max(0.2,sw*.78):.2f}" stroke-linejoin="round" stroke-linecap="round"/>'

def obj_svg(m):
    if isinstance(m,VMobject) and len(m.submobjects)==0:
        return leaf_svg(m)
    return "".join(obj_svg(x) for x in m.submobjects)

def tag(name,content):
    return f'<g id="{name}">{content}</g>'

def figure(kind):
    raw=NL.nina(expr="ironica",cenario="tarde") if kind=="nina" else PREV.dona_maria(humor="simpatica")
    g=raw["grupo"]
    nodes=[]
    if kind=="nina":
        for i,obj in enumerate(g):
            if i==19: 
                face=obj
                nodes.append(tag("eye_left",obj_svg(face[0][0])))
                nodes.append(tag("eye_right",obj_svg(face[0][1])))
                nodes.append(tag("brow_left",obj_svg(face[2][0])))
                nodes.append(tag("brow_right",obj_svg(face[2][1])))
                # Preserva boca original e adiciona formato aberto com paleta Nina.
                mouth_closed=obj_svg(face[3])
                cp=raw["cab"].get_center()
                xx=(float(cp[0])+2.16)*96
                yy=(2.82-(float(cp[1])-0.5))*96
                open_shape=f'<ellipse cx="{xx:.1f}" cy="{yy:.1f}" rx="21" ry="17" fill="#5e1820" stroke="#b8323c" stroke-width="5"/>'
                nodes.append(tag("mouth_group", f'<g data-kugutu-mouth-closed="true">{mouth_closed}</g><g data-kugutu-mouth-open="true">{open_shape}</g>'))
            elif i==8:
                nodes.append(tag("arm_left",obj_svg(obj)+obj_svg(g[9])))
            elif i==9:continue
            elif i==10:
                nodes.append(tag("arm_right",obj_svg(obj)+obj_svg(g[11])))
            elif i==11:continue
            elif i==5:
                nodes.append(tag("torso_group",obj_svg(obj)))
            else:
                nodes.append(obj_svg(obj))
    else:
        for i,obj in enumerate(g):
            if i==28:nodes.append(tag("eye_left",obj_svg(obj)))
            elif i==29:nodes.append(tag("eye_right",obj_svg(obj)))
            elif i==26:nodes.append(tag("brow_left",obj_svg(obj)))
            elif i==27:nodes.append(tag("brow_right",obj_svg(obj)))
            elif i==31:
                cp=raw["cab"].get_center()
                xx=(float(cp[0])+2.16)*96;yy=(2.82-(float(cp[1])-0.52))*96
                open_shape=f'<ellipse cx="{xx:.1f}" cy="{yy:.1f}" rx="21" ry="15" fill="#4b2526" stroke="#111111" stroke-width="5"/>'
                nodes.append(tag("mouth_group",f'<g data-kugutu-mouth-closed="true">{obj_svg(obj)}</g><g data-kugutu-mouth-open="true">{open_shape}</g>'))
            elif i==11:nodes.append(tag("arm_left",obj_svg(obj)+obj_svg(g[13])))
            elif i==13:continue
            elif i==12:nodes.append(tag("arm_right",obj_svg(obj)+obj_svg(g[14])))
            elif i==14:continue
            elif i==6:nodes.append(tag("torso_group",obj_svg(obj)))
            else:nodes.append(obj_svg(obj))
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="440" height="650" viewBox="0 0 440 650">{tag("head_group","".join(nodes))}</svg>'
    folder=OUT/kind;folder.mkdir(parents=True,exist_ok=True)
    (folder/"artwork.svg").write_text(svg,encoding="utf-8")
    definition={
        "schemaVersion":"0.1.0",
        "character":{"id":kind,"displayName":kind.upper(),"template":"avatar-lite"},
        "assets":{"primary":"artwork.svg"},
        "slots":{"head":"head_group","eye.l":"eye_left","eye.r":"eye_right",
                "brow.l":"brow_left","brow.r":"brow_right",
                "mouth":"mouth_group","torso":"torso_group",
                "upperArm.l":"arm_left","upperArm.r":"arm_right"},
        "behaviors":[
            {"id":"blink-natural","type":"blink","targets":["eye.l","eye.r"],"params":{"closeMs":110,"openMs":160,"minIntervalMs":2700,"maxIntervalMs":3900}},
            {"id":"breathing-natural","type":"breathing","targets":["torso","head"],"params":{"cycleMs":3100,"amplitudeY":0.045,"torsoTiltDeg":0.8}},
            {"id":"mouth-voice","type":"mouth-open","targets":["mouth"],"params":{"maxOpen":0.95,"smoothing":0.32}},
            {"id":"gaze","type":"look-at","targets":["eye.l","eye.r","head"],"params":{"radiusX":0.15,"radiusY":0.10,"headFollow":0.15,"smoothing":0.22}},
            {"id":"arm-sway","type":"arm-idle","targets":["upperArm.l","upperArm.r"],"params":{"cycleMs":3600,"amplitudeDeg":3.5}}
        ]
    }
    (folder/"character.json").write_text(json.dumps(definition,ensure_ascii=False,indent=2),encoding="utf8")
    print(kind,"Original VGroup children:",len(g),"SVG bytes:",len(svg))
for key in ("nina","maria"):figure(key)
