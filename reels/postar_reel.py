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
    python postar_reel.py --video ... --legenda-arquivo LEGENDA.txt   # legenda pronta
                                                                       # (Mito ou Verdade)

CAPA (thumb_offset)
-------------------
O Instagram usa o PRIMEIRO frame do vídeo como capa, e a capa é o que vira a
miniatura da grade. Isso já foi um problema: o primeiro frame era limpo de
propósito, pro loop fechar sem emenda, e a grade ficava com dez miniaturas
iguais sem dizer de que cidade era cada vídeo. A solução da época foi mandar
`thumb_offset=1500` e pescar um frame do meio da abertura.

Não é mais necessário: o selo da cidade agora começa NO FRAME ZERO e volta nos
últimos 0,3 s, então os dois extremos do vídeo trazem o nome e o loop continua
fechado (ver piloto.py). O frame 0 virou a melhor capa que existe aqui —
cenário limpo e o nome da cidade, sem o cartaz do gancho cobrindo o rosto do
personagem.

Por isso `--capa-ms` vem 0 (não manda o parâmetro, o Instagram usa o frame 0).
Passar um valor continua funcionando, se um dia a capa tiver que ser outra.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engajamento

# ATENÇÃO — este host precisa bater com o tipo de token.
# A conta @previsaosulflu usa "Instagram API com login do Instagram",
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

# O convite ao comentário vem de engajamento.pergunta(): fechada, com o nome de
# uma cidade real e respondível numa palavra. O texto fixo que estava aqui
# ("comenta aí") acompanhou 33 Reels e 20 deles fecharam com zero interação.
# A assinatura da Dona Maria (a passagem de bastão) continua, antes da pergunta.
ASSINATURA = {
    "ranzinza": "",
    "maria": "Amanhã cedo o ranzinza confirma — do jeito mal-humorado dele.",
}

# As hashtags saíam idênticas em todo Reel, todo dia. Agora rodam em 5
# conjuntos (engajamento.py), com manhã e noite nunca coincidindo no mesmo dia.


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
    slot = "noite" if voz == "maria" else "manha"
    # A assinatura vem ANTES da chamada: o pedido tem que ser a última linha
    # antes das hashtags, que é onde o olho para antes de abrir a legenda toda.
    assinatura = ASSINATURA.get(voz, "")
    if assinatura:
        linhas += ["", assinatura]
    # CTA por intenção: de manhã abre conversa no bairro; à noite pede
    # salvamento, porque a utilidade é consultar a previsão no dia seguinte.
    if slot == "noite":
        linhas += ["", "📌 Salva esta previsão para conferir amanhã de manhã."]
    else:
        linhas += ["", engajamento.chamada_bairro(slot)]
    # a cidade da vez vai na frente das hashtags: o vídeo pode ser inteiro
    # sobre Quatis enquanto o conjunto do dia só cita Volta Redonda
    linhas += ["", engajamento.hashtags(
        slot, cond, destaque=dia.get("destaque") or (cid[0]["nome"] if cid else None))]
    return "\n".join(linhas)


def _dia_br(data_iso):
    """'2026-08-14' -> '14/08'. Devolve '' se a data não vier."""
    if not data_iso or len(data_iso) < 10:
        return ""
    return f"{data_iso[8:10]}/{data_iso[5:7]}"


def validar_legenda(cap: str, quando: str = "hoje") -> None:
    """Bloqueia identidade antiga e incoerência hoje/amanhã antes da API."""
    texto = (cap or "").strip()
    baixo = texto.casefold()
    if not texto:
        raise SystemExit("legenda vazia: publicação bloqueada")
    if "@previsaovr" in baixo:
        raise SystemExit("legenda contém @previsaovr: publicação bloqueada")
    if quando == "amanha" and "amanhã" not in baixo:
        raise SystemExit("Reel noturno sem indicação de AMANHÃ: publicação bloqueada")
    if len(texto) > 2200:
        raise SystemExit(f"legenda excede 2200 caracteres ({len(texto)})")


def ja_publicado(ig_user: str, token: str, cap: str) -> bool:
    """Evita republicar a mesma legenda entre reexecuções do workflow."""
    try:
        r = _get(f"{ig_user}/media", {
            "fields": "id,caption,timestamp",
            "limit": "25",
            "access_token": token,
        })
    except SystemExit as exc:
        print(f"  AVISO: não foi possível conferir duplicidade: {exc}")
        return False
    alvo = " ".join((cap or "").split()).casefold()
    for item in r.get("data") or []:
        existente = " ".join((item.get("caption") or "").split()).casefold()
        if existente and existente == alvo:
            print(f"  duplicata encontrada: media id {item.get('id')}")
            return True
    return False


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


