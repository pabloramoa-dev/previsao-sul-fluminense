# -*- coding: utf-8 -*-
"""
astronomia.py -- Fase da lua para os carrosseis do @previsaosulfluminense.
Usa a biblioteca astral (Apache-2.0, gratuita, sem API/chave), ja que o
Open-Meteo NAO fornece fase da lua. Nascer/por do sol continuam vindo do
Open-Meteo; aqui tratamos apenas a Lua.
"""

import math
from datetime import date
from astral import moon

# Fatia o ciclo lunar (0-28) em 8 fases nomeadas em portugues + emoji.
_FASES = [
    (0.0, 1.75, "Lua nova", "🌑"),
    (1.75, 5.25, "Lua crescente", "🌒"),
    (5.25, 8.75, "Quarto crescente", "🌓"),
    (8.75, 12.25, "Crescente gibosa", "🌔"),
    (12.25, 15.75, "Lua cheia", "🌕"),
    (15.75, 19.25, "Minguante gibosa", "🌖"),
    (19.25, 22.75, "Quarto minguante", "🌗"),
    (22.75, 26.25, "Lua minguante", "🌘"),
    (26.25, 28.0, "Lua nova", "🌑"),
]


def fase_da_lua(dia: date | None = None) -> dict:
    """Retorna a fase da lua para a data informada (padrao: hoje)."""
    if dia is None:
        dia = date.today()

    valor = moon.phase(dia)  # 0 a ~27.99

    nome, emoji = "Lua nova", "🌑"
    for inicio, fim, n, e in _FASES:
        if inicio <= valor < fim:
            nome, emoji = n, e
            break

    return {
        "nome": nome,
        "emoji": emoji,
        "texto": f"{nome} {emoji}",
        "valor": round(valor, 1),
    }


def iluminacao_aproximada(dia: date | None = None) -> int:
    """Percentual aproximado do disco iluminado (0 = nova, 100 = cheia)."""
    if dia is None:
        dia = date.today()

    valor = moon.phase(dia)  # 0..~28
    angulo = (valor / 28.0) * 360.0
    fracao = (1 - math.cos(math.radians(angulo))) / 2
    return round(fracao * 100)


if __name__ == "__main__":
    f = fase_da_lua()
    print(f["texto"], f'({iluminacao_aproximada()}% iluminada)')
# -*- coding: utf-8 -*-
"""
astronomia.py -- Fase da lua para os carrosseis do @previsaosulfluminense.
Usa a biblioteca astral (Apache-2.0, gratuita, sem API/chave), ja que o
Open-Meteo NAO fornece fase da lua. Nascer/por do sol continuam vindo do
Open-Meteo; aqui tratamos apenas a Lua.
"""

import math
from datetime import date
from astral import moon

# Fatia o ciclo lunar (0-28) em 8 fases nomeadas em portugues + emoji.
_FASES = [
    (0.0, 1.75, "Lua nova", "U0001F311"),
    (1.75, 5.25, "Lua crescente", "U0001F312"),
    (5.25, 8.75, "Quarto crescente", "U0001F313"),
    (8.75, 12.25, "Crescente gibosa", "U0001F314"),
    (12.25, 15.75, "Lua cheia", "U0001F315"),
    (15.75, 19.25, "Minguante gibosa", "U0001F316"),
    (19.25, 22.75, "Quarto minguante", "U0001F317"),
    (22.75, 26.25, "Lua minguante", "U0001F318"),
    (26.25, 28.0, "Lua nova", "U0001F311"),
]


def fase_da_lua(dia: date | None = None) -> dict:
    """Retorna a fase da lua para a data informada (padrao: hoje)."""
    if dia is None:
        dia = date.today()

    valor = moon.phase(dia)  # 0 a ~27.99

    nome, emoji = "Lua nova", "U0001F311"
    for inicio, fim, n, e in _FASES:
        if inicio <= valor < fim:
            nome, emoji = n, e
            break

    return {
        "nome": nome,
        "emoji": emoji,
        "texto": f"{nome} {emoji}",
        "valor": round(valor, 1),
    }


def iluminacao_aproximada(dia: date | None = None) -> int:
    """Percentual aproximado do disco iluminado (0 = nova, 100 = cheia)."""
    if dia is None:
        dia = date.today()

    valor = moon.phase(dia)  # 0..~28
    angulo = (valor / 28.0) * 360.0
    fracao = (1 - math.cos(math.radians(angulo))) / 2
    return round(fracao * 100)


if __name__ == "__main__":
    f = fase_da_lua()
    print(f["texto"], f'({iluminacao_aproximada()}% iluminada)')
