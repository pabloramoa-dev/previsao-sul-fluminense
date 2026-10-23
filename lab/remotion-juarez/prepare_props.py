#!/usr/bin/env python3
"""Converte o pacote real do Juarez (com dados demonstrativos) em props Remotion."""
import json,math,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
source=root.parents[1]/'hyperframes'/'build'/'pacote.json'
out=root/'props.json'
p=json.loads(source.read_text(encoding='utf-8'))
cidades=[{k:c.get(k) for k in ('nome','min','max','cond','chuva_mm')} for c in p['cidades']]
batidas=[{'tipo':b['tipo'],'ini':b['ini'],'fim':b['fim'],'legenda':b.get('legenda','')} for b in p['batidas']]
video=root/'public'/'juarez-original.mp4'
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(video)],text=True))
duration=float(info['format']['duration'])
if abs(duration-float(p['dur']))>.16:raise ValueError(f'Duração origem divergente: {duration} vs {p["dur"]}')
assert all((c['nome'] and isinstance(c['min'], (int,float)) and isinstance(c['max'], (int,float))) for c in cidades)
props={'durationFrames':math.ceil(duration*30),'data':p['data'],'cidades':cidades,'batidas':batidas}
out.write_text(json.dumps(props,ensure_ascii=False,indent=2),encoding='utf-8')
print('props:',duration,'s',len(cidades),'cidades; demonstacao:',p['data'])
