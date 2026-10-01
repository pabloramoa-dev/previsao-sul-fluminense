# -*- coding: utf-8 -*-
"""
compor.py — transforma o pacote.json (roteiro + tempos + boca + palavras) no
index.html do HyperFrames.

Tudo aqui é determinístico: nada de Math.random, Date.now ou rede. As
posições "aleatórias" (nuvens, gotas, tufos) saem de um gerador com semente
fixa em Python e entram no HTML já como números.

Camadas (de trás pra frente):
  1. CENAS (.scene)  — capturadas pelo @hyperframes/shader-transitions:
                       abertura -> quadro -> chuva -> cta (e 'frase' se houver)
  2. OVERLAY FIXO    — barra AO VIVO, Juarez + bancada, lower third, ticker,
                       legenda karaokê, card do Instagram (sub-composição)
  3. TEXTURA         — grão de filme e vinheta (componentes do registry)
"""
import html
import json
import random

W, H = 1080, 1920
NAVY = "#13243a"
NAVY2 = "#0b1624"
RED = "#d63a2f"
YEL = "#ffd34e"
OFF = "#f2f0e6"
PT = "#1c1c1e"

CEUS = {  # topo, meio, serra, vale  (mesma paleta do juarez_lib.py)
    "sol": ("#3f95d6", "#bfe6f7", "#6f9fb5", "#4f7f62"),
    "calor": ("#f08a3c", "#ffd9a0", "#b98a6a", "#6f7f52"),
    "abafado": ("#e0a05a", "#f6dcb0", "#a58f7a", "#62785a"),
    "ameno": ("#5aa7d9", "#d4eef8", "#7ea7b8", "#557f66"),
    "nublado": ("#7f8e9c", "#cfd6dc", "#8a9aa6", "#5b7566"),
    "chuva": ("#4c5a6b", "#8e9aa6", "#6a7784", "#465c52"),
    "tempestade": ("#262d3a", "#5c6474", "#4a5362", "#34463f"),
    "frio": ("#8fb1c9", "#e7eef3", "#a7bccb", "#6e8a80"),
}
MOUTH = {"X": 0.06, "A": 0.1, "B": 0.35, "C": 0.6, "D": 1.0, "E": 0.7,
         "F": 0.3, "G": 0.3, "H": 0.45}


def esc(s):
    return html.escape(str(s), quote=True)


# ------------------------------------------------------------- Juarez ---
def juarez_svg():
    """Juarez Plantão redesenhado em SVG a partir do juarez_lib.py (Manim):
    1 unidade Manim = 150 px, cabeça centrada em (250, 190)."""
    u, cx, cy = 150, 250, 190

    def P(dx, dy):
        return f"{cx + u * dx:.1f},{cy - u * dy:.1f}"

    def poly(pts, fill, sw=7, extra=""):
        return (f'<polygon points="{" ".join(P(*p) for p in pts)}" fill="{fill}" '
                f'stroke="{PT}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>')

    t = (0, -0.9 - 0.2)          # base do pescoço (abaixo da cabeça)
    tx, ty = t

    def T(dx, dy):
        return (tx + dx, ty + dy)

    omb = T(0, -0.2)
    cot = (omb[0] + 0.6, omb[1] - 0.45)
    mao = (cot[0] + 0.55, cot[1] + 0.15)
    mic_top = (mao[0] + 0.08, mao[1] + 0.55)
    mic_mid = (mao[0] + 0.036, mao[1] + 0.25)
    be_fim = (omb[0] - 0.85, omb[1] - 0.55)

    tufos = "".join(
        poly([(dx, 0.75), (dx - 0.05, 1.15 + h), (dx + 0.16, 1.05 + h)], "#2b2118", 7)
        for dx, h in [(-0.55, 0.15), (-0.30, 0.30), (-0.02, 0.20), (0.26, 0.32), (0.52, 0.12)])
    topete = poly([(-0.15, 0.80), (-0.30, 1.45), (0.10, 1.30)], "#2b2118", 7)

    rng = random.Random(3)
    barba = []
    dx = -0.5
    while dx <= 0.51:
        dy = 0.56 + abs(dx) * 0.25
        x0, y0 = cx + u * dx, cy + u * dy
        barba.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0 + rng.uniform(-3, 3):.1f}" '
                     f'y2="{y0 + 5:.1f}" stroke="#2b2118" stroke-width="3" stroke-linecap="round"/>')
        dx += 0.09
    mx, my = cx, cy + u * 0.56
    return f'''
<svg id="jz-svg" viewBox="0 0 520 620" width="520" height="620" style="overflow:visible" xmlns="http://www.w3.org/2000/svg">
 <g id="jz-corpo">
  {poly([T(-0.85, -1.55), T(0.85, -1.55), T(0.70, -2.10), T(-0.70, -2.10)], "#1c2b38", 8)}
  {poly([T(-0.55, 0), T(0.55, 0), T(0.85, -1.55), T(-0.85, -1.55)], OFF, 9)}
  {poly([T(-0.08, -0.05), T(0.14, -0.05), T(0.20, -0.30), T(0.02, -1.15), T(-0.02, -0.30)], "#8a2f28", 6)}
  <line x1="{P(*omb).split(',')[0]}" y1="{P(*omb).split(',')[1]}" x2="{P(*be_fim).split(',')[0]}" y2="{P(*be_fim).split(',')[1]}" stroke="#2c3e50" stroke-width="33" stroke-linecap="round"/>
  {poly([T(-0.62, 0.05), T(-0.10, -0.10), T(-0.30, -0.55), T(-0.90, -1.58), T(-0.40, -1.58), T(-0.50, -0.20)], "#2c3e50", 9)}
  {poly([T(0.62, 0.05), T(0.10, -0.10), T(0.30, -0.55), T(0.90, -1.58), T(0.40, -1.58), T(0.50, -0.20)], "#2c3e50", 9)}
  <circle cx="{P(*be_fim).split(',')[0]}" cy="{P(*be_fim).split(',')[1]}" r="19" fill="#e8b48f" stroke="{PT}" stroke-width="5"/>
 </g>
 <g id="jz-braco">
  <line x1="{P(*omb).split(',')[0]}" y1="{P(*omb).split(',')[1]}" x2="{P(*cot).split(',')[0]}" y2="{P(*cot).split(',')[1]}" stroke="#2c3e50" stroke-width="33" stroke-linecap="round"/>
  <line x1="{P(*cot).split(',')[0]}" y1="{P(*cot).split(',')[1]}" x2="{P(*mao).split(',')[0]}" y2="{P(*mao).split(',')[1]}" stroke="#2c3e50" stroke-width="29" stroke-linecap="round"/>
  <line x1="{P(*mao).split(',')[0]}" y1="{P(*mao).split(',')[1]}" x2="{P(*mic_top).split(',')[0]}" y2="{P(*mic_top).split(',')[1]}" stroke="#3a3a3c" stroke-width="20" stroke-linecap="round"/>
  <circle cx="{P(*mic_top).split(',')[0]}" cy="{P(*mic_top).split(',')[1]}" r="30" fill="#1c1c1e" stroke="{PT}" stroke-width="6"/>
  <g transform="translate({P(*mic_mid)})"><rect x="-26" y="-26" width="52" height="52" fill="{RED}" stroke="{PT}" stroke-width="5"/>
   <text x="0" y="10" text-anchor="middle" font-family="BarlowC" font-size="30" fill="#ffffff">SF</text></g>
  <circle cx="{P(*mao).split(',')[0]}" cy="{P(*mao).split(',')[1]}" r="20" fill="#e8b48f" stroke="{PT}" stroke-width="5"/>
 </g>
 <g id="jz-cabeca">
  <line x1="{cx}" y1="{cy + 135}" x2="{cx}" y2="{cy + 165}" stroke="{PT}" stroke-width="22"/>
  <ellipse cx="{P(-0.9, -0.1).split(',')[0]}" cy="{P(-0.9, -0.1).split(',')[1]}" rx="15" ry="24" fill="#e8b48f" stroke="{PT}" stroke-width="7"/>
  <ellipse cx="{P(0.9, -0.1).split(',')[0]}" cy="{P(0.9, -0.1).split(',')[1]}" rx="15" ry="24" fill="#e8b48f" stroke="{PT}" stroke-width="7"/>
  {tufos}{topete}
  <circle cx="{cx}" cy="{cy}" r="135" fill="#e8b48f" stroke="{PT}" stroke-width="12"/>
  {''.join(barba)}
  <g id="jz-olhos">
   <circle cx="{P(-0.32, 0.04).split(',')[0]}" cy="{P(-0.32, 0.04).split(',')[1]}" r="28" fill="#ffffff" stroke="{PT}" stroke-width="6"/>
   <circle cx="{P(0.32, 0.04).split(',')[0]}" cy="{P(0.32, 0.04).split(',')[1]}" r="28" fill="#ffffff" stroke="{PT}" stroke-width="6"/>
   <circle id="jz-pe" cx="{P(-0.32, 0.02).split(',')[0]}" cy="{P(-0.32, 0.02).split(',')[1]}" r="15" fill="{PT}"/>
   <circle id="jz-pd" cx="{P(0.32, 0.02).split(',')[0]}" cy="{P(0.32, 0.02).split(',')[1]}" r="15" fill="{PT}"/>
  </g>
  <g id="jz-palp" opacity="0">
   <rect x="{cx - 80}" y="{cy - 40}" width="72" height="44" rx="14" fill="#e8b48f"/>
   <rect x="{cx + 8}" y="{cy - 40}" width="72" height="44" rx="14" fill="#e8b48f"/>
   <line x1="{cx - 74}" y1="{cy - 6}" x2="{cx - 14}" y2="{cy - 6}" stroke="{PT}" stroke-width="6" stroke-linecap="round"/>
   <line x1="{cx + 14}" y1="{cy - 6}" x2="{cx + 74}" y2="{cy - 6}" stroke="{PT}" stroke-width="6" stroke-linecap="round"/>
  </g>
  <line id="jz-sobE" x1="{P(-0.54, 0.5).split(',')[0]}" y1="{P(-0.54, 0.5).split(',')[1]}" x2="{P(-0.14, 0.3).split(',')[0]}" y2="{P(-0.14, 0.3).split(',')[1]}" stroke="#2b2118" stroke-width="18" stroke-linecap="round"/>
  <line id="jz-sobD" x1="{P(0.14, 0.26).split(',')[0]}" y1="{P(0.14, 0.26).split(',')[1]}" x2="{P(0.54, 0.30).split(',')[0]}" y2="{P(0.54, 0.30).split(',')[1]}" stroke="#2b2118" stroke-width="18" stroke-linecap="round"/>
  <ellipse cx="{cx}" cy="{cy + 24}" rx="15" ry="16.5" fill="#d99b73" stroke="{PT}" stroke-width="5"/>
  <g id="jz-boca" transform="translate({mx:.1f},{my - 12:.1f})">
   <g id="jz-boca-abre"><ellipse cx="0" cy="0" rx="30" ry="24" fill="#5b1f1f" stroke="{PT}" stroke-width="7"/>
    <ellipse cx="0" cy="12" rx="16" ry="8" fill="#c0504d"/></g>
  </g>
 </g>
</svg>'''


