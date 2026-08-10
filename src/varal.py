# -*- coding: utf-8 -*-
"""
varal.py -- Alerta condicional de varal (Fase 6, item 6.5).

O indice de varal SAI do formato fixo do carrossel da manha (ver indices.py:
a chamada a indice_lavar_roupa deve ser removida de resumo_indices).

Aqui ele vira um ALERTA CONDICIONAL, inserido APENAS no slot da NOITE e
somente quando a chance de chuva entre 18h e 06h for maior que 70%.
"""

from __future__ import annotations

from typing import Any, Optional

LIMIAR = 70.0  # % de chance de chuva 18h-06h para disparar o alerta


def alerta_varal(cidades_noite: list[dict[str, Any]]) -> Optional[str]:
    """Retorna o texto do alerta de varal, ou None se nao deve inserir.

    cidades_noite: dicts com 'nome' e 'prob_chuva_noite' (chance 18h-06h).
    Regra: so insere se a maior chance na regiao for > 70%.
    """
    if not cidades_noite:
        return None

    pior = max(cidades_noite, key=lambda c: c.get("prob_chuva_noite", 0))
    prob = float(pior.get("prob_chuva_noite", 0) or 0)
    if prob <= LIMIAR:
        return None

    cidade = pior.get("nome", "na regiao")
    return (f"Chuva a noite em {cidade} ({prob:.0f}%) -- "
            "recolhe a roupa do varal antes das 21h.")


def _sanity() -> None:
    assert alerta_varal([{"nome": "Volta Redonda", "prob_chuva_noite": 84}]) is not None
    assert alerta_varal([{"nome": "Resende", "prob_chuva_noite": 40}]) is None
    assert alerta_varal([]) is None


_sanity()
