"""Compositor HyperFrames: conserva arte, personagens e dados do Manim."""
import html
import json
import math
import os
from pathlib import Path
import shutil
import subprocess


def sh(cmd, **kw):
    subprocess.run([str(x) for x in cmd], check=True, **kw)


def validar(batidas, segs):
    if not batidas or len(batidas) != len(segs):
        raise ValueError('Batidas e segmentos não correspondem')
    prev = 0
    for b, s in zip(batidas, segs):
        a, z = float(s['ini']), float(s['fim'])
        if not all(math.isfinite(x) for x in (a, z)) or a < prev - .001 or z <= a:
            raise ValueError('Timeline inválida')
        prev = z
    return prev


def compor(batidas, segs, pasta):
    dur = validar(batidas, segs)
    parts, anim = [], []
    for i, (b, s) in enumerate(zip(batidas, segs)):
        a, z = s['ini'], s['fim']
        # Os painéis meteorológicos e o CTA originais ficam integralmente visíveis.
        if b['tipo'] not in ('gancho', 'cta', 'resumo'):
            words = b.get('legenda', b['fala']).split()
            groups = [words[k:k+5] for k in range(0, len(words), 5)]
            for k, group in enumerate(groups):
                start = a + (z-a)*k/len(groups)
                length = (z-a)/len(groups)
                spans = []
                for j, word in enumerate(group):
                    ident = f'w{i}_{k}_{j}'
                    spans.append(f'<span id="{ident}">{html.escape(word)}</span>')
                    t = start + length*j/len(group)
                    anim.append(f'tl.set("#{ident}",{{color:"#ffd24a"}},{t});')
                parts.append(f'<div id="cap{i}_{k}" class="clip caption" data-start="{start}" data-duration="{length}" data-track-index="2">{" ".join(spans)}</div>')
        if i:
            anim.append(f'tl.fromTo("#flash",{{opacity:.12}},{{opacity:0,duration:.22,immediateRender:false}},{a});')
        # Moldura animada sem recortar os números nem deslocar os mapas originais.
    anim.append(f'tl.fromTo("#progress",{{scaleX:0}},{{scaleX:1,duration:{dur},ease:"none"}},0);')
    text = f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Local;src:url(assets/bold.ttf)}}
