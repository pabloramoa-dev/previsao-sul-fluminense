# -*- coding: utf-8 -*-
"""recomendar_roupa.py - Linha "Hoje pede: ..." para os Reels e para a DM."""


def recomendar_roupa(tmin: float, tmax: float, prob_chuva: float,
                     rajada_kmh: float = 0) -> str:
    pecas = []
    if tmin <= 13:
        pecas.append("casaco de frio")
    elif tmin <= 17:
        pecas.append("moletom ou blusa leve")
    else:
        pecas.append("roupa leve")
    if prob_chuva >= 60:
        pecas.append("guarda-chuva")
    if tmax >= 30:
        pecas.append("garrafa d'água")
    if rajada_kmh >= 45:
        pecas.append("capa de chuva, porque guarda-chuva vira do avesso")
    return "👕 Hoje pede: " + " + ".join(pecas) + "."
