#!/usr/bin/env python3
"""
gerar_tarde.py — o Reel do meio-dia com a DONA MARIA.

Contraponto do Ranzinza: ele reclama de manhã, ela resolve à tarde. Ela cita
ele de propósito — quem viu um vídeo quer ver o outro, e isso é a mecânica de
retenção mais barata do projeto todo.

Quatro blocos, todos vindos da MESMA chamada ao Open-Meteo que o vídeo da
manhã já faz (menos o "neste dia", que usa o endpoint de arquivo):
    1. índice de varal  — dá pra estender roupa hoje? nota de 0 a 10
    2. sensação térmica — por que o termômetro "mente"
    3. índice UV        — protetor solar
    4. neste dia        — o recorde histórico da data

Uso:
    python gerar_tarde.py --dados dia.json --saida TARDE.mp4
    python gerar_tarde.py --demo
"""
import argparse, json, os, random, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from gerar_dia import produzir, num_extenso, LIMIAR_CHUVA_MM, cenario_do_dia
from historico import carregar as carregar_historico, recorde_do_dia


# =====================================================================
#  ÍNDICE DE VARAL — o carro-chefe dela
# =====================================================================
def indice_varal(umidade, chuva_mm, vento_kmh, sol_h, tmax, chuva_hora=None):
    """Nota de 0 a 10 para estender roupa. Devolve (nota, frase).

    Não existe índice oficial disso — é composição própria dos quatro fatores
    que realmente secam roupa. Os pesos vêm do senso comum de quem estende:
    umidade alta é o maior inimigo, vento seca quase tanto quanto sol, e chuva
    anula tudo.

    `chuva_hora` = primeira hora da TARDE com chuva prevista (ou None). É o caso
    mais traiçoeiro do dia: manhã seca e boa, chuva chegando às 15h. O índice
    sozinho diria "pode estender" e a roupa tomaria chuva — então a hora da
    virada limita a nota a 6 e vira aviso explícito, que é onde ela é útil.
    """
    if chuva_hora is None:
        # mesmos limiares do Ranzinza (LIMIAR_CHUVA_MM, em gerar_dia.py)
        if chuva_mm >= 5 * LIMIAR_CHUVA_MM:
            return 0, "Hoje não. Vai chover de verdade."
        if chuva_mm >= LIMIAR_CHUVA_MM:
            return 2, "Eu não arriscaria. Pinga alguma coisa."

    n_umid = max(0.0, min(1.0, (85 - umidade) / 50))   # 35% ótimo, 85% péssimo
    n_vento = max(0.0, min(1.0, vento_kmh / 20))       # até ~20 km/h ajuda muito
    n_sol = max(0.0, min(1.0, sol_h / 8))
    n_temp = max(0.0, min(1.0, (tmax - 14) / 16))
    nota = int(round(10 * (0.35 * n_umid + 0.25 * n_vento
                           + 0.28 * n_sol + 0.12 * n_temp)))

    if chuva_hora is not None:
        nota = min(nota, 6)
        return nota, f"Dá pra estender, mas recolhe até as {chuva_hora} horas."

    if nota >= 9:
        return nota, "Dia perfeito de varal. Estende tudo."
    if nota >= 7:
        return nota, "Pode estender à vontade."
    if nota >= 5:
        return nota, "Estende, mas recolhe antes do fim da tarde."
    if nota >= 3:
        return nota, "Só peça leve. Toalha não seca."
    return nota, "Deixa pra amanhã, meu bem."


UV_AVISO = [
    (2, "tranquilo"), (5, "passa protetor"), (7, "protetor e chapéu"),
    (10, "evite o sol do meio-dia"), (99, "sol forte demais, fique na sombra"),
]


def aviso_uv(uv):
    for lim, txt in UV_AVISO:
        if uv <= lim:
            return txt
    return "sol forte"


# =====================================================================
#  FALAS — voz dela: acolhedora, prática, e sempre alfinetando o velho
# =====================================================================
ABERTURAS = [
    "Boa tarde, meus queridos.",
    "Oi, gente. Já almoçaram?",
    "Boa tarde. Senta aqui que eu já te conto.",
    "Cheguei. Trouxe as informações que importam.",
]

CITA_VELHO = [
    "O velho já reclamou do tempo hoje cedo. Mas ele exagera.",
    "Não liga pro que aquele ranzinza falou de manhã.",
    "Ele reclamou. Ele sempre reclama. Vamos ao que interessa.",
    "De manhã teve resmungo. Agora tem solução.",
]

FECHOS_CHUVA = [
    "Recolhe a roupa e não esquece o guarda-chuva.",
    "Guarda-chuva na bolsa, meus queridos. Confia em mim.",
    "Fecha a janela antes de sair. Até amanhã.",
]

# Mesmo CTA, outra voz: ela pede com jeito, ele pede contrariado.
CTA = [
    "E segue a gente, viu? Assim você não perde nenhum.",
    "Aperta o seguir, meu bem. É rapidinho.",
    "Segue o perfil pra não esquecer da roupa amanhã.",
    "Se ainda não segue, segue agora. Eu agradeço.",
]

FECHOS = [
    "É isso, meus queridos. Amanhã eu volto.",
    "Qualquer coisa, me chama nos comentários.",
    "Cuidem-se. E bebam água.",
    "Até amanhã, viu? Um beijo.",
]


