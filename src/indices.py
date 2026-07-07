# -*- coding: utf-8 -*-
"""
indices.py - Indices praticos do dia, calculados a partir dos dados
brutos do Open-Meteo. Alimentam o slide "resumo util" do carrossel das 06h.

Cada funcao retorna (bool_ou_nivel, texto_com_emoji).
"""

from __future__ import annotations

from typing import Any


def indice_casaco(tmax: float) -> tuple[bool, str]:
    """Dia de casaco se a maxima for baixa."""
    if tmax < 18:
        return True, "Dia de casaco pesado"
    if tmax < 22:
        return True, "Leve um casaco leve"
    return False, "Dispensa casaco"


def indice_guarda_chuva(prob_chuva: float) -> tuple[bool, str]:
    if prob_chuva >= 60:
        return True, f"Leve guarda-chuva (chuva {prob_chuva:.0f}%)"
    if prob_chuva >= 30:
        return True, f"Talvez chova ({prob_chuva:.0f}%)"
    return False, "Sem previsao de chuva"


def indice_protetor_solar(uv_max: float) -> tuple[bool, str]:
    if uv_max >= 11:
        return True, "UV EXTREMO - protetor e sombra!"
    if uv_max >= 8:
        return True, f"UV muito alto ({uv_max:.0f}) - use protetor"
    if uv_max >= 6:
        return True, f"UV alto ({uv_max:.0f})"
    return False, f"UV moderado/baixo ({uv_max:.0f})"


def indice_lavar_roupa(prob_chuva: float, umidade: float) -> tuple[bool, str]:
    """Bom pra lavar roupa: sem chuva e umidade nao muito alta."""
    if prob_chuva < 30 and umidade < 70:
        return True, "Bom dia pra lavar e secar roupa"
    if prob_chuva < 30:
        return True, "Da pra lavar, mas seca devagar (umidade alta)"
    return False, "Nao e um bom dia pra estender roupa"


def indice_qualidade_ar(aqi: int) -> tuple[str, str]:
    """Classificacao pelo AQI europeu do Open-Meteo."""
    if aqi <= 20:
        return "boa", "Qualidade do ar: boa"
    if aqi <= 40:
        return "razoavel", "Qualidade do ar: razoavel"
    if aqi <= 60:
        return "moderada", "Qualidade do ar: moderada"
    if aqi <= 80:
        return "ruim", "Qualidade do ar: ruim"
    if aqi <= 100:
        return "muito_ruim", "Qualidade do ar: muito ruim"
    return "pessima", "Qualidade do ar: pessima - evite esforco ao ar livre"


def resumo_indices(resumo_regional: dict[str, Any], umidade_media: float,
                   aqi_regional: int) -> list[dict[str, Any]]:
    """
    Monta a lista de indices para o slide 'resumo util'.
    resumo_regional vem de clima.resumo_regional().
    """
    itens = []

    ativo, txt = indice_casaco(resumo_regional["tmax"])
    itens.append({"emoji": "\U0001F9E5", "texto": txt, "ativo": ativo})

    ativo, txt = indice_guarda_chuva(resumo_regional["prob_chuva"])
    itens.append({"emoji": "\u2602\uFE0F", "texto": txt, "ativo": ativo})

    ativo, txt = indice_protetor_solar(resumo_regional["uv_max"])
    itens.append({"emoji": "\U0001F9F4", "texto": txt, "ativo": ativo})

    ativo, txt = indice_lavar_roupa(resumo_regional["prob_chuva"], umidade_media)
    itens.append({"emoji": "\U0001F455", "texto": txt, "ativo": ativo})

    _, txt = indice_qualidade_ar(aqi_regional)
    itens.append({"emoji": "\U0001F62E\u200D\U0001F4A8", "texto": txt, "ativo": True})

    return itens


if __name__ == "__main__":
    exemplo = {"tmax": 19, "prob_chuva": 70, "uv_max": 9}
    for item in resumo_indices(exemplo, umidade_media=80, aqi_regional=35):
        print(item["emoji"], item["texto"], "->", item["ativo"])
