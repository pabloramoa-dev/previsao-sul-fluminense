# -*- coding: utf-8 -*-
"""Interpreta comandos e relatos meteorologicos recebidos por DM."""
from __future__ import annotations

import re
import unicodedata

from dm_bairro import resolver

CONDICOES = {
    "chuva": "chuva", "chovendo": "chuva", "garoa": "garoa",
    "sol": "sol", "ensolarado": "sol", "nublado": "nublado",
    "nuvens": "nublado", "vento": "vento", "ventando": "vento",
    "neblina": "neblina", "granizo": "granizo",
}
COMANDOS = {"radar", "hoje", "amanha", "ajuda"}


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().strip().split())


def comando(texto: str) -> tuple[str | None, str]:
    """Retorna (comando, argumento)."""
    partes = _norm(texto).split(maxsplit=1)
    if partes and partes[0] in COMANDOS:
        return partes[0], partes[1] if len(partes) > 1 else ""
    return None, ""


def condicao_simples(texto: str) -> str | None:
    """Aceita somente uma condicao, com pequenas variacoes naturais."""
    tokens = re.findall(r"[a-z0-9]+", _norm(texto))
    relevantes = [CONDICOES[t] for t in tokens if t in CONDICOES]
    extras = [t for t in tokens if t not in CONDICOES
              and t not in {"esta", "ta", "aqui", "agora", "sim", "nao"}]
    if len(relevantes) == 1 and not extras:
        return relevantes[0]
    return None


def relato(texto: str) -> tuple[str, object, object, str] | None:
    """Extrai local e condicao: 'Retiro chuva' ou 'chuva no Retiro'."""
    normal = _norm(texto)
    tokens = re.findall(r"[a-z0-9]+", normal)
    condicao = next((CONDICOES[t] for t in tokens if t in CONDICOES), None)
    if not condicao:
        return None

    local = normal
    for token in CONDICOES:
        local = re.sub(rf"\b{re.escape(token)}\b", " ", local)
    local = re.sub(r"\b(no|na|em|agora|aqui|esta|ta)\b", " ", local)
    local = " ".join(local.split())
    if not local:
        return None

    situacao, dado, rotulo = resolver(local)
    return situacao, dado, rotulo, condicao
