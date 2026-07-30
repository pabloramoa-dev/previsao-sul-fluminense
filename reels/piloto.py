"""
piloto.py — Reel diário do @previsaosulfluminense com o Seu Ranzinza.

9:16 (1080x1920), no tempo EXATO da narração, sem slow-fit (lição #14: cena com
boca sincronizada não pode ser desacelerada).

ORIENTADO A DADOS: nada do dia de hoje está escrito aqui. A cena lê
    {TRAB}/segs.json      -> quando cada fala começa e termina (vem do Kokoro)
    {TRAB}/conteudo.json  -> batidas (tipo de painel, ação do personagem) e cenário

AS QUATRO TÉCNICAS DE RETENÇÃO:
  1. GANCHO — abre com o número mais extremo do dia estalando na tela, não com
     o velho parado dando bom-dia (a decisão de deslizar é tomada em ~1,5s).
  2. LOOP — o primeiro e o último frame são a mesma imagem limpa (sem painel,
     sem legenda), então o replay não tem emenda. Replay é sinal forte.
  3. LEGENDA KARAOKÊ no terço central, palavra por palavra — 65% assiste sem
     som, e o rodapé fica coberto pela interface do Instagram.
  4. CÂMERA — push-in nos primeiros segundos e deriva lenta depois; nunca
     totalmente parada.

Render:
  RANZINZA_TRAB=_trab DVH_LIP_JSON=_trab/lip_full.json \
      manim -qm --fps 30 piloto.py Piloto
"""
from manim import *
import numpy as np
import sys, os, json

AQUI = os.path.dirname(os.path.abspath(__file__))
TRAB = os.environ.get("RANZINZA_TRAB", AQUI)
sys.path.insert(0, AQUI)
# dvh_lib.py e dvh_lip.py agora moram nesta mesma pasta (AQUI ja cobre os dois).
# Antes havia aqui um caminho absoluto para /mnt/skills/..., que não existe fora
# da máquina de desenvolvimento.

import previsao_lib as P
import dvh_lib as L
import dvh_lip as LIP

config.frame_width = 8.0
config.frame_height = 14.222
config.pixel_width = 1080
config.pixel_height = 1920

SEGS = json.load(open(os.path.join(TRAB, "segs.json")))
CONT = json.load(open(os.path.join(TRAB, "conteudo.json")))
BATIDAS = CONT["batidas"]
CENARIO = CONT.get("cenario", "sol")
PERSONAGEM = CONT.get("personagem", "ranzinza")
CENARIO_TIPO = CONT.get("cenario_tipo", "varanda")
CALOR = CONT.get("calor", False)
FIM = SEGS[-1]["fim"]

Y_PAINEL = 4.5
Y_LEGENDA = -2.2          # terço central, não o rodapé
TETO_CENA = 3.25          # nada do personagem passa disto: acima é o painel
LIMPO = 0.30              # frame limpo no FIM, pro loop fechar
ABERTURA = 0.18           # frame limpo no INÍCIO, pelo mesmo motivo:
                          # se o gancho já estiver na tela no frame 0, o replay
                          # emenda um frame com número num frame sem número.


def janelas(acao):
    """Segundos em que uma ação do personagem deve acontecer."""
    return [(SEGS[i]["ini"], SEGS[i]["fim"])
            for i, b in enumerate(BATIDAS)
            if i < len(SEGS) and (b.get("dados") or {}).get("acao") == acao]


# =====================================================================
#  PAINÉIS — um construtor por tipo de batida
# =====================================================================
CORES_GANCHO = {"frio": "#7ec8f0", "calor": "#ff8a3d", "chuva": "#5aa9e6",
                "seco": P.AMAR, "normal": P.AMAR}


def _duplo(a, b):
    return VGroup(a.scale(0.86), b.scale(0.86)).arrange(DOWN, buff=0.25)


def _nuvem_grande():
    n = VGroup(*[Circle(radius=r, fill_color="#cfd8e0", fill_opacity=1,
                        stroke_color=BLACK, stroke_width=5) for r in [0.42, 0.6, 0.48]])
    n[0].shift(LEFT * 0.6)
    n[2].shift(RIGHT * 0.6)
    return n


def _faixa(texto, sub=None, cor=P.AMAR, cor_txt=BLACK, largura=None):
    largura = P.LARG_SEGURA if largura is None else largura
    largura = P.SEGURA if largura is None else largura
    largura = largura if largura is not None else P.larg_segura()
    itens = [Text(texto, font=P.FONTE, weight=BOLD, font_size=44, color=cor_txt)]
    if sub:
        itens.append(Text(sub, font=P.FONTE, weight=BOLD, font_size=30, color="#4a3b00"))
    miolo = VGroup(*itens).arrange(DOWN, buff=0.10)
    if miolo.width > largura - 0.6:
        miolo.scale((largura - 0.6) / miolo.width)
    band = RoundedRectangle(width=largura, height=miolo.height + 0.55, corner_radius=0.2,
                            fill_color=cor, fill_opacity=0.95, stroke_color=BLACK, stroke_width=4)
    miolo.move_to(band)
    return VGroup(band, miolo)


