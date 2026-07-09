# -*- coding: utf-8 -*-
"""
publicar.py - Publicacao no Instagram via Graph API v22.0.

Suporta: carrossel (feed), imagem unica (alerta) e story.
Modo --dry-run gera tudo e loga o que faria, SEM publicar.

Fases (via env PUBLICAR_FASE):
- "completo" (default): gera E publica na mesma execucao (uso local/dry-run).
- "gerar": NAO publica; enfileira os itens (paths + caption + tipo) em
  assets/output/_fila_publicacao.json. A fila e ZERADA no inicio do processo.
  As imagens ja foram salvas pela etapa de geracao. O workflow deve
  commitar/pushar assets/output ANTES de publicar.
- "publicar": ignora geracao; le a fila e publica os itens ja pushados,
  garantindo que as URLs raw do GitHub estejam acessiveis.

Credenciais lidas SOMENTE de variaveis de ambiente (GitHub Secrets):
- IG_ACCESS_TOKEN : token de longa duracao (~60 dias)
- IG_USER_ID      : ID da conta Instagram (default 27148485038175)

As imagens precisam estar acessiveis por URL publica (raw do repo).
Configure RAW_BASE_URL apontando para assets/output no branch principal.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

API_VERSION = "v22.0"
GRAPH = f"https://graph.instagram.com/{API_VERSION}"
TIMEOUT = 60

IG_USER_ID = os.environ.get("IG_USER_ID", "27148485038175")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")

# Ex.: https://raw.githubusercontent.com/pabloramoa-dev/previsao-sul-fluminense/main/assets/output
RAW_BASE_URL = os.environ.get(
    "RAW_BASE_URL",
    "https://raw.githubusercontent.com/pabloramoa-dev/previsao-sul-fluminense/main/assets/output",
)

# Fase de execucao: completo | gerar | publicar
FASE = os.environ.get("PUBLICAR_FASE", "completo").strip().lower()

# Arquivo de fila usado para desacoplar geracao de publicacao.
FILA_PATH = Path("assets/output/_fila_publicacao.json")


class PublicacaoError(Exception):
    pass


def _url_publica(caminho_local: str) -> str:
    nome = caminho_local.replace("\\", "/").split("/")[-1]
    return f"{RAW_BASE_URL}/{nome}"


def _checar_credenciais() -> None:
    if not IG_ACCESS_TOKEN:
        raise PublicacaoError(
            "IG_ACCESS_TOKEN ausente. Configure o GitHub Secret antes de publicar.")


# ----------------------- FILA (fases gerar/publicar) -----------------------

def _reset_fila() -> None:
    FILA_PATH.parent.mkdir(parents=True, exist_ok=True)
    FILA_PATH.write_text("[]", encoding="utf-8")


def _enfileirar(item: dict[str, Any]) -> None:
    FILA_PATH.parent.mkdir(parents=True, exist_ok=True)
    fila: list[dict[str, Any]] = []
    if FILA_PATH.exists():
        try:
            fila = json.loads(FILA_PATH.read_text(encoding="utf-8"))
        except Exception:
            fila = []
    fila.append(item)
    FILA_PATH.write_text(json.dumps(fila, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[FILA] Enfileirado tipo={item['tipo']} ({len(item.get('caminhos', []))} img)")


def publicar_fila() -> None:
    """Le assets/output/_fila_publicacao.json e publica cada item (fase 'publicar')."""
    if not FILA_PATH.exists():
        raise PublicacaoError(f"Fila nao encontrada em {FILA_PATH}. Rode a fase 'gerar' antes.")
    fila = json.loads(FILA_PATH.read_text(encoding="utf-8"))
    if not fila:
        print("[FILA] Vazia, nada a publicar.")
        return
    _checar_credenciais()
    for item in fila:
        tipo = item["tipo"]
        if tipo == "carrossel":
            _publicar_carrossel_real(item["caminhos"], item["caption"])
        elif tipo == "imagem":
            _publicar_imagem_real(item["caminhos"][0], item["caption"])
        elif tipo == "story":
            _publicar_story_real(item["caminhos"][0])
        else:
            raise PublicacaoError(f"Tipo desconhecido na fila: {tipo}")
    print(f"[FILA] {len(fila)} item(ns) publicado(s) com sucesso.")


def _post(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    params = dict(params)
    params["access_token"] = IG_ACCESS_TOKEN
    resp = requests.post(f"{GRAPH}/{endpoint}", data=params, timeout=TIMEOUT)
    if resp.status_code >= 400:
        raise PublicacaoError(f"Graph API {resp.status_code}: {resp.text}")
    return resp.json()


def _criar_item_carrossel(url_imagem: str) -> str:
    r = _post(f"{IG_USER_ID}/media", {
        "image_url": url_imagem,
        "is_carousel_item": "true",
    })
    return r["id"]


def _aguardar_pronto(container_id: str, tentativas: int = 20) -> None:
    """Aguarda o container ficar FINISHED antes de publicar."""
    for _ in range(tentativas):
        r = requests.get(f"{GRAPH}/{container_id}", params={
            "fields": "status_code",
            "access_token": IG_ACCESS_TOKEN,
        }, timeout=TIMEOUT).json()
        status = r.get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise PublicacaoError(f"Container {container_id} deu ERROR")
        time.sleep(5)
    raise PublicacaoError(f"Container {container_id} nao ficou pronto a tempo")


# ----------------------- IMPLEMENTACOES REAIS -----------------------

def _publicar_carrossel_real(caminhos: list[str], caption: str) -> dict[str, Any]:
    urls = [_url_publica(c) for c in caminhos]
    children = [_criar_item_carrossel(u) for u in urls]
    container = _post(f"{IG_USER_ID}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": caption,
    })
    _aguardar_pronto(container["id"])
    resultado = _post(f"{IG_USER_ID}/media_publish", {
        "creation_id": container["id"],
    })
    print("[OK] Carrossel publicado:", resultado)
    return resultado


def _publicar_imagem_real(caminho: str, caption: str) -> dict[str, Any]:
    url = _url_publica(caminho)
    container = _post(f"{IG_USER_ID}/media", {"image_url": url, "caption": caption})
    _aguardar_pronto(container["id"])
    resultado = _post(f"{IG_USER_ID}/media_publish", {"creation_id": container["id"]})
    print("[OK] Imagem publicada:", resultado)
    return resultado


def _publicar_story_real(caminho: str) -> dict[str, Any]:
    url = _url_publica(caminho)
    container = _post(f"{IG_USER_ID}/media", {"image_url": url, "media_type": "STORIES"})
    _aguardar_pronto(container["id"])
    resultado = _post(f"{IG_USER_ID}/media_publish", {"creation_id": container["id"]})
    print("[OK] Story publicado:", resultado)
    return resultado


# ----------------------- API PUBLICA (usada por main.py) -----------------------

def publicar_carrossel(caminhos: list[str], caption: str,
                       dry_run: bool = False) -> dict[str, Any] | None:
    urls = [_url_publica(c) for c in caminhos]
    if dry_run:
        print("[DRY-RUN] Carrossel com", len(urls), "slides:")
        for u in urls:
            print("   -", u)
        print("[DRY-RUN] Caption:\n", caption)
        return None
    if FASE == "gerar":
        _enfileirar({"tipo": "carrossel", "caminhos": caminhos, "caption": caption})
        return None
    _checar_credenciais()
    return _publicar_carrossel_real(caminhos, caption)


def publicar_imagem(caminho: str, caption: str,
                    dry_run: bool = False) -> dict[str, Any] | None:
    url = _url_publica(caminho)
    if dry_run:
        print("[DRY-RUN] Imagem unica:", url)
        print("[DRY-RUN] Caption:\n", caption)
        return None
    if FASE == "gerar":
        _enfileirar({"tipo": "imagem", "caminhos": [caminho], "caption": caption})
        return None
    _checar_credenciais()
    return _publicar_imagem_real(caminho, caption)


def publicar_story(caminho: str, dry_run: bool = False) -> dict[str, Any] | None:
    url = _url_publica(caminho)
    if dry_run:
        print("[DRY-RUN] Story:", url)
        return None
    if FASE == "gerar":
        _enfileirar({"tipo": "story", "caminhos": [caminho], "caption": ""})
        return None
    _checar_credenciais()
    return _publicar_story_real(caminho)


# Ao iniciar a fase de geracao, zera a fila para nao acumular itens antigos.
if FASE == "gerar":
    _reset_fila()


def _cli() -> None:
    p = argparse.ArgumentParser(description="Publicacao Instagram Graph API")
    p.add_argument("--dry-run", action="store_true", help="nao publica, so simula")
    p.add_argument("--tipo", choices=["carrossel", "imagem", "story"], required=True)
    args = p.parse_args()
    print(f"Modo: {'DRY-RUN' if args.dry_run else 'PUBLICACAO REAL'} | tipo={args.tipo}")
    if not args.dry_run and not IG_ACCESS_TOKEN:
        print("ERRO: sem IG_ACCESS_TOKEN. Abortando publicacao real.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
