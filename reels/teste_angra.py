# -*- coding: utf-8 -*-
"""Travas do rodízio especial de Angra dos Reis (sem rede e sem render)."""
import datetime

from coletar_tempo import (ANGRA_DOS_REIS, CIDADES, DIAS_ANGRA,
                          cidades_para_publicacao, resumo_cinco)

assert len(CIDADES) == 10
assert ANGRA_DOS_REIS[0] not in {nome for nome, _, _ in CIDADES}
assert DIAS_ANGRA == {4, 6}

# Quatro semanas: Angra apenas às sextas e domingos, independentemente do giro.
inicio = datetime.date(2026, 11, 2)  # segunda-feira
for delta in range(28):
    data = inicio + datetime.timedelta(days=delta)
    dia_angra = data.weekday() in DIAS_ANGRA
    for desloca in (0, 5):  # Reel da manhã e compatibilidade com rodízio da tarde
        selecionadas = cidades_para_publicacao(data=data, desloca=desloca)
        nomes = [cidade[0] for cidade in selecionadas]
        assert len(nomes) == (11 if dia_angra else 10), (data, nomes)
        assert len(set(nomes)) == len(nomes), (data, nomes)
        assert (ANGRA_DOS_REIS[0] in nomes) == dia_angra, (data, nomes)
        if dia_angra:
            assert nomes[0] == ANGRA_DOS_REIS[0], (data, nomes)
        else:
            assert nomes[0] != ANGRA_DOS_REIS[0], (data, nomes)

        # Os quadros, roteiros e legendas compartilham esta seleção de 5 cidades.
        dados = [{"nome": nome, "min": 20, "max": 29}
                 for nome, _lat, _lon in selecionadas]
        resumo = resumo_cinco(dados)
        assert len(resumo) == 5
        assert len({c["nome"] for c in resumo}) == 5
        assert (ANGRA_DOS_REIS[0] in {c["nome"] for c in resumo}) == dia_angra
        if dia_angra:
            assert resumo[0]["nome"] == ANGRA_DOS_REIS[0]

# O modo sem rodízio também respeita o calendário editorial.
assert cidades_para_publicacao(data=datetime.date(2026, 11, 6),
                              sem_rodizio=True)[0] == ANGRA_DOS_REIS
assert cidades_para_publicacao(data=datetime.date(2026, 11, 7),
                              sem_rodizio=True)[0] == CIDADES[0]

# Duas chamadas iguais devem produzir o mesmo boletim.
data = datetime.date(2026, 11, 8)
assert cidades_para_publicacao(data=data) == cidades_para_publicacao(data=data)
print("Angra: sextas e domingos garantidos; dez cidades mantidas; cinco no resumo.")