def texto_primeiro_comentario(dia: dict, voz: str = "ranzinza") -> str:
    """Pergunta curta publicada pela própria conta depois do Reel."""
    cidades = dia.get("cidades") or []
    cidade = (dia.get("destaque") or
              (cidades[0].get("nome") if cidades else "sua cidade"))
    if voz == "maria":
        return f"📌 Você vai sair cedo amanhã em {cidade}? Salva o Reel e conta aqui."
    return f"📍 Como está o tempo agora em {cidade}? Conta aqui em uma palavra."


def publicar_primeiro_comentario(media_id: str, token: str, texto: str) -> None:
    """Comenta no post publicado; falha aqui nunca apaga nem derruba o Reel."""
    if not media_id or not texto:
        return
    try:
        r = _post(f"{media_id}/comments", {
            "message": texto,
            "access_token": token,
        })
        print(f"primeiro comentário publicado: {r.get('id')}")
    except SystemExit as exc:
        print(f"AVISO: Reel publicado, mas o primeiro comentário falhou: {exc}")


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
    ap.add_argument("--dados", help="dia.json — dispensável com --legenda-arquivo")
    ap.add_argument("--legenda-arquivo",
                    help="legenda já pronta (ex.: LEGENDA.txt do Mito ou Verdade); "
                         "quando passado, ignora --dados/--voz/--quando na montagem "
                         "da legenda")
    ap.add_argument("--dry-run", action="store_true", help="mostra a legenda e sai")
    ap.add_argument("--sem-feed", action="store_true", help="não espelhar o Reel no feed")
    ap.add_argument("--sem-stories", action="store_true", help="nao publicar tambem no Stories")
    ap.add_argument("--voz", choices=["ranzinza", "maria"], default="ranzinza",
                    help="de quem é a legenda")
    ap.add_argument("--quando", choices=["hoje", "amanha"], default="hoje",
                    help="de que dia são os números (o Reel das 18h é 'amanha')")
    ap.add_argument("--capa-ms", type=int, default=0,
                    help="milissegundo do vídeo usado como capa na grade. "
                         "0 (padrão) = primeiro frame, que já traz o selo da cidade")
    a = ap.parse_args()

    if a.legenda_arquivo:
        # Mito ou Verdade e qualquer outro Reel sem dia.json: a legenda já
        # vem pronta do gerador (ver gerar_curiosidade.py). destaque só serve
        # pra logar qual cidade tem o selo na tela; sem dia.json, não existe.
        cap = open(a.legenda_arquivo, encoding="utf-8").read().strip()
        dia = {}
    else:
        if not a.dados:
            sys.exit("faltou --dados (ou use --legenda-arquivo)")
        dia = json.load(open(a.dados))
        cap = legenda(dia, voz=a.voz, quando=a.quando)

    # As mesmas travas rodam no dry-run e na publicação real.
    validar_legenda(cap, quando=a.quando if not a.legenda_arquivo else "hoje")

    if a.dry_run:
        print(cap)
        return

    ig_user = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_TOKEN")
    if not ig_user or not token:
        sys.exit("faltam as variáveis IG_USER_ID e IG_TOKEN")

    cota(ig_user, token)
    if ja_publicado(ig_user, token, cap):
        raise SystemExit("publicação cancelada: esta legenda já existe entre as 25 mídias recentes")

    print("[1/3] criando o container do Reel")
    if a.capa_ms:
        print(f"  capa: frame de {a.capa_ms} ms "
              f"(onde o selo de {dia.get('destaque') or 'cidade'} está na tela)")
    corpo_reel = {
        "media_type": "REELS",
        "video_url": a.video,
        "caption": cap,
        "share_to_feed": "false" if a.sem_feed else "true",
        "access_token": token,
    }
    if a.capa_ms:
        corpo_reel["thumb_offset"] = str(a.capa_ms)
    r = _post(f"{ig_user}/media", corpo_reel)
    cid = r["id"]
    print(f"  container {cid}")

    print("[2/3] aguardando o processamento do vídeo")
    esperar_container(cid, token)

    print("[3/3] publicando")
    pub = publicar_com_retentativa(ig_user, cid, token)
    media_id = pub.get("id")
    print(f"publicado: media id {media_id}")
    if a.legenda_arquivo:
        comentario = "🌦️ Qual cidade do Sul Fluminense você quer ver no próximo vídeo?"
    else:
        comentario = texto_primeiro_comentario(dia, voz=a.voz)
    publicar_primeiro_comentario(media_id, token, comentario)
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
