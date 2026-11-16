"""Teste sem rede do rodízio de cidade e dos encerramentos regionais."""
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reels"))
sys.path.insert(0, str(ROOT / "estudio"))
from coletar_tempo import CIDADES, MAIORES
from regional import escolher_destaque, preparar_boletim


def fixture():
    return [{"nome": nome, "max": 28 + (i % 3), "min": 19,
             "chuva_mm": 0, "rajada_kmh": 20} for i, (nome, _, _) in enumerate(CIDADES)]


class RodizioRegional(unittest.TestCase):
    def test_dez_municipios_em_dez_dias_por_turno(self):
        inicio = date(2026, 11, 16)
        vistos_bira, vistos_bia = set(), set()
        for i in range(10):
            dia = inicio + timedelta(days=i)
            manha = escolher_destaque(fixture(), dia, "bira")
            tarde = escolher_destaque(fixture(), dia, "bia")
            self.assertEqual(len(manha), 5)
            self.assertEqual(len({c["nome"] for c in manha}), 5)
            self.assertEqual(len(tarde), 5)
            self.assertNotEqual(manha[0]["nome"], tarde[0]["nome"])
            vistos_bira.add(manha[0]["nome"])
            vistos_bia.add(tarde[0]["nome"])
            self.assertGreaterEqual(len({c["nome"] for c in manha} & set(MAIORES)), 4)
        self.assertEqual(vistos_bira, {x[0] for x in CIDADES})
        self.assertEqual(vistos_bia, vistos_bira)

    def test_roteiro_e_legenda_usam_cidade_selecionada(self):
        dados = {"data": "2026-11-16", "cidades": fixture()}
        with tempfile.TemporaryDirectory() as tmp:
            with patch("regional.datetime") as tempo:
                tempo.now.return_value.date.return_value = date(2026, 11, 16)
                _, cidades, batidas = preparar_boletim(dados, "bira", tmp)
            meta = json.loads((Path(tmp) / "REEL.metadata.json").read_text())
            legenda = (Path(tmp) / "LEGENDA.txt").read_text()
            self.assertIn(cidades[0]["nome"], batidas[0]["fala"])
            self.assertEqual(meta["cidade_destaque"], cidades[0]["nome"])
            self.assertIn(cidades[0]["nome"], legenda.splitlines()[0])
            self.assertEqual(meta["cta"], batidas[-1]["fala"])
            self.assertEqual(len([b for b in batidas if b["tipo"] == "cta"]), 1)


if __name__ == "__main__":
    unittest.main()
