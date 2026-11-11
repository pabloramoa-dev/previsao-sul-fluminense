"""Testes sem rede para o rodizio editorial de bairros."""
import ast
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "estudio"))
from bairros_foco import BAIRROS_EM_FOCO, bairro_do_dia


def literal_do_arquivo(caminho, nome):
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(
            isinstance(alvo, ast.Name) and alvo.id == nome for alvo in no.targets
        ):
            return ast.literal_eval(no.value)
    raise AssertionError(f"{nome} nao encontrado em {caminho}")


class RodizioBairros(unittest.TestCase):
    def test_todos_os_bairros_pertencem_ao_cadastro(self):
        bruto = literal_do_arquivo(ROOT / "dm/dm_bairro.py", "BAIRROS")
        for cidade, nomes in BAIRROS_EM_FOCO.items():
            self.assertIn(cidade, bruto)
            validos = bruto[cidade].split("|")
            self.assertTrue(nomes)
            self.assertEqual(len(nomes), len(set(nomes)))
            for bairro in nomes:
                self.assertIn(bairro, validos, f"{cidade}: {bairro}")

    def test_todas_as_cidades_do_boletim_estao_cobertas(self):
        nomes = literal_do_arquivo(ROOT / "reels/coletar_tempo.py", "CIDADES")
        angra = literal_do_arquivo(ROOT / "reels/coletar_tempo.py", "ANGRA_DOS_REIS")
        esperado = {x[0] for x in nomes} | {angra[0]}
        self.assertEqual(set(BAIRROS_EM_FOCO), esperado)

    def test_gira_de_dia_para_dia_e_separa_turnos(self):
        dia = date(2026, 11, 11)
        seguinte = date(2026, 11, 12)
        for cidade, bairros in BAIRROS_EM_FOCO.items():
            b1 = bairro_do_dia(cidade, dia, "bira")
            b2 = bairro_do_dia(cidade, dia, "bia")
            self.assertIn(b1, bairros)
            self.assertEqual(b1, bairro_do_dia(cidade, dia, "bira"))
            if len(bairros) > 1:
                self.assertNotEqual(b1, b2)
                self.assertNotEqual(b1, bairro_do_dia(cidade, seguinte, "bira"))
            else:
                self.assertEqual(b1, b2)


if __name__ == "__main__":
    unittest.main()
