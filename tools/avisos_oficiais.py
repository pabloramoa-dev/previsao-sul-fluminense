"""Consulta fontes oficiais; não confunde risco geológico com tempestade.

Os avisos complementam a trava de dois modelos, sem liberar publicação sozinhos.
"""
import re
import unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import urlparse
import requests

INMET = 'https://apiprevmet3.inmet.gov.br/avisos/ativos'
BASE = 'https://painelcemadenrj.defesacivil.rj.gov.br/monitoramento/v2/'
FONTES = {'inmet': INMET, 'severidade_meteorologica': BASE+'mapa/redec.php?action=1',
          'risco_deslizamento': BASE+'municipio/?action=1',
          'risco_hidrologico': BASE+'municipio/?action=2'}
NS = {'c': 'urn:oasis:names:tc:emergency:cap:1.2'}

def normalizar(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).upper().strip()

class Tabela(HTMLParser):
    def __init__(self):
        super().__init__(); self.linhas=[]; self.linha=None; self.celula=None; self.textos=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.linha=[]
        if tag in ('td', 'th'): self.celula=[]
    def handle_data(self, s):
        self.textos.append(s)
        if self.celula is not None: self.celula.append(s)
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.celula is not None:
            if self.linha is not None: self.linha.append(' '.join(''.join(self.celula).split()))
            self.celula=None
        if tag == 'tr' and self.linha is not None:
            self.linhas.append(self.linha); self.linha=None

def baixar(url):
    r = requests.get(url, timeout=(10, 35), headers={'User-Agent':'PrevisaoSulFlu/1.0 (consulta de avisos publicos)'})
    r.raise_for_status()
    if urlparse(r.url).hostname != urlparse(url).hostname:
        raise ValueError('Redirecionamento para outra origem')
    # Bytes XML evitam mojibake: o CAP declara UTF-8.
    return r.content

def municipios(texto, cidades):
    presentes = {normalizar(m) for m in re.findall(r'(?:^|,)\s*([^,]+?)\s+-\s+RJ\s+\(\d{7}\)', texto)}
    return [c['nome'] for c in cidades if normalizar(c['nome']) in presentes]

def ler_cap(conteudo, cidades, agora):
    root=ET.fromstring(conteudo)
    def campo(nome): return root.findtext('c:'+nome, '', NS)
    if campo('status')!='Actual' or campo('msgType') not in ('Alert','Update') or campo('scope')!='Public': return []
    if not campo('sender').lower().endswith('@inmet.gov.br'): return []
    enviado=datetime.fromisoformat(campo('sent'))
    if enviado.tzinfo is None or enviado>agora+timedelta(minutes=5): return []
    avisos=[]
    for info in root.findall('c:info',NS):
        def dado(nome): return info.findtext('c:'+nome,'',NS)
        if dado('language') not in ('pt-BR','pt'): continue
        inicio=datetime.fromisoformat(dado('onset') or dado('effective'))
        fim=datetime.fromisoformat(dado('expires'))
        if inicio.tzinfo is None or fim.tzinfo is None or fim<=agora or inicio>=fim or inicio>agora+timedelta(hours=24): continue
        params={p.findtext('c:valueName','',NS):p.findtext('c:value','',NS) for p in info.findall('c:parameter',NS)}
        locais=municipios(params.get('Municipios',''),cidades)
        if not locais: continue
        evento=normalizar(dado('event'))
        tipo={'TEMPESTADE':'temporal','CHUVAS INTENSAS':'chuva','ACUMULADO DE CHUVA':'chuva','VENDAVAL':'vento','GRANIZO':'granizo'}.get(evento)
        if not tipo: continue
        link=dado('web')
        if urlparse(link).hostname != 'avisos.inmet.gov.br': continue
        avisos.append(dict(id=campo('identifier'), fonte='INMET', url=link, tipo=tipo,
            evento=dado('event'), severidade=dado('severity'), cidades=locais,
            inicio=inicio.isoformat(), fim=fim.isoformat(), emitido_em=enviado.isoformat(),
            descricao=dado('description'), instrucoes=dado('instruction')))
    return avisos

def ler_painel(conteudo, tipo, cidades):
    p=Tabela();p.feed(conteudo.decode('utf-8'))
    texto=' '.join(' '.join(p.textos).split())
    if tipo=='severidade_meteorologica':
        if 'Nível de Severidade Meteorológica' not in texto: raise ValueError('Painel meteorológico não reconhecido')
        resultados=[]
        for regiao in ('SUL I','SUL II'):
            m=re.search(r'\b'+regiao+r'\s+-\s+(MUITO BAIXO|MUITO ALTO|MODERADO|BAIXO|ALTO)\s+-',texto)
            if not m: raise ValueError('Regional ausente: '+regiao)
            resultados.append(dict(regiao=regiao,nivel=m[1],validade_explicita=False))
        return resultados
    titulo={'risco_deslizamento':'Risco de Deslizamento','risco_hidrologico':'Risco Hidrológico'}[tipo]
    if titulo not in texto: raise ValueError('Tipo de painel inesperado')
    nomes={normalizar(c['nome']):c['nome'] for c in cidades}
    resultados=[]
    for row in p.linhas:
        if len(row)<4 or normalizar(row[0]) not in nomes: continue
        atualizado=datetime.strptime(row[3],'%d/%m/%Y %H:%M:%S')
        resultados.append(dict(local=nomes[normalizar(row[0])],regiao=row[1],nivel=row[2],
                               atualizado_em_local=atualizado.isoformat(),validade_explicita=False))
    if len(resultados)!=len(cidades): raise ValueError('Painel municipal incompleto')
    return resultados

def coletar(cidades, agora):
    def fonte(item):
        nome,url=item
        try:
            raw=baixar(url)
            if nome=='inmet':
                import json
                j=json.loads(raw)
                if not isinstance(j.get('hoje'),list) or not isinstance(j.get('futuro'),list): raise ValueError('Lista INMET inválida')
                ids={str(a['id']) for a in j['hoje']+j['futuro'] if municipios(a.get('municipios',''),cidades)}
                avisos=[]
                for aid in sorted(ids):
                    if not aid.isdigit(): raise ValueError('Identificador INMET inválido')
                    avisos+=ler_cap(baixar('https://apiprevmet3.inmet.gov.br/avisos/rss/'+aid),cidades,agora)
                dados=avisos
            else: dados=ler_painel(raw,nome,cidades)
            return nome,dict(status='ok',url=url,consultado_em=agora.isoformat(),dados=dados)
        except Exception as exc:
            return nome,dict(status='indisponivel',url=url,consultado_em=agora.isoformat(),erro=str(exc)[:250],dados=[])
    with ThreadPoolExecutor(max_workers=4) as pool:
        fontes=dict(pool.map(fonte,FONTES.items()))
    return dict(fontes=fontes,completa=all(f['status']=='ok' for f in fontes.values()),
                observacao='Painéis sem validade explícita são contexto, não comprovam temporal ou granizo. Falha de consulta não significa ausência de aviso.')

def correspondentes(eventos, oficiais):
    avisos=oficiais.get('fontes',{}).get('inmet',{}).get('dados',[])
    return [a for a in avisos if any(e['local'] in a['cidades'] and e['tipo']==a['tipo']
        and max(datetime.fromisoformat(e['inicio']),datetime.fromisoformat(a['inicio']))
        < min(datetime.fromisoformat(e['fim']),datetime.fromisoformat(a['fim'])) for e in eventos)]
