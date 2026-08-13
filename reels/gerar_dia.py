#!/usr/bin/env python3
"""
gerar_dia.py — pipeline completo do Reel diário do Seu Ranzinza.

    dados do tempo  ->  roteiro ranzinza  ->  Kokoro  ->  lip sync  ->  Manim  ->  MP4

Uso:
    python gerar_dia.py --dados dia.json --saida REEL.mp4
    python gerar_dia.py --demo                 # usa dados de exemplo

Formato do dia.json (o que o Open-Meteo devolve, já resumido):
{
  "data": "2026-07-29",
  "cidades": [
    {"nome": "Volta Redonda", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0},
    ...
  ],
  "umidade_min": 30
}

O gerador de falas é uma MÁQUINA DE RESMUNGO: cada condição tem várias frases e
ele sorteia usando a data como semente. Assim o texto varia todo dia, mas é
reproduzível (rodar de novo no mesmo dia dá o mesmo vídeo).

DIVISÃO DE DIAS ENTRE OS DOIS PERSONAGENS (regra do perfil):
    Seu Ranzinza, 06:10 -> o dia de HOJE
    Dona Maria,   18:00 -> o dia de AMANHÃ  (gerar_tarde.py)
Nenhuma fala do velho pode afirmar coisa nenhuma sobre amanhã: a previsão do dia
seguinte é dela, feita 12 horas depois e com dados mais novos.
"""
import argparse, json, os, random, subprocess, sys, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))


# =====================================================================
#  MÁQUINA DE RESMUNGO — a personalidade do velho
# =====================================================================
ABERTURAS = [
    "Bom dia. Ou nem tanto.",
    "Acordei. Infelizmente vocês também.",
    "Olha eu aqui de novo. Que alegria pra vocês.",
    "Bom dia. Já vou avisando: não melhorou.",
]

# CTA de seguir — entra no FIM DE TODO VÍDEO, na voz do personagem. Pedido
# seco funciona mal; no jeito dele (a contragosto) vira piada e as pessoas
# lembram. É a última batida antes do frame limpo que fecha o loop.
CTA = [
    "E segue o perfil. Não que eu me importe.",
    "Aperta o seguir aí. Faz isso por mim, vai.",
    "Se seguir, eu volto amanhã. Se não seguir, também volto.",
    "Segue aí. Custa o quê, um dedo?",
]

FECHOS = [
    "Amanhã eu volto. Infelizmente.",
    "Amanhã tem mais. Preparem-se.",
    "É isso. Podem reclamar, não adianta.",
    "Amanhã eu conto o resto. Se eu estiver de bom humor.",
]

# a piada do personagem: ele reclama de TODO tipo de tempo, inclusive do bom
RESMUNGO = {
    "sol": [
        "Sol de rachar. Depois não venham chorar com dor de cabeça.",
        "Esse sol não tem hora pra parar. Nem juízo.",
        "Céu limpo demais. Isso não presta, tem coisa vindo.",
    ],
    "nublado": [
        "Nublado. Nem chove, nem faz sol. Só enrola.",
        "Céu fechado o dia inteiro. Que animação.",
        "Nublado é o tempo dos indecisos.",
    ],
    "chuva": [
        "Chuva o dia todo. Levem guarda-chuva, criaturas.",
        "Vai chover sem parar. Vai molhar. Vai reclamar. Eu avisei.",
        "Chuva o dia inteiro de novo. Meu joelho já tinha avisado ontem.",
    ],
    "chuva_pontual": [
        "Uma pancada e passa. Não é o dilúvio, mas leva o guarda-chuva.",
        "Chuva rápida em algum momento. Depois volta a enrolar.",
        "Vai pingar uma hora ou outra. Nada de dia inteiro, calma.",
    ],
    "tempestade": [
        "Temporal à vista. Tirem o carro debaixo da árvore.",
        "Tempestade. Desliga o computador, criatura.",
        "Vai vir com tudo. Não digam que eu não falei.",
    ],
    "frio": [
        "Frio de rachar. Casaco, e não é sugestão.",
        "Vai fazer frio. Do tipo que dói o osso.",
        "Frio danado. Isso é castigo, só pode.",
    ],
}

AMPLITUDE = [
    "Frio de rachar cedo, forno à tarde. Escolham um, ora bolas.",
    "De manhã casaco, de tarde ventilador. Uma bagunça.",
    "Amanhece congelando e almoça assando. Não tem lógica.",
]

UMIDADE = [
    "E a umidade despencando pra {u} por cento. Bebe água, criatura.",
    "Umidade em {u} por cento. Isso resseca até o mau humor.",
    "{u} por cento de umidade. Bebam água, não me façam repetir.",
]