# ------------------------------------------------------------- cenário ---
def paisagem(ceu, uid, com_sol=True):
    """Telão com a paisagem regional: Mantiqueira, Paraíba do Sul e as
    chaminés da usina. O céu é o tempo do dia."""
    topo, meio, serra, vale = CEUS.get(ceu, CEUS["sol"])
    rng = random.Random(len(uid) * 7 + 11)
    nuvens = []
    ncl = {"sol": 3, "calor": 2, "ameno": 3, "nublado": 6, "chuva": 7,
           "tempestade": 7, "frio": 4, "abafado": 4}.get(ceu, 3)
    cor_n = {"chuva": "#b7c1cb", "tempestade": "#6d7686", "nublado": "#eef1f4"}.get(ceu, "#ffffff")
    for k in range(ncl):
        x = rng.randint(-80, 900)
        y = rng.randint(250, 620)
        s = rng.uniform(0.8, 1.5)
        nuvens.append(
            f'<g class="{uid}-nuvem" data-dx="{rng.choice([-1, 1]) * rng.randint(40, 90)}" '
            f'transform="translate({x},{y}) scale({s:.2f})">'
            f'<ellipse cx="60" cy="40" rx="60" ry="34" fill="{cor_n}"/>'
            f'<ellipse cx="120" cy="30" rx="56" ry="42" fill="{cor_n}"/>'
            f'<ellipse cx="170" cy="46" rx="44" ry="28" fill="{cor_n}"/>'
            f'<rect x="20" y="44" width="190" height="30" rx="15" fill="{cor_n}"/></g>')
    sol = ""
    if com_sol and ceu in ("sol", "calor", "ameno", "abafado", "frio"):
        raios = "".join(
            f'<rect x="-8" y="-190" width="16" height="54" rx="8" fill="#ffd34e" '
            f'transform="rotate({a})"/>' for a in range(0, 360, 30))
        sol = (f'<g transform="translate(860,380)"><g class="{uid}-raios">{raios}</g>'
               f'<circle r="118" fill="#ffd34e" stroke="#e8a93a" stroke-width="8"/></g>')
    chuva = ""
    if ceu in ("chuva", "tempestade"):
        gotas = "".join(
            f'<line x1="{rng.randint(0, 1080)}" y1="{rng.randint(0, 1500)}" x2="{0}" y2="0" '
            f'stroke="#dbe9f5" stroke-width="4" stroke-linecap="round" opacity="0.7"/>'
            for _ in range(0))
        linhas = []
        for _ in range(70):
            x, y = rng.randint(-100, 1100), rng.randint(0, 1500)
            linhas.append(f'<line x1="{x}" y1="{y}" x2="{x - 14}" y2="{y + 52}" stroke="#dbe9f5" '
                          f'stroke-width="4" stroke-linecap="round" opacity="0.75"/>')
        chuva = f'<g class="{uid}-chuva">{"".join(linhas)}{gotas}</g>'
    return f'''
<svg class="paisagem" viewBox="0 0 1080 1920" width="1080" height="1920" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
 <defs><linearGradient id="{uid}-g" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{topo}"/><stop offset="0.62" stop-color="{meio}"/></linearGradient></defs>
 <rect width="1080" height="1920" fill="url(#{uid}-g)"/>
 {sol}
 {"".join(nuvens)}
 <path d="M0 1180 L140 1010 L260 1090 L400 930 L560 1060 L700 960 L860 1080 L1080 940 L1080 1920 L0 1920 Z" fill="{serra}"/>
 <path d="M0 1260 L180 1150 L330 1220 L520 1120 L700 1210 L900 1130 L1080 1200 L1080 1920 L0 1920 Z" fill="{vale}"/>
 <g transform="translate(720,1080)">
  <rect x="0" y="40" width="34" height="170" fill="#5b4f4a" stroke="{PT}" stroke-width="4"/>
  <rect x="0" y="40" width="34" height="18" fill="#c0392b"/>
  <rect x="60" y="0" width="40" height="210" fill="#5b4f4a" stroke="{PT}" stroke-width="4"/>
  <rect x="60" y="0" width="40" height="20" fill="#c0392b"/>
  <rect x="-40" y="150" width="200" height="80" fill="#3a4a5c" stroke="{PT}" stroke-width="4"/>
  <g class="{uid}-fumaca"><circle cx="16" cy="20" r="22" fill="#e9e6e1" opacity="0.75"/>
   <circle cx="84" cy="-24" r="26" fill="#e9e6e1" opacity="0.7"/><circle cx="104" cy="-60" r="20" fill="#e9e6e1" opacity="0.55"/></g>
 </g>
 <path d="M0 1330 C220 1290 360 1370 560 1330 C760 1290 900 1360 1080 1320 L1080 1390 C900 1430 760 1360 560 1400 C360 1440 220 1360 0 1400 Z" fill="{"#6fb3d6" if ceu in ("sol", "frio", "ameno") else "#7f98aa"}"/>
 {chuva}
</svg>'''


