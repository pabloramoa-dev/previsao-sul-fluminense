# -*- coding: utf-8 -*-
"""
teste_juarez.py — o Reel unico das 06h.

Cobre o que nao da pra ver sem renderizar: que o modo do dia sai do
`limiares.py` e nao de uma regra escrita a mao aqui; que os dois modos montam o
roteiro que devem montar; que a duracao estimada cai na faixa de 18-22s do
plano v3; que o CTA alterna por paridade em vez de sortear; e que a cena sabe
desenhar o painel de alerta que o modo alerta manda desenhar.

O que este teste NAO cobre, e nenhum teste cobre: o video. Enquadramento, cor,
lip sync e o desenho do Juarez so se conferem olhando o MP4 — rode o workflow
`juarez.yml` pelo botao "Run workflow" com o "publicar" DESMARCADO e baixe o
artifact. E por isso que o workflow imprime a duracao real medida no MP4: a
`estimar_segundos()` daqui e estimativa, e o numero real e que calibra ela.

Roda sem rede, sem manim e sem render.
"""
import ast
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))

import limiares as L
import gerar_juarez as J
import postar_reel as PR

falhas = []


def checar(nome, obtido, esperado):
    ok = obtido == esperado
    print(("  ok   " if ok else "  FALHA ") + nome + f"  ({obtido!r})")
    if not ok:
        falhas.append(f"{nome}: esperado {esperado!r}, veio {obtido!r}")


def entre(nome, valor, lo, hi):
    ok = lo <= valor <= hi
    print(("  ok   " if ok else "  FALHA ") + nome + f"  ({valor:.1f}s)")
    if not ok:
        falhas.append(f"{nome}: {valor:.1f}s fora de [{lo}, {hi}]")


def aborta(nome, fn):
    try:
        fn()
    except SystemExit as e:
        print(f"  ok   {nome}  ({str(e)[:56]}...)")
        return
    print(f"  FALHA {nome}  (nao abortou)")
    falhas.append(nome)


def c(nome, mn, mx, cond="sol", mm=0.0, rajada=None):
    d = {"nome": nome, "min": mn, "max": mx, "cond": cond, "chuva_mm": mm}
    if rajada is not None:
        d["rajada_kmh"] = rajada
    return d


def dia(cidades, umidade=60, data="2026-09-08"):
    return {"data": data, "cidades": cidades, "umidade_min": umidade,
            "destaque": cidades[0]["nome"]}


# As dez cidades do perfil, pra que o resumo_cinco tenha de onde escolher
def regiao(**mudancas):
    base = [c("Volta Redonda", 17, 27), c("Barra Mansa", 17, 28),
            c("Resende", 16, 26), c("Porto Real", 17, 27),
            c("Itatiaia", 15, 25), c("Quatis", 16, 27)]
    for nome, novo in mudancas.items():
        for i, x in enumerate(base):
            if x["nome"].replace(" ", "_").lower() == nome:
                base[i] = novo
    return base


COMUM = dia(regiao())

print("o modo NAO se decide aqui — sai do limiares.py:")
checar("dia comum e rotina", L.modo_do_dia(COMUM), "rotina")
b = J.montar_roteiro(COMUM)
checar("o roteiro concorda com o limiar", b[0]["dados"].get("modo"), "rotina")
checar("e nao abre com o cartaz de alerta", b[0]["tipo"], "gancho")

print("modo ROTINA — as cinco batidas, nesta ordem:")
checar("sequencia", [x["tipo"] for x in b],
       ["gancho", "nenhum", "resumo", "sem_chuva", "cta"])
checar("o resumo le TRES cidades, nao cinco",
       len(b[2]["dados"]["cidades"]), 3)
checar("a cidade da vez abre o resumo",
       b[2]["dados"]["cidades"][0]["nome"], "Volta Redonda")
entre("duracao estimada", J.estimar_segundos(b), J.DUR_MIN, J.DUR_MAX)

print("modo ALERTA — abre pelo cartaz, fecha com instrucao:")
ALERTA = dia(regiao(resende=c("Resende", 17, 24, "chuva", 27.0)), data="2026-09-09")
checar("o limiar diz alerta", L.modo_do_dia(ALERTA), "alerta")
ba = J.montar_roteiro(ALERTA)
checar("sequencia", [x["tipo"] for x in ba],
       ["alerta", "gancho", "resumo", "nenhum", "cta"])
checar("o cartaz traz o tipo certo", ba[0]["dados"]["titulo"], "ALERTA DE CHUVA")
checar("o detalhe traz o numero", ba[0]["dados"]["detalhe"], "chuva de 27mm")
checar("o numero grande na tela", ba[1]["dados"]["numero"], "27mm")
checar("a cidade do pico vai no subtitulo", ba[1]["dados"]["sub"], "RESENDE")
checar("a instrucao e a de chuva", ba[3]["fala"], J.INSTRUCAO["chuva"])
entre("duracao estimada", J.estimar_segundos(ba), J.DUR_MIN, J.DUR_MAX)

