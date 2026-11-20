import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from tools.alerta_14h import TZ, horas, sinais, confirmar, validar
from tools import publicar_alerta_14h as pub
from estudio.alerta_regional import preparar_boletim

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
    def test_story_retomado_sem_duplicar_reel(self):
        with tempfile.TemporaryDirectory() as d, patch.object(pub, 'ESTADO', Path(d)/'recibos.json'), patch.object(pub, 'validar'), patch.dict('os.environ', {'IG_USER_ID':'user', 'IG_TOKEN':'fake'}), patch.object(pub, '_post', return_value={'id':'container'}), patch.object(pub, 'esperar_container'), patch('reels.postar_reel._get', return_value={'status_code':'FINISHED'}), patch.object(pub, 'publicar_com_retentativa', side_effect=[{'id':'reel'}, RuntimeError('story falhou'), {'id':'story'}]) as enviar:
            with self.assertRaises(RuntimeError): pub.publicar(relatorio(), 'https://example.test/video.mp4', 'Previsão')
            self.assertEqual(json.loads(pub.ESTADO.read_text())['2026-11-20']['REELS'], 'reel')
            pub.publicar(relatorio(), 'https://example.test/video.mp4', 'Previsão')
            self.assertEqual(enviar.call_count, 3)
            self.assertEqual(json.loads(pub.ESTADO.read_text())['2026-11-20']['STORIES'], 'story')

if __name__ == '__main__': unittest.main()
