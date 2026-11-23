#!/usr/bin/env python3
"""Piloto nao-publicavel: efeitos HyperFrames sobre Reel ORIGINAL do SulFlu."""
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reels"))
from coletar_tempo import CIDADES


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def gerar(base="original", destino="piloto_hf"):
    entrada = Path(base) / "REEL.mp4"
    info = json.loads((Path(base) / "REEL.metadata.json").read_text(encoding="utf-8"))
    legenda = (Path(base) / "LEGENDA.txt").read_text(encoding="utf-8")
    if not entrada.is_file() or entrada.stat().st_size < 30000:
        raise ValueError("O Reel original nao existe ou esta vazio")
    probe = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(entrada)]))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    next(s for s in probe["streams"] if s["codec_type"] == "audio")
    if (video["width"], video["height"]) != (1080, 1920):
        raise ValueError("Resolucao diferente de 1080x1920")
    dur = float(probe["format"]["duration"])
    if not 20 <= dur <= 25.1:
        raise ValueError(f"Duracao original inesperada: {dur}")
    work = Path(destino)
    assets = work / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    run("ffmpeg", "-y", "-v", "error", "-i", entrada, "-map", "0:v:0",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", assets / "base.mp4")
    run("ffmpeg", "-y", "-v", "error", "-i", entrada, "-map", "0:a:0",
        "-vn", "-ac", "2", "-ar", "48000", assets / "original.wav")
    shutil.copy(ROOT / "video/node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js")
    selecionadas = [(nome,lat,lon) for nome,lat,lon in CIDADES
                    if re.search(r"^" + re.escape(nome) + r"(?:\s+—|\s*:)", legenda, re.M)]
    if len(selecionadas) != 5:
        raise ValueError(f"Necessarias cinco cidades da legenda real, recebidas {len(selecionadas)}")
    xs,ys = [c[2] for c in selecionadas], [c[1] for c in selecionadas]
    lo_x, hi_x = min(xs)-.05, max(xs)+.05
    lo_y, hi_y = min(ys)-.05, max(ys)+.05
    pontos = []
    for nome,lat,lon in selecionadas:
        px = 22 + 210*(lon-lo_x)/max(.02,hi_x-lo_x)
        py = 18 + 110*(lat-lo_y)/max(.02,hi_y-lo_y)
        pontos.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="#ffd45e" stroke="white" stroke-width="2"/>')
    maximas = []
    for linha in legenda.splitlines():
        m = re.search(r":\s*-?\d+°\s+a\s+(-?\d+)°", linha)
        if m:
            maximas.append(int(m.group(1)))
    if len(maximas) != 5:
        raise ValueError("A legenda original nao contem cinco temperaturas reais")
    mn,mx = min(maximas),max(maximas)
    barras = "".join(
        '<div class="bar" style="height:'+str(round(28+79*(v-mn)/max(1,mx-mn)))+'px"></div>'
        for v in maximas)
    page = r'''<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#112e43;font-family:Arial,sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden}
#base{position:absolute;inset:0;width:1080px;height:1920px}
#vignette{position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse at center,transparent 62%,rgba(0,12,30,.22))}
#progress{position:absolute;top:0;left:0;width:1080px;height:8px;background:linear-gradient(90deg,#14b9df,#ffe091);transform-origin:left}
#brand{position:absolute;top:73px;left:65px;border-left:7px solid #ffd45e;background:rgba(2,28,47,.86);color:white;padding:12px 18px;border-radius:8px;font-size:24px;font-weight:bold}
#citytag{position:absolute;top:180px;right:58px;border:1px solid #ffd45e;border-radius:14px;background:rgba(2,26,43,.91);color:white;padding:15px 19px;opacity:0;font-size:25px;font-weight:bold}
#citytag strong{display:block;color:#ffd45e;font-size:34px}
#map{position:absolute;top:170px;right:58px;width:282px;height:230px;border:2px solid #ffd45e;background:rgba(4,27,46,.94);border-radius:15px;padding:12px;color:#fff;opacity:0}
#map b,#chart b{font-size:20px;color:#ffdf87}
#map svg{display:block;width:254px;height:155px;margin-top:6px}
#chart{position:absolute;top:175px;right:58px;width:280px;height:195px;border:2px solid #66c0e4;border-radius:15px;background:rgba(4,27,46,.92);color:white;opacity:0;padding:12px}
#bars{height:125px;display:flex;align-items:flex-end;justify-content:center;gap:14px}
.bar{width:30px;border-radius:5px 5px 0 0;background:linear-gradient(#ffdf85,#269ccb)}
#shine{position:absolute;top:0;left:-400px;width:300px;height:1920px;transform:skew(-19deg);pointer-events:none;background:linear-gradient(to right,transparent,rgba(255,255,255,.08),transparent)}
#flash{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none}
#qa{position:absolute;left:75px;bottom:57px;border:1px solid #78c2de;border-radius:16px;background:rgba(2,28,47,.94);color:white;font-size:20px;padding:12px 18px}
#follow{position:absolute;bottom:155px;left:330px;width:420px;border-radius:17px;background:#fff;color:#14324a;font-size:31px;text-align:center;font-weight:bold;padding:18px 12px;opacity:0}
#follow b{color:#da3858}
</style></head><body><div id="root" data-composition-id="piloto-sulflu" data-width="1080" data-height="1920" data-duration="__DUR__" data-fps="25">
<video id="base" class="clip" src="assets/base.mp4" data-start="0" data-duration="__DUR__" data-track-index="0" muted playsinline></video>
<div id="vignette"></div><div id="progress"></div><div id="shine"></div><div id="flash"></div>
<div id="brand">PREVISÃO SUL FLU <span style="color:#ffdc71">• PILOTO VFX</span></div>
<div id="citytag">CIDADE EM DESTAQUE <strong>__CITY__</strong> __TEMP__°</div>
<div id="map"><b>MAPA REGIONAL • CIDADES</b><svg viewBox="0 0 254 155"><path d="M5 100 Q80 25 175 105 L245 60" fill="none" stroke="#55a6c2" stroke-width="4"/>__PONTOS__</svg></div>
<div id="chart"><b>MÁXIMAS • 5 CIDADES</b><div id="bars">__BARRAS__</div></div>
<div id="follow"><b>SEGUIR</b> @previsaosulflu</div>
<div id="qa">TESTE VISUAL · VOZ E CENÁRIOS ORIGINAIS · NÃO PUBLICAR</div>
<audio id="voice" src="assets/original.wav" data-start="0" data-duration="__DUR__" data-track-index="8"></audio>
<script src="assets/gsap.min.js"></script><script>
const tl=gsap.timeline({paused:true});
tl.fromTo('#progress',{scaleX:0},{scaleX:1,duration:__DUR__,ease:'none'},0);
tl.fromTo('#brand',{opacity:0,y:-90},{opacity:1,y:0,duration:.5,ease:'back.out(1.5)'},.1);
tl.fromTo('#shine',{x:-600},{x:2150,duration:1.7,ease:'power2.inOut'},.3);
tl.fromTo('#citytag',{opacity:0,x:50},{opacity:1,x:0,duration:.4,ease:'power3.out'},3.85);
tl.to('#citytag',{opacity:0,duration:.3},6.2);
tl.fromTo('#map',{opacity:0,scale:.9},{opacity:1,scale:1,duration:.45,ease:'back.out(1.4)'},6.7);
tl.to('#map',{opacity:0,duration:.3},10.1);
tl.fromTo('#chart',{opacity:0,y:42},{opacity:1,y:0,duration:.45,ease:'power3.out'},10.5);
tl.to('#chart',{opacity:0,duration:.3},13.8);
tl.fromTo('#shine',{x:-600},{x:2150,duration:1.7,ease:'power2.inOut'},14);
tl.fromTo('#flash',{opacity:.07},{opacity:0,duration:.22},14);
tl.fromTo('#follow',{opacity:0,y:30,scale:.9},{opacity:1,y:0,scale:1,duration:.5,ease:'back.out(1.4)'},Math.max(1,__DUR__-2.8));
tl.to('#follow',{opacity:0,duration:.3},Math.max(2,__DUR__-.5));
window.__timelines={'piloto-sulflu':tl};
</script></div></body></html>'''
    page = (page.replace("__DUR__",f"{dur:.3f}")
              .replace("__CITY__",html.escape(info["cidade_destaque"]))
              .replace("__TEMP__",html.escape(str(info["temperatura_destaque"])))
              .replace("__PONTOS__","".join(pontos))
              .replace("__BARRAS__",barras))
    (work / "index.html").write_text(page,encoding="utf-8")
    report = {"origem": "boletim-regional.yml, publicar=false", "personagem":"bira",
              "cidade": info["cidade_destaque"], "duracao_s":round(dur,3),
              "vozes": "Kokoro originais preservadas do MP4",
              "imagens": "cenarios e personagens originais preservados",
              "mapa": "posicoes reais dos municipios, sem chuva inventada",
              "barras": "temperaturas maximas reais da legenda",
              "efeitos": ["HUD newsroom","progress bar","light sweep","city chip",
                          "mini map","bar chart","soft flash","vignette","CTA follow"]}
    Path("piloto_meta.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")


if __name__ == "__main__":
    gerar()
