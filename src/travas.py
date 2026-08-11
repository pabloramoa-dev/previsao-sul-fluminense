# -*- coding: utf-8 -*-
"""
travas.py -- Travas de seguranca de publicacao (Fase 6, itens 6.2 e 6.3).

6.2 Nunca publicar sem legenda: legenda vazia/None/< MIN_CAPTION chars => erro.
6.3 Trava contra duplicata: registro em .publicado.json com hash+data+slot,
    mais um lock de execucao para impedir dois jobs simultaneos publicando.

Uso previsto em publicar.py, no inicio de cada publicar_*:
    from . import travas
    travas.validar_caption(caption)
    with travas.lock_execucao(slot):
        if travas.ja_publicado(data, slot, caption):
            raise travas.DuplicataError(...)
        ... publica ...
        travas.registrar_publicacao(data, slot, caption)
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

MIN_CAPTION = 40

REGISTRO_PATH = Path("assets/output/.publicado.json")
LOCK_PATH = Path("assets/output/.lock")
LOCK_TTL = 20 * 60  # segundos: lock velho e considerado morto


class LegendaInvalidaError(Exception):
    pass


class DuplicataError(Exception):
    pass


class LockError(Exception):
    pass


def validar_caption(caption):
    """6.2 -- falha alto e cedo se a legenda for vazia/curta demais."""
    if caption is None:
        raise LegendaInvalidaError("Legenda None: publicacao abortada.")
    texto = caption.strip()
    if not texto:
        raise LegendaInvalidaError("Legenda vazia: publicacao abortada.")
    if len(texto) < MIN_CAPTION:
        raise LegendaInvalidaError(
            f"Legenda com {len(texto)} chars (< {MIN_CAPTION}): abortado.")


def _hash_conteudo(data, slot, caption):
    base = f"{data}|{slot}|{caption.strip()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def _ler_registro():
    if REGISTRO_PATH.exists():
        try:
            return json.loads(REGISTRO_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def ja_publicado(data, slot, caption):
    """6.3 -- True se ja existe post com mesmo (data, slot, conteudo)."""
    reg = _ler_registro()
    return _hash_conteudo(data, slot, caption) in reg


def registrar_publicacao(data, slot, caption):
    REGISTRO_PATH.parent.mkdir(parents=True, exist_ok=True)
    reg = _ler_registro()
    reg[_hash_conteudo(data, slot, caption)] = {
        "data": data, "slot": slot, "quando": int(time.time()),
    }
    REGISTRO_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2),
                             encoding="utf-8")


@contextmanager
def lock_execucao(slot):
    """6.3 -- lock simples baseado em arquivo para impedir execucao dupla."""
    REGISTRO_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        idade = time.time() - LOCK_PATH.stat().st_mtime
        if idade < LOCK_TTL:
            raise LockError(
                f"Lock ativo ({idade:.0f}s) para slot={slot}. Outro job publicando?")
    LOCK_PATH.write_text(f"{slot}:{os.getpid()}:{int(time.time())}",
                         encoding="utf-8")
    try:
        yield
    finally:
        try:
            LOCK_PATH.unlink()
        except FileNotFoundError:
            pass


def _sanity():
    ok = False
    try:
        validar_caption("")
    except LegendaInvalidaError:
        ok = True
    assert ok, "validar_caption deveria falhar em legenda vazia"
    assert _hash_conteudo("2026-08-09", "manha", "abc") != _hash_conteudo("2026-08-09", "noite", "abc")


_sanity()