# ATENÇÃO: o velho só fala do dia de HOJE. A previsão de amanhã é da Dona Maria,
# no Reel das 18h — e ela usa dados baixados 12h depois destes. A primeira frase
# daqui era "Nem hoje, nem amanhã", que é exatamente o palpite que ela desmentia
# à noite quando a previsão virava. Nenhuma fala dele promete nada sobre amanhã.
SEM_CHUVA = [
    "Chuva? Nenhuma. Hoje não cai uma gota.",
    "De chuva, nada. Continua tudo seco.",
    "Chuva nem pensar. Poeira até o teto.",
]


# o gancho: a decisão de deslizar acontece em ~1,5s, então o Reel abre pelo
# dado mais EXTREMO do dia, dito curto — nunca pelo cumprimento.
GANCHO_FRIO = ["{t} graus. {t}!", "{t} graus em {c}. {t}!"]
GANCHO_CALOR = ["{t} graus hoje. {t}!", "{t} graus em {c}. Prepare-se."]
GANCHO_CHUVA = ["{v} milímetros de chuva hoje.", "Vem chuva. {v} milímetros."]
GANCHO_SECO = ["Umidade em {u} por cento. Isso é deserto."]


# Um dia só é "de chuva" acima deste acumulado. O código WMO marca "chuva" até
# numa garoa de 0,2 mm — e era daí que vinha a contradição do roteiro: a batida
# do resmungo olhava só o código (prometia chuva) e a batida final olhava só o
# acumulado (negava a chuva). Agora as duas leem o MESMO limiar.
LIMIAR_CHUVA_MM = 1.0


def chove_de_verdade(cidade):
    """O dia é de chuva nesta cidade? Código WMO e acumulado precisam concordar."""
    return (cidade.get("cond") in ("chuva", "tempestade")
            and (cidade.get("chuva_mm", 0) or 0) >= LIMIAR_CHUVA_MM)


def cenario_do_dia(cidade):
    """Cenário visual pela MESMA regra da fala: nada de chuva animada na tela
    enquanto a narração diz que não chove."""
    cond = cidade.get("cond", "sol")
    if cond in ("chuva", "tempestade") and not chove_de_verdade(cidade):
        return "nublado"
    return cond


def escolher_gancho(cid, umidade, rnd):
    """Devolve (fala, numero_grande, subtitulo, cor) do gancho do dia.

    Prioridade pelo que mais choca quem mora aqui: frio extremo > calor
    extremo > chuva forte > ar seco. Se nada for extremo, usa a máxima da
    cidade principal — sempre há um número pra mostrar.
    """
    mais_frio = min(cid, key=lambda c: c["min"])
    mais_quente = max(cid, key=lambda c: c["max"])
    mais_chuva = max(cid, key=lambda c: c.get("chuva_mm", 0))

    if mais_frio["min"] <= 11:
        t = mais_frio["min"]
        return (rnd.choice(GANCHO_FRIO).format(t=num_extenso(t), c=mais_frio["nome"]),
                f"{t}°", mais_frio["nome"].upper(), "frio")
    if mais_quente["max"] >= 32:
        t = mais_quente["max"]
        return (rnd.choice(GANCHO_CALOR).format(t=num_extenso(t), c=mais_quente["nome"]),
                f"{t}°", mais_quente["nome"].upper(), "calor")
    if mais_chuva.get("chuva_mm", 0) >= 10:
        v = round(mais_chuva["chuva_mm"])
        return (rnd.choice(GANCHO_CHUVA).format(v=num_extenso(v)),
                f"{v}mm", mais_chuva["nome"].upper(), "chuva")
    if umidade and umidade <= 30:
        return (rnd.choice(GANCHO_SECO).format(u=num_extenso(umidade)),
                f"{umidade}%", "UMIDADE", "seco")
    c = cid[0]
    return (f"{num_extenso(c['max'])} graus hoje em {c['nome']}.",
            f"{c['max']}°", c["nome"].upper(), "normal")


def maiusculizar(t):
    """Primeira letra da frase E depois de cada ponto.

    Os templates repetem o número ('{t} graus. {t}!') e a 2ª ocorrência vinha
    minúscula. Vive aqui, no nível do módulo, porque o roteiro da Dona Maria
    (gerar_tarde.py) tem o mesmo problema e precisa da mesma regra.
    """
    if not t:
        return t
    saida, novo = [], True
    for ch in t:
        saida.append(ch.upper() if novo and ch.isalpha() else ch)
        if ch.isalpha():
            novo = False
        elif ch in ".!?":
            novo = True
    return "".join(saida)


