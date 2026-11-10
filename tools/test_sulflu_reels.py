"""Testes rápidos sem rede nem vídeo para mudanças de retenção SulFlu."""
import json
import tempfile
import unittest
from pathlib import Path
from metricas_organicas import atualizar
from finalizar_reel_sulflu import CAIXA, LARGURA, ALTURA

class SulFluTeste(unittest.TestCase):
    def test_area_segura(self):
        x,y,w,h = CAIXA
        self.assertGreaterEqual(x,60)
        self.assertGreaterEqual(y,250)
        self.assertLessEqual(x+w,LARGURA-60)
        self.assertLessEqual(y+h,1550)
    def test_desconto_nao_altera_bruto(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            met=p/"metricas.json"
            registro=p/"registro.json"
            met.write_text(json.dumps({"measurements":[
                {"media_id":"123","metrics":{"comments":1,"reach":42}},
                {"media_id":"456","metrics":{"comments":0}},
                {"media_id":"789","metrics":{"reach":12}}
            ]}), encoding="utf-8")
            registro.write_text(json.dumps([{"media_id":"123","formato":"amanha_sulflu_20_25","gancho":"Amanhã"}]))
            self.assertEqual(atualizar(met,registro),3)
            itens=json.loads(met.read_text())["measurements"]
            self.assertEqual(itens[0]["metrics"]["comments"],1)
            self.assertEqual(itens[0]["metrics"]["comments_organic_estimate"],0)
            self.assertEqual(itens[1]["metrics"]["comments_organic_estimate"],0)
            self.assertNotIn("comments_organic_estimate",itens[2]["metrics"])
            self.assertEqual(itens[0]["editorial"]["gancho"],"Amanhã")

if __name__ == "__main__":
    unittest.main()
