# -*- coding: utf-8 -*-
"""
teste_roteiro.py — as travas do lado do VÍDEO.

O `teste_limiares.py` prova que os números do `limiares.py` estão certos e o
`teste_coerencia_legenda.py` prova que a LEGENDA não contradiz o dado. Faltava
o terceiro lado: que o ROTEIRO do Reel leia esses mesmos números e pare quando
o gancho promete o que o dado não sustenta.

Também é aqui que fica a trava contra a regressão que motivou tudo isto: o
`LIMIAR_CHUVA_MM` já esteve escrito em quatro arquivos com quatro cópias do
mesmo 1.0. Os testes de identidade abaixo falham no minuto em que alguém
reescrever o número em vez de importá-lo.

Roda sem rede, sem manim e sem render.
"""
import os
import sys
import ast

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))

import limiares as L
import gerar_dia as G
import gerar_tarde as T
import postar_reel as PR

falhas = []


def checar(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA ") + nome + f"  ({obtido!r})")
    if not ok:
        falhas.append(f"{nome}: esperado {esperado!r}, veio {obtido!r}")


def aborta(nome, fn):
    """A função TEM que levantar SystemExit."""
    try:
        fn()
    except SystemExit as e:
        print(f"  ok   {nome}  ({str(e)[:64]}...)")
        return
    print(f"  FALHA {nome}  (não abortou)")
    falhas.append(nome)


def c(nome, mn, mx, cond="sol", mm=0.0, rajada=None):
    d = {"nome": nome, "min": mn, "max": mx, "cond": cond, "chuva_mm": mm}
    if rajada is not None:
        d["rajada_kmh"] = rajada
    return d


def dia(cidades, umidade=60, data="2026-09-04"):
    return {"data": data, "cidades": cidades, "umidade_min": umidade,
            "uv_max": 7, "sensacao_max": 29, "vento_kmh": 20, "sol_h": 8.0}


COMUM = dia([c("Volta Redonda", 18, 27), c("Resende", 17, 26),
             c("Barra Mansa", 18, 28)])

print("os limiares são um OBJETO só, não quatro cópias do mesmo número:")
checar("gerar_dia lê o LIMIAR_CHUVA_MM da raiz",
       G.LIMIAR_CHUVA_MM is L.LIMIAR_CHUVA_MM, True)
checar("gerar_tarde lê o mesmo", T.LIMIAR_CHUVA_MM is L.LIMIAR_CHUVA_MM, True)
checar("postar_reel lê o mesmo", PR.LIMIAR_CHUVA_MM is L.LIMIAR_CHUVA_MM, True)
checar("chove_de_verdade é a mesma função nos três",
       G.chove_de_verdade is L.chove_de_verdade
       and T.chove_de_verdade is L.chove_de_verdade
       and PR.chove_de_verdade is L.chove_de_verdade, True)
print("os quatro números do gancho também:")
for nome in ("GANCHO_FRIO_C", "GANCHO_CALOR_C", "GANCHO_CHUVA_MM",
             "GANCHO_SECO_PCT"):
    checar(f"{nome} vem do limiares.py nos dois roteiros",
           getattr(G, nome) is getattr(L, nome)
           and getattr(T, nome) is getattr(L, nome), True)

print("o gancho escolhe o mesmo número nos dois vídeos, nos QUATRO limiares:")
# Tabela em vez de quatro pares escritos à mão de propósito: foi exatamente
# aqui que a unificação escorregou primeiro. O `GANCHO_SECO_PCT` acabou
# aplicado no `o_que_separar()` do gerar_tarde — outra função, que por acaso
# usava o mesmo 30 pra decidir se manda encher a garrafa — enquanto o
# escolher_gancho() dela ficou com o literal. Os dois vídeos passaram a usar
# réguas diferentes pro ar seco e nada quebrou: os testes de identidade das
# constantes seguiam verdes, porque a constante ESTAVA importada, só que no
# lugar errado. Só um teste de COMPORTAMENTO nos dois lados pega isso.
neutra = c("Volta Redonda", 18, 27)
CASOS = [
    ("frio", 60, [c("Itatiaia", 11, 20), neutra], [c("Itatiaia", 12, 20), neutra]),
    ("calor", 60, [c("Resende", 20, 32), neutra], [c("Resende", 20, 31), neutra]),
    ("chuva", 60, [c("Resende", 18, 26, "chuva", 10.0)],
                  [c("Resende", 18, 26, "chuva", 9.9)]),
    ("seco", None, [neutra], [neutra]),
]
rnd = __import__("random").Random(1)
for cor, _u, dentro, fora in CASOS:
    u_dentro, u_fora = (30, 31) if cor == "seco" else (60, 60)
    checar(f"{cor}: manhã dispara", G.escolher_gancho(dentro, u_dentro, rnd)[3], cor)
    checar(f"{cor}: tarde dispara", T.escolher_gancho(dentro, u_dentro)[3], cor)
    checar(f"{cor}: manhã não dispara um passo abaixo",
           G.escolher_gancho(fora, u_fora, rnd)[3], "normal")
    checar(f"{cor}: tarde não dispara um passo abaixo",
           T.escolher_gancho(fora, u_fora)[3], "normal")

print("dia comum: o roteiro sai exatamente como saía antes:")
b = G.montar_roteiro(COMUM)
checar("mesma sequência de batidas (manhã)", [x["tipo"] for x in b],
       ["gancho", "nenhum", "nenhum", "resumo", "sem_chuva", "fecho", "cta"])
checar("gancho em modo rotina", b[0]["dados"]["modo"], "rotina")
checar("cor do gancho intacta", b[0]["dados"]["cor"], "normal")
bt = T.montar_roteiro(COMUM)
checar("mesma sequência de batidas (tarde)", [x["tipo"] for x in bt],
       ["gancho", "nenhum", "nenhum", "resumo", "preparar", "sensacao", "uv",
        "fecho", "cta"])
checar("gancho da tarde em modo rotina", bt[0]["dados"]["modo"], "rotina")

print("dia de alerta: pinta o gancho e NÃO acrescenta batida nenhuma:")
alerta = dia([c("Volta Redonda", 18, 27, "chuva", 25.0), c("Resende", 17, 26),
              c("Barra Mansa", 18, 28)])
ba = G.montar_roteiro(alerta)
checar("modo do gancho", ba[0]["dados"]["modo"], "alerta")
checar("cor do gancho", ba[0]["dados"]["cor"], "alerta")
checar("manchete gravada no roteiro", ba[0]["dados"]["manchete"],
       "ALERTA — CHUVA DE 25MM")
checar("nenhuma batida a mais que o dia comum", len(ba), len(b))
bat = T.montar_roteiro(alerta)
checar("a tarde também pinta o gancho", bat[0]["dados"]["cor"], "alerta")
checar("a tarde não carrega manchete com 'HOJE'",
       "manchete" in bat[0]["dados"], False)

print("alerta por RAJADA, o dado que faltava (nenhuma cidade com chuva):")
vento = dia([c("Volta Redonda", 18, 27, rajada=63), c("Resende", 17, 26)])
checar("modo do gancho", G.montar_roteiro(vento)[0]["dados"]["modo"], "alerta")

print("a trava nova: gancho que promete chuva sem código de chuva:")
# 12 mm de acumulado num dia cujo código WMO não é de chuva (céu encoberto,
# 2/3/45/48 — ou neve, 71-77). `chove_de_verdade()` diz NÃO, mas o gancho é a
# única batida que decide por acumulado PURO (>= GANCHO_CHUVA_MM) sem olhar o
# código: ele abriria o Reel com "Vem chuva, doze milímetros" e cinco batidas
# depois a batida SEM_CHUVA diria "Chuva nenhuma". A contradição de 07/08 e
# 12/08 outra vez, agora dentro do MP4, onde a trava da legenda não alcança.
neve = dia([c("Resende", 16, 26, "nublado", 12.0), c("Volta Redonda", 17, 27)])
checar("chove_de_verdade nega", any(L.chove_de_verdade(x)
                                    for x in neve["cidades"]), False)
checar("o gancho promete chuva mesmo assim",
       G.escolher_gancho(neve["cidades"], 60,
                         __import__("random").Random(1))[3], "chuva")
aborta("montar_roteiro da manhã aborta", lambda: G.montar_roteiro(neve))
aborta("montar_roteiro da tarde aborta", lambda: T.montar_roteiro(neve))
aborta("conferir_gancho isolado aborta",
       lambda: L.conferir_gancho(neve["cidades"], "chuva"))
checar("com chuva de verdade não aborta",
       L.conferir_gancho([c("Volta Redonda", 18, 24, "chuva", 12.0)],
                         "chuva"), None)
checar("gancho de frio não é conferido contra chuva",
       L.conferir_gancho(neve["cidades"], "frio"), None)

print("o painel sabe pintar o modo alerta:")
# piloto.py importa manim, que não existe no runner dos testes — então o dict
# é lido do FONTE. O que se quer provar é que a cor "alerta" que o roteiro
# manda tem entrada lá: sem ela o dia de alerta sairia amarelo, calado.
fonte = ast.parse(open(os.path.join(AQUI, "piloto.py"),
                       encoding="utf-8").read())
cores = []
for no in ast.walk(fonte):
    if (isinstance(no, ast.Assign) and no.targets
            and getattr(no.targets[0], "id", None) == "CORES_GANCHO"):
        cores = [k.value for k in no.value.keys]
checar("CORES_GANCHO tem 'alerta'", "alerta" in cores, True)
checar("e não perdeu as outras",
       sorted(cores), ["alerta", "calor", "chuva", "frio", "normal", "seco"])

print()
if falhas:
    print("FALHOU:")
    for f in falhas:
        print("  -", f)
    raise SystemExit(1)
print("todos os testes passaram")
