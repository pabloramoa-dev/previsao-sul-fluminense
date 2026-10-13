"""Regressões da direção expressiva (sem Manim, rede nem IA)."""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import direcao_previsao as D
import qualidade_previsao as Q


def amostra():
    b = [
        {"tipo":"gancho", "fala":"Em Resende, trinta graus.", "legenda":"RESENDE 30°", "dados":{"cor":"calor"}},
        {"tipo":"resumo", "fala":"Barra Mansa, vinte e oito graus.", "legenda":"BARRA MANSA 28°"},
        {"tipo":"chuva", "fala":"Pode chover em Volta Redonda.", "legenda":"CHUVA EM VOLTA REDONDA"},
        {"tipo":"alerta", "fala":"Atenção, chuva forte.", "legenda":"ATENÇÃO", "dados":{"cor":"alerta"}},
        {"tipo":"cta", "fala":"Siga para acompanhar.", "legenda":"SIGA"},
    ]
    s = [dict(ini=i*3.0,fim=(i+1)*3.0) for i in range(len(b))]
    return b,s


class TestDirecao(unittest.TestCase):
    def test_sem_inventar_previsao(self):
        b,s = amostra()
        original = json.dumps(b,sort_keys=True,ensure_ascii=False)
        for personagem in ("ranzinza","maria","juarez"):
            plano = D.planejar(b,s,personagem)
            self.assertEqual(plano,D.planejar(b,s,personagem))
            self.assertEqual(json.dumps(b,sort_keys=True,ensure_ascii=False),original)
            self.assertEqual([p["tipo"] for p in plano],[x["tipo"] for x in b])
            self.assertEqual(plano[0]["gesto"],"enfatizar")
            self.assertEqual(plano[1]["gesto"],"apontar")
            self.assertEqual(plano[3]["gesto"],"alertar")
            self.assertEqual(plano[-1]["gesto"],"acolher")

    def test_suavidade_sem_salto(self):
        for gesture in D.GESTOS:
            self.assertEqual(D.deslocamento(gesture,0,0,3),(0.,0.))
            self.assertEqual(D.deslocamento(gesture,3,0,3),(0.,0.))
            for t in (0.05,0.3,0.9,1.5,2.6):
                dx,dy = D.deslocamento(gesture,t,0,3)
                self.assertTrue(math.isfinite(dx) and math.isfinite(dy))
                self.assertLessEqual(abs(dx),0.4)
                self.assertLessEqual(abs(dy),0.45)

    def test_camera_segura(self):
        b,s=amostra()
        for p in D.planejar(b,s,"maria"):
            scale,x=D.camera(p)
            self.assertTrue(1.0 <= scale <= 1.07)
            self.assertTrue(-8<=x<=8)

    def test_timeline_rejeita_erros(self):
        b,s = amostra()
        with self.assertRaises(ValueError):
            D.planejar(b,s[:-1])
        s[1]["ini"]=2.5
        with self.assertRaises(ValueError):
            D.planejar(b,s)

    def test_qa_tecnico_e_dados_preservados(self):
        b,s = amostra()
        plano = D.planejar(b,s,"juarez")
        probe={"streams":[{"codec_type":"video"},{"codec_type":"audio"}]}
        qa = Q.verificar(b,s,plano,probe)
        self.assertTrue(qa["aprovado_tecnicamente"])
        self.assertGreaterEqual(len(qa["gestos"]),4)
        self.assertNotIn("30°",json.dumps(qa)) # QA não reescreve dados meteorológicos
        self.assertFalse(Q.verificar(b,s,plano,{"streams":[{"codec_type":"video"}]})["aprovado_tecnicamente"])

    def test_config_disable(self):
        from unittest.mock import patch
        with patch.dict("os.environ",{"PREVISAO_DIRECAO":"0"}):
            self.assertFalse(D.ativo())
        with patch.dict("os.environ",{"PREVISAO_DIRECAO":"1"}):
            self.assertTrue(D.ativo())


if __name__ == "__main__":
    unittest.main()
