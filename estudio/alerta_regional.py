"""Entrada do mesmo estúdio Bira/Bia, exclusiva para previsão corroborada."""
import json
from datetime import datetime
from pathlib import Path

NOMES = {'temporal': 'risco de temporal', 'chuva': 'chuva intensa',
         'granizo': 'possibilidade de granizo', 'vento': 'ventos fortes'}

def preparar_boletim(rel, personagem, destino):
    if not rel.get('publicar') or not rel.get('eventos'):
        raise ValueError('Sem evento confirmado nos dois modelos')
    e = rel['eventos'][0]
    inicio, fim = [datetime.fromisoformat(e[k]) for k in ('inicio', 'fim')]
    janela = f"de {inicio:%d/%m às %Hh} até {fim:%d/%m às %Hh}"
    abertura = f"Atenção, {e['local']}! Há previsão de {NOMES[e['tipo']]} {janela}."
    detalhe = (f"Os modelos indicam até {e['valor']:g} {e['unidade']}."
               if e['tipo'] in ('vento', 'chuva') else
               'Dois modelos meteorológicos indicam esse risco para a cidade.')
    # Nunca apresentar previsão como ocorrência garantida ou aviso oficial.
    fechamento = 'É uma previsão, não uma certeza. Acompanhe os avisos da Defesa Civil.'
    def batida(tipo, fala, **dados):
        return dict(tipo=tipo, fala=fala, legenda=fala, dados=dados)
    batidas = [batida('frase', abertura),
               batida('alerta', detalhe, titulo=NOMES[e['tipo']], detalhe=e['local']),
               batida('frase', fechamento),
               batida('cta', 'Compartilhe com quem está nessa região.', chamada='COMPARTILHE')]
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    linhas = [abertura, detalhe, fechamento, '', 'Outras previsões corroboradas:']
    vistos = set()
    for ev in rel['eventos']:
        chave = ev['local'], ev['tipo']
        if chave in vistos: continue
        vistos.add(chave)
        linhas.append(f"{ev['local']}: {NOMES[ev['tipo']]}")
    oficiais = rel.get('avisos_oficiais_correspondentes', [])
    if oficiais:
        linhas += ['', 'Avisos oficiais válidos para os eventos citados:']
        linhas += [f"INMET: {a['evento']} — válido até {a['fim']}. {a['url']}" for a in oficiais[:2]]
    linhas += ['', f"Consulta: {rel['emitido_em']}",
               'Fontes: modelos DWD ICON e NOAA GFS via Open-Meteo.',
               'Consulta complementar: INMET e CEMADEN-RJ/Defesa Civil.',
               '@previsaosulflu #SulFluminense #PrevisãoDoTempo']
    (destino/'LEGENDA.txt').write_text('\n'.join(linhas), encoding='utf-8')
    bloco = {'date': rel['data'], 'locations': []}
    # Sem painel de temperaturas: o plantão só mostra o evento comprovado na previsão.
    cidades = [{'nome': e['local'], 'cond': 'chuva'}]
    return {'forecast': {'today': bloco, 'tomorrow': bloco}}, cidades, batidas
