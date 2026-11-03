import unittest
from piloto import DEMO, FPS, H, SEGUNDOS, W, compor, normalizar, paginas

class PilotoOpuscarTest(unittest.TestCase):
    def test_dez_cidades_em_duas_paginas(self):
        cidades = normalizar(DEMO)
        self.assertEqual(len(cidades), 10)
        self.assertEqual([len(x) for x in paginas(cidades)], [5, 5])

    def test_numeros_incoerentes_sao_recusados(self):
        for alteracao in ({"min": 45, "max": 21}, {"chuva_mm": -1},
                          {"min": float("nan")}):
            with self.subTest(alteracao=alteracao):
                payload = {"cidades": [{**DEMO["cidades"][0], **alteracao}]}
                with self.assertRaises(ValueError):
                    normalizar(payload)

    def test_zero_de_chuva_nao_quebra_grafico(self):
        dados = {"cidades": [{**c, "chuva_mm": 0} for c in DEMO["cidades"]]}
        frame = compor(4.0, normalizar(dados), "dados")
        self.assertEqual(frame.size, (W, H))

    def test_vinte_cidades_sem_omissao(self):
        base = normalizar(DEMO)
        muitas = base + [dict(c, nome=c["nome"]+" II") for c in base]
        self.assertEqual(len(paginas(muitas)), 4)
        self.assertEqual(len(paginas(muitas)[-1]), 5)
        self.assertEqual(compor(11.5, muitas, "noticiario").size, (W, H))

    def test_estilos_e_tempos(self):
        self.assertEqual(FPS*SEGUNDOS, 210)
        for estilo in ("noticiario", "dados"):
            for momento in (0, 1.4, 6.9, 12.5, 13.9):
                with self.subTest(estilo=estilo, t=momento):
                    frame = compor(momento, normalizar(DEMO), estilo)
                    self.assertEqual(frame.size, (540, 960))
                    self.assertEqual(frame.mode, "RGB")

if __name__ == "__main__":
    unittest.main()