def _card_valor(rotulo, valor):
    """Card com UM número só, no mesmo estilo escuro do card_cidade.

    Existe porque card_cidade() sempre desenha um par "min° / máx°". O painel
    "amplitude" quer mostrar a variação do dia — manhã = mínima, tarde = máxima,
    um número em cada card. Chamando card_cidade(rotulo, x, x) o mesmo valor
    saía impresso duas vezes ("12° / 12°"), que é o que aparece no REEL_V22.mp4.
    """
    largura = P.larg_segura()
    nome = Text(rotulo, font=P.FONTE, weight=BOLD, font_size=42, color=WHITE)
    temp = Text(f"{int(valor)}°", font=P.FONTE, weight=BOLD, font_size=52, color=P.AMAR)
    linha = VGroup(nome, temp).arrange(RIGHT, buff=0.5)
    if linha.width > largura - 0.7:
        linha.scale((largura - 0.7) / linha.width)
    band = RoundedRectangle(width=largura, height=linha.height + 0.55,
                            corner_radius=0.2, fill_color=BLACK, fill_opacity=0.68,
                            stroke_color=WHITE, stroke_width=3)
    linha.move_to(band)
    return VGroup(band, linha)


def painel(tipo, d):
    if tipo == "gancho":
        return P.numero_gigante(d["numero"], d.get("sub"),
                                cor=CORES_GANCHO.get(d.get("cor"), P.AMAR))
    if tipo == "cidade":
        c = d["cidade"]
        return P.card_cidade(c["nome"], c["min"], c["max"], c.get("cond", "sol"))
    if tipo == "amplitude":
        c = d["cidade"]
        return _duplo(_card_valor("Manhã", c["min"]),
                      _card_valor("Tarde", c["max"]))
    if tipo == "duas_cidades":
        a, b = d["a"], d["b"]
        return _duplo(P.card_cidade(a["nome"], a["min"], a["max"]),
                      P.card_cidade(b["nome"], b["min"], b["max"]))
    if tipo == "umidade":
        return _faixa(f"UMIDADE {d['umidade']}%", "beba água", largura=P.larg_segura())
    if tipo == "sem_chuva":
        xis = VGroup(
            Line(LEFT * 0.85 + UP * 0.85, RIGHT * 0.85 + DOWN * 0.85, stroke_color=P.VERM, stroke_width=18),
            Line(LEFT * 0.85 + DOWN * 0.85, RIGHT * 0.85 + UP * 0.85, stroke_color=P.VERM, stroke_width=18))
        return VGroup(_nuvem_grande(), xis)
    if tipo == "chuva":
        c = d["cidade"]
        gotas = VGroup(*[Line(ORIGIN, DOWN * 0.32, stroke_color="#5aa9e6", stroke_width=8)
                         .shift(RIGHT * x + DOWN * 0.85) for x in (-0.5, 0.0, 0.5)])
        return VGroup(_nuvem_grande(), gotas,
                      Text(f"{c['chuva_mm']}mm", font=P.FONTE, weight=BOLD,
                           font_size=38, color=WHITE).shift(DOWN * 1.6))
    if tipo == "recolher":
        return P.alerta_varal(d.get("hora"))
    if tipo == "varal":
        nota = d["nota"]
        cor = "#8fbf72" if nota >= 7 else ("#e8b04b" if nota >= 4 else P.VERM)
        return P.numero_gigante(f"{nota}/10", "VARAL HOJE", cor=cor, fs=150)
    if tipo == "uv":
        u = d["uv"]
        cor = "#8fbf72" if u <= 5 else ("#e8b04b" if u <= 7 else P.VERM)
        return _faixa(f"UV {u}", d.get("aviso", ""), cor=cor,
                      cor_txt=BLACK if u <= 7 else WHITE)
    if tipo == "sensacao":
        return _duplo(_card_valor("Termômetro", d["real"]),
                      _card_valor("Você sente", d["sente"]))
    if tipo == "neste_dia":
        return _faixa(f"{d['valor']}", f"neste dia em {d['ano']}",
                      cor="#7aa9c4", cor_txt=BLACK)
    if tipo == "cta":
        return P.cta_seguir(chamada=d.get("chamada", "TOCA NO SEGUIR"))
    if tipo == "fecho":
        return _faixa("SEGUE PRA PREVISÃO DE AMANHÃ", cor=P.VERM, cor_txt=WHITE)
    return None