def num_extenso(n):
    """Kokoro lê melhor número por extenso em PT-BR."""
    u = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito",
         "nove", "dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis",
         "dezessete", "dezoito", "dezenove"]
    d = {20: "vinte", 30: "trinta", 40: "quarenta", 50: "cinquenta"}
    n = int(n)
    if n < 20:
        return u[n]
    dez, resto = (n // 10) * 10, n % 10
    base = d.get(dez, str(n))
    return base if resto == 0 else f"{base} e {u[resto]}"


def montar_roteiro(dados):
    """Devolve a lista de BATIDAS do vídeo.

    Cada batida é um dict: {"fala", "legenda", "tipo", "dados"}.
    - `fala`    -> vai pro Kokoro (números por extenso, pontuação pra respiro)
    - `legenda` -> vai pra tela (curta, com números em algarismo)
    - `tipo`    -> diz ao piloto.py QUAL painel desenhar acima da cabeça
    - `dados`   -> o que aquele painel precisa

    Separar fala de legenda é de propósito: a boca lê "vinte e sete", a tela
    mostra "27°". Um texto só não serviria bem aos dois.
    """
    semente = int(dados["data"].replace("-", ""))
    rnd = random.Random(semente)
    cid = dados["cidades"]
    principal = cid[0]
    batidas = []

    def add(fala, legenda=None, tipo="nenhum", **dd):
        fala = maiusculizar(fala)
        batidas.append({"fala": fala,
                        "legenda": legenda if legenda is not None else fala,
                        "tipo": tipo, "dados": dd})

    fala_g, num_g, sub_g, cor_g = escolher_gancho(cid, dados.get("umidade_min"), rnd)
    add(fala_g, num_g, tipo="gancho", numero=num_g, sub=sub_g, cor=cor_g)

    add(rnd.choice(ABERTURAS))

    cond = principal.get("cond", "sol")
    # "chuva" pelo código WMO diário só diz que chove, não por quanto tempo.
    # Se são poucas horas de chuva de fato, é pancada pontual — não "dia todo".
    if cond in ("chuva", "tempestade") and not chove_de_verdade(principal):
        # garoa que nem junta LIMIAR_CHUVA_MM: não promete chuva nenhuma,
        # senão a batida sem_chuva desmente o velho no mesmo vídeo.
        cond_fala = "nublado"
    elif cond == "chuva" and principal.get("horas_chuva", 0) <= 3:
        cond_fala = "chuva_pontual"
    else:
        cond_fala = cond
    add(rnd.choice(RESMUNGO.get(cond_fala, RESMUNGO["sol"])))

    add(f"{principal['nome']}: mínima de {num_extenso(principal['min'])} graus, "
        f"máxima de {num_extenso(principal['max'])}.",
        f"Mínima de {principal['min']}°, máxima de {principal['max']}°.",
        tipo="cidade", cidade=principal)

    if principal["max"] - principal["min"] >= 12 and principal["min"] <= 15:
        add(rnd.choice(AMPLITUDE), "Frio de rachar cedo, forno à tarde.",
            tipo="amplitude", cidade=principal,
            acao="abanar" if principal["max"] >= 30 else None)

    if len(cid) > 2:
        add(f"{cid[1]['nome']} e {cid[2]['nome']}, a mesma bagunça.",
            f"{cid[1]['nome']} e {cid[2]['nome']}: a mesma bagunça.",
            tipo="duas_cidades", a=cid[1], b=cid[2])

    if len(cid) > 3:
        c = cid[3]
        extra = " e neblina" if c.get("cond") in ("frio", "nublado") else ""
        add(f"{c['nome']} amanhece com {num_extenso(c['min'])} graus{extra}.",
            f"{c['min']} graus{extra} em {c['nome']}.",
            tipo="cidade", cidade=c, nevoa=bool(extra),
            acao="tremer" if c["min"] <= 12 else None)

    u = dados.get("umidade_min")
    if u and u <= 40:
        add(rnd.choice(UMIDADE).format(u=num_extenso(u)),
            "Umidade despencando. Bebe água, criatura.",
            tipo="umidade", umidade=u, acao="beber")

    # mesma regra do resmungo (ver chove_de_verdade): ou o vídeo inteiro
    # promete chuva, ou o vídeo inteiro nega. Nunca os dois.
    if not any(chove_de_verdade(c) for c in cid):
        add(rnd.choice(SEM_CHUVA), tipo="sem_chuva")
    else:
        pico = max(cid, key=lambda c: c.get("chuva_mm", 0))
        add(f"E chuva, viu. Até {num_extenso(round(pico['chuva_mm']))} "
            f"milímetros em {pico['nome']}.",
            f"Chuva: até {pico['chuva_mm']}mm em {pico['nome']}.",
            tipo="chuva", cidade=pico)

    add(rnd.choice(FECHOS), tipo="fecho")
    add(rnd.choice(CTA), tipo="cta", chamada="TOCA NO SEGUIR")
    return batidas


# =====================================================================
#  ORQUESTRAÇÃO
# =====================================================================
def rodar(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, **kw)


def produzir(batidas, saida, cenario="sol", calor=False, personagem="ranzinza",
             cenario_tipo="varanda", quality="m", fps=30, voz="pm_alex",
             pitch=0.88, extra=None):
    """Do roteiro ao MP4. Compartilhado pelos dois vídeos do dia.

    `batidas` já vem pronta de quem chamou (previsão do tempo ou bloco da
    Dona Maria) — esta função só executa: voz, lip sync, render e montagem.
    `pitch` < 1 abaixa o tom (0.88 envelhece o Ranzinza; 0.94 assenta a voz
    da Dona Maria sem deixá-la rouca).
    """
    trab = os.path.join(AQUI, "_trab")
    os.makedirs(trab, exist_ok=True)
    falas = [b["fala"] for b in batidas]

    print(f"[1/5] roteiro — {len(batidas)} batidas ({personagem})")
    rot = os.path.join(trab, "roteiro.txt")
    open(rot, "w").write("\n".join(falas) + "\n")

    print("[2/5] narração (Kokoro, local)")
    bruta = os.path.join(trab, "voz_bruta.wav")
    segs = os.path.join(trab, "segs.json")
    rodar([sys.executable, os.path.join(AQUI, "gerar_voz_kokoro.py"),
           rot, "--voz", voz, "--speed", "0.95", "--gap", "0.30",
           "--out", bruta, "--seg-json", segs])

    print(f"[3/5] ajustando o timbre (pitch {int((pitch-1)*100)}%)")
    narr = os.path.join(trab, "narracao.wav")
    rodar(["ffmpeg", "-y", "-v", "error", "-i", bruta, "-af",
           f"asetrate=44100*{pitch},aresample=44100,atempo={1/pitch:.5f},"
           "vibrato=f=5.5:d=0.09,highpass=f=90,"
           "acompressor=threshold=-18dB:ratio=3:attack=8:release=180,volume=1.15",
           "-ar", "44100", "-ac", "1", narr])

    print("[4/5] lip sync por amplitude")
    lip = os.path.join(trab, "lip_full.json")
    rodar([sys.executable, os.path.join(AQUI, "lipsync_amplitude.py"),
           narr, lip, "--fps", "22"])

    print("[5/5] render Manim + montagem")
    conteudo = {"batidas": batidas, "cenario": cenario, "calor": calor,
                "personagem": personagem, "cenario_tipo": cenario_tipo}
    conteudo.update(extra or {})
    json.dump(conteudo, open(os.path.join(trab, "conteudo.json"), "w"),
              ensure_ascii=False)
    env = dict(os.environ, DVH_LIP_JSON=lip, RANZINZA_TRAB=trab)
    rodar(["manim", f"-q{quality}", "--fps", str(fps),
           os.path.join(AQUI, "piloto.py"), "Piloto"], env=env)

    mp4 = f"media/videos/piloto/1920p{fps}/Piloto.mp4"
    rodar(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-i", narr,
           "-c:v", "libx264", "-crf", "22", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-shortest", saida])
    print(f"pronto: {saida}")
    return saida


def gerar(dados, saida, quality="m"):
    """Vídeo da manhã: previsão do tempo com o Seu Ranzinza."""
    batidas = montar_roteiro(dados)
    for b in batidas:
        print(f'     [{b["tipo"]:13s}] {b["fala"]}')
    return produzir(batidas, saida,
                    cenario=cenario_do_dia(dados["cidades"][0]),
                    calor=max(c["max"] for c in dados["cidades"]) >= 31,
                    personagem="ranzinza", cenario_tipo="varanda",
                    quality=quality, voz="pm_alex", pitch=0.88,
                    extra={"data": dados["data"]})


DEMO = {
    "data": "2026-07-29",
    "cidades": [
        {"nome": "Volta Redonda", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0},
        {"nome": "Barra Mansa", "min": 11, "max": 28, "cond": "sol", "chuva_mm": 0},
        {"nome": "Porto Real", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0},
        {"nome": "Resende", "min": 9, "max": 25, "cond": "frio", "chuva_mm": 0},
    ],
    "umidade_min": 30,
}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados")
    ap.add_argument("--saida", default="REEL.mp4")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--quality", default="m")
    a = ap.parse_args()
    d = DEMO if a.demo or not a.dados else json.load(open(a.dados))
    gerar(d, a.saida, a.quality)
