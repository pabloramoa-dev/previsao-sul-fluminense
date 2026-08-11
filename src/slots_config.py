# -*- coding: utf-8 -*-
"""
slots_config.py -- Roteamento de formato por slot (Fase 6, item 6.4).

Desativa os carrosseis de FEED nos slots diarios:
- MANHA (06h13): NAO publica carrossel no feed; vira STORY apenas.
- NOITE (18h00): NAO publica carrossel; e substituido pelo REEL noturno,
  que e o POST PRINCIPAL do slot (nao vira story).

Este modulo centraliza a decisao para que main.py apenas consulte
formato_do_slot(slot) e chame o publicador correto. Assim a mudanca fica
explicita e reversivel (basta editar o mapa abaixo).

Integracao esperada em main.py:
    from . import slots_config
    fmt = slots_config.formato_do_slot("manha")   # -> "story"
    fmt = slots_config.formato_do_slot("noite")    # -> "reel"
    # rodar_manha: gerar story e publicar_story(...) -- sem carrossel de feed
    # rodar_noite: gerar/publicar o REEL como post principal -- sem carrossel
"""

from __future__ import annotations

# Formato principal publicado em cada slot diario.
FORMATO_POR_SLOT = {
    "manha": "story",   # 06h13: apenas story, sem carrossel de feed
    "noite": "reel",    # 18h00: reel noturno como post principal
}

# Slots que NAO devem mais gerar carrossel de feed.
CARROSSEL_FEED_DESATIVADO = {"manha", "noite"}


def formato_do_slot(slot: str) -> str:
    if slot not in FORMATO_POR_SLOT:
        raise ValueError(f"slot desconhecido: {slot}")
    return FORMATO_POR_SLOT[slot]


def deve_gerar_carrossel_feed(slot: str) -> bool:
    return slot not in CARROSSEL_FEED_DESATIVADO


def _sanity() -> None:
    assert formato_do_slot("manha") == "story"
    assert formato_do_slot("noite") == "reel"
    assert not deve_gerar_carrossel_feed("manha")
    assert not deve_gerar_carrossel_feed("noite")


_sanity()
