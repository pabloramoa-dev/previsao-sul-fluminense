#!/usr/bin/env python3
"""Testes dos limiares e da cascata de manchete (seções 3 e 5 do plano v3).

Rode com `python teste_limiares.py` a partir da raiz do repo. Não faz rede.
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import limiares as L


def c(nome, mn, mx, mm=0.0, rajada=None, cond="sol"):
    return {"nome": nome, "min": mn, "max": mx, "cond": cond,
            "chuva_mm": mm, "rajada_kmh": rajada}


def dia(cidades, umidade=55, **extra):
    d = {"data": "2026-09-10", "cidades": cidades, "umidade_min": umidade}
    d.update(extra)
    return d


falhas = []


def checar(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok    " if ok else "  FALHA ") + f"{nome}  ({obtido!r})")
    if not ok:
        falhas.append(f"{nome}: esperava {esperado!r}, veio {obtido!r}")


# ------------------------------------------------------------------ rotina
print("dias que NÃO podem virar alerta:")
comum = dia([c("Volta Redonda", 16, 27), c("Resende", 15, 26)])
checar("dia comum", L.modo_do_dia(comum), "rotina")
checar("chuva de 19mm fica um passo abaixo do limiar",
       L.modo_do_dia(dia([c("Volta Redonda", 18, 24, mm=19.9)])), "rotina")
checar("rajada de 49 km/h fica abaixo",
       L.modo_do_dia(dia([c("Volta Redonda", 18, 24, rajada=49)])), "rotina")
checar("36 graus ainda é rotina",
       L.modo_do_dia(dia([c("Resende", 20, 36)])), "rotina")
checar("9 graus ainda é rotina",
       L.modo_do_dia(dia([c("Itatiaia", 9, 20)])), "rotina")
checar("21% de umidade ainda é rotina",
       L.modo_do_dia(dia([c("Resende", 18, 30)], umidade=21)), "rotina")

# ------------------------------------------------------------------ alerta
print("dias que TÊM que virar alerta:")
checar("20mm exatos", L.modo_do_dia(dia([c("Volta Redonda", 18, 24, mm=20.0)])),
       "alerta")
checar("rajada de 50 km/h",
       L.modo_do_dia(dia([c("Volta Redonda", 18, 24, rajada=50)])), "alerta")
checar("37 graus", L.modo_do_dia(dia([c("Resende", 22, 37)])), "alerta")
checar("8 graus", L.modo_do_dia(dia([c("Itatiaia", 8, 19)])), "alerta")
checar("20% de umidade",
       L.modo_do_dia(dia([c("Resende", 18, 30)], umidade=20)), "alerta")

print("o alerta é REGIONAL — basta uma cidade cruzar:")
checar("temporal só em Resende",
       L.modo_do_dia(dia([c("Quatis", 16, 27), c("Resende", 17, 25, mm=31.0)])),
       "alerta")

print("rajada vinda do campo antigo do dia (dia.json sem rajada por cidade):")
checar("rajada_max do dia",
       L.modo_do_dia(dia([c("Volta Redonda", 18, 24)], rajada_max=62)), "alerta")

# --------------------------------------------------------------- manchete
print("cascata da manchete (seção 5), de cima para baixo:")
checar("alerta vence tudo",
       L.manchete(dia([c("Volta Redonda", 8, 24, mm=25.0)]))[0],
       "ALERTA — CHUVA DE 25MM")
checar("chuva de 1,0mm",
       L.manchete(dia([c("Volta Redonda", 18, 24, mm=1.0)]))[0], "HOJE CHOVE")
checar("chuva de 0,9mm não é chuva",
       L.manchete(dia([c("Volta Redonda", 18, 24, mm=0.9)]))[0], "HOJE NÃO CHOVE")
checar("calor de 33",
       L.manchete(dia([c("Resende", 20, 33)]))[0], "HOJE FAZ 33°")
checar("frio de 14",
       L.manchete(dia([c("Itatiaia", 14, 25)]))[0], "HOJE ESFRIA")
checar("ar seco de 30%",
       L.manchete(dia([c("Resende", 18, 30)], umidade=30))[0], "AR SECO HOJE")
checar("nada de especial",
       L.manchete(comum)[0], "HOJE NÃO CHOVE")

print("a manchete de calor vence a de frio quando as duas valem:")
checar("máxima 34 e mínima 13 -> calor",
       L.manchete(dia([c("Resende", 13, 34)]))[0], "HOJE FAZ 34°")

print("o modo devolvido acompanha a manchete:")
checar("modo do alerta", L.manchete(dia([c("X", 8, 24, mm=25.0)]))[1], "alerta")
checar("modo da rotina", L.manchete(comum)[1], "rotina")


# ------------------------------------------------------------------ trava
def barra(d, texto):
    try:
        L.conferir_manchete(d, texto)
        return False
    except SystemExit:
        return True


print("a trava de coerência:")
checar("CHOVE com 0mm é barrado", barra(comum, "HOJE CHOVE"), True)
checar("NÃO CHOVE com 0mm passa", barra(comum, "HOJE NÃO CHOVE"), False)
checar("CHOVE com 4mm passa",
       barra(dia([c("VR", 18, 24, mm=4.0)]), "HOJE CHOVE"), False)
checar("NÃO CHOVE com 25mm é barrado",
       barra(dia([c("VR", 18, 24, mm=25.0)]), "HOJE NÃO CHOVE"), True)
checar("ALERTA sem limiar cruzado é barrado",
       barra(comum, "ALERTA — CHUVA DE 25MM"), True)
checar("ALERTA com limiar cruzado passa",
       barra(dia([c("VR", 18, 24, mm=25.0)]), "ALERTA — CHUVA DE 25MM"), False)

print("dia vazio não explode:")
checar("sem cidades", L.modo_do_dia({}), "rotina")

print()
if falhas:
    sys.exit(f"{len(falhas)} falha(s):\n  " + "\n  ".join(falhas))
print("todos os testes passaram")
