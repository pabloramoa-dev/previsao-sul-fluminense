from __future__ import annotations

import os
from pathlib import Path

from gerar_dia import produzir
from gerar_juarez import FILTRO_BIRA, GAP_ENTRE_BATIDAS, SPEED_BIRA

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "promo_crossover_out"
OUT.mkdir(parents=True, exist_ok=True)


def batida(fala: str):
    return [{"fala": fala, "legenda": fala, "tipo": "nenhum", "dados": {}}]


def kokoro():
    for k in ("PREVISAO_TTS", "PREVISAO_EDGE_VOICE", "PREVISAO_EDGE_RATE", "PREVISAO_EDGE_PITCH", "PREVISAO_EDGE_VOLUME"):
        os.environ.pop(k, None)


def edge_juarez():
    os.environ["PREVISAO_TTS"] = "edge"
    os.environ["PREVISAO_EDGE_VOICE"] = "pt-BR-AntonioNeural"
    os.environ["PREVISAO_EDGE_RATE"] = "+10%"
    os.environ["PREVISAO_EDGE_PITCH"] = "+6Hz"
    os.environ["PREVISAO_EDGE_VOLUME"] = "+6%"


kokoro()
produzir(
    batida("Eu sou o Ranzinza. Até previsão do tempo vira conteúdo com personalidade."),
    str(OUT / "ranzinza.mp4"), cenario="sol", personagem="ranzinza",
    cenario_tipo="varanda", quality="m", voz="pm_alex", pitch=0.88,
    extra={"data": "2026-10-06", "destaque": "SUL FLUMINENSE", "destaque_rotulo": "AO VIVO"},
)

kokoro()
produzir(
    batida("E eu sou Dona Maria. Eu conto o amanhã do meu jeito, como conversa de vizinha."),
    str(OUT / "dona-maria.mp4"), cenario="entardecer", personagem="maria",
    cenario_tipo="quintal", quality="m", voz="pf_dora", pitch=0.94,
    extra={"data": "2026-10-06", "vento_visual": 0.7},
)

edge_juarez()
produzir(
    batida("Juarez Plantão! Informação rápida, visual e direto ao ponto."),
    str(OUT / "juarez.mp4"), cenario="sol", personagem="juarez",
    cenario_tipo="estudio", quality="m", voz="pm_alex", speed=SPEED_BIRA,
    gap=GAP_ENTRE_BATIDAS, filtro=FILTRO_BIRA,
    extra={"data": "2026-10-06", "hora": "06:00", "modo": "rotina"},
)

print("PROMO_CROSSOVER_OK")