print("os cinco tipos de alerta produzem cartaz, numero e instrucao:")
CASOS = [
    ("chuva", dia(regiao(resende=c("Resende", 17, 24, "chuva", 27.0)))),
    ("rajada", dia(regiao(quatis=c("Quatis", 16, 27, rajada=63)))),
    ("calor", dia(regiao(resende=c("Resende", 22, 38)))),
    ("frio", dia(regiao(itatiaia=c("Itatiaia", 6, 18)))),
    ("umidade", dia(regiao(), umidade=17)),
]
for chave, d in CASOS:
    checar(f"{chave}: o limiares devolve a chave", L.alerta_do_dia(d)[0], chave)
    bb = J.montar_roteiro(d)
    checar(f"{chave}: cartaz", bb[0]["dados"]["titulo"], J.CARTAZ[chave])
    checar(f"{chave}: tem instrucao propria",
           bb[3]["fala"].startswith(J.INSTRUCAO[chave][:12].capitalize()[:8]), True)
    entre(f"{chave}: duracao", J.estimar_segundos(bb), J.DUR_MIN, J.DUR_MAX)

print("CTA alternado por PARIDADE, nao sorteado:")
# Sorteio nao serve: numa sequencia azarada de 14 dias um dos dois CTAs sairia
# tres vezes e o outro onze, e o experimento mediria um CTA so.
for d_mes, esperado in [("08", "TEU BAIRRO NA DM"), ("09", "SALVA PRA CONFERIR"),
                        ("10", "TEU BAIRRO NA DM"), ("21", "SALVA PRA CONFERIR")]:
    bb = J.montar_roteiro(dia(regiao(), data=f"2026-09-{d_mes}"))
    checar(f"dia {d_mes}", bb[-1]["dados"]["chamada"], esperado)
saidas = [J.montar_roteiro(dia(regiao(), data=f"2026-09-{n:02d}"))[-1]["dados"]["chamada"]
          for n in range(8, 22)]
checar("nos 14 dias do experimento, 7 de cada",
       sorted({x: saidas.count(x) for x in set(saidas)}.values()), [7, 7])

print("as travas do roteiro valem aqui tambem:")
# 12mm sem codigo de chuva: o gancho prometeria chuva que a batida final nega
neve = dia(regiao(resende=c("Resende", 16, 26, "nublado", 12.0)))
aborta("gancho incoerente aborta antes de renderizar",
       lambda: J.montar_roteiro(neve))

print("a legenda do Juarez existe e passa nas travas do postar_reel:")
checar("tem gancho proprio pros cinco tempos",
       sorted(PR.GANCHOS["juarez"]), ["chuva", "frio", "nublado", "sol", "tempestade"])
checar("nao repete nenhuma frase do velho",
       set(PR.GANCHOS["juarez"].values()) & set(PR.GANCHOS["ranzinza"].values()), set())
cap = PR.legenda(ALERTA, voz="juarez", quando="hoje")
PR.validar_legenda(cap)
PR.validar_coerencia(ALERTA, cap)
checar("a legenda do dia de chuva passa nas duas travas", True, True)
cap2 = PR.legenda(COMUM, voz="juarez", quando="hoje")
PR.validar_legenda(cap2)
PR.validar_coerencia(COMUM, cap2)
checar("a do dia comum tambem", True, True)

print("a cena sabe desenhar o que o roteiro manda:")
# piloto.py importa manim, que nao existe no runner dos testes: le pelo AST.
fonte = ast.parse(open(os.path.join(AQUI, "piloto.py"), encoding="utf-8").read())
texto = open(os.path.join(AQUI, "piloto.py"), encoding="utf-8").read()
tipos = {n.value for n in ast.walk(fonte)
         if isinstance(n, ast.Constant) and isinstance(n.value, str)}
for tipo in {b["tipo"] for b in J.montar_roteiro(COMUM)} | {b["tipo"] for b in ba}:
    if tipo == "nenhum":
        continue
    checar(f"o painel() conhece o tipo {tipo!r}", f'tipo == "{tipo}"' in texto, True)
checar("o piloto importa o juarez_lib", "import juarez_lib as J" in texto, True)
checar("e sabe que o Juarez e um personagem",
       'PERSONAGEM == "juarez"' in texto, True)
checar("'alerta' esta entre as constantes do piloto", "alerta" in tipos, True)

print("o juarez_lib traz o que a cena pede:")
jl = ast.parse(open(os.path.join(AQUI, "juarez_lib.py"), encoding="utf-8").read())
defs = {n.name for n in jl.body if isinstance(n, ast.FunctionDef)}
for nome in ("juarez", "estudio_juarez", "painel_alerta"):
    checar(f"{nome}() existe", nome in defs, True)
# a versao da skill carregava dois sys.path.insert absolutos que so existiam na
# maquina de desenvolvimento; procurar a STRING nao serve, porque o docstring
# conta essa historia de proposito — o que nao pode e sobrar codigo com ela
caminhos = [n.value for n in ast.walk(jl)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and n.value.startswith("/")]
checar("nenhum caminho absoluto no codigo", caminhos, [])

