#!/usr/bin/env python3
"""
postar_reel.py — publica o vídeo do Seu Ranzinza como REELS no Instagram.

A publicação de vídeo na Graph API tem 3 etapas (não dá pra enviar o arquivo
direto — a Meta busca o MP4 numa URL pública, que no nosso caso é o asset do
Release do GitHub que o workflow acabou de subir):

    1. cria um "container" apontando pro video_url
    2. espera o container terminar de processar (status_code = FINISHED)
    3. publica o container

Variáveis de ambiente:
    IG_USER_ID   — id da conta profissional (o seu: 27148485038175)
    IG_TOKEN     — token de acesso de longa duração

Uso:
    python postar_reel.py --video https://.../REEL.mp4 --dados dia.json
    python postar_reel.py --video ... --dados amanha.json --voz maria --quando amanha
    python postar_reel.py --video ... --dados dia.json --dry-run   # só mostra a legenda
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error

# ATENÇÃO — este host precisa bater com o tipo de token.
# A conta @previsaosulfluminense usa "Instagram API com login do Instagram",
# cujo token só é aceito em graph.instagram.com. O bot de imagens que já
# funciona (publicar.py) usa exatamente este host. Apontar para
# graph.facebook.com com este mesmo token devolve erro 190 (OAuth inválido).
API = "https://graph.instagram.com/v22.0"

EMOJI = {"sol": "☀️", "nublado": "☁️", "chuva": "🌧️", "tempestade": "⛈️", "frio": "🥶"}

# A legenda também tem que ter a voz do personagem — não pode ser um boletim
# seco. E cada um fala do SEU dia: o velho, do dia de hoje, às 06:10; a Dona
# Maria, do dia seguinte, às 18:00. A legenda dela precisa dizer "AMANHÃ" logo
# na primeira linha, senão os mesmos números aparecem duas vezes no perfil sem
# nada indicando que são de dias diferentes.
GANCHOS = {
    "ranzinza": {
        "sol": "Sol de rachar de novo. Alguém avisa esse céu que já deu.",
        "nublado": "Nublado. Nem chove, nem faz sol. Só enrola.",
        "chuva": "Vai chover. Depois não venham dizer que eu não avisei.",
        "tempestade": "Temporal à vista. Guardem o que voa.",
        "frio": "Frio de doer o osso. Casaco, e não é sugestão.",
    },
    "maria": {
        "sol": "Amanhã tem sol, meus queridos. Já deixa o protetor na bolsa.",
        "nublado": "Amanhã vem encoberto. Nada demais, mas não conta com sol.",
        "chuva": "Amanhã chove. Deixa o guarda-chuva na porta hoje à noite.",
        "tempestade": "Amanhã vem temporal. Guarda o que voa antes de dormir.",
        "frio": "Amanhã amanhece frio. Separa o casaco hoje, meu bem.",
    },
}

FECHOS_LEGENDA = {
    "ranzinza": "E aí, vai precisar de casaco na sua cidade? Comenta aí 👇",
    "maria": ("Já sabe o que separar pra amanhã? Conta aqui embaixo 👇\n"
              "Amanhã cedo o ranzinza confirma — do jeito mal-humorado dele."),
}

HASHTAGS = ("#sulfluminense #voltaredonda #barramansa #resende #portoreal "
            "#barradopirai #previsaodotempo #tempo #riodejaneiro #interiordorio")


def legenda(dia, voz="ranzinza", quando="hoje"):
    """Monta a legenda do post.

    `voz`    — "ranzinza" ou "maria"; muda o gancho e o convite ao comentário.
    `quando` — "hoje" ou "amanha"; só marca de que dia são os números. Os dados
               já vêm do arquivo certo (o workflow das 18h passa amanha.json).
    """
    ganchos = GANCHOS.get(voz, GANCHOS["ranzinza"])
    amanha = quando == "amanha"
    cid = dia["cidades"]
    cond = cid[0].get("cond", "sol")
    linhas = [ganchos.get(cond, ganchos["sol"]), ""]
    if amanha:
        dma = _dia_br(dia.get("data"))
        linhas += ["🗓️ PREVISÃO PARA AMANHÃ" + (f" — {dma}" if dma else ""), ""]
    for c in cid[:6]:
        linhas.append(f"{EMOJI.get(c.get('cond','sol'),'🌡️')} {c['nome']}: "
                      f"{c['min']}° / {c['max']}°")
    u = dia.get("umidade_min")
    if u and u <= 40:
        seco = ("Umidade mínima de {u}%. Já enche a garrafa de água."
                if voz == "maria" else
                "Umidade mínima de {u}%. Bebam água, criaturas.")
        linhas += ["", "💧 " + seco.format(u=u)]
    if all((c.get("chuva_mm", 0) or 0) < 1 for c in cid):
        linhas += ["", "☔ Amanhã: sem chuva prevista." if amanha
                       else "☔ Chuva: nenhuma."]
    else:
        pico = max(cid, key=lambda c: c.get("chuva_mm", 0) or 0)
        linhas += ["", f"☔ {'Amanhã, chuva' if amanha else 'Chuva prevista'}, "
                       f"até {pico['chuva_mm']}mm em {pico['nome']}."]
    linhas += ["", FECHOS_LEGENDA.get(voz, FECHOS_LEGENDA["ranzinza"]),
               "", HASHTAGS]
    return "\n".join(linhas)


def _dia_br(data_iso):
    """'2026-08-14' -> '14/08'. Devolve '' se a data não vier."""
    if not data_iso or len(data_iso) < 10:
        return ""
    return f"{data_iso[8:10]}/{data_iso[5:7]}"


# ---------------------------------------------------------------- HTTP
def _post(caminho, params, timeout=60):
    url = f"{API}/{caminho}"
    corpo = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=corpo), timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode()
        raise SystemExit(f"erro da Graph API em {caminho}: HTTP {e.code}\n{detalhe}")


def _get(caminho, params, timeout=60):
    url = f"{API}/{caminho}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"erro da Graph API em {caminho}: HTTP {e.code}\n{e.read().decode()}")


def esperar_container(cid, token, limite=900, intervalo=6):
    """Vídeo demora pra processar. Sem esta espera, o media_publish falha.

    O teto era 300s. Subiu pra 900s porque o tempo de processamento do Reel do
    lado da Meta não depende só do tamanho do arquivo — depende da fila deles,
    que varia bastante ao longo do dia. O laço sai assim que fica FINISHED, então
    um teto alto não custa nada no caso normal; ele só evita que um dia de fila
    ruim derrube a publicação.
    """
    inicio = time.time()
    while time.time() - inicio < limite:
        r = _get(cid, {"fields": "status_code,status", "access_token": token})
        st = r.get("status_code")
        if st == "FINISHED":
            print(f"  container pronto em {int(time.time()-inicio)}s")
            return True
        if st in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container falhou: {st} — {r.get('status')}")
        print(f"  processando... ({st}, {int(time.time()-inicio)}s)")
        time.sleep(intervalo)
    raise SystemExit(f"container não ficou pronto em {limite}s")


def publicar_com_retentativa(ig_user, cid, token, tentativas=4, espera=15):
    """Republica se o media_publish falhar logo após o container ficar pronto.

    É uma inconsistência conhecida da Meta: o container é reportado FINISHED mas
    o publish ainda responde "Media Not Found" por alguns segundos. O bot de
    imagens já tratava isso nos stories; para Reels vale o mesmo cuidado.
    """
    for n in range(1, tentativas + 1):
        try:
            return _post(f"{ig_user}/media_publish",
                         {"creation_id": cid, "access_token": token})
        except SystemExit as e:
            if n == tentativas:
                raise
            print(f"  publish falhou (tentativa {n}/{tentativas}): {e}")
            print(f"  repetindo em {espera}s...")
            time.sleep(espera)


def cota(ig_user, token):
    """A conta tem limite de ~50 publicações por 24h. Vale conferir antes."""
    try:
        r = _get(f"{ig_user}/content_publishing_limit",
                 {"fields": "config,quota_usage", "access_token": token})
        d = (r.get("data") or [{}])[0]
        print(f"  cota: {d.get('quota_usage')} de "
              f"{(d.get('config') or {}).get('quota_total')} nas últimas 24h")
    except SystemExit:
        pass   # informativo apenas; não impede a publicação


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="URL pública do MP4")
    ap.add_argument("--dados", required=True, help="dia.json")
    ap.add_argument("--dry-run", action="store_true", help="mostra a legenda e sai")
    ap.add_argument("--sem-feed", action="store_true", help="não espelhar o Reel no feed")
    ap.add_argument("--sem-stories", action="store_true", help="nao publicar tambem no Stories")
    ap.add_argument("--voz", choices=["ranzinza", "maria"], default="ranzinza",
                    help="de quem é a legenda")
    ap.add_argument("--quando", choices=["hoje", "amanha"], default="hoje",
                    help="de que dia são os números (o Reel das 18h é 'amanha')")
    a = ap.parse_args()

    dia = json.load(open(a.dados))
    cap = legenda(dia, voz=a.voz, quando=a.quando)

    if a.dry_run:
        print(cap)
        return

    ig_user = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_TOKEN")
    if not ig_user or not token:
        sys.exit("faltam as variáveis IG_USER_ID e IG_TOKEN")

    cota(ig_user, token)

    print("[1/3] criando o container do Reel")
    r = _post(f"{ig_user}/media", {
        "media_type": "REELS",
        "video_url": a.video,
        "caption": cap,
        "share_to_feed": "false" if a.sem_feed else "true",
        "access_token": token,
    })
    cid = r["id"]
    print(f"  container {cid}")

    print("[2/3] aguardando o processamento do vídeo")
    esperar_container(cid, token)

    print("[3/3] publicando")
    pub = publicar_com_retentativa(ig_user, cid, token)
    print(f"publicado: media id {pub.get('id')}")
    if not a.sem_stories:
        try:
            print("[4/5] criando o container do Story")
            rs = _post(f"{ig_user}/media", {
                "media_type": "STORIES",
                "video_url": a.video,
                "access_token": token,
            })
            sid = rs["id"]
            print(f"  container {sid}")
            print("[5/5] aguardando o processamento e publicando o Story")
            esperar_container(sid, token)
            pubs = publicar_com_retentativa(ig_user, sid, token)
            print(f"story publicado: media id {pubs.get('id')}")
        except SystemExit as e:
            print(f"AVISO: o Reel foi publicado, mas o Story falhou: {e}")


if __name__ == "__main__":
    main()
