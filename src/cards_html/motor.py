# -*- coding: utf-8 -*-
"""
motor.py - monta os slides do carrossel em HTML/CSS e renderiza com o Chromium
(Playwright), gravando JPEGs 1080x1350 em src/assets/output/.

Substitui o desenho feito com Pillow em src/gerar_carrossel.py. As funcoes
publicas carrossel_manha() e carrossel_noite() recebem exatamente os mesmos
argumentos das antigas e devolvem a mesma coisa: a lista de caminhos dos JPEGs
na ordem dos slides.

Se o Chromium nao estiver instalado no runner, quem chama (gerar_carrossel.py)
cai sozinho de volta no motor antigo, entao o post nunca deixa de sair.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

from .. import astronomia, clima, indices, perguntas

AQUI = Path(__file__).parent
RAIZ = AQUI.parents[1]
TEMPLATE = AQUI / "template.html"
CAPA = AQUI / "capa.html"
LISTA = AQUI / "lista.html"
PERGUNTA = AQUI / "pergunta.html"
SAIDA = RAIZ / "assets" / "output"

LARGURA, ALTURA = 1080, 1350
PERFIL = "@previsaosulfluminense"

# paleta fixa dos slides que nao dependem do weathercode
PALETAS_TIPO = {
    "manha": ("#0b5cb5", "#5fb4ff", "#ffd60a"),
    "noite": ("#101a33", "#31456f", "#8fb8ff"),
}

# indices.resumo_indices devolve sempre a mesma ordem de itens
ICONES_INDICE = ("casaco", "guarda_chuva", "protetor", "roupa", "vento")

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
    "casaco": _svg(
        '<path d="M24 9l-13 7-4 17 8 3v19h34V36l8-3-4-17-13-7z"/>'
        '<path d="M24 9l8 12 8-12M32 21v34"/>'
    ),
    "guarda_chuva": _svg(
        '<path d="M32 6v8"/><path d="M5 34a27 27 0 0 1 54 0z"/>'
        '<path d="M32 34v18a7 7 0 0 1-14 0"/>'
    ),
    "protetor": _svg(
        '<path d="M25 6h14v10H25z"/><rect x="19" y="16" width="26" height="42" rx="8"/>'
        '<path d="M19 30h26"/>'
    ),
    "roupa": _svg(
        '<path d="M24 8l-15 8 6 11 6-3v28h22V24l6 3 6-11-15-8z"/>'
        '<path d="M24 8a8 8 0 0 0 16 0"/>'
    ),
    "lua": _svg('<path d="M42 6a25 25 0 1 0 16 42A23 23 0 0 1 42 6z"/>'),
    "nascer": _svg(
        '<circle cx="32" cy="36" r="9"/><path d="M6 52h52"/>'
        '<path d="M32 16V4M26 10l6-6 6 6"/>'
        '<path d="M14 36H7M57 36h-7M18 22l4 4M46 22l-4 4"/>'
    ),
    "por": _svg(
        '<circle cx="32" cy="36" r="9"/><path d="M6 52h52"/>'
        '<path d="M32 4v12M26 10l6 6 6-6"/>'
        '<path d="M14 36H7M57 36h-7M18 22l4 4M46 22l-4 4"/>'
    ),
    "termometro": _svg(
        '<path d="M26 38V13a6 6 0 0 1 12 0v25a12 12 0 1 1-12 0z"/>'
        '<path d="M32 22v18"/>'
    ),
    "balao": _svg(
        '<path d="M10 12h44a5 5 0 0 1 5 5v24a5 5 0 0 1-5 5H30L16 57V46h-6'
        'a5 5 0 0 1-5-5V17a5 5 0 0 1 5-5z"/>'
    ),
    "seta": _svg('<path d="M12 32h36M34 18l14 14-14 14"/>'),
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
    probs = _serie(c.horarias, "precipitation_probability", indices)

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
        "{{BARRAS}}": _barras(probs),
    }

    html = TEMPLATE.read_text(encoding="utf-8")
    for chave, valor in valores.items():
        html = html.replace(chave, valor)
    return html


def _preencher(arquivo: Path, valores: dict) -> str:
    html = arquivo.read_text(encoding="utf-8")
    for chave, valor in valores.items():
        html = html.replace(chave, str(valor))
    return html


def _base(tipo: str) -> dict:
    cor1, cor2, destaque = PALETAS_TIPO[tipo]
    return {
        "{{PERFIL}}": PERFIL,
        "{{DATA}}": clima.data_por_extenso(),
        "{{ICONE_MARCA}}": ICONES["sol"] if tipo == "manha" else ICONES["lua"],
        "{{COR1}}": cor1,
        "{{COR2}}": cor2,
        "{{DESTAQUE}}": destaque,
    }


def montar_capa(tipo, chapeu, titulo, subtitulo, destaque_txt, cidades) -> str:
    valores = _base(tipo)
    valores["{{CHAPEU}}"] = chapeu
    valores["{{TITULO}}"] = titulo
    valores["{{SUBTITULO}}"] = subtitulo
    valores["{{DESTAQUE_TXT}}"] = destaque_txt
    valores["{{ICONE_FAIXA}}"] = ICONES["termometro"]
    valores["{{CIDADES}}"] = "".join(f"<span>{n}</span>" for n in cidades)
    valores["{{RODAPE_ESQ}}"] = "Arraste para o lado"
    return _preencher(CAPA, valores)


def montar_lista(tipo, titulo, legenda, itens, rodape="Sul Fluminense") -> str:
    """itens: lista de (nome_do_icone, texto, ativo)."""
    blocos = []
    for icone, texto, ativo in itens:
        classe = "item" if ativo else "item apagado"
        blocos.append(
            f'<div class="{classe}">{ICONES.get(icone, ICONES["sol"])}'
            f'<div class="texto">{texto}</div></div>'
        )
    valores = _base(tipo)
    valores["{{TITULO}}"] = titulo
    valores["{{LEGENDA}}"] = legenda
    valores["{{ITENS}}"] = "".join(blocos)
    valores["{{RODAPE_ESQ}}"] = rodape
    return _preencher(LISTA, valores)


def montar_pergunta(tipo: str, pergunta: str) -> str:
    valores = _base(tipo)
    valores["{{PERGUNTA}}"] = pergunta
    valores["{{ICONE_BALAO}}"] = ICONES["balao"]
    valores["{{ICONE_CONVITE}}"] = ICONES["seta"]
    valores["{{RODAPE_ESQ}}"] = PERFIL
    return _preencher(PERGUNTA, valores)


def _fase_lua() -> str:
    try:
        return astronomia.fase_da_lua().get("nome", "indisponivel")
    except Exception:
        return "indisponivel"


# ----------------------- PAGINAS DO CARROSSEL -----------------------

def paginas_manha(cidades, resumo, indices_itens, pergunta, fase_lua,
                  recorde=None) -> list:
    """Mesma ordem de slides do carrossel da manha feito com Pillow."""
    if recorde:
        destaque = recorde.upper()
    else:
        destaque = f"{resumo['tmin']:.0f}\u00b0C a {resumo['tmax']:.0f}\u00b0C hoje"

    paginas = []
    paginas.append(("01 capa", montar_capa(
        "manha", "Sul Fluminense", "Previsao do tempo",
        resumo["data_extenso"], destaque, [c.nome for c in cidades])))
    paginas.append(("02 resumo do dia", montar_lista(
        "manha", "Resumo do dia", "O que levar em conta antes de sair",
        [(ICONES_INDICE[i % len(ICONES_INDICE)], it["texto"], it["ativo"])
         for i, it in enumerate(indices_itens)])))
    for i, c in enumerate(cidades, start=3):
        paginas.append((f"{i:02d} {c.nome}", montar_html(c)))

    n = len(cidades) + 3
    paginas.append((f"{n:02d} sol e lua", montar_lista(
        "manha", "Sol e lua", "Como fica o ceu de hoje",
        [("nascer", f"Sol nasce as {cidades[0].nascer_sol}", True),
         ("por", f"Sol se poe as {cidades[0].por_sol}", True),
         ("lua", f"Fase da lua: {fase_lua}", True),
         ("protetor", f"Indice UV maximo: {resumo['uv_max']:.0f}", True)])))
    paginas.append((f"{n + 1:02d} pergunta", montar_pergunta("manha", pergunta)))
    return paginas


def paginas_noite(cidades, resumo, pergunta, fase_lua) -> list:
    """Mesma ordem de slides do carrossel da noite feito com Pillow."""
    madrugada = min(c.tmin_madrugada for c in cidades)

    paginas = []
    paginas.append(("01 capa", montar_capa(
        "noite", "Sul Fluminense", "Como sera a noite",
        resumo["data_extenso"],
        f"Minima de {madrugada:.0f}\u00b0C na madrugada",
        [c.nome for c in cidades])))
    for i, c in enumerate(cidades, start=2):
        paginas.append((f"{i:02d} {c.nome}", montar_html(c)))

    n = len(cidades) + 2
    paginas.append((f"{n:02d} lua e amanha", montar_lista(
        "noite", "Lua e amanha", "Antes de dormir",
        [("lua", f"Fase da lua: {fase_lua}", True),
         ("nascer", f"Amanha o sol nasce as {cidades[0].nascer_sol}", True),
         ("termometro", f"Minima da madrugada: {madrugada:.0f}\u00b0C", True)])))
    paginas.append((f"{n + 1:02d} pergunta", montar_pergunta("noite", pergunta)))
    return paginas


def montar_carrossel(tipo: str) -> list:
    """Coleta os dados sozinho e monta o carrossel. Usado pelo teste do lab."""
    cidades = clima.coletar_todas()
    resumo = clima.resumo_regional(cidades)
    pergunta = perguntas.escolher_pergunta(
        resumo["tmax"], resumo["weathercode_pred"])
    fase = _fase_lua()

    if tipo == "manha":
        umidade_media = sum(c.umidade for c in cidades) / len(cidades)
        aqi_regional = max(c.aqi for c in cidades)
        itens = indices.resumo_indices(resumo, umidade_media, aqi_regional)
        return paginas_manha(cidades, resumo, itens, pergunta, fase)
    return paginas_noite(cidades, resumo, pergunta, fase)


def renderizar(paginas: list) -> list:
    from playwright.sync_api import sync_playwright

    SAIDA.mkdir(parents=True, exist_ok=True)
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
            gerados.append(str(destino))
        nav.close()
    return gerados


# ----------------------- API USADA PELA PRODUCAO -----------------------

def carrossel_manha(cidades, resumo, indices_itens, pergunta, fase_lua,
                    recorde=None) -> list[str]:
    return renderizar(
        paginas_manha(cidades, resumo, indices_itens, pergunta, fase_lua,
                      recorde))


def carrossel_noite(cidades, resumo, pergunta, fase_lua) -> list[str]:
    return renderizar(paginas_noite(cidades, resumo, pergunta, fase_lua))