# --------------------------------------------------------------- cenas ---
def cena_abertura(p, cena, bat):
    b = [bat[i] for i in cena["batidas"]]
    g = next((x for x in b if x["tipo"] == "gancho"), b[0])
    alerta = next((x for x in b if x["tipo"] == "alerta"), None)
    d = g["dados"]
    num = str(d.get("numero", g["legenda"]))
    digitos = "".join(ch for ch in num if ch.isdigit())
    sufixo = num[len(digitos):] if num.startswith(digitos) else ""
    cor = RED if d.get("cor") == "alerta" or alerta else "#ffffff"
    manchete = (alerta["dados"].get("titulo") if alerta else d.get("manchete")) or "PLANTÃO"
    return f'''
<div id="{cena["id"]}" class="scene clip" data-start="0" data-duration="{p['dur']}" data-track-index="1" style="background-color:{CEUS.get(p["ceu"], CEUS["sol"])[0]}">
 {paisagem(p["ceu"], "ab")}
 <div class="ab-kicker"><span class="tag tag-red">PLANTÃO DAS SEIS</span>
  <span class="tag tag-yel">{esc(manchete)}</span></div>
 <div class="ab-placa"></div>
 <div class="ab-num-wrap" data-layout-allow-overlap="true"><div class="ab-num" style="color:{cor}"><span id="ab-dig" data-alvo="{digitos or 0}">{esc(digitos or num)}</span><span class="ab-suf">{esc(sufixo)}</span></div></div>
 <div class="ab-sub"><span class="ab-sub-in"><span class="ab-sub-pre">HOJE EM</span> {esc(d.get("sub", ""))}</span></div>
</div>'''


def cena_quadro(p, cena, bat):
    b = [bat[i] for i in cena["batidas"]]
    res = next(x for x in b if x["tipo"] == "resumo")
    cab = next((x for x in b if x["tipo"] == "nenhum"), None)
    titulo = (cab["legenda"] if cab else "NÚMEROS CONFIRMADOS").rstrip(".").upper()
    linhas = []
    for k, c in enumerate(res["dados"]["cidades"]):
        def cel(v, cls):
            s = f"{int(v):02d}" if int(v) >= 0 else str(int(v))
            return "".join(f'<span class="flap {cls}" data-alvo="{ch}">{ch}</span>' for ch in s)
        linhas.append(f'''
  <div class="qd-linha" id="qd-l{k}">
   <div class="qd-barra"></div>
   <div class="qd-cidade">{esc(c["nome"].upper())}</div>
   <div class="qd-cels"><div class="qd-cel qd-min">{cel(c["min"], "fmin")}<i>°</i></div>
   <div class="qd-cel qd-max">{cel(c["max"], "fmax")}<i>°</i></div></div>
  </div>''')
    return f'''
<div id="{cena["id"]}" class="scene clip" data-start="0" data-duration="{p['dur']}" data-track-index="1" style="background-color:{NAVY2}">
 {paisagem(p["ceu"], "qd")}
 <div class="qd-veu"></div>
 <div class="qd-topo"><span class="qd-check">✓</span><span class="qd-titulo">{esc(titulo)}</span></div>
 <div class="qd-painel">
  <div class="qd-head"><span>{esc(res["dados"].get("titulo", "AS TRÊS MAIORES"))}</span><span class="qd-cols"><b>MÍN</b><b>MÁX</b></span></div>
  {"".join(linhas)}
 </div>
</div>'''


def cena_chuva(p, cena, bat):
    b = bat[cena["batidas"][0]]
    partes = [s.strip() for s in b["legenda"].split(".") if s.strip()]
    if b["tipo"] == "sem_chuva":
        icone = ('<svg viewBox="-150 -150 300 300" width="250" height="250"><g id="ch-raios">'
                 + "".join(f'<rect x="-9" y="-140" width="18" height="46" rx="9" fill="#ffd34e" transform="rotate({a})"/>'
                           for a in range(0, 360, 30))
                 + '</g><circle r="86" fill="#ffd34e" stroke="#e8a93a" stroke-width="8"/></svg>')
        valor, unidade = "0", "mm"
        rotulo = "CHUVA HOJE"
        carimbo = (partes[-1] if len(partes) > 1 else "SEM CHUVA").upper()
        bg = "#1f6fb0"
    else:
        icone = ('<svg viewBox="-150 -150 300 300" width="300" height="300"><g>'
                 '<ellipse cx="-40" cy="-20" rx="80" ry="56" fill="#dfe6ee"/><ellipse cx="40" cy="-34" rx="74" ry="64" fill="#dfe6ee"/>'
                 '<rect x="-110" y="-10" width="220" height="56" rx="28" fill="#dfe6ee"/></g><g id="ch-gotas">'
                 + "".join(f'<line x1="{x}" y1="70" x2="{x - 10}" y2="112" stroke="#8fd0ff" stroke-width="10" stroke-linecap="round"/>'
                           for x in (-70, -25, 20, 65))
                 + '</g></svg>')
        cid = b["dados"].get("cidade", {})
        valor, unidade = str(round(cid.get("chuva_mm", 0))), "mm"
        rotulo = "CHUVA PREVISTA"
        carimbo = f"EM {cid.get('nome', '').upper()}"
        bg = "#2b3a4f"
    return f'''
<div id="{cena["id"]}" class="scene clip" data-start="0" data-duration="{p['dur']}" data-track-index="1" style="background-color:{bg}">
 {paisagem(p["ceu"], "ch", com_sol=False)}
 <div class="ch-veu"></div>
 <div class="ch-icone">{icone}</div>
 <div class="ch-rot" data-layout-allow-overlap="true">{esc(rotulo)}</div>
 <div class="ch-val"><span id="ch-num" data-alvo="{esc(valor)}">{esc(valor)}</span><span class="ch-un">{unidade}</span></div>
 <div class="ch-carimbo" data-layout-allow-overlap="true"><span>{esc(carimbo)}</span></div>
</div>'''