class Piloto(MovingCameraScene):
    def construct(self):
        # ---------------- cenário com movimento ----------------
        if CENARIO_TIPO == "quintal":
            cen = P.quintal_varal(CENARIO)
            # a força do balanço das roupas ESPELHA o índice de varal do dia:
            # o fundo mostra o que ela está dizendo, sem precisar explicar
            P.roupas_balancando(cen["roupas"], vento=CONT.get("vento_visual", 1.0))
        else:
            cen = P.varanda(CENARIO)
        self.add(cen["grupo"])
        P.animar_cenario(self, cen, CENARIO, calor=CALOR, duracao=FIM)

        # ---------------- personagem ----------------
        v = P.dona_maria() if PERSONAGEM == "maria" else P.ranzinza()
        G = v["grupo"]
        G.scale(1.3).move_to([0, -2.4 if PERSONAGEM == "maria" else -1.2, 0])

        # Em dia de chuva o guarda-chuva soma altura ao personagem e o domo
        # invade a faixa do painel de dados. Mede o conjunto ANTES de montar a
        # cena e abaixa o personagem só o necessário — assim funciona pros dois,
        # que ficam em alturas diferentes no quadro.
        if CENARIO in ("chuva", "tempestade"):
            prova = P.guarda_chuva(v)
            excesso = prova.get_top()[1] - TETO_CENA
            if excesso > 0:
                G.shift(DOWN * excesso)
        self.add(G)
        # período ajustado pra caber um nº inteiro de respiros no vídeo (loop)
        L.respirar(G, amp=0.045, periodo=FIM / max(1, round(FIM / 3.0)))

        v["boca"].set_stroke(opacity=0)
        LIP.anexar_lipsync(self, v["boca"], t0=0.0, escala=1.25, deslocamento=DOWN * 0.04)

        # ---------------- ações e adereços ----------------
        if PERSONAGEM == "maria":
            jw = [(SEGS[i]["ini"], SEGS[i]["fim"]) for i, b in enumerate(BATIDAS)
                  if i < len(SEGS) and b["tipo"] in ("varal", "recolher")]
            if jw:
                P.apontar(v, jw)
            jr = [(SEGS[i]["ini"], SEGS[i]["fim"]) for i, b in enumerate(BATIDAS)
                  if i < len(SEGS) and b["tipo"] == "recolher"]
            if jr and CENARIO_TIPO == "quintal":
                P.roupa_molhada(self, cen["roupas"], jr)
        P.vestir(self, v, CENARIO,
                 janelas_frio=janelas("tremer") or None,
                 janelas_calor=janelas("abanar") or None,
                 janelas_beber=janelas("beber") or None)

        self.add(P.marca_dagua().move_to([0, 6.35, 0]))

        # ---------------- TÉCNICA 4: câmera nunca parada ----------------
        # a câmera termina de voltar ANTES do fim e fica parada no enquadramento
        # inicial durante os últimos LIMPO segundos — assim o último frame é
        # mesmo igual ao primeiro, e não "quase"
        P.camera_push_in(self, dur=2.0, duracao=FIM - LIMPO)

        # ---------------- painéis (TÉCNICA 1: gancho estala) --------------
        paineis = []
        for i, b in enumerate(BATIDAS):
            if i >= len(SEGS):
                break
            # TÉCNICA 2: primeiro e último frame IGUAIS (limpos) -> replay sem emenda
            ini = max(SEGS[i]["ini"], ABERTURA)
            fim = SEGS[i]["fim"] if i + 1 < len(BATIDAS) else FIM - LIMPO
            m = painel(b["tipo"], b.get("dados") or {})
            if m is None:
                continue
            if b["tipo"] in ("gancho", "cta"):
                m.move_to([0, 1.2, 0])          # centro da tela
            else:
                m.move_to([0, Y_PAINEL, 0])
            paineis.append((ini, fim, m))
        self.add(P.trilha_temporal(paineis, pop=0.20))

        # ---------------- TÉCNICA 3: legenda karaokê central --------------
        legs = []
        for i, b in enumerate(BATIDAS):
            if i >= len(SEGS) or b["tipo"] in ("gancho", "cta"):
                continue                         # no gancho, o número JÁ é o texto
            ini = max(SEGS[i]["ini"], ABERTURA)
            fim = SEGS[i]["fim"] if i + 1 < len(BATIDAS) else FIM - LIMPO
            legs += P.legenda_karaoke(b["legenda"], ini, fim, y=Y_LEGENDA, fs=48)
        self.add(P.trilha_temporal(legs, pop=0.10))

        # ---------------- névoa nas batidas marcadas ----------------
        jn = [(SEGS[i]["ini"], SEGS[i]["fim"]) for i, b in enumerate(BATIDAS)
              if i < len(SEGS) and (b.get("dados") or {}).get("nevoa")]
        if jn and CENARIO != "frio":
            P.nevoa(self, janelas=jn)

        # ---------------- bengala batendo no chão (só o Ranzinza) ----------
        if "bengala" not in v:
            self.wait(FIM)
            return
        beng = v["bengala"]
        stb = {"t": 0.0, "o": 0.0}
        b_ini = SEGS[min(1, len(SEGS) - 1)]["ini"] + 0.4

        def _bengala(mo, dt):
            stb["t"] += dt
            d = stb["t"] - b_ini
            novo = 0.20 * np.sin(d / 0.34 * PI) if 0 <= d < 0.34 else 0.0
            mo.shift(UP * (novo - stb["o"]))
            stb["o"] = novo
        beng.add_updater(_bengala)

        self.wait(FIM)