print("o CONTRATO da cena — o que quebraria so na hora de renderizar:")
# Um render custa ~10 minutos de runner. Um AttributeError no minuto 9 (um
# `v["chapeu"]` que o personagem nao devolve, um `J.painel_x` que nao existe)
# custa os 10 minutos inteiros e um dia sem post. Nada disso precisa de manim
# pra ser pego: e tudo nome, e nome se le no AST.


def definidos(arq):
    a = ast.parse(open(os.path.join(AQUI, arq), encoding="utf-8").read())
    nomes = {n.name for n in a.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    nomes |= {t.id for n in a.body if isinstance(n, ast.Assign)
              for t in n.targets if isinstance(t, ast.Name)}
    return nomes


def atributos_de(arq, modulo):
    """Tudo que `arq` le de `modulo.` (ex.: todo J.x dentro do piloto.py)."""
    a = ast.parse(open(os.path.join(AQUI, arq), encoding="utf-8").read())
    return {n.attr for n in ast.walk(a) if isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Name) and n.value.id == modulo}


def chaves_do_dict(arq, funcao):
    """As chaves do dict(...) que `funcao` devolve."""
    a = ast.parse(open(os.path.join(AQUI, arq), encoding="utf-8").read())
    for n in ast.walk(a):
        if isinstance(n, ast.FunctionDef) and n.name == funcao:
            for r in ast.walk(n):
                if (isinstance(r, ast.Return) and isinstance(r.value, ast.Call)
                        and getattr(r.value.func, "id", "") == "dict"):
                    return {k.arg for k in r.value.keywords}
    return set()


checar("o juarez_lib so pede do dvh_lib o que existe la",
       sorted(atributos_de("juarez_lib.py", "L") - definidos("dvh_lib.py")), [])
checar("o piloto so pede do juarez_lib o que existe la",
       sorted(atributos_de("piloto.py", "J") - definidos("juarez_lib.py")), [])
checar("e do previsao_lib idem",
       sorted(atributos_de("piloto.py", "P") - definidos("previsao_lib.py")), [])

# o dict do personagem: o piloto le v["grupo"], v["boca"] e v["bengala"] — este
# ultimo protegido por `if "bengala" not in v`, que e como o Juarez e a Dona
# Maria escapam da batida da bengala do velho
personagem = chaves_do_dict("juarez_lib.py", "juarez")
for chave in ("grupo", "boca"):
    checar(f"juarez() devolve {chave!r}", chave in personagem, True)
checar("e o piloto protege o que ele nao tem",
       'if "bengala" not in v' in open(os.path.join(AQUI, "piloto.py"),
                                       encoding="utf-8").read(), True)
checar("estudio_juarez() devolve o piso onde o personagem pisa",
       "piso_y" in chaves_do_dict("juarez_lib.py", "estudio_juarez"), True)

print("UM Reel por dia, e um so — o que o experimento mede:")
# A invariante mais importante deste arquivo, e a que nenhum outro teste pega.
# Nao usa PyYAML de proposito: o job dos testes roda sem `pip install` (fecha em
# menos de 30s por causa disso), entao a leitura e por texto mesmo. Basta: um
# cron comentado tem "#" antes do traco, e e exatamente essa a diferenca que
# importa aqui.
WF = os.path.join(os.path.dirname(AQUI), ".github", "workflows")


def crons_ativos(arquivo):
    linhas = open(os.path.join(WF, arquivo), encoding="utf-8").read().splitlines()
    return [l.strip() for l in linhas
            if l.strip().startswith("- cron:")]


# NO MAXIMO um, e nao exatamente um: entre a mesclagem e a aprovacao do
# primeiro MP4 o cron do juarez.yml fica comentado de proposito, pra que o
# merge nao publique um video que ninguem viu. Zero cron e seguro HOJE e
# desastroso no dia 08 — o lembrete pra descomentar esta no topo do juarez.yml,
# que e onde quem for religar vai olhar.
checar("o juarez.yml tem no maximo um cron",
       len(crons_ativos("juarez.yml")) <= 1, True)
checar("e o ranzinza.yml nenhum", crons_ativos("ranzinza.yml"), [])
checar("o monitor de alertas tambem segue desligado",
       crons_ativos("monitor_alertas.yml"), [])
# quem publica Reel no perfil do experimento
publicam_reel = sorted(f for f in os.listdir(WF)
                       if f.endswith(".yml")
                       and "postar_reel.py" in open(os.path.join(WF, f),
                                                    encoding="utf-8").read()
                       and crons_ativos(f))
# ou so o juarez, ou nenhum (cron comentado no periodo de conferencia do MP4).
# O que NAO pode, em hipotese nenhuma, e outro workflow publicar Reel agendado.
checar("nenhum outro workflow publica Reel por agendamento",
       publicam_reel in ([], ["juarez.yml"]), True)

print()
if falhas:
    print("FALHOU:")
    for f in falhas:
        print("  -", f)
    raise SystemExit(1)
print("todos os testes passaram")
