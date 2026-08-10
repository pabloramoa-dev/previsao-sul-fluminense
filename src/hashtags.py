# -*- coding: utf-8 -*-
"""
hashtags.py -- Rotacao real de hashtags (Fase 6, item 6.7).

- 5 conjuntos fixos. Cada conjunto = 3 cidade + 3 tema + 2 regiao + 1-2 contexto.
- Manha e noite NUNCA usam o mesmo conjunto no mesmo dia.
- A escolha do conjunto varia por dia (ordinal da data) e por slot.
"""

from __future__ import annotations

import datetime as _dt

CONJUNTOS = [
    ["#voltaredonda", "#barramansa", "#resende",
     "#previsaodotempo", "#climatempo", "#tempoagora",
     "#sulfluminense", "#interiordorj"],
    ["#portoreal", "#angradosreis", "#barradopirai",
     "#meteorologia", "#chuva", "#calor",
     "#regiaodovale", "#riodejaneiro"],
    ["#voltaredonda", "#resende", "#pirai",
     "#previsao", "#temperatura", "#frio",
     "#sulfluminense", "#valedoparaiba"],
    ["#barramansa", "#portoreal", "#angradosreis",
     "#climarj", "#previsaodotempo", "#sol",
     "#interiordorj", "#regiaodovale"],
    ["#resende", "#voltaredonda", "#barradopirai",
     "#tempoagora", "#meteorologia", "#chuvahoje",
     "#valedoparaiba", "#riodejaneiro"],
]

CONTEXTO = {
    "chuva": ["#chuvahoje", "#guardachuva"],
    "calor": ["#calorao", "#verao"],
    "frio": ["#friozinho", "#casaco"],
    "sol": ["#diadesol", "#ceuazul"],
    "nublado": ["#temponublado", "#ceufechado"],
}


def _ordinal(data=None):
    return (data or _dt.date.today()).toordinal()


def escolher_conjunto(slot: str, condicao: str = "nublado", data=None) -> str:
    """Retorna a string de hashtags para o slot, garantindo que manha e
    noite do mesmo dia nunca coincidam de conjunto.
    """
    if slot not in ("manha", "noite"):
        raise ValueError("slot deve ser 'manha' ou 'noite'")

    o = _ordinal(data)
    idx_manha = o % len(CONJUNTOS)
    idx_noite = (o + 2) % len(CONJUNTOS)
    if idx_noite == idx_manha:
        idx_noite = (idx_noite + 1) % len(CONJUNTOS)

    idx = idx_manha if slot == "manha" else idx_noite
    tags = list(CONJUNTOS[idx])
    tags += CONTEXTO.get(condicao, [])
    return " ".join(tags)


def _sanity() -> None:
    for c in CONJUNTOS:
        assert len(c) == 8, "cada conjunto base deve ter 8 tags (3+3+2)"
    hoje = _dt.date(2026, 8, 9)
    assert (escolher_conjunto("manha", data=hoje)
            != escolher_conjunto("noite", data=hoje)), "manha == noite no mesmo dia"


_sanity()
