#!/usr/bin/env python3
"""Testes da coerência entre a legenda e o dado de chuva.

Rode com `python teste_coerencia_legenda.py` (não precisa de pytest, não faz
rede). O caso 1 é a reprodução exata dos posts de 07/08 e 12/08 de 2026: código
WMO "chuva" com 0,2 mm acumulados, que produzia um post prometendo chuva no
gancho e negando chuva seis linhas abaixo.
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import postar_reel as P


def cidade(nome, mn, mx, cond, mm):
    return {"nome": nome, "min": mn, "max": mx, "cond": cond, "chuva_mm": mm}


GAROA = {                       # o caso do bug: WMO diz chuva, acumulado não
    "data": "2026-08-07", "umidade_min": 55, "destaque": "Volta Redonda",
    "cidades": [cidade("Volta Redonda", 16, 27, "chuva", 0.2),
                cidade("Barra Mansa", 16, 28, "chuva", 0.1),
                cidade("Resende", 15, 26, "nublado", 0.0)],
}

CHUVA = {                       # dia de chuva de verdade
    "data": "2026-08-20", "umidade_min": 80, "destaque": "Volta Redonda",
    "cidades": [cidade("Volta Redonda", 18, 24, "chuva", 12.0),
                cidade("Barra Mansa", 18, 25, "chuva", 9.0),
                cidade("Resende", 17, 23, "chuva", 7.0)],
}

SOL = {
    "data": "2026-08-25", "umidade_min": 45, "destaque": "Resende",
    "cidades": [cidade("Resende", 14, 30, "sol", 0.0),
                cidade("Volta Redonda", 15, 31, "sol", 0.0)],
}

falhas = []


def checar(nome, condicao):
    print(("  ok   " if condicao else "  FALHA ") + nome)
    if not condicao:
        falhas.append(nome)


def aborta(dia, cap):
    try:
        P.validar_coerencia(dia, cap)
        return False
    except SystemExit:
        return True


print("garoa de 0,2mm (o bug de 07/08 e 12/08):")
cap = P.legenda(GAROA, voz="ranzinza", quando="hoje")
gancho = cap.splitlines()[0]
checar("o gancho não promete chuva", "chover" not in gancho.casefold())
checar("o gancho é o de nublado", gancho == P.GANCHOS["ranzinza"]["nublado"])
checar("a linha do acumulado continua negando chuva", "Chuva: nenhuma." in cap)
checar("nenhum emoji de chuva nas cidades", "🌧️" not in cap)
checar("a legenda passa na trava", not aborta(GAROA, cap))

print("chuva de verdade (12mm):")
cap = P.legenda(CHUVA, voz="ranzinza", quando="hoje")
checar("o gancho promete chuva", "chover" in cap.splitlines()[0].casefold())
checar("a legenda traz o pico", "12.0mm" in cap or "12mm" in cap)
checar("a legenda passa na trava", not aborta(CHUVA, cap))

print("dia de sol:")
cap = P.legenda(SOL, voz="ranzinza", quando="hoje")
checar("a legenda passa na trava", not aborta(SOL, cap))

print("a trava barra as duas divergências:")
checar("gancho promete chuva sem dado",
       aborta(GAROA, "Vai chover. Depois não venham dizer que eu não avisei.\n\n☔ Chuva: nenhuma."))
checar("legenda nega chuva com dado de chuva",
       aborta(CHUVA, "Frio de doer o osso. Casaco, e não é sugestão.\n\n☔ Chuva: nenhuma."))

print("Reel sem dia.json (Mito ou Verdade) não é barrado:")
checar("dia vazio passa", not aborta({}, "Mito ou Verdade: chuva de manga existe?"))

print()
if falhas:
    sys.exit(f"{len(falhas)} falha(s): " + "; ".join(falhas))
print("todos os testes passaram")
