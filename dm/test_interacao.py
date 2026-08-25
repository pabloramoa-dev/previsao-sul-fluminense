# -*- coding: utf-8 -*-
import os
import unittest

os.environ.pop("DATABASE_URL", None)

from interacao import comando, relato
from dm_bairro import resolver
import radar


class InteracaoTest(unittest.TestCase):
    def test_comando(self):
        self.assertEqual(comando("RADAR Resende"), ("radar", "resende"))

    def test_relato_bairro(self):
        situacao, cidade, rotulo, condicao = relato("Retiro chuva")
        self.assertEqual((situacao, cidade, condicao), ("cidade", "Volta Redonda", "chuva"))
        self.assertIn("Retiro", rotulo)

    def test_relato_com_cidade(self):
        situacao, cidade, _, condicao = relato("sol no Centro de Resende")
        self.assertEqual((situacao, cidade, condicao), ("cidade", "Resende", "sol"))

    def test_bairro_novo_com_cidade(self):
        situacao, cidade, rotulo = resolver("Parque Mambucaba, Angra dos Reis")
        self.assertEqual((situacao, cidade), ("cidade", "Angra dos Reis"))
        self.assertIn("Parque Mambucaba", rotulo)

    def test_localidade_livre_com_cidade(self):
        situacao, cidade, rotulo = resolver("Minha Localidade, Paraty")
        self.assertEqual((situacao, cidade), ("cidade", "Paraty"))
        self.assertEqual(rotulo, "Minha Localidade (Paraty)")

    def test_deduplicacao(self):
        self.assertTrue(radar.registrar("mid-teste", "u1", "Resende", "Centro", "sol"))
        self.assertFalse(radar.registrar("mid-teste", "u1", "Resende", "Centro", "sol"))


if __name__ == "__main__":
    unittest.main()
