# -*- coding: utf-8 -*-
"""
publicar.py - Publicacao no Instagram via Graph API v22.0.

Suporta: carrossel (feed), imagem unica (alerta) e story.
Modo --dry-run gera tudo e loga o que faria, SEM publicar.

Credenciais lidas SOMENTE de variaveis de ambiente (GitHub Secrets):
- IG_ACCESS_TOKEN : token de longa duracao (~60 dias)
- IG_USER_ID      : ID da conta Instagram (default 27148485038175)

As imagens precisam estar acessiveis por URL publica (raw do repo).
Configure RAW_BASE_URL apontando para assets/output no branch principal.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
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


class PublicacaoError(Exception):
    pass


def _url_publica(caminho_local: str) -> str:
    nome = caminho_local.replace("\\", "/").split("/")[-1]
    return f"{RAW_BASE_URL}/{nome}"


def _checar_credenciais() -> None:
    if not IG_ACCESS_TOKEN:
        raise PublicacaoError(
            "IG_ACCESS_TOKEN ausente. Configure o GitHub Secret antes de publicar.")


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


def publicar_carrossel(caminhos: list[str], caption: str,
                       dry_run: bool = False) -> dict[str, Any] | None:
    urls = [_url_publica(c) for c in caminhos]
    if dry_run:
        print("[DRY-RUN] Carrossel com", len(urls), "slides:")
        for u in urls:
            print("   -", u)
        print("[DRY-RUN] Caption:\n", caption)
        return None

    _checar_credenciais()
    children = [_criar_item_carrossel(u) for u in urls]
    for cid in children:
        _aguardar_pronto(cid)
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


def publicar_imagem(caminho: str, caption: str,
                    dry_run: bool = False) -> dict[str, Any] | None:
    url = _url_publica(caminho)
    if dry_run:
        print("[DRY-RUN] Imagem unica:", url)
        print("[DRY-RUN] Caption:\n", caption)
        return None

    _checar_credenciais()
    container = _post(f"{IG_USER_ID}/media", {"image_url": url, "caption": caption})
    _aguardar_pronto(container["id"])
    resultado = _post(f"{IG_USER_ID}/media_publish", {"creation_id": container["id"]})
    print("[OK] Imagem publicada:", resultado)
    return resultado


def publicar_story(caminho: str, dry_run: bool = False) -> dict[str, Any] | None:
    url = _url_publica(caminho)
    if dry_run:
        print("[DRY-RUN] Story:", url)
        return None

    _checar_credenciais()
    container = _post(f"{IG_USER_ID}/media", {"image_url": url, "media_type": "STORIES"})
    _aguardar_pronto(container["id"])
    resultado = _post(f"{IG_USER_ID}/media_publish", {"creation_id": container["id"]})
    print("[OK] Story publicado:", resultado)
    return resultado


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
