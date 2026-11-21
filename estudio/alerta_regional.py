"""Entrada do mesmo estúdio Bira/Bia, exclusiva para previsão corroborada."""
import json
from datetime import datetime
from pathlib import Path
from tools.areas_alagamento import resumo, cidades_com_chuva_intensa

NOMES = {'temporal': 'risco de temporal', 'chuva': 'chuva intensa',
         'granizo': 'possibilidade de granizo', 'vento': 'ventos fortes'}

def preparar_boletim(rel, personagem, destino):
    if rel.get('modo') == 'aviso_oficial_inmet':
        return preparar_aviso_oficial(rel, destino)
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
               batida('alerta', detalhe, titulo=NOMES[e['tipo']], detalhe=e['local'])]
    # Só nomear bairros quando houver CHUVA INTENSA confirmada na mesma cidade
    # pelos dois modelos (não basta WMO de tempestade ou chuva em outra cidade).
    cidades_chuva = cidades_com_chuva_intensa(rel['eventos'])
    if e['local'] in cidades_chuva and e['tipo'] in ('temporal', 'chuva'):
        trechos = resumo(e['local'], grupos=1, locais_por_grupo=2)
        if trechos:
            batidas.append(batida('frase',
                f"Em {e['local']}, atenção a {trechos}. "
                "São áreas com histórico de alagamento, não uma cheia confirmada."))
    batidas += [batida('frase', fechamento),
                batida('cta', 'Compartilhe com quem está nessa região.', chamada='COMPARTILHE')]
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    linhas = [abertura, detalhe, fechamento, '', 'Outras previsões corroboradas:']
    # Resumir por cidade para evitar legendas com dezenas de linhas duplicadas
    # e respeitar o limite de 2.200 caracteres do Instagram.
    por_cidade = {}
    for ev in rel['eventos']:
        tipos = por_cidade.setdefault(ev['local'], [])
        if ev['tipo'] not in tipos:
            tipos.append(ev['tipo'])
    for nome, tipos in por_cidade.items():
        linhas.append(f"{nome}: {', '.join(NOMES[t] for t in tipos)}")
    # Legenda: explicitar rios/bairros por MUNICÍPIO, sem misturar com a previsão
    # de outra cidade e sem prometer que haverá alagamento.
    if cidades_chuva:
        linhas += ['', 'Áreas historicamente afetadas ou suscetíveis a cheias (atenção preventiva):']
        por_cidade = list(dict.fromkeys(ev['local'] for ev in rel['eventos']
                                       if ev['local'] in cidades_chuva))
        for nome in por_cidade[:6]:
            trecho = resumo(nome, grupos=2, locais_por_grupo=3)
            if trecho:
                linhas.append(f"{nome}: {trecho}.")
        if len(por_cidade) > 6:
            linhas.append('Outros municípios também têm chuva intensa prevista; consulte a Defesa Civil local.')
        linhas.append('São históricos/pontos de atenção, NÃO alagamentos confirmados nem previsão por bairro.')
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

def preparar_aviso_oficial(rel, destino):
    """Plantão dedicado ao aviso público e válido do INMET, sem inferir ocorrência certa."""
    if not rel.get('publicar') or not rel.get('aviso_oficial'):
        raise ValueError('Sem aviso oficial válido')
    aviso = rel['aviso_oficial']
    fim = datetime.fromisoformat(aviso['fim'])
    if aviso.get('fonte') != 'INMET' or aviso.get('evento') != 'Tempestade':
        raise ValueError('Tipo de comunicado não permitido')
    if not rel.get('oficiais', {}).get('completa'):
        raise ValueError('Fontes oficiais incompletas')
    hora = fim.strftime('%Hh%M')
    foco = ['Volta Redonda', 'Barra Mansa', 'Resende']
    nomes = [n for n in foco if n in aviso['cidades']]
    if len(nomes) < 3:
        raise ValueError('Cobertura regional do aviso insuficiente')
    abertura = (f"Atenção, Sul Fluminense! O INMET mantém alerta amarelo de tempestade "
                f"válido hoje até as {hora}. O aviso inclui {', '.join(nomes)} e outros municípios.")
    detalhe = ("Segundo o INMET, existe possibilidade de chuva entre 20 e 30 milímetros por hora, "
               "ventos de 40 a 60 quilômetros por hora e queda de granizo.")
    cautela = ("O nível amarelo indica perigo potencial. Não significa temporal certo em toda a região. "
               "Durante rajadas, evite ficar sob árvores e acompanhe a Defesa Civil.")
    fecho = "Compartilhe este aviso com quem mora no Sul Fluminense."
    def b(tipo, fala, **dados):
        return {'tipo': tipo, 'fala': fala, 'legenda': fala, 'dados': dados}
    batidas = [b('frase', abertura), b('alerta', detalhe, titulo='ALERTA AMARELO DO INMET',
                 detalhe='RISCO DE TEMPESTADE'),
               b('frase', 'Em áreas ribeirinhas e bairros com histórico de alagamentos, redobre a atenção. Confira os locais na legenda.'),
               b('frase', cautela), b('cta', fecho, chamada='COMPARTILHE')]
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    cidades = ', '.join(aviso['cidades'])
    legenda = (f"ALERTA AMARELO DO INMET — SUL FLUMINENSE | {rel['data']}\n\n"
               f"O INMET mantém aviso de perigo potencial de tempestade até {hora} de hoje "
               f"para: {cidades}.\n\n"
               "Possibilidade de chuva entre 20 e 30 mm/h (até 50 mm/dia), rajadas de 40 a 60 km/h "
               "e queda de granizo. Isto NÃO significa que esses fenômenos ocorrerão em todas as cidades.\n\n"
               "Não se abrigue debaixo de árvores em caso de rajadas. Em emergência: Defesa Civil 199 e Bombeiros 193.\n"
               f"Fonte: INMET — {aviso['url']}. Emissão do boletim: {aviso['emitido_em']}. "
               "Este comunicado informa um AVISO OFICIAL, não uma concordância de dois modelos numéricos.\n"
               "@previsaosulflu #AlertaDeTempestade #SulFluminense")
    # Apenas os municípios COBERTOS pelo aviso oficial, e como histórico.
    historicos = [f"{nome}: {resumo(nome, grupos=2, locais_por_grupo=3)}."
                  for nome in nomes if resumo(nome)]
    if historicos:
        legenda += ("\n\nPONTOS HISTORICAMENTE AFETADOS OU SUSCETÍVEIS A ALAGAMENTOS:\n"
                    + "\n".join(historicos)
                    + "\nAtenção preventiva: NÃO há confirmação de transbordamento nesses locais."
                    + "\nAcompanhe orientações oficiais e não atravesse ruas alagadas.")
    (destino/'LEGENDA.txt').write_text(legenda, encoding='utf-8')
    bloco = {'date': rel['data'], 'locations': []}
    return {'forecast': {'today': bloco, 'tomorrow': bloco}}, [], batidas
