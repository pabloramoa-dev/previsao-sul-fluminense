# -*- coding: utf-8 -*-
"""Webhook de DM: previsao por bairro e radar meteorologico colaborativo."""
from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time

import requests
from flask import Flask, jsonify, request

import dados
import radar
from dm_bairro import resolver
from interacao import comando, relato
from recomendar_roupa import recomendar_roupa
from resposta import MSG_SIGA, montar_resposta

app = Flask(__name__)

VERIFY = os.environ["IG_VERIFY_TOKEN"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
APP_SECRET = os.environ.get("META_APP_SECRET", "")
GRAPH = "https://graph.instagram.com/v22.0/me/messages"
GRAPH_PERFIL = "https://graph.instagram.com/v22.0"
INICIO = time.time()

_cortesia_gasta: set[str] = set()
_follow_cache: dict[str, tuple[float, bool]] = {}
_FOLLOW_TTL = 10 * 60


@app.get("/ping")
def ping():
    return jsonify({
        "status": "ok",
        "uptime_s": int(time.time() - INICIO),
        "radar": radar.status(),
        "assinatura_meta": bool(APP_SECRET),
    }), 200


@app.get("/webhook")
def verificar():
    if request.args.get("hub.verify_token") == VERIFY:
        return request.args.get("hub.challenge", ""), 200
    return "token invalido", 403


def _assinatura_valida(corpo: bytes) -> bool:
    if not APP_SECRET:
        return True
    recebida = request.headers.get("X-Hub-Signature-256", "")
    esperada = "sha256=" + hmac.new(
        APP_SECRET.encode(), corpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(recebida, esperada)


@app.post("/webhook")
def receber():
    bruto = request.get_data(cache=True)
    if not _assinatura_valida(bruto):
        return "assinatura invalida", 403
    corpo = request.get_json(silent=True) or {}
    threading.Thread(target=_processar, args=(corpo,), daemon=True).start()
    return "ok", 200


def _segue_perfil(uid: str):
    agora = time.time()
    em_cache = _follow_cache.get(uid)
    if em_cache and agora - em_cache[0] < _FOLLOW_TTL:
        return em_cache[1]
    try:
        r = requests.get(
            f"{GRAPH_PERFIL}/{uid}",
            params={"fields": "is_user_follow_business", "access_token": TOKEN},
            timeout=10,
        )
        if r.status_code >= 400:
            print(f"[webhook] perfil indisponivel ({r.status_code}): {r.text[:200]}")
            return None
        segue = bool(r.json().get("is_user_follow_business"))
        _follow_cache[uid] = (agora, segue)
        return segue
    except requests.RequestException as exc:
        print(f"[webhook] erro ao checar follow: {exc}")
        return None


def _cidade_do_argumento(argumento: str):
    if not argumento:
        return None, None
    situacao, dado, rotulo = resolver(argumento)
    if situacao == "cidade":
        return dado, None
    if situacao == "ambiguo":
        return None, f"Qual cidade? {', '.join(dado)}."
    return None, "Não reconheci a cidade. Envie RADAR + nome da cidade."


def _processar(corpo: dict) -> None:
    previsao = None
    for entrada in corpo.get("entry", []):
        for evento in entrada.get("messaging", []):
            mensagem = evento.get("message", {})
            if mensagem.get("is_echo"):
                continue
            texto = mensagem.get("text", "").strip()
            destino = evento.get("sender", {}).get("id")
            mid = mensagem.get("mid") or f"{destino}:{evento.get('timestamp')}:{texto}"
            if not texto or not destino:
                continue

            cmd, argumento = comando(texto)
            if cmd == "ajuda":
                _enviar(destino, "Envie um BAIRRO para a previsão; BAIRRO + CHUVA/SOL/VENTO/NUBLADO para relatar; ou RADAR + CIDADE.")
                continue
            if cmd == "radar":
                cidade, erro = _cidade_do_argumento(argumento)
                _enviar(destino, erro or radar.resumo(cidade))
                continue

            extraido = relato(texto)
            if extraido:
                situacao, cidade, rotulo, condicao = extraido
                if situacao == "ambiguo":
                    _enviar(destino, f"Esse bairro existe em mais de uma cidade. Informe também a cidade: {', '.join(cidade)}.")
                elif situacao == "nao_achou":
                    _enviar(destino, "Não reconheci o bairro do relato. Envie BAIRRO + CIDADE + condição.")
                else:
                    bairro = str(rotulo).split(" (", 1)[0]
                    novo = radar.registrar(mid, destino, cidade, bairro, condicao)
                    if novo:
                        _enviar(destino, "✅ Relato recebido, obrigado!\n" + radar.resumo(cidade))
                continue

            texto_previsao = argumento if cmd in {"hoje", "amanha"} and argumento else texto
            segue = _segue_perfil(destino)
            if segue is False and destino in _cortesia_gasta:
                _enviar(destino, MSG_SIGA)
                continue

            if previsao is None:
                try:
                    previsao = dados.previsao_hoje()
                except Exception as exc:
                    print(f"[webhook] falha ao coletar previsao: {exc}")
                    _enviar(destino, "A previsão está temporariamente indisponível. Tente novamente em alguns minutos.")
                    continue

            resposta, deu_previsao = montar_resposta(
                texto_previsao, previsao, segue, recomendar_roupa)
            _enviar(destino, resposta)
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
        print(f"[webhook] erro ao responder: {exc}")


if __name__ == "__main__":
    radar.inicializar()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
