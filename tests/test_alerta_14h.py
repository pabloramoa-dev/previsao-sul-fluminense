import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from tools.alerta_14h import TZ, horas, sinais, confirmar, validar
from tools import publicar_alerta_14h as pub
from tools.capa_alerta import detalhes, gerar_capa
from PIL import Image
from estudio.alerta_regional import preparar_boletim, preparar_aviso_oficial
from tools.areas_alagamento import PONTOS, resumo, cidades_com_chuva_intensa

AGORA = datetime(2026, 11, 20, 14, tzinfo=TZ)

def payload(mm=0, vento=10, code=0):
    return {'hourly_units': {'precipitation': 'mm', 'wind_gusts_10m': 'km/h'},
            'hourly': {'time': [(AGORA+timedelta(hours=i+1)).isoformat() for i in range(24)],
                       'precipitation': [mm]*24, 'wind_gusts_10m': [vento]*24,
                       'weather_code': [code]*24}}

def eventos(mm=0, vento=10, code=0):
    return sinais(horas(payload(mm, vento, code), AGORA))

def relatorio():
    ev = confirmar(eventos(code=95), eventos(code=95), 'Volta Redonda')
    return dict(emitido_em=AGORA.isoformat(), data='2026-11-20', publicar=True, eventos=ev)