*{{box-sizing:border-box}}html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#102c43}}
#root{{position:relative;width:1080px;height:1920px}}#base{{position:absolute;width:1080px;height:1920px}}
.caption{{position:absolute;left:100px;bottom:310px;width:880px;padding:20px 26px;border-radius:22px;background:rgba(9,25,40,.94);color:white;text-align:center;font: bold 46px/1.2 Local,sans-serif;overflow-wrap:anywhere}}
#progress{{position:absolute;left:70px;bottom:220px;width:940px;height:7px;background:#ffd24a;transform-origin:left}}
#flash{{position:absolute;inset:0;background:white;opacity:0;pointer-events:none}}
</style></head><body><div id="root" data-composition-id="previsaosulflu" data-width="1080" data-height="1920" data-duration="{dur}" data-fps="30">
<video id="base" class="clip" src="assets/base.mp4" data-start="0" data-duration="{dur}" data-track-index="0" muted playsinline></video>
{''.join(parts)}<div id="progress"></div><div id="flash"></div>
<audio id="voice" src="assets/mix.wav" data-start="0" data-duration="{dur}" data-track-index="3"></audio>
<script src="assets/gsap.min.js"></script><script>const tl=gsap.timeline({{paused:true}});{''.join(anim)}window.__timelines={{previsaosulflu:tl}};</script></div></body></html>'''
    (Path(pasta)/'index.html').write_text(text, encoding='utf-8')
    return dur


def renderizar(base, voz, batidas, segs_path, saida, trab):
    raiz = Path(__file__).resolve().parents[1]
    video = raiz/'video'
    cli = video/'node_modules/hyperframes/bin/hyperframes.mjs'
    if not cli.is_file():
        raise FileNotFoundError('Execute npm ci --prefix video antes de produzir')
    work = Path(trab).resolve()/'hyperframes'
    assets = work/'assets'
    assets.mkdir(parents=True, exist_ok=True)
    segs = json.loads(Path(segs_path).read_text())
    dur = compor(batidas, segs, work)
    sh(['ffmpeg','-y','-v','error','-i',base,'-c:v','libx264','-preset','fast','-crf','18','-g','30','-keyint_min','30','-sc_threshold','0','-pix_fmt','yuv420p','-an',assets/'base.mp4'])
    shutil.copy('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', assets/'bold.ttf')
    shutil.copy(video/'node_modules/gsap/dist/gsap.min.js', assets/'gsap.min.js')
    mixar(Path(voz), segs, dur, assets/'mix.wav')
    env = dict(os.environ, HYPERFRAMES_NO_TELEMETRY='1', DO_NOT_TRACK='1', HYPERFRAMES_FFMPEG_PATH=shutil.which('ffmpeg'), HYPERFRAMES_FFPROBE_PATH=shutil.which('ffprobe'))
    sh(['node',cli,'lint',work], env=env)
    final = Path(saida).resolve()
    tmp = final.with_name(final.stem+'.rendering.mp4')
    sh(['node',cli,'render',work,'--output',tmp,'--workers',os.environ.get('PREVISAO_HF_WORKERS','2'),'--no-browser-gpu'], env=env)
    conferir(tmp,dur)
    tmp.replace(final)
    final.with_suffix('.render.json').write_text(json.dumps({'motor':'hyperframes','versao':'0.8.96','duracao':dur,'fps':30,'resolucao':[1080,1920]}, indent=2))

def mixar(voz,segs,dur,destino):
    import numpy as np
    import soundfile as sf
    sr=48000;out=np.zeros(math.ceil(sr*dur));rng=np.random.default_rng(91)
    def add(t,s):
        i=int(t*sr);n=min(len(s),len(out)-i)
        if n>0:out[i:i+n]+=s[:n]
    for k,t0 in enumerate(np.arange(0,dur,.6)):
        t=np.arange(int(.22*sr))/sr
        add(t0,.008*np.sin(2*np.pi*65*t)*np.exp(-t*25))
        if k%2:add(t0,.002*rng.normal(size=len(t))*np.exp(-t*38))
    for k,t0 in enumerate(np.arange(0,dur,2.4)):
        t=np.arange(int(1.8*sr))/sr;notes=[220,261.63,329.63] if k%2 else [196,246.94,293.66]
        add(t0,sum(.003*np.sin(2*np.pi*f*t)*np.exp(-t*2.8) for f in notes))
    for s in segs[1:]:
        t=np.arange(int(.18*sr))/sr
        add(s['ini'],.006*rng.normal(size=len(t))*np.sin(np.pi*t/.18)**2)
    for i,s in enumerate(segs):
        if i==0 or i%4==0:
            for k,f in enumerate([880,1174]):
                t=np.arange(int(.14*sr))/sr
                add(s['ini']+.15+k*.14,.018*np.sin(2*np.pi*f*t)*np.exp(-t*25))
    bed=destino.with_name('bed.wav');sf.write(bed,out,sr)
    sh(['ffmpeg','-y','-v','error','-i',voz,'-i',bed,'-filter_complex',f'[0:a]apad,atrim=duration={dur}[v];[v][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=disabled[a]','-map','[a]','-ar','48000',destino])

def conferir(mp4,dur):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)]))
    videos=[s for s in data['streams'] if s['codec_type']=='video'];audios=[s for s in data['streams'] if s['codec_type']=='audio']
    if len(videos)!=1 or not audios:raise ValueError('MP4 incompleto: vídeo ou áudio ausente')
    v=videos[0]
    if (v['width'],v['height'],v['avg_frame_rate'])!=(1080,1920,'30/1') or abs(float(data['format']['duration'])-dur)>.15:
        raise ValueError('Resolução, fps ou duração divergente')
    return data

