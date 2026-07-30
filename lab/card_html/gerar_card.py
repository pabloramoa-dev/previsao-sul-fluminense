# -*- coding: utf-8 -*-
"""
gerar_card.py - PROTOTIPO de card de previsao em HTML/CSS renderizado pelo Chromium.

Isolado de proposito: nao e importado por src/, nao publica nada em rede social
e nao roda em nenhum workflow agendado. Serve para comparar o resultado visual
com os cards atuais (feitos com Pillow) antes de decidir trocar o pipeline.

Fluxo: le dados reais de src/clima.py -> preenche template.html -> Playwright
tira um screenshot 1080x1350 -> salva em lab/card_html/saida/.

Uso:
    python lab/card_html/gerar_card.py
    python lab/card_html/gerar_card.py --cidade Resende
    python lab/card_html/gerar_card.py --todas
    python lab/card_html/gerar_card.py --so-html
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src import clima  # noqa: E402

AQUI = Path(__file__).parent
TEMPLATE = AQUI / "template.html"
SAIDA = AQUI / "saida"

LARGURA, ALTURA = 1080, 1350
PERFIL = "@previsaosulfluminense"

# Area do grafico dentro do SVG do template (viewBox 880x170)
GRAF_L, GRAF_A = 880, 240
GRAF_PAD_X, GRAF_TOPO, GRAF_BASE = 16, 38, 38

PERIODOS = (
    ("Madrugada", 0, 6),
    ("Manha", 6, 12),
    ("Tarde", 12, 18),
    ("Noite", 18, 24),
)

# weathercode -> (rotulo, icone, cor_topo, cor_base, destaque)
CONDICOES = {
    0: ("Ceu limpo", "sol", "#0b5cb5", "#5fb4ff", "#ffd60a"),
    1: ("Sol com poucas nuvens", "sol", "#0b5cb5", "#5fb4ff", "#ffd60a"),
    2: ("Sol entre nuvens", "sol_nuvem", "#17568f", "#7db0d8", "#ffd60a"),
    3: ("Ceu nublado", "nuvem", "#2c5673", "#93b4c9", "#eaf6ff"),
    45: ("Neblina", "neblina", "#3b5a6d", "#9db8c6", "#eaf6ff"),
    48: ("Neblina com geada", "neblina", "#3b5a6d", "#9db8c6", "#eaf6ff"),
    51: ("Garoa fraca", "garoa", "#164a72", "#4d89b2", "#8be9ff"),
    53: ("Garoa", "garoa", "#164a72", "#4d89b2", "#8be9ff"),
    55: ("Garoa forte", "garoa", "#164a72", "#4d89b2", "#8be9ff"),
    61: ("Chuva fraca", "chuva", "#123f63", "#3f7ba6", "#7fdcff"),
    63: ("Chuva", "chuva", "#123f63", "#3f7ba6", "#7fdcff"),
    65: ("Chuva forte", "chuva_forte", "#0e3452", "#356a91", "#7fdcff"),
    80: ("Pancadas isoladas", "chuva", "#123f63", "#3f7ba6", "#7fdcff"),
    81: ("Pancadas de chuva", "chuva", "#123f63", "#3f7ba6", "#7fdcff"),
    82: ("Pancadas fortes", "chuva_forte", "#0e3452", "#356a91", "#7fdcff"),
    95: ("Tempestade", "tempestade", "#241a45", "#5a3f8c", "#ffd166"),
    96: ("Tempestade com granizo", "tempestade", "#241a45", "#5a3f8c", "#ffd166"),
    99: ("Tempestade com granizo", "tempestade", "#241a45", "#5a3f8c", "#ffd166"),
}
PADRAO = ("Tempo variavel", "nuvem", "#17568f", "#7db0d8", "#ffd60a")


def _svg(corpo: str) -> str:
    return (
        '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="4"'
        ' stroke-linecap="round" stroke-linejoin="round">' + corpo + "</svg>"
    )


_NUVEM_BAIXA = '<path d="M18 46h26a11 11 0 0 0 0-22 15 15 0 0 0-28-2 10 10 0 0 0 2 24z"/>'
_NUVEM_ALTA = '<path d="M18 38h26a11 11 0 0 0 0-22 15 15 0 0 0-28-2 10 10 0 0 0 2 24z"/>'

ICONES = {
    "sol": _svg(
        '<circle cx="32" cy="32" r="12"/>'
        '<path d="M32 6v7M32 51v7M6 32h7M51 32h7M14 14l5 5M45 45l5 5M50 14l-5 5M19 45l-5 5"/>'
    ),
    "sol_nuvem": _svg(
        '<circle cx="21" cy="19" r="8"/>'
        '<path d="M21 5v4M7 19h4M11 9l3 3M31 9l-3 3"/>'
        '<path d="M24 50h22a10 10 0 0 0 0-20 13 13 0 0 0-24-2 9 9 0 0 0 2 22z"/>'
    ),
    "nuvem": _svg(_NUVEM_BAIXA),
    "neblina": _svg(_NUVEM_ALTA + '<path d="M14 48h22M42 48h8M20 56h24"/>'),
    "garoa": _svg(_NUVEM_ALTA + '<path d="M24 46v5M34 46v6M44 46v4"/>'),
    "chuva": _svg(_NUVEM_ALTA + '<path d="M23 45l-3 10M33 45l-3 10M43 45l-3 10"/>'),
    "chuva_forte": _svg(
        _NUVEM_ALTA + '<path d="M19 44l-4 12M29 44l-4 12M39 44l-4 12M49 44l-4 12"/>'
    ),
    "tempestade": _svg(
        _NUVEM_ALTA
        + '<path d="M34 42l-9 12h8l-3 9 12-14h-8z" fill="currentColor" stroke="none"/>'
    ),
    "gota": _svg('<path d="M32 8s14 16 14 26a14 14 0 0 1-28 0C18 24 32 8 32 8z"/>'),
    "proveta": _svg('<path d="M20 8h24M25 8v34a7 7 0 0 0 14 0V8"/><path d="M25 32h14"/>'),
    "vento": _svg(
        '<path d="M6 22h30a7 7 0 1 0-7-7"/><path d="M6 34h38a7 7 0 1 1-7 7"/><path d="M6 46h20"/>'
    ),
    "umidade": _svg(
        '<path d="M32 8s14 16 14 26a14 14 0 0 1-28 0C18 24 32 8 32 8z"/>'
        '<path d="M26 36a6 6 0 0 0 6 6"/>'
    ),
}


def _condicao(codigo: int):
    return CONDICOES.get(int(codigo), PADRAO)


def _slug(nome: str) -> str:
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return base.strip().lower().replace(" ", "_")


def _indices_de_hoje(horas: list) -> list:
    """A API devolve 2 dias; aqui ficam so as 24 posicoes do primeiro dia."""
    if not horas:
        return []
    dia = str(horas[0])[:10]
    return [i for i, h in enumerate(horas) if str(h)[:10] == dia]


def _serie(horarias: dict, chave: str, indices: list) -> list:
    bruta = horarias.get(chave, []) or []
    return [
        float(bruta[i])
        for i in indices
        if i < len(bruta) and bruta[i] is not None
    ]


def _curva(temps: list):
    """Devolve (pontos, area, marcas, faixa) prontos para o SVG do template."""
    if len(temps) < 2:
        return "", "", "", ""
    tmin, tmax = min(temps), max(temps)
    span = max(tmax - tmin, 1.0)
    n = len(temps)
    util_l = GRAF_L - 2 * GRAF_PAD_X
    util_a = GRAF_A - GRAF_TOPO - GRAF_BASE
    pontos = []
    for i, t in enumerate(temps):
        x = GRAF_PAD_X + util_l * i / (n - 1)
        y = GRAF_TOPO + util_a * (1 - (t - tmin) / span)
        pontos.append((x, y))

    linha = " ".join(f"{x:.1f},{y:.1f}" for x, y in pontos)
    area = (
        f"M {pontos[0][0]:.1f},{GRAF_A} "
        + " ".join(f"L {x:.1f},{y:.1f}" for x, y in pontos)
        + f" L {pontos[-1][0]:.1f},{GRAF_A} Z"
    )

    def marca(i: int, acima: bool):
        x, y = pontos[i]
        # se o rotulo cairia fora da area do grafico, joga ele para cima
        if not acima and y + 30 > GRAF_A - 34:
            acima = True
        dy = -18 if acima else 30
        anc, tx = "middle", x
        if x < 50:
            anc, tx = "start", x - 8
        elif x > GRAF_L - 50:
            anc, tx = "end", x + 8
        desenho = (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#ffffff"/>'
            f'<text x="{tx:.1f}" y="{y + dy:.1f}" text-anchor="{anc}" fill="#ffffff"'
            f' font-size="23" font-weight="700">{temps[i]:.0f}&#176;</text>'
        )
        return desenho, x, y + dy

    svg_max, x_max, y_max = marca(temps.index(tmax), True)
    svg_min, x_min, y_min = marca(temps.index(tmin), False)
    marcas = svg_max + svg_min
    ocupados = ((x_max, y_max), (x_min, y_min))
    for hora in (0, 6, 12, 18, n - 1):
        if not 0 <= hora < n:
            continue
        x = pontos[hora][0]
        # pula a marcacao de hora quando ela colide com o rotulo de max/min
        if any(abs(x - ox) < 50 and oy > GRAF_A - 70 for ox, oy in ocupados):
            continue
        marcas += (
            f'<text x="{x:.1f}" y="{GRAF_A - 4}" text-anchor="middle" fill="#ffffff"'
            f' fill-opacity=".6" font-size="17" font-weight="500">{hora:02d}h</text>'
        )
    faixa = f"{tmin:.0f}&#176; a {tmax:.0f}&#176; ao longo do dia"
    return linha, area, marcas, faixa


def _barras(probs: list) -> str:
    partes = []
    for nome, ini, fim in PERIODOS:
        trecho = probs[ini:fim]
        pct = round(sum(trecho) / len(trecho)) if trecho else 0
        partes.append(
            '<div class="barra">'
            f'<div class="nome">{nome}</div>'
            f'<div class="trilha"><div class="preenche" style="width:{pct}%"></div></div>'
            f'<div class="pct">{pct}%</div>'
            "</div>"
        )
    return "".join(partes)


def montar_html(c) -> str:
    rotulo, icone, cor1, cor2, destaque = _condicao(c.weathercode)
    indices = _indices_de_hoje(c.horarias.get("time", []))
    temps = _serie(c.horarias, "temperature_2m", indices)
    probs = _serie(c.horarias, "precipitation_probability", indices)
    linha, area, marcas, faixa = _curva(temps)

    valores = {
        "{{PERFIL}}": PERFIL,
        "{{DATA}}": clima.data_por_extenso(),
        "{{CIDADE}}": c.nome,
        "{{ROTULO}}": rotulo,
        "{{ICONE}}": ICONES[icone],
        "{{ICONE_MARCA}}": ICONES["sol"],
        "{{ICONE_CHUVA}}": ICONES["gota"],
        "{{ICONE_VOLUME}}": ICONES["proveta"],
        "{{ICONE_VENTO}}": ICONES["vento"],
        "{{ICONE_UMIDADE}}": ICONES["umidade"],
        "{{TMAX}}": f"{c.tmax:.0f}",
        "{{TMIN}}": f"{c.tmin:.0f}",
        "{{CHUVA}}": f"{c.prob_chuva:.0f}",
        "{{VOLUME}}": f"{c.precipitacao_mm:.1f}",
        "{{VENTO}}": f"{c.vento_max:.0f}",
        "{{UMIDADE}}": f"{c.umidade:.0f}",
        "{{UV}}": f"{c.uv_max:.0f}",
        "{{NASCER}}": c.nascer_sol or "--",
        "{{POR}}": c.por_sol or "--",
        "{{COR1}}": cor1,
        "{{COR2}}": cor2,
        "{{DESTAQUE}}": destaque,
        "{{CURVA_LINHA}}": linha,
        "{{CURVA_AREA}}": area,
        "{{CURVA_MARCAS}}": marcas,
        "{{FAIXA_HORARIA}}": faixa,
        "{{BARRAS}}": _barras(probs),
    }

    html = TEMPLATE.read_text(encoding="utf-8")
    for chave, valor in valores.items():
        html = html.replace(chave, valor)
    return html


def renderizar(paginas: list) -> list:
    from playwright.sync_api import sync_playwright

    gerados = []
    with sync_playwright() as p:
        nav = p.chromium.launch(args=["--force-color-profile=srgb", "--hide-scrollbars"])
        pag = nav.new_page(
            viewport={"width": LARGURA, "height": ALTURA}, device_scale_factor=1
        )
        for nome, html in paginas:
            pag.set_content(html, wait_until="networkidle")
            pag.evaluate("async () => { await document.fonts.ready; return true; }")
            pag.wait_for_timeout(250)
            destino = SAIDA / f"card_{_slug(nome)}.jpg"
            pag.screenshot(path=str(destino), type="jpeg", quality=92)
            print(f"[card] gerado: {destino.relative_to(RAIZ)}")
            gerados.append(destino)
        nav.close()
    return gerados


def main() -> int:
    ap = argparse.ArgumentParser(description="Prototipo de card em HTML/CSS.")
    ap.add_argument("--cidade", default="Volta Redonda")
    ap.add_argument("--todas", action="store_true", help="gera as 5 cidades")
    ap.add_argument(
        "--so-html", action="store_true", help="salva o HTML e nao abre o navegador"
    )
    args = ap.parse_args()

    SAIDA.mkdir(parents=True, exist_ok=True)

    if args.todas:
        alvos = list(clima.CIDADES)
    else:
        alvos = [c for c in clima.CIDADES if _slug(c["nome"]) == _slug(args.cidade)]
        if not alvos:
            nomes = ", ".join(c["nome"] for c in clima.CIDADES)
            print(f"[card] cidade nao encontrada: {args.cidade}")
            print(f"[card] opcoes: {nomes}")
            return 2

    paginas = []
    for alvo in alvos:
        print(f"[card] coletando dados de {alvo['nome']}...")
        c = clima.processar_cidade(alvo)
        print(
            f"[card] {c.nome}: {c.tmin:.0f}C a {c.tmax:.0f}C, "
            f"chuva {c.prob_chuva:.0f}%, codigo {c.weathercode}"
        )
        html = montar_html(c)
        (SAIDA / f"card_{_slug(c.nome)}.html").write_text(html, encoding="utf-8")
        paginas.append((c.nome, html))

    if args.so_html:
        print("[card] --so-html: HTML salvo, navegador nao foi aberto.")
        return 0

    renderizar(paginas)
    print(f"[card] pronto: {len(paginas)} card(s) em lab/card_html/saida/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
