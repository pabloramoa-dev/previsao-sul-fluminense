# -*- coding: utf-8 -*-
"""
webhook_ig.py - Recebe a DM do Instagram e responde com a previsao do bairro.

Roda no Render (plano Free). Variaveis de ambiente necessarias:
  IG_VERIFY_TOKEN  - qualquer frase que voce inventa; tem que ser a mesma que
                     voce digitar no painel do Meta ao configurar o webhook
  IG_ACCESS_TOKEN  - o mesmo token que o bot ja usa para publicar

O endpoint /ping existe para um servico de keep-alive (cron-job.org) manter o
Render acordado no horario das previsoes. No plano Free o servico dorme depois
de ~15 min sem uso, e a primeira mensagem depois disso demora 30-60s.

FOLLOW-GATE (desde 2026-08-23)
------------------------------
Antes de responder, o robo consulta o perfil de quem mandou a mensagem
(GET /{IGSID}?fields=is_user_follow_business — mesma API, mesmo token, custo
zero) e descobre se a pessoa segue o @previsaosulflu.

  - Segue           -> responde normal, fecho de agradecimento.
  - Nao segue, 1a   -> responde a previsao MAIS o aviso de que a proxima so
    vem seguindo (a cortesia mostra que o robo funciona de verdade; pedir
    follow antes de provar valor faz muita gente desistir).
  - Nao segue, 2a+  -> nao entrega previsao; pede o follow e convida a mandar
    o bairro de novo.
  - API falhou      -> trata como seguidor. Nunca bloquear por erro nosso.

A memoria da cortesia (_cortesia_gasta) vive no processo. No plano Free do
Render ela zera quando o servico dorme ou reimplanta — ou seja, de tempos em
tempos um nao-seguidor ganha outra resposta gratis. Aceitavel: o custo e zero
e o comportamento continua empurrando para o follow. Se um dia precisar de
memoria de verdade, um Redis gratis resolve; nao complique antes disso.
"""

import os
import threading
import time

import requests
from flask import Flask, request

from resposta import montar_resposta, MSG_SIGA
from recomendar_roupa import recomendar_roupa
import dados  # expoe previsao_hoje() -> {cidade: {tmin,tmax,...,tmin_amanha,...}}

app = Flask(__name__)

VERIFY = os.environ["IG_VERIFY_TOKEN"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
GRAPH = "https://graph.instagram.com/v22.0/me/messages"
GRAPH_PERFIL = "https://graph.instagram.com/v22.0"

# IGSIDs de nao-seguidores que ja receberam a resposta de cortesia.
_cortesia_gasta: set[str] = set()

# Cache curto do status de follow, para nao consultar a API duas vezes na
# mesma conversa (ex.: pessoa manda "Centro", robo pergunta a cidade, pessoa
# responde "Resende" — duas mensagens em um minuto).
_follow_cache: dict[str, tuple[float, bool]] = {}
_FOLLOW_TTL = 10 * 60


@app.get("/ping")
def ping():
    return "ok", 200


@app.get("/webhook")
def verificar():
    """O Meta chama isso uma vez, na hora de cadastrar o webhook."""
    if request.args.get("hub.verify_token") == VERIFY:
        return request.args.get("hub.challenge", ""), 200
    return "token invalido", 403


@app.post("/webhook")
def receber():
    """O Meta reenvia a mensagem se demorarmos a responder, entao devolvemos
    200 na hora e processamos numa thread separada."""
    corpo = request.get_json(silent=True) or {}
    threading.Thread(target=_processar, args=(corpo,), daemon=True).start()
    return "ok", 200


def _segue_perfil(uid: str):
    """True/False se deu para saber; None se a API nao respondeu.

    O campo is_user_follow_business so existe depois que a pessoa mandou
    mensagem para a conta — que e exatamente o nosso caso aqui.
    """
    agora = time.time()
    em_cache = _follow_cache.get(uid)
    if em_cache and agora - em_cache[0] < _FOLLOW_TTL:
        return em_cache[1]
    try:
        r = requests.get(
            f"{GRAPH_PERFIL}/{uid}",
            params={"fields": "is_user_follow_business",
                    "access_token": TOKEN},
            timeout=10,
        )
        if r.status_code >= 400:
            print(f"[webhook] perfil {uid} indisponivel "
                  f"({r.status_code}): {r.text[:200]}")
            return None
        segue = bool(r.json().get("is_user_follow_business"))
        _follow_cache[uid] = (agora, segue)
        return segue
    except requests.RequestException as exc:
        print(f"[webhook] erro de rede ao checar follow: {exc}")
        return None


def _processar(corpo: dict) -> None:
    try:
        previsao = dados.previsao_hoje()
    except Exception as exc:                      # nao derruba o servico
        print(f"[webhook] falha ao coletar previsao: {exc}")
        return

    for entrada in corpo.get("entry", []):
        for evento in entrada.get("messaging", []):
            # Ignora o eco das nossas proprias mensagens, senao o bot
            # conversa sozinho em loop.
            if evento.get("message", {}).get("is_echo"):
                continue
            texto = evento.get("message", {}).get("text", "")
            destino = evento.get("sender", {}).get("id")
            if not texto or not destino:
                continue

            segue = _segue_perfil(destino)

            # Nao segue e ja gastou a cortesia: pede o follow e para por ai.
            if segue is False and destino in _cortesia_gasta:
                _enviar(destino, MSG_SIGA)
                continue

            resposta, deu_previsao = montar_resposta(
                texto, previsao, segue, recomendar_roupa)
            _enviar(destino, resposta)

            # A cortesia so conta quando a previsao foi entregue de verdade —
            # pergunta de desambiguacao ("qual cidade?") nao gasta a vez.
            if segue is False and deu_previsao:
                _cortesia_gasta.add(destino)


def _enviar(uid: str, texto: str) -> None:
    try:
        r = requests.post(
            GRAPH,
            params={"access_token": TOKEN},
            json={"recipient": {"id": uid}, "message": {"text": texto}},
            timeout=15,
        )
        if r.status_code >= 400:
            print(f"[webhook] Instagram recusou ({r.status_code}): {r.text[:300]}")
    except requests.RequestException as exc:
        print(f"[webhook] erro de rede ao responder: {exc}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
