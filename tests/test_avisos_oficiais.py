import unittest
from datetime import datetime
from unittest.mock import patch
from tools.avisos_oficiais import ler_cap,ler_painel,municipios,coletar,correspondentes
from tools.alerta_14h import TZ,validar

C=[{'nome':'Rio Claro'}]
NOW=datetime(2026,11,20,14,tzinfo=TZ)
CAP='''<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2"><identifier>x</identifier><sender>info.aviso@inmet.gov.br</sender><sent>2026-11-20T10:00:00-03:00</sent><status>Actual</status><msgType>Alert</msgType><scope>Public</scope><info><language>pt-BR</language><event>Tempestade</event><severity>Moderate</severity><onset>2026-11-20T10:00:00-03:00</onset><expires>2026-11-20T23:59:00-03:00</expires><web>https://avisos.inmet.gov.br/1</web><parameter><valueName>Municipios</valueName><value>Rio Claro - RJ (3304409)</value></parameter></info></alert>'''
class Oficiais(unittest.TestCase):
    def test_municipio_e_uf_exatos(self):
        self.assertEqual(municipios('Rio Claro - SP (3543907)',C),[])
        self.assertEqual(municipios('Rio Claro - RJ (3304409)',C),['Rio Claro'])
    def test_cap_valido(self):
        a=ler_cap(CAP,C,NOW);self.assertEqual(a[0]['tipo'],'temporal')
    def test_vencido_cancelado_teste_e_futuro(self):
        for a,b in [('23:59:00','11:00:00'),('<status>Actual','<status>Test'),('<msgType>Alert','<msgType>Cancel'),('Rio Claro - RJ','Rio Claro - SP'),('2026-11-20T10:00:00','2026-12-20T10:00:00')]:
            self.assertEqual(ler_cap(CAP.replace(a,b),C,NOW),[])
    def test_painel_nao_e_temporal(self):
        h='<h5>Risco de Deslizamento</h5><table><tr><td>RIO CLARO</td><td>SUL II</td><td>ALTO</td><td>20/11/2026 10:00:00</td></tr></table>'
        r=ler_painel(h.encode(),'risco_deslizamento',C)
        self.assertEqual(r[0]['nivel'],'ALTO');self.assertFalse(r[0]['validade_explicita'])
        self.assertNotIn('tipo',r[0])
    def test_falha_nao_e_sem_alerta(self):
        with patch('tools.avisos_oficiais.baixar',side_effect=RuntimeError('offline')):
            r=coletar(C,NOW)
        self.assertFalse(r['completa'])
        self.assertTrue(all(f['status']=='indisponivel' for f in r['fontes'].values()))
    def test_bloqueio_consulta_incompleta(self):
        with self.assertRaises(ValueError):
            validar({'emitido_em':NOW.isoformat(),'oficiais':{'completa':False},'publicar':True},NOW)
    def test_correspondencia_temporal(self):
        aviso=ler_cap(CAP,C,NOW)[0]
        oficiais={'fontes':{'inmet':{'dados':[aviso]}}}
        e=dict(local='Rio Claro',tipo='temporal',inicio='2026-11-21T10:00:00-03:00',fim='2026-11-21T11:00:00-03:00')
        self.assertEqual(correspondentes([e],oficiais),[])
        e.update(inicio='2026-11-20T14:00:00-03:00',fim='2026-11-20T15:00:00-03:00')
        self.assertEqual(len(correspondentes([e],oficiais)),1)
    def test_painel_errado_bloqueado(self):
        with self.assertRaises(ValueError): ler_painel(b'login','severidade_meteorologica',C)
if __name__=='__main__':unittest.main()
