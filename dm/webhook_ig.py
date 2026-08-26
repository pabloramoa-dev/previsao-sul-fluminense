# -*- coding: utf-8 -*-
"""Webhook de DM: previsao por bairro e radar meteorologico colaborativo."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import threading
import time

import requests
from flask import Flask, jsonify, request

import dados
import radar
from dm_bairro import resolver
from interacao import comando, condicao_simples, relato
from recomendar_roupa import recomendar_roupa
from resposta import MSG_SIGA, montar_resposta

app = Flask(__name__)

VERIFY = os.environ["IG_VERIFY_TOKEN"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
APP_SECRET = os.environ.get("META_APP_SECRET", "")
GRAPH = "https://graph.instagram.com/v22.0/me/messages"
GRAPH_PERFIL = "https://graph.instagram.com/v22.0"
USUARIO_PERFIL = os.environ.get("IG_USERNAME", "previsaosulflu").casefold()
INICIO = time.time()

_cortesia_gasta: set[str] = set()
_follow_cache: dict[str, tuple[float, bool]] = {}
_FOLLOW_TTL = 10 * 60
_assinatura_comentarios_feita = False
_trava_assinatura = threading.Lock()
_diag_lock = threading.Lock()
_diag = {
    "webhooks": 0,
    "eventos_comentario": 0,
    "pedidos_reconhecidos": 0,
    "dm_enviadas": 0,
    "respostas_publicas": 0,
    "ultimo_estagio": "aguardando_evento",
    "ultimo_http_meta": None,
}


def _diagnosticar(estagio: str, **valores) -> None:
    with _diag_lock:
        _diag["ultimo_estagio"] = estagio
        for chave, valor in valores.items():
            _diag[chave] = valor


@app.get("/ping")
def ping():
    _assinar_comentarios()
    return jsonify({
        "status": "ok",
        "uptime_s": int(time.time() - INICIO),
        "radar": radar.status(),
        "assinatura_meta": bool(APP_SECRET),
        "comentarios": "habilitados" if _assinatura_comentarios_feita else "pendente",
    }), 200


@app.get("/diagnostico-comentarios")
def diagnostico_comentarios():
    """Telemetria sem textos, IDs de usuarios ou credenciais."""
    with _diag_lock:
        estado = dict(_diag)
    estado["assinatura_comments"] = _assinatura_comentarios_feita
    return jsonify(estado), 200


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


def _assinar_comentarios() -> None:
    """Garante que a conta envie eventos de comentarios para este webhook."""
    global _assinatura_comentarios_feita
    if _assinatura_comentarios_feita:
        return
    with _trava_assinatura:
        if _assinatura_comentarios_feita:
            return
        try:
            r = requests.post(
                f"{GRAPH_PERFIL}/me/subscribed_apps",
                params={
                    "subscribed_fields": "comments,messages",
                    "access_token": TOKEN,
                },
                timeout=15,
            )
            if r.status_code >= 400:
                print(f"[webhook] assinatura de comentarios recusada "
                      f"({r.status_code}): {r.text[:300]}")
                return
            _assinatura_comentarios_feita = bool(r.json().get("success", True))
            print("[webhook] comentarios assinados na Meta")
        except requests.RequestException as exc:
            print(f"[webhook] erro ao assinar comentarios: {exc}")


@app.post("/webhook")
def receber():
    bruto = request.get_data(cache=True)
    if not _assinatura_valida(bruto):
        return "assinatura invalida", 403
    corpo = request.get_json(silent=True) or {}
    with _diag_lock:
        _diag["webhooks"] += 1
        _diag["ultimo_estagio"] = "webhook_recebido"
    _assinar_comentarios()
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
        for valor in _comentarios_da_entrada(entrada):
            _processar_comentario(valor, str(entrada.get("id", "")))
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

            condicao_curta = condicao_simples(texto)
            contexto = radar.obter_contexto(destino) if condicao_curta else None
            if condicao_curta and contexto:
                cidade, bairro = contexto
                novo = radar.registrar(
                    mid, destino, cidade, bairro, condicao_curta)
                if novo:
                    _enviar(
                        destino,
                        "✅ Obrigado! Seu relato entrou no radar colaborativo "
                        f"de {cidade}.\n" + radar.resumo(cidade))
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
            if deu_previsao:
                situacao, cidade, rotulo = resolver(texto_previsao)
                if situacao == "cidade":
                    bairro = str(rotulo).split(" (", 1)[0]
                    radar.guardar_contexto(destino, cidade, bairro)
                    resposta += (
                        f"\n\nE como está o tempo em {bairro} agora? "
                        "Responda apenas: CHUVA, GAROA, NUBLADO, SOL ou VENTO.")
            _enviar(destino, resposta)
            if segue is False and deu_previsao:
                _cortesia_gasta.add(destino)


def _comentarios_da_entrada(entrada: dict):
    """Aceita os dois formatos de webhook usados pela Meta.

    Instagram Login envia field/value diretamente em entry. Integracoes mais
    antigas do Graph API encapsulam o mesmo conteudo dentro de changes[].
    """
    if entrada.get("field") in {"comments", "live_comments"}:
        valor = entrada.get("value")
        if isinstance(valor, dict):
            yield valor
    for alteracao in entrada.get("changes", []):
        if alteracao.get("field") not in {"comments", "live_comments"}:
            continue
        valor = alteracao.get("value")
        if isinstance(valor, dict):
            yield valor


def _limpar_pedido_comentario(texto: str) -> str:
    texto = re.sub(r"@previsaosulflu\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(
        r"^\s*(?:previs[aã]o|tempo|clima)(?:\s+(?:para|de|do|da|em))?\s*[:\-]?\s*",
        "", texto, flags=re.IGNORECASE)
    return texto.strip()


def _processar_comentario(valor: dict, id_perfil: str) -> None:
    """Envia a previsao por DM e confirma de forma curta no comentario."""
    comentario_id = str(valor.get("id") or "")
    with _diag_lock:
        _diag["eventos_comentario"] += 1
        _diag["ultimo_estagio"] = "comentario_recebido"
    texto = _limpar_pedido_comentario(str(valor.get("text") or ""))
    autor = valor.get("from") or {}
    autor_id = str(autor.get("id") or "")
    username = str(autor.get("username") or "").casefold()
    if (not comentario_id or not texto or autor_id == id_perfil
            or username == USUARIO_PERFIL):
        return

    situacao, _, _ = resolver(texto)
    if situacao not in {"cidade", "ambiguo"}:
        _diagnosticar("localidade_nao_reconhecida")
        return
    if not radar.marcar_evento(f"comentario:{comentario_id}"):
        _diagnosticar("comentario_duplicado")
        return
    with _diag_lock:
        _diag["pedidos_reconhecidos"] += 1
        _diag["ultimo_estagio"] = "pedido_reconhecido"

    try:
        previsao = dados.previsao_hoje()
        resposta, _ = montar_resposta(
            texto, previsao, True, recomendar_roupa)
    except Exception as exc:
        print(f"[webhook] falha na previsao do comentario: {exc}")
        resposta = "A previsão está temporariamente indisponível. Tente novamente em alguns minutos."
    if _enviar_previsao_privada(comentario_id, resposta):
        _responder_comentario(
            comentario_id,
            "📩 Te enviei a previsão na DM. Dá uma olhadinha! 🌦️")


def _enviar_previsao_privada(comentario_id: str, texto: str) -> bool:
    """Usa Private Reply da Instagram Login API via /me/messages."""
    try:
        r = requests.post(
            GRAPH,
            params={"access_token": TOKEN},
            json={
                "recipient": {"comment_id": comentario_id},
                "message": {"text": texto[:1000]},
            },
            timeout=15,
        )
        if r.status_code >= 400:
            _diagnosticar("dm_recusada", ultimo_http_meta=r.status_code)
            print(f"[webhook] DM privada recusada ({r.status_code}): "
                  f"{r.text[:300]}")
            return False
        print(f"[webhook] previsao enviada por DM: {comentario_id}")
        with _diag_lock:
            _diag["dm_enviadas"] += 1
            _diag["ultimo_estagio"] = "dm_enviada"
            _diag["ultimo_http_meta"] = r.status_code
        return True
    except requests.RequestException as exc:
        _diagnosticar("erro_rede_dm", ultimo_http_meta=None)
        print(f"[webhook] erro ao enviar DM privada: {exc}")
        return False


def _responder_comentario(comentario_id: str, texto: str) -> bool:
    try:
        r = requests.post(
            f"{GRAPH_PERFIL}/{comentario_id}/replies",
            params={"access_token": TOKEN},
            data={"message": texto[:2200]},
            timeout=15,
        )
        if r.status_code >= 400:
            _diagnosticar("comentario_publico_recusado", ultimo_http_meta=r.status_code)
            print(f"[webhook] resposta ao comentario recusada "
                  f"({r.status_code}): {r.text[:300]}")
            return False
        print(f"[webhook] comentario respondido: {comentario_id}")
        with _diag_lock:
            _diag["respostas_publicas"] += 1
            _diag["ultimo_estagio"] = "fluxo_concluido"
            _diag["ultimo_http_meta"] = r.status_code
        return True
    except requests.RequestException as exc:
        _diagnosticar("erro_rede_comentario", ultimo_http_meta=None)
        print(f"[webhook] erro ao responder comentario: {exc}")
        return False


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