def cena_cta(p, cena, bat):
    b = [bat[i] for i in cena["batidas"]]
    c1 = b[0]["dados"]
    return f'''
<div id="{cena["id"]}" class="scene clip" data-start="0" data-duration="{p['dur']}" data-track-index="1" style="background-color:{RED}">
 <div class="cta-fundo"></div>
 <div class="cta-bloco" id="cta-b1">
  <div class="cta-aviao"><svg viewBox="0 0 120 120" width="150" height="150"><path d="M10 58 L110 12 L78 108 L58 70 Z" fill="#ffffff" stroke="{PT}" stroke-width="6" stroke-linejoin="round"/><path d="M58 70 L110 12" stroke="{PT}" stroke-width="6"/></svg></div>
  <div class="cta-chamada">{esc(c1.get("chamada", b[0]["legenda"]))}</div>
  <div class="cta-sub">{esc(c1.get("sub", ""))}</div>
  <div class="cta-bolha"><span>@previsaosulflu</span></div>
 </div>
</div>'''


def cena_frase(p, cena, bat):
    b = bat[cena["batidas"][0]]
    return f'''
<div id="{cena["id"]}" class="scene clip" data-start="0" data-duration="{p['dur']}" data-track-index="1" style="background-color:{NAVY}">
 {paisagem(p["ceu"], "fr" + cena["id"][1])}
 <div class="qd-veu"></div>
 <div class="fr-texto">{esc(b["legenda"].upper())}</div>
</div>'''


FAB = {"abertura": cena_abertura, "quadro": cena_quadro, "chuva": cena_chuva,
       "cta": cena_cta, "frase": cena_frase}


# ------------------------------------------------------------ overlay ---
def ticker(p):
    itens = " &#9679; ".join(
        f'{esc(c["nome"].upper())} <b>{c["min"]}°/{c["max"]}°</b>' for c in p["cidades"])
    itens += " &#9679; SIGA @PREVISAOSULFLU"
    return f'<div class="tk-faixa"><div class="tk-rot">SUL FLU</div><div class="tk-janela"><div id="tk-trilho">{itens} &#9679; {itens}</div></div></div>'


def legenda_html(p):
    """Páginas de até 4 palavras por batida — cada página é um grupo."""
    paginas = []
    for bi in range(len(p["batidas"])):
        ws = [w for w in p["palavras"] if w["b"] == bi]
        pag = []
        for w in ws:
            pag.append(w)
            if len(pag) == 4 or w["w"][-1] in ".!?":
                paginas.append(pag)
                pag = []
        if pag:
            paginas.append(pag)
    out = []
    for k, pg in enumerate(paginas):
        palavras = "".join(
            f'<span class="lg-w" data-s="{w["s"]}" data-e="{w["e"]}"><span class="lg-bg"></span>'
            f'<span class="lg-t">{esc(w["w"].upper())}</span></span>' for w in pg)
        out.append(f'<div class="lg-pag" id="lg-p{k}" data-s="{pg[0]["s"]}" data-e="{pg[-1]["e"]}">{palavras}</div>')
    return "".join(out), paginas


