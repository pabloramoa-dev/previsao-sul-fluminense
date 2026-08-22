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
"""

import os
import threading

import requests
from flask import Flask, request

from dm_bairro import montar_resposta_dm
from recomendar_roupa import recomendar_roupa
import dados  # precisa expor previsao_hoje() -> {cidade: {tmin,tmax,prob_chuva,...}}

app = Flask(__name__)

VERIFY = os.environ["IG_VERIFY_TOKEN"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
GRAPH = "https://graph.instagram.com/v22.0/me/messages"


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
            resposta = montar_resposta_dm(texto, previsao, recomendar_roupa)
            _enviar(destino, resposta)


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
