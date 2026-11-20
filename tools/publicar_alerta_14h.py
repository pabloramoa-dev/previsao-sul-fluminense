"""Recibos separados de Reel/Story permitem retomar sem republicar o Reel."""
import argparse
import json
import os
from pathlib import Path
from tools.alerta_14h import validar
from reels.postar_reel import _post, esperar_container, publicar_com_retentativa, validar_legenda

ESTADO = Path('data/alertas_14h_publicados.json')

def publicar(rel, url, legenda):
    validar(rel)
    validar_legenda(legenda)
    uid, token = os.environ['IG_USER_ID'], os.environ['IG_TOKEN']
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    dia = rel['data']
    recibo = estado.setdefault(dia, {})
    def salvar():
        ESTADO.parent.mkdir(parents=True, exist_ok=True)
        temp = ESTADO.with_suffix('.tmp')
        temp.write_text(json.dumps(estado, ensure_ascii=False, indent=2))
        temp.replace(ESTADO)
    for tipo in ('REELS', 'STORIES'):
        if recibo.get(tipo): continue
        # Persiste o container antes de publicar: reexecuções consultam o estado da Meta.
        chave = tipo + '_container'
        if not recibo.get(chave):
            corpo = dict(media_type=tipo, video_url=url, access_token=token)
            if tipo == 'REELS': corpo.update(caption=legenda, share_to_feed='true')
            recibo[chave] = _post(f'{uid}/media', corpo)['id']
            salvar()
        from reels.postar_reel import _get
        status = _get(recibo[chave], {'fields': 'status_code', 'access_token': token})
        if status.get('status_code') == 'PUBLISHED':
            recibo[tipo] = {'container_publicado': recibo[chave]}
        else:
            esperar_container(recibo[chave], token)
            pub = publicar_com_retentativa(uid, recibo[chave], token)
            if not pub.get('id'): raise RuntimeError('Meta não confirmou a publicação')
            recibo[tipo] = pub['id']
        salvar()
        print(f'{tipo}: publicação confirmada')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--consulta', required=True)
    ap.add_argument('--video', required=True)
    ap.add_argument('--legenda', required=True)
    a = ap.parse_args()
    publicar(json.loads(Path(a.consulta).read_text()), a.video, Path(a.legenda).read_text())