# ------------------------------------------------------------- página ---
def compor(p):
    y, m, d = p["data"].split("-")
    p["data_curta"] = f"{p['data_ext'].split(',')[0][:3]} {d}/{m}"
    dur = p["dur"]
    bat = p["batidas"]
    cenas = p["cenas"]
    cenas_html = "".join(FAB[c["tipo"]](p, c, bat) for c in cenas)
    leg_html, paginas = legenda_html(p)
    ultima = cenas[-1]
    siga = [bat[i] for i in ultima["batidas"]][-1] if ultima["tipo"] == "cta" else None
    t_siga = siga["ini"] if siga else dur - 3
    dur_follow = round(dur - t_siga, 2)

    dados_js = json.dumps({
        "dur": dur,
        "cenas": [{"id": c["id"], "tipo": c["tipo"], "ini": c["ini"],
                   "fim": (cenas[k + 1]["ini"] if k + 1 < len(cenas) else dur)}
                  for k, c in enumerate(cenas)],
        "cortes": p["cortes"], "transicoes": p["transicoes"],
        "batidas": [{"tipo": b["tipo"], "ini": b["ini"], "fim": b["fim"]} for b in bat],
        "boca": [[t, MOUTH.get(v, 0.3)] for t, v in p["boca"]],
        "paginas": [[pg[0]["s"], pg[-1]["e"]] for pg in paginas],
        "palavras": [[w["s"], w["e"], w["w"]] for w in p["palavras"]],
        "tSiga": t_siga,
    }, ensure_ascii=False)
    transicoes = [{"time": c, "shader": s, "duration": 0.45}
                  for c, s in zip(p["cortes"], p["transicoes"])]

    return f'''<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>Juarez Plantão — HyperFrames</title>
<script src="assets/vendor/gsap.min.js"></script>
<style>
@font-face {{ font-family: "BarlowC"; src: url("assets/fonts/BarlowCondensed-ExtraBold.woff2") format("woff2"); font-weight: 800; }}
@font-face {{ font-family: "BarlowCB"; src: url("assets/fonts/BarlowCondensed-Bold.woff2") format("woff2"); font-weight: 700; }}
@font-face {{ font-family: "Poppins"; src: url("assets/fonts/Poppins-Regular.ttf") format("truetype"); font-weight: 400; }}
@font-face {{ font-family: "Poppins"; src: url("assets/fonts/Poppins-Bold.ttf") format("truetype"); font-weight: 700; }}
@font-face {{ font-family: "Poppins"; src: url("assets/fonts/Poppins-ExtraBold.ttf") format("truetype"); font-weight: 800; }}
@font-face {{ font-family: "Poppins"; src: url("assets/fonts/Poppins-Black.ttf") format("truetype"); font-weight: 900; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {NAVY2}; }}
#root {{ position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Poppins", sans-serif; color: #ffffff; }}
#palco {{ position: absolute; inset: 0; overflow: hidden; }}
.scene {{ position: absolute; inset: 0; overflow: hidden; }}
.paisagem {{ position: absolute; inset: 0; }}
/* ---------- abertura ---------- */
.ab-kicker {{ position: absolute; top: 262px; left: 0; right: 0; display: flex; justify-content: center; gap: 18px; }}
.tag {{ display: block; font-family: "BarlowC", sans-serif; font-size: 50px; letter-spacing: 2px; padding: 6px 22px 4px; border: 5px solid {PT}; }}
.tag-red {{ background-color: {RED}; color: #ffffff; }}
.tag-yel {{ background-color: {YEL}; color: {PT}; }}
.ab-num-wrap {{ position: absolute; top: 345px; left: 0; right: 0; height: 430px; display: flex; justify-content: center; align-items: center; }}
.ab-num {{ font-family: "BarlowC", sans-serif; font-size: 400px; line-height: 1; letter-spacing: -8px; text-shadow: 0 14px 0 {PT}, 10px 10px 0 {PT}, -6px 6px 0 {PT}; }}
.ab-suf {{ font-size: 300px; }}
.ab-placa {{ position: absolute; top: 350px; left: 90px; right: 90px; height: 540px; background-color: rgba(19,36,58,0.78); border: 6px solid {PT}; border-radius: 36px; box-shadow: 0 14px 0 {PT}; }}
.ab-sub {{ position: absolute; top: 785px; left: 60px; right: 60px; display: flex; justify-content: center; font-family: "BarlowC", sans-serif; font-size: 88px; color: #ffffff; }}
.ab-sub-in {{ display: block; background-color: {PT}; padding: 2px 28px 0; border-radius: 14px; }}
.ab-sub-pre {{ color: {YEL}; }}
/* ---------- quadro (split-flap) ---------- */
.qd-veu {{ position: absolute; inset: 0; background-color: rgba(11,22,36,0.72); }}
.qd-topo {{ position: absolute; top: 262px; left: 60px; right: 60px; display: flex; align-items: center; justify-content: center; gap: 18px; }}
.qd-check {{ display: flex; align-items: center; justify-content: center; width: 76px; height: 76px; border-radius: 38px; background-color: #1e8449; border: 5px solid {PT}; font-size: 48px; font-weight: 900; color: #ffffff; }}
.qd-titulo {{ font-family: "BarlowC", sans-serif; font-size: 70px; color: #ffffff; text-shadow: 0 5px 0 {PT}; }}
.qd-painel {{ position: absolute; top: 380px; left: 50px; right: 50px; padding: 26px 30px 30px; background-color: #0e1a2b; border: 6px solid {PT}; border-radius: 26px; box-shadow: 0 16px 0 {PT}; }}
.qd-head {{ display: flex; justify-content: space-between; align-items: center; font-family: "BarlowCB", sans-serif; font-size: 40px; color: {YEL}; letter-spacing: 3px; margin-bottom: 12px; }}
.qd-cols {{ display: flex; gap: 58px; padding-right: 18px; }}
.qd-cols b {{ font-weight: 700; }}
.qd-linha {{ position: relative; display: flex; align-items: center; justify-content: space-between; height: 128px; padding-left: 26px; border-top: 3px solid #22324a; }}
.qd-barra {{ position: absolute; left: 0; top: 18px; width: 10px; height: 92px; background-color: {YEL}; border-radius: 5px; }}
.qd-cidade {{ font-family: "BarlowC", sans-serif; font-size: 66px; color: #ffffff; }}
.qd-cels {{ display: flex; gap: 22px; }}
.qd-cel {{ display: flex; align-items: center; gap: 4px; }}
.qd-cel i {{ font-style: normal; font-family: "BarlowC", sans-serif; font-size: 50px; color: #9fb3c8; }}
.flap {{ display: block; width: 58px; height: 86px; line-height: 86px; text-align: center; font-family: "BarlowC", sans-serif; font-size: 70px; color: #ffffff; background-color: #1d2c42; border-radius: 8px; border-bottom: 3px solid #0a1320; }}
.qd-max .flap {{ color: {YEL}; }}
/* ---------- chuva ---------- */
.ch-veu {{ position: absolute; inset: 0; background-color: rgba(11,22,36,0.55); }}
.ch-icone {{ position: absolute; top: 262px; left: 0; right: 0; display: flex; justify-content: center; }}
.ch-rot {{ position: absolute; top: 530px; left: 0; right: 0; text-align: center; font-family: "BarlowCB", sans-serif; font-size: 54px; letter-spacing: 6px; color: {YEL}; text-shadow: 0 4px 0 {PT}; }}
.ch-val {{ position: absolute; top: 575px; left: 0; right: 0; text-align: center; font-family: "BarlowC", sans-serif; font-size: 190px; line-height: 1; color: #ffffff; text-shadow: 0 10px 0 {PT}; }}
.ch-un {{ font-size: 110px; margin-left: 10px; }}
.ch-carimbo {{ position: absolute; top: 790px; left: 0; right: 0; display: flex; justify-content: center; }}
.ch-carimbo span {{ display: block; font-family: "BarlowC", sans-serif; font-size: 78px; color: #ffffff; background-color: #1e8449; padding: 6px 34px 2px; border: 7px solid {PT}; border-radius: 14px; box-shadow: 0 10px 0 {PT}; }}
/* ---------- cta ---------- */
.cta-fundo {{ position: absolute; inset: 0; background-color: {RED}; background-image: repeating-linear-gradient(135deg, rgba(0,0,0,0.16) 0 40px, rgba(0,0,0,0) 40px 80px); }}
.cta-bloco {{ position: absolute; top: 250px; left: 60px; right: 60px; display: flex; flex-direction: column; align-items: center; }}
.cta-chamada {{ margin-top: 10px; font-family: "BarlowC", sans-serif; font-size: 116px; line-height: 1; text-align: center; color: #ffffff; text-shadow: 0 8px 0 {PT}; }}
.cta-sub {{ margin-top: 18px; font-size: 38px; font-weight: 700; text-align: center; color: {YEL}; }}
.cta-bolha {{ margin-top: 34px; background-color: #ffffff; color: {PT}; border: 5px solid {PT}; border-radius: 40px; padding: 14px 40px; font-size: 44px; font-weight: 800; }}
/* ---------- frase ---------- */
.fr-texto {{ position: absolute; top: 330px; left: 70px; right: 70px; text-align: center; font-family: "BarlowC", sans-serif; font-size: 110px; line-height: 1.05; color: #ffffff; text-shadow: 0 8px 0 {PT}; }}
/* ---------- overlay fixo ---------- */
#hud {{ position: absolute; top: 150px; left: 36px; right: 36px; height: 84px; display: flex; align-items: center; gap: 16px; z-index: 300; }}
.hud-vivo {{ display: flex; align-items: center; gap: 12px; background-color: {RED}; border: 5px solid {PT}; border-radius: 12px; padding: 4px 18px 2px; font-family: "BarlowC", sans-serif; font-size: 44px; color: #ffffff; }}
.hud-ponto {{ width: 20px; height: 20px; border-radius: 10px; background-color: #ffffff; }}
.hud-nome {{ flex: 1; font-family: "BarlowC", sans-serif; font-size: 42px; color: #ffffff; background-color: {NAVY}; border: 5px solid {PT}; border-radius: 12px; padding: 4px 18px 2px; }}
.hud-rel {{ font-family: "BarlowC", sans-serif; font-size: 44px; color: {PT}; background-color: {YEL}; border: 5px solid {PT}; border-radius: 12px; padding: 4px 16px 2px; }}
#jz-wrap {{ position: absolute; left: -6px; top: 1040px; width: 520px; height: 620px; z-index: 310; }}
#bancada {{ position: absolute; left: 0; right: 0; top: 1520px; bottom: 0; z-index: 320; background-color: {NAVY}; border-top: 8px solid {PT}; }}
.bc-faixa {{ position: absolute; top: 0; left: 0; right: 0; height: 18px; background-color: {RED}; }}
.tk-faixa {{ position: absolute; top: 36px; left: 0; right: 0; height: 78px; display: flex; background-color: #ffffff; border-top: 5px solid {PT}; border-bottom: 5px solid {PT}; }}
.tk-rot {{ flex: 0 0 auto; display: flex; align-items: center; padding: 0 22px; background-color: {RED}; color: #ffffff; font-family: "BarlowC", sans-serif; font-size: 42px; border-right: 5px solid {PT}; }}
.tk-janela {{ position: relative; flex: 1; overflow: hidden; }}
#tk-trilho {{ position: absolute; left: 0; top: 0; height: 68px; line-height: 70px; white-space: nowrap; font-family: "BarlowCB", sans-serif; font-size: 42px; color: {PT}; }}
#tk-trilho b {{ color: #a3211a; }}
#lt {{ position: absolute; left: 470px; top: 1330px; z-index: 330; }}
.lt-nome {{ display: block; background-color: #ffffff; color: {PT}; font-family: "BarlowC", sans-serif; font-size: 64px; padding: 4px 20px 0; box-shadow: 10px 10px 0 {RED}; }}
.lt-cargo {{ display: block; margin-top: 16px; background-color: {PT}; color: {YEL}; font-family: "BarlowCB", sans-serif; font-size: 34px; padding: 4px 18px 2px; width: fit-content; }}
#legenda {{ position: absolute; left: 40px; right: 40px; top: 900px; height: 150px; z-index: 340; }}
.lg-pag {{ position: absolute; inset: 0; display: flex; flex-wrap: wrap; justify-content: center; align-content: center; gap: 6px 14px; opacity: 0; }}
.lg-w {{ position: relative; display: block; padding: 2px 14px 0; background-color: rgba(11,22,36,0.82); border-radius: 12px; }}
.lg-bg {{ position: absolute; inset: 0; border-radius: 10px; background-color: {RED}; border: 4px solid {PT}; transform: scaleX(0); transform-origin: 0% 50%; }}
.lg-t {{ position: relative; display: block; font-family: "Poppins", sans-serif; font-weight: 900; font-size: 60px; line-height: 1.15; color: #ffffff; -webkit-text-stroke: 5px {PT}; paint-order: stroke fill; text-shadow: 0 5px 0 {PT}; }}
#follow-slot {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; z-index: 350; }}
#grao {{ position: absolute; inset: -40px; z-index: 900; pointer-events: none; opacity: 0.07;
  background-image: repeating-radial-gradient(circle at 17% 32%, rgba(255,255,255,0.9) 0 1px, rgba(255,255,255,0) 1px 3px), repeating-radial-gradient(circle at 73% 61%, rgba(0,0,0,0.9) 0 1px, rgba(0,0,0,0) 1px 4px); }}
#vinheta {{ position: absolute; inset: 0; z-index: 910; pointer-events: none; background: radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.42) 100%); }}
#glitch {{ position: absolute; inset: 0; z-index: 915; opacity: 0; pointer-events: none; mix-blend-mode: screen; background-image: repeating-linear-gradient(0deg, rgba(255,0,60,0.55) 0 14px, rgba(0,0,0,0) 14px 46px, rgba(0,220,255,0.5) 46px 58px, rgba(0,0,0,0) 58px 120px); }}
#flash {{ position: absolute; inset: 0; z-index: 920; background-color: #ffffff; opacity: 0; pointer-events: none; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{W}" data-height="{H}">

 <div id="palco">{cenas_html}</div>

 <div id="hud" class="clip" data-start="0" data-duration="{dur}" data-track-index="2">
  <div class="hud-vivo"><span class="hud-ponto" id="hud-ponto"></span>PREVISÃO</div>
  <div class="hud-nome">PLANTÃO SUL FLU · {esc(p["data_curta"])}</div>
  <div class="hud-rel">06:00</div>
 </div>

 <div id="jz-wrap" class="clip" data-start="0" data-duration="{dur}" data-track-index="3"><div id="jz-mov">{juarez_svg()}</div></div>

 <div id="bancada" class="clip" data-start="0" data-duration="{dur}" data-track-index="4">
  <div class="bc-faixa"></div>
  {ticker(p)}
 </div>

 <div id="lt" class="clip" data-start="0.5" data-duration="4.2" data-track-index="5">
  <span class="lt-nome" id="lt-nome">JUAREZ PLANTÃO</span>
  <span class="lt-cargo" id="lt-cargo">TEMPO NO SUL FLUMINENSE</span>
 </div>

 <div id="legenda" class="clip" data-start="0" data-duration="{dur}" data-track-index="6">{leg_html}</div>

 <div id="follow-slot" data-composition-id="instagram-follow" data-composition-src="compositions/instagram-follow.html"
      data-start="{t_siga}" data-duration="{dur_follow}" data-width="1080" data-height="1920" data-track-index="7"></div>

 <div id="grao" class="clip" data-start="0" data-duration="{dur}" data-track-index="8"></div>
 <div id="vinheta" class="clip" data-start="0" data-duration="{dur}" data-track-index="9"></div>
 <div id="glitch" class="clip" data-start="0" data-duration="{dur}" data-track-index="11"></div>
 <div id="flash" class="clip" data-start="0" data-duration="{dur}" data-track-index="10"></div>

 <audio id="aud-voz" src="assets/audio/narracao.wav" data-start="0" data-duration="{dur}" data-track-index="20" data-volume="1"></audio>
 <audio id="aud-trilha" src="assets/audio/trilha.wav" data-start="0" data-duration="{dur}" data-track-index="21" data-volume="0.16"></audio>
 <audio id="aud-whoosh" src="assets/audio/whoosh.wav" data-start="0" data-duration="{dur}" data-track-index="22" data-volume="0.35"></audio>
</div>

<script>
(function () {{
  var D = {dados_js};
  var cenaIds = D.cenas.map(function (c) {{ return c.id; }});

  // 1) TRANSIÇÕES entre cenas — receitas CSS do catálogo de transições do
  //    HyperFrames (css-distortion: glitch · css-push/blur: whip pan ·
  //    css-light: flash). CSS em vez de WebGL porque renderiza igual em
  //    qualquer máquina, inclusive no runner do GitHub sem GPU.
  var tl = gsap.timeline({{ paused: true }});
  var TR = {json.dumps(transicoes)};
  cenaIds.forEach(function (id, k) {{ tl.set("#" + id, {{ opacity: k === 0 ? 1 : 0, x: 0 }}, 0); }});
  TR.forEach(function (t, k) {{
    var A = "#" + cenaIds[k], B = "#" + cenaIds[k + 1], T = t.time, d = t.duration;
    if (t.shader === "glitch") {{
      var passos = [[-40, 6, 0.9], [55, -8, 0.4], [-25, 12, 1], [70, -4, 0.6], [-15, 3, 0.8], [30, -10, 0.5], [0, 0, 0]];
      passos.forEach(function (p, j) {{
        var tt = T + j * d / passos.length;
        tl.set("#palco", {{ x: p[0], skewX: p[1] }}, tt);
        tl.set("#glitch", {{ opacity: p[2], backgroundPositionY: (j * 97 % 300) + "px" }}, tt);
      }});
      tl.set(B, {{ opacity: 1 }}, T + d * 0.45);
      tl.set(A, {{ opacity: 0 }}, T + d * 0.5);
    }} else if (t.shader === "whip-pan") {{
      tl.set(B, {{ opacity: 1 }}, T);
      tl.fromTo(A, {{ x: 0, filter: "blur(0px)" }}, {{ x: -1080, filter: "blur(24px)", duration: d, ease: "power3.in" }}, T);
      tl.fromTo(B, {{ x: 1080, filter: "blur(24px)" }}, {{ x: 0, filter: "blur(0px)", duration: d, ease: "power3.out" }}, T + d * 0.35);
      tl.set(A, {{ opacity: 0 }}, T + d);
    }} else {{
      tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 1, duration: d * 0.45, ease: "power2.in" }}, T);
      tl.set(B, {{ opacity: 1 }}, T + d * 0.45);
      tl.set(A, {{ opacity: 0 }}, T + d * 0.45);
      tl.to("#flash", {{ opacity: 0, duration: d * 0.55, ease: "power2.out" }}, T + d * 0.45);
    }}
  }});

  function cena(tipo) {{ for (var i = 0; i < D.cenas.length; i++) if (D.cenas[i].tipo === tipo) return D.cenas[i]; return null; }}

  // 2) ABERTURA — count-up + headline-slam + camera-shake
  var ab = cena("abertura");
  if (ab) {{
    var dig = document.getElementById("ab-dig");
    var alvo = parseInt(dig.getAttribute("data-alvo"), 10) || 0;
    var cont = {{ v: Math.max(0, alvo - 14) }};
    tl.fromTo(".ab-kicker .tag", {{ yPercent: -140, opacity: 0 }}, {{ yPercent: 0, opacity: 1, duration: 0.35, stagger: 0.08, ease: "back.out(2)" }}, ab.ini + 0.02);
    tl.fromTo(".ab-placa", {{ scaleY: 0, transformOrigin: "50% 50%" }}, {{ scaleY: 1, duration: 0.3, ease: "power3.out" }}, ab.ini);
    tl.fromTo(".ab-num", {{ scale: 2.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.42, ease: "power4.in" }}, ab.ini + 0.05);
    for (var n=0;n<=16;n++) tl.set(dig, {{textContent:String(Math.round(alvo*n/16))}}, ab.ini + .05 + .55*n/16);
    // shake de câmera de 3 quadros no impacto (padrão headline-slam/camera-shake)
    [[6, -5], [-5, 4], [3, -2], [0, 0]].forEach(function (s, k) {{
      tl.set(".ab-num-wrap", {{ x: s[0] * 3, y: s[1] * 3 }}, ab.ini + 0.47 + k / 30);
    }});
    tl.fromTo(".ab-sub", {{ y: 50, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "power3.out" }}, ab.ini + 0.55);
    tl.fromTo(".ab-raios", {{ rotation: 0, transformOrigin: "50% 50%" }}, {{ rotation: 40, duration: ab.fim - ab.ini + 0.5, ease: "none" }}, ab.ini);
    tl.to("#flash", {{ opacity: 0.5, duration: 0.04 }}, ab.ini + 0.47);
    tl.to("#flash", {{ opacity: 0, duration: 0.25 }}, ab.ini + 0.51);
  }}

  // 3) QUADRO — split-flap (Solari) + destaque da cidade falada
  var qd = cena("quadro");
  if (qd) {{
    tl.fromTo(".qd-topo", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.2)" }}, qd.ini + 0.05);
    tl.fromTo(".qd-painel", {{ y: 120, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "power3.out" }}, qd.ini + 0.2);
    tl.fromTo(".qd-linha", {{ x: -60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, stagger: 0.12, ease: "power2.out" }}, qd.ini + 0.4);
    var flaps = document.querySelectorAll(".flap");
    var seq = "0123456789";
    flaps.forEach(function (f, k) {{
      var alvoF = f.getAttribute("data-alvo");
      var fim = seq.indexOf(alvoF);
      var t0 = qd.ini + 0.55 + k * 0.05;
      for (var j = 0; j < 7; j++) {{
        (function (ch, t) {{ tl.set(f, {{ textContent: ch }}, t); }})(seq[(fim + 3 + j) % 10], t0 + j * 0.045);
      }}
      tl.set(f, {{ textContent: alvoF }}, t0 + 7 * 0.045);
      tl.fromTo(f, {{ scaleY: 0.2 }}, {{ scaleY: 1, duration: 0.32, ease: "bounce.out" }}, t0);
    }});
    // cada linha acende quando o nome da cidade é falado
    var linhas = document.querySelectorAll(".qd-linha");
    var nomes = Array.prototype.map.call(document.querySelectorAll(".qd-cidade"), function (e) {{ return e.textContent.split(" ")[0]; }});
    nomes.forEach(function (nome, k) {{
      for (var i = 0; i < D.palavras.length; i++) {{
        var w = D.palavras[i];
        if (w[0] >= qd.ini && w[2].toUpperCase().replace(/[^A-ZÁÉÍÓÚÂÊÔÃÕÇ]/g, "") === nome.replace(/[^A-ZÁÉÍÓÚÂÊÔÃÕÇ]/g, "")) {{
          tl.fromTo(linhas[k].querySelector(".qd-barra"), {{ scaleY: 0.1 }}, {{ scaleY: 1, duration: 0.25, ease: "back.out(3)" }}, w[0]);
          tl.fromTo(linhas[k], {{ backgroundColor: "rgba(255,211,78,0.28)" }}, {{ backgroundColor: "rgba(255,211,78,0)", duration: 1.0, ease: "power1.out", immediateRender: false }}, w[0]);
          break;
        }}
      }}
    }});
  }}

  // 4) CHUVA — ícone, contador e carimbo com impacto
  var ch = cena("chuva");
  if (ch) {{
    tl.fromTo(".ch-icone", {{ scale: 0.3, rotation: -40, opacity: 0 }}, {{ scale: 1, rotation: 0, opacity: 1, duration: 0.5, ease: "back.out(1.8)" }}, ch.ini + 0.02);
    tl.fromTo(".ch-rot", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3 }}, ch.ini + 0.15);
    tl.fromTo(".ch-val", {{ scale: 0.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2)" }}, ch.ini + 0.22);
    var raios = document.getElementById("ch-raios");
    if (raios) tl.fromTo(raios, {{ rotation: 0, svgOrigin: "0 0" }}, {{ rotation: 60, duration: ch.fim - ch.ini, ease: "none" }}, ch.ini);
    var gotas = document.getElementById("ch-gotas");
    if (gotas) tl.fromTo(gotas, {{ y: -10 }}, {{ y: 14, duration: 0.25, repeat: Math.max(1, Math.floor((ch.fim - ch.ini) / 0.5)), yoyo: true, ease: "sine.inOut" }}, ch.ini);
    var tCar = ch.ini + (ch.fim - ch.ini) * 0.45;
    tl.fromTo(".ch-carimbo span", {{ scale: 3, rotation: -18, opacity: 0 }}, {{ scale: 1, rotation: -7, opacity: 1, duration: 0.28, ease: "power4.in" }}, tCar);
    [[5, -4], [-4, 3], [2, -1], [0, 0]].forEach(function (s, k) {{ tl.set(".ch-carimbo", {{ x: s[0] * 3, y: s[1] * 3 }}, tCar + 0.28 + k / 30); }});
  }}

  // 5) CTA — DM e depois o card de seguir (sub-composição do registry)
  var cta = cena("cta");
  if (cta) {{
    tl.fromTo(".cta-aviao", {{ x: -500, y: 200, rotation: -30 }}, {{ x: 0, y: 0, rotation: 0, duration: 0.55, ease: "power3.out" }}, cta.ini + 0.02);
    tl.fromTo(".cta-chamada", {{ scale: 0.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }}, cta.ini + 0.12);
    tl.fromTo(".cta-sub", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.3 }}, cta.ini + 0.35);
    tl.fromTo(".cta-bolha", {{ scale: 0, transformOrigin: "0% 100%" }}, {{ scale: 1, duration: 0.35, ease: "back.out(2.5)" }}, cta.ini + 0.6);
    tl.to("#cta-b1", {{ y: -40, scale: 0.86, duration: 0.4, ease: "power2.inOut" }}, D.tSiga - 0.1);
    tl.to("#vinheta", {{ opacity: 1.0, duration: 0.3 }}, D.dur - 0.35);
  }}

  // 6) HUD: ponto do AO VIVO piscando (repeat finito), ticker correndo
  var nPisca = Math.floor(D.dur / 0.9);
  tl.fromTo("#hud-ponto", {{ opacity: 1 }}, {{ opacity: 0.15, duration: 0.45, repeat: nPisca * 2 - 1, yoyo: true, ease: "steps(1)" }}, 0);
  tl.fromTo("#hud", {{ y: -140 }}, {{ y: 0, duration: 0.4, ease: "back.out(1.6)" }}, 0);
  var trilho = document.getElementById("tk-trilho");
  tl.fromTo(trilho, {{ x: 0 }}, {{ x: -trilho.scrollWidth / 2, duration: D.dur, ease: "none" }}, 0);

  // 7) LOWER THIRD (lower-third-bild adaptado) — entra e sai
  tl.fromTo("#lt-nome", {{ xPercent: -120, opacity: 0 }}, {{ xPercent: 0, opacity: 1, duration: 0.35, ease: "power3.out" }}, 0.5);
  tl.fromTo("#lt-cargo", {{ xPercent: -120, opacity: 0 }}, {{ xPercent: 0, opacity: 1, duration: 0.35, ease: "power3.out" }}, 0.62);
  tl.to(["#lt-nome", "#lt-cargo"], {{ xPercent: 130, opacity: 0, duration: 0.3, ease: "power2.in", stagger: 0.06 }}, 4.3);

  // 8) JUAREZ — respiração, piscadas, sobrancelha nas ênfases, braço do microfone
  tl.fromTo("#jz-wrap", {{ y: 700 }}, {{ y: 0, duration: 0.5, ease: "back.out(1.4)" }}, 0);
  var nResp = Math.max(1, Math.floor(D.dur / 1.6));
  tl.fromTo("#jz-corpo", {{ scaleY: 1, svgOrigin: "250 600" }}, {{ scaleY: 1.018, duration: 0.8, repeat: nResp * 2 - 1, yoyo: true, ease: "sine.inOut" }}, 0);
  tl.fromTo("#jz-cabeca", {{ y: 0 }}, {{ y: -5, duration: 0.8, repeat: nResp * 2 - 1, yoyo: true, ease: "sine.inOut" }}, 0);
  var piscadas = [];
  for (var tp = 1.3; tp < D.dur - 0.3; tp += 2.7) piscadas.push(tp);
  piscadas.forEach(function (t) {{
    tl.set("#jz-palp", {{ opacity: 1 }}, t);
    tl.set("#jz-palp", {{ opacity: 0 }}, t + 0.1);
  }});
  D.batidas.forEach(function (b, k) {{
    // a cada batida: sobrancelha sobe, cabeça dá um "tranco" de plantão
    tl.fromTo(["#jz-sobE", "#jz-sobD"], {{ y: 0 }}, {{ y: -14, duration: 0.12, yoyo: true, repeat: 1, ease: "power2.out" }}, b.ini);
    tl.fromTo("#jz-mov", {{ rotation: 0, svgOrigin: "250 600" }}, {{ rotation: (k % 2 ? 2.5 : -2.5), duration: 0.18, yoyo: true, repeat: 1, ease: "power1.inOut" }}, b.ini);
    tl.fromTo("#jz-braco", {{ rotation: 0, svgOrigin: "250 385" }}, {{ rotation: (k % 2 ? -4 : 3), duration: 0.22, yoyo: true, repeat: 1, ease: "sine.inOut" }}, b.ini + 0.05);
  }});
  // pupilas olham pro número/quadro nas cenas de dado
  D.cenas.forEach(function (c) {{
    var dx = (c.tipo === "cta") ? 0 : 7, dy = (c.tipo === "cta") ? 0 : -6;
    tl.to(["#jz-pe", "#jz-pd"], {{ x: dx, y: dy, duration: 0.2 }}, c.ini + 0.1);
  }});

  // 9) LIP SYNC — a boca segue a energia do áudio (lipsync_amplitude.py)
  D.boca.forEach(function (c) {{
    tl.set("#jz-boca-abre", {{ scaleY: c[1], scaleX: 0.75 + 0.25 * c[1], svgOrigin: "0 0" }}, c[0]);
  }});

  // 10) LEGENDA KARAOKÊ (caption-highlight): página por página, palavra por palavra
  var pags = document.querySelectorAll(".lg-pag");
  pags.forEach(function (pg, k) {{
    var s = parseFloat(pg.getAttribute("data-s")), e = parseFloat(pg.getAttribute("data-e"));
    var prox = k + 1 < pags.length ? parseFloat(pags[k + 1].getAttribute("data-s")) : D.dur;
    var sai = Math.min(prox, e + 0.35);
    tl.fromTo(pg, {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.12, ease: "power2.out" }}, s - 0.05);
    tl.to(pg, {{ opacity: 0, duration: 0.06 }}, sai - 0.06);
    pg.querySelectorAll(".lg-w").forEach(function (w) {{
      var ws = parseFloat(w.getAttribute("data-s")), we = parseFloat(w.getAttribute("data-e"));
      var bg = w.querySelector(".lg-bg");
      tl.fromTo(bg, {{ scaleX: 0 }}, {{ scaleX: 1, duration: Math.min(0.12, we - ws), ease: "power2.out" }}, ws);
      tl.fromTo(w, {{ scale: 1 }}, {{ scale: 1.08, duration: 0.08, yoyo: true, repeat: 1, ease: "power1.out" }}, ws);
      tl.to(bg, {{ scaleX: 0, transformOrigin: "100% 50%", duration: 0.08 }}, we);
    }});
  }});

  // 11) nuvens, fumaça da usina e chuva do telão (movimento contínuo, finito)
  document.querySelectorAll("[class$='-nuvem']").forEach(function (n) {{
    tl.to(n, {{ x: "+=" + n.getAttribute("data-dx"), duration: D.dur, ease: "none" }}, 0);
  }});
  document.querySelectorAll("[class$='-fumaca']").forEach(function (f) {{
    tl.fromTo(f, {{ y: 0, opacity: 0.9 }}, {{ y: -40, opacity: 0.5, duration: 1.2, repeat: Math.floor(D.dur / 1.2), ease: "none" }}, 0);
  }});
  document.querySelectorAll("[class$='-chuva']").forEach(function (c) {{
    tl.fromTo(c, {{ y: -120 }}, {{ y: 0, duration: 0.35, repeat: Math.floor(D.dur / 0.35), ease: "none" }}, 0);
  }});

  // 12) grão de filme (grain-overlay) com deslocamento em degraus
  for (var gk = 0; gk < D.dur * 12; gk++) {{
    tl.set("#grao", {{ x: ((gk * 37) % 40) - 20, y: ((gk * 53) % 40) - 20 }}, gk / 12);
  }}

  window.__timelines["main"] = tl;
}})();
</script>
</body>
</html>
'''