class Alertas(unittest.TestCase):
    def test_tempo_normal_e_chuva_comum(self):
        self.assertEqual(eventos(mm=1), [])
    def test_um_modelo_so_bloqueia(self):
        self.assertEqual(confirmar(eventos(code=95), eventos(), 'VR'), [])
    def test_temporal_sem_inventar_granizo(self):
        e = confirmar(eventos(code=95), eventos(code=95), 'VR')
        self.assertEqual({x['tipo'] for x in e}, {'temporal'})
    def test_granizo_exige_codigo_explicito_nos_dois(self):
        self.assertNotIn('granizo', {x['tipo'] for x in confirmar(eventos(code=99), eventos(code=95), 'VR')})
        self.assertIn('granizo', {x['tipo'] for x in confirmar(eventos(code=99), eventos(code=96), 'VR')})
    def test_chuva_e_vento(self):
        self.assertIn('vento', {e['tipo'] for e in eventos(vento=60)})
        self.assertIn('chuva', {e['tipo'] for e in eventos(mm=20)})
    def test_sem_sobreposicao_bloqueia(self):
        a = eventos(code=95)[:1]
        b = eventos(code=95)[5:6]
        self.assertEqual(confirmar(a, b, 'VR'), [])
    def test_dados_faltantes_e_nan(self):
        for valor in (None, float('nan'), -1):
            p = payload(); p['hourly']['precipitation'][0] = valor
            with self.assertRaises(ValueError): horas(p, AGORA)
    def test_consulta_vencida(self):
        with self.assertRaises(ValueError): validar(relatorio(), AGORA+timedelta(hours=3))
        validar(relatorio(), AGORA)
    def test_roteiro_condicional(self):
        with tempfile.TemporaryDirectory() as d:
            _, _, batidas = preparar_boletim(relatorio(), 'bia', d)
            self.assertIn('não uma certeza', ' '.join(b['fala'] for b in batidas))
            self.assertIn('Volta Redonda', Path(d, 'LEGENDA.txt').read_text())
            with self.assertRaises(ValueError): preparar_boletim({'publicar': False}, 'bia', d)
    def test_base_hidrologica_cobre_dez_cidades_sem_inventar_risco_bairro(self):
        self.assertEqual(len(PONTOS), 10)
        self.assertIn('Vila Santa Cecília', resumo('Volta Redonda'))
        self.assertIn('Ribeirão dos Quatis', resumo('Quatis'))
        self.assertNotIn('Jardim Real', resumo('Porto Real'))
        self.assertEqual(resumo('Cidade inexistente'), '')

    def test_sem_alto_volume_nao_citar_bairros_no_video(self):
        with tempfile.TemporaryDirectory() as d:
            _, _, batidas = preparar_boletim(relatorio(), 'bia', d)
            texto = ' '.join(b['fala'] for b in batidas)
            self.assertNotIn('Córrego Secades', texto)
            self.assertNotIn('Vila Santa Cecília', texto)
            self.assertNotIn('Áreas historicamente', Path(d, 'LEGENDA.txt').read_text())

    def test_alto_volume_mesma_cidade_libera_contexto_nao_cheia(self):
        rel = relatorio()
        rel['eventos'] += confirmar(eventos(mm=20), eventos(mm=20), 'Volta Redonda')
        with tempfile.TemporaryDirectory() as d:
            _, _, batidas = preparar_boletim(rel, 'bia', d)
            texto = ' '.join(b['fala'] for b in batidas)
            legenda = Path(d, 'LEGENDA.txt').read_text()
            self.assertIn('Vila Santa Cecília', texto)
            self.assertIn('não uma cheia confirmada', texto)
            self.assertIn('Córrego Secades', legenda)
            self.assertIn('NÃO alagamentos confirmados', legenda)

    def test_chuva_outra_cidade_nao_empresta_bairro_ao_destaque(self):
        rel = relatorio()
        rel['eventos'] += confirmar(eventos(mm=20), eventos(mm=20), 'Barra Mansa')
        with tempfile.TemporaryDirectory() as d:
            _, _, batidas = preparar_boletim(rel, 'bia', d)
            self.assertNotIn('Vila Santa Cecília', ' '.join(b['fala'] for b in batidas))
            legenda = Path(d, 'LEGENDA.txt').read_text()
            self.assertIn('Barra Mansa: Nova Esperança', legenda)
            self.assertNotIn('Volta Redonda: Vila Santa Cecília', legenda)

    def test_alerta_oficial_identifica_historico_sem_afirmar_transbordo(self):
        rel = dict(data='2026-11-20', publicar=True, modo='aviso_oficial_inmet',
                   oficiais={'completa': True},
                   aviso_oficial={'fonte': 'INMET', 'evento': 'Tempestade',
                     'fim': '2026-11-20T23:00:00-03:00',
                     'emitido_em': '2026-11-20T14:00:00-03:00',
                     'url': 'https://avisos.inmet.gov.br/',
                     'cidades': ['Volta Redonda', 'Barra Mansa', 'Resende']})
        with tempfile.TemporaryDirectory() as d:
            _, _, batidas = preparar_aviso_oficial(rel, d)
            legenda = Path(d, 'LEGENDA.txt').read_text()
            self.assertIn('Nova Esperança', legenda)
            self.assertIn('Parque Ipiranga', legenda)
            self.assertIn('NÃO há confirmação de transbordamento', legenda)
            self.assertIn('histórico de alagamento', ' '.join(b['fala'] for b in batidas))
            self.assertIn('não cheia confirmada', ' '.join(b['fala'] for b in batidas))

    def test_capa_da_grade_legivel_e_baseada_no_evento_real(self):
        rel = relatorio()
        a, b, _, cidade, fim, base = detalhes(rel)
        self.assertEqual((a, b), ('RISCO DE', 'TEMPORAL'))
        self.assertEqual(cidade, 'VOLTA REDONDA')
        self.assertEqual(base, 'PREVISÃO • 2 MODELOS')
        with tempfile.TemporaryDirectory() as d:
            jpg = gerar_capa(rel, Path(d) / 'CAPA_ALERTA.jpg')
            with Image.open(jpg) as capa:
                self.assertEqual(capa.format, 'JPEG')
                self.assertEqual(capa.size, (1080, 1920))
            self.assertGreater(jpg.stat().st_size, 18000)

    def test_capa_rejeita_risco_sem_confirmacao_e_inmet_errado(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                gerar_capa({'publicar': False}, Path(d) / 'capa.jpg')
            with self.assertRaises(ValueError):
                detalhes({'publicar': True, 'modo': 'aviso_oficial_inmet',
                          'aviso_oficial': {'fonte': 'OUTRA', 'evento': 'Tempestade'}})

    def test_story_retomado_sem_duplicar_reel(self):
        with tempfile.TemporaryDirectory() as d, patch.object(pub, 'ESTADO', Path(d)/'recibos.json'), patch.object(pub, 'validar'), patch.dict('os.environ', {'IG_USER_ID':'user', 'IG_TOKEN':'fake'}), patch.object(pub, '_post', return_value={'id':'container'}) as enviar_container, patch.object(pub, 'esperar_container'), patch('reels.postar_reel._get', return_value={'status_code':'FINISHED'}), patch.object(pub, 'publicar_com_retentativa', side_effect=[{'id':'reel'}, RuntimeError('story falhou'), {'id':'story'}]) as enviar:
            with self.assertRaises(RuntimeError): pub.publicar(relatorio(), 'https://example.test/video.mp4', 'Previsão', 'https://example.test/CAPA_ALERTA.jpg')
            self.assertEqual(json.loads(pub.ESTADO.read_text())['2026-11-20']['REELS'], 'reel')
            pub.publicar(relatorio(), 'https://example.test/video.mp4', 'Previsão', 'https://example.test/CAPA_ALERTA.jpg')
            self.assertEqual(enviar.call_count, 3)
            criacoes = [call.args[1] for call in enviar_container.call_args_list if call.args[1].get('media_type')]
            self.assertEqual(criacoes[0]['cover_url'], 'https://example.test/CAPA_ALERTA.jpg')
            self.assertNotIn('cover_url', criacoes[1])
            self.assertEqual(json.loads(pub.ESTADO.read_text())['2026-11-20']['STORIES'], 'story')

if __name__ == '__main__': unittest.main()