def montar_roteiro(d):
    """`d` = dia.json enriquecido (umidade, vento, sol, uv, sensação, histórico)."""
    rnd = random.Random(int(d["data"].replace("-", "")))
    cid = d["cidades"][0]
    batidas = []

    def add(fala, legenda=None, tipo="nenhum", **dd):
        f = fala[0].upper() + fala[1:] if fala else fala
        batidas.append({"fala": f, "legenda": legenda if legenda is not None else f,
                        "tipo": tipo, "dados": dd})

    # --- 1. GANCHO: a nota do varal, que é o que ela tem de mais útil ---
    chuva_hora = d.get("chuva_hora")     # 1ª hora da tarde com chuva prevista
    # Coerência com o Ranzinza: chuva_hora marca garoa a partir de 0,2 mm/h. Se
    # o dia inteiro não junta LIMIAR_CHUVA_MM, ele nega chuva às 6h e ela não
    # pode mandar recolher o varal às 11h20 do mesmo dia.
    if (cid.get("chuva_mm", 0) or 0) < LIMIAR_CHUVA_MM:
        chuva_hora = None
    nota, frase = indice_varal(d["umidade_min"], cid.get("chuva_mm", 0),
                               d.get("vento_kmh", 12), d.get("sol_h", 7),
                               cid["max"], chuva_hora)
    add(f"Varal hoje: nota {num_extenso(nota)}.", f"{nota}/10",
        tipo="varal", nota=nota)

    add(rnd.choice(ABERTURAS))
    add(rnd.choice(CITA_VELHO))
    add(frase, frase, tipo="varal", nota=nota)

    # --- aviso de recolher: entra logo depois do varal, com hora e urgência ---
    if chuva_hora is not None:
        add(f"Chuva chegando por volta das {num_extenso(chuva_hora)} horas. "
            f"Tira a roupa do varal, viu?",
            f"Tire a roupa até as {chuva_hora}h",
            tipo="recolher", hora=chuva_hora)
        add("Não adianta correr depois, que aí já molhou tudo.",
            "Depois já molhou.")

    # --- 2. sensação térmica ---
    real, sente = cid["max"], d.get("sensacao_max", cid["max"])
    if abs(real - sente) >= 2:
        add(f"O termômetro marca {num_extenso(real)} graus, mas o corpo sente "
            f"{num_extenso(sente)}.",
            f"Termômetro {real}°, você sente {sente}°.",
            tipo="sensacao", real=real, sente=sente)

    # --- 3. UV ---
    uv = d.get("uv_max")
    if uv:
        add(f"O sol hoje está índice {num_extenso(round(uv))}. {aviso_uv(uv).capitalize()}.",
            f"UV {round(uv)} — {aviso_uv(uv)}",
            tipo="uv", uv=round(uv), aviso=aviso_uv(uv))

    # --- 4. neste dia ---
    h = d.get("historico")
    if h:
        add(f"E olha só: neste dia, em {h['ano']}, aqui fez {num_extenso(h['valor_num'])} graus.",
            f"{h['valor']} em {h['ano']}",
            tipo="neste_dia", valor=h["valor"], ano=h["ano"])

    chovendo = (chuva_hora is not None
                or (cid.get("chuva_mm", 0) or 0) >= LIMIAR_CHUVA_MM)
    add(rnd.choice(FECHOS_CHUVA if chovendo else FECHOS), tipo="fecho")
    add(rnd.choice(CTA), tipo="cta", chamada="TOCA NO SEGUIR")
    return batidas, nota


DEMO = {
    "data": "2026-07-29",
    "cidades": [{"nome": "Volta Redonda", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0}],
    "umidade_min": 34, "vento_kmh": 14, "sol_h": 9,
    "sensacao_max": 30, "uv_max": 8,
    "historico": {"ano": 1994, "valor": "2°", "valor_num": 2},
}


DEMO_CHUVA = {
    "data": "2026-11-12",
    "cidades": [{"nome": "Volta Redonda", "min": 19, "max": 28, "cond": "chuva",
                 "chuva_mm": 12.0}],
    "umidade_min": 72, "vento_kmh": 9, "sol_h": 3,
    "sensacao_max": 31, "uv_max": 6, "chuva_hora": 15,
    "historico": {"ano": 2008, "valor": "38°", "valor_num": 38},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados")
    ap.add_argument("--saida", default="TARDE.mp4")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--demo-chuva", action="store_true",
                    help="cenário de chuva à tarde, pro aviso de recolher a roupa")
    ap.add_argument("--quality", default="m")
    a = ap.parse_args()

    if getattr(a, "demo_chuva", False):
        d = DEMO_CHUVA
    elif a.demo or not a.dados:
        d = DEMO
    else:
        d = json.load(open(a.dados))
    # "neste dia": vem da tabela local (construída 1x por historico.py).
    # Se o arquivo não existir, a batida simplesmente não entra — o vídeo sai
    # igual, um pouco mais curto.
    if "historico" not in d:
        tab = carregar_historico()
        cid0 = d["cidades"][0]
        rec = recorde_do_dia(tab, d["data"], cid0.get("min"), cid0.get("max"))
        if rec:
            d["historico"] = rec
            print(f"   [histórico ] recorde de {rec['lado']}: {rec['valor']} em {rec['ano']}")

    batidas, nota = montar_roteiro(d)
    for b in batidas:
        print(f"   [{b['tipo']:10s}] {b['fala']}")

    # o balanço das roupas no varal espelha a nota: dia bom = vento e movimento
    vento_visual = 0.4 + 1.2 * (nota / 10)

    produzir(batidas, a.saida,
             cenario=cenario_do_dia(d["cidades"][0]),
             personagem="maria", cenario_tipo="quintal",
             quality=a.quality, voz="pf_dora", pitch=0.94,
             extra={"data": d["data"], "vento_visual": round(vento_visual, 2)})




if __name__ == "__main__":
    main()
