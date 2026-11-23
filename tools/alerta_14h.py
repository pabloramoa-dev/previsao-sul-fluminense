"""Plantão conservador: dois modelos concordantes, próximas 24h, falha fechada."""
import argparse
import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from src.clima import CIDADES, _get_json, FORECAST_URL

TZ = ZoneInfo('America/Sao_Paulo')
MODELOS = ('icon_seamless', 'gfs_seamless')
CAMPOS = ('precipitation', 'wind_gusts_10m', 'weather_code')
NOMES = {'temporal': 'risco de temporal', 'chuva': 'chuva intensa',
         'granizo': 'possibilidade de granizo', 'vento': 'ventos fortes'}

def horas(payload, agora):
    h = payload['hourly']
    unidades = payload['hourly_units']
    if unidades.get('precipitation') != 'mm' or unidades.get('wind_gusts_10m') != 'km/h':
        raise ValueError('Unidades meteorológicas inesperadas')
    inicio = agora.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    linhas = {}
    for i, s in enumerate(h['time']):
        t = datetime.fromisoformat(s).replace(tzinfo=TZ)
        if inicio <= t < inicio + timedelta(hours=24):
            valores = [h[k][i] for k in CAMPOS]
            if any(v is None or not math.isfinite(float(v)) or float(v) < 0 for v in valores):
                raise ValueError('Dado ausente ou inválido; não publicar')
            linhas[t] = dict(zip(CAMPOS, valores))
    if len(linhas) != 24:
        raise ValueError('Previsão incompleta para as próximas 24 horas')
    return linhas

def sinais(linhas):
    resultado = []
    for t, r in sorted(linhas.items()):
        def add(tipo, valor, unidade, janela=1):
            resultado.append(dict(tipo=tipo, inicio=(t-timedelta(hours=1)).isoformat(),
                                  fim=(t+timedelta(hours=janela-1)).isoformat(),
                                  valor=round(valor, 1), unidade=unidade))
        if r['weather_code'] in (95, 96, 99): add('temporal', r['weather_code'], 'WMO')
        if r['weather_code'] in (96, 99): add('granizo', r['weather_code'], 'WMO')
        if r['wind_gusts_10m'] >= 60: add('vento', r['wind_gusts_10m'], 'km/h')
        if r['precipitation'] >= 20: add('chuva', r['precipitation'], 'mm em 1h')
        for n, limite in ((3, 30), (24, 50)):
            janela = [linhas.get(t+timedelta(hours=i)) for i in range(n)]
            if all(janela):
                mm = sum(x['precipitation'] for x in janela)
                if mm >= limite: add('chuva', mm, f'mm em {n}h', n)
    return resultado

def confirmar(a, b, cidade):
    confirmados = []
    for e in a:
        pares = [f for f in b if f['tipo'] == e['tipo'] and f['unidade'] == e['unidade']
                 and max(e['inicio'], f['inicio']) < min(e['fim'], f['fim'])]
        if pares:
            f = max(pares, key=lambda x: x['valor'])
            confirmados.append(dict(e, local=cidade, modelos=list(MODELOS),
                                    valor=min(e['valor'], f['valor']),
                                    evidencias=[e, f]))
    return confirmados

def verificar(agora=None):
    agora = agora or datetime.now(TZ)
    from tools.avisos_oficiais import coletar, correspondentes
    oficiais = coletar(CIDADES, agora)
    respostas = {}
    for modelo in MODELOS:
        respostas[modelo] = _get_json(FORECAST_URL, {
            'latitude': ','.join(str(c['lat']) for c in CIDADES),
            'longitude': ','.join(str(c['lon']) for c in CIDADES),
            'hourly': ','.join(CAMPOS), 'models': modelo,
            'timezone': 'America/Sao_Paulo', 'forecast_days': 3,
            'wind_speed_unit': 'kmh', 'precipitation_unit': 'mm'})
        if not isinstance(respostas[modelo], list) or len(respostas[modelo]) != len(CIDADES):
            raise ValueError('Cobertura regional incompleta')
    eventos = []
    for i, cidade in enumerate(CIDADES):
        a, b = [sinais(horas(respostas[m][i], agora)) for m in MODELOS]
        eventos += confirmar(a, b, cidade['nome'])
    prioridade = {'granizo': 4, 'temporal': 3, 'chuva': 2, 'vento': 1}
    eventos.sort(key=lambda e: (-prioridade[e['tipo']], -e['valor'], e['inicio']))
    # Um aviso CAP de ciclone vigente na área pode fundamentar o plantão
    # independentemente dos modelos; nunca deduzir ciclone a partir de vento.
    aviso_ciclone = next((a for a in oficiais['fontes']['inmet']['dados']
        if a.get('tipo') == 'ciclone' and a.get('fonte') == 'INMET'
        and a.get('cidades') and datetime.fromisoformat(a['fim']) > agora
        and datetime.fromisoformat(a['inicio']) <= agora + timedelta(hours=24)), None)
    if aviso_ciclone:
        eventos.insert(0, dict(tipo='ciclone', local=aviso_ciclone['cidades'][0],
            inicio=aviso_ciclone['inicio'], fim=aviso_ciclone['fim'],
            aviso_id=aviso_ciclone['id']))
    # Um plantão por dia, foco no evento mais relevante; demais locais na legenda.
    return dict(emitido_em=agora.isoformat(), data=agora.date().isoformat(),
                fonte=FORECAST_URL, modelos=list(MODELOS), eventos=eventos,
                publicar=bool(eventos) and oficiais['completa'],
                modo='aviso_oficial_inmet' if aviso_ciclone else 'dois_modelos',
                aviso_oficial=aviso_ciclone, cidades_consultadas=len(CIDADES),
                oficiais=oficiais, avisos_oficiais_correspondentes=([aviso_ciclone] if aviso_ciclone else correspondentes(eventos, oficiais)))

def validar(relatorio, agora=None):
    agora = agora or datetime.now(TZ)
    emitido = datetime.fromisoformat(relatorio['emitido_em'])
    if not timedelta(0) <= agora-emitido <= timedelta(hours=2):
        raise ValueError('Consulta vencida; publicação bloqueada')
    if relatorio.get('oficiais') and not relatorio['oficiais']['completa']:
        raise ValueError('Consulta oficial incompleta; publicação bloqueada')
    if not relatorio.get('publicar') or not relatorio.get('eventos'):
        raise ValueError('Sem previsão corroborada; publicação bloqueada')
    if datetime.fromisoformat(relatorio['eventos'][0]['fim']) <= agora:
        raise ValueError('Todos os eventos já passaram')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--saida', default='saida/alertas/consulta.json')
    a = ap.parse_args()
    p = Path(a.saida)
    p.parent.mkdir(parents=True, exist_ok=True)
    rel = verificar()
    p.write_text(json.dumps(rel, ensure_ascii=False, indent=2))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"publicar={str(rel['publicar']).lower()}\n")
    print(json.dumps({'publicar': rel['publicar'], 'eventos': len(rel['eventos'])}))

if __name__ == '__main__': main()
