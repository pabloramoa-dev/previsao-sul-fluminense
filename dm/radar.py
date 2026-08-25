# -*- coding: utf-8 -*-
"""Persistencia do radar colaborativo. Usa Postgres; cai para memoria se indisponivel."""
from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timedelta, timezone
import hashlib
import os
import threading

_MEMORIA = deque(maxlen=1000)
_EVENTOS = set()
_LOCK = threading.Lock()
_URL = os.environ.get("DATABASE_URL", "")
_DB_OK = False


def _hash(uid: str) -> str:
    sal = os.environ.get("RADAR_HASH_SALT", "previsaosulflu")
    return hashlib.sha256(f"{sal}:{uid}".encode()).hexdigest()[:20]


def _conectar():
    if not _URL:
        return None
    import psycopg
    return psycopg.connect(_URL, connect_timeout=5)


def inicializar() -> bool:
    global _DB_OK
    if not _URL:
        return False
    try:
        with _conectar() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS relatos (
                id BIGSERIAL PRIMARY KEY,
                message_id TEXT UNIQUE NOT NULL,
                user_hash TEXT NOT NULL,
                cidade TEXT NOT NULL,
                bairro TEXT NOT NULL,
                condicao TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""")
            con.execute("CREATE INDEX IF NOT EXISTS relatos_cidade_data ON relatos (cidade, created_at DESC)")
        _DB_OK = True
    except Exception as exc:
        _DB_OK = False
        print(f"[radar] Postgres indisponivel; usando memoria: {exc}")
    return _DB_OK


def registrar(message_id: str, uid: str, cidade: str, bairro: str, condicao: str) -> bool:
    """Registra uma vez por message_id. Guarda apenas hash do usuario."""
    if _DB_OK or inicializar():
        try:
            with _conectar() as con:
                cur = con.execute(
                    """INSERT INTO relatos(message_id,user_hash,cidade,bairro,condicao)
                       VALUES (%s,%s,%s,%s,%s) ON CONFLICT(message_id) DO NOTHING""",
                    (message_id, _hash(uid), cidade, bairro, condicao),
                )
                return cur.rowcount == 1
        except Exception as exc:
            print(f"[radar] falha ao gravar; usando memoria: {exc}")

    with _LOCK:
        if message_id in _EVENTOS:
            return False
        _EVENTOS.add(message_id)
        _MEMORIA.append({
            "cidade": cidade, "bairro": bairro, "condicao": condicao,
            "created_at": datetime.now(timezone.utc), "user_hash": _hash(uid),
        })
        return True


def resumo(cidade: str | None = None, horas: int = 3) -> str:
    desde = datetime.now(timezone.utc) - timedelta(hours=horas)
    linhas = []
    if _DB_OK or inicializar():
        try:
            with _conectar() as con:
                if cidade:
                    linhas = con.execute(
                        """SELECT bairro,condicao,COUNT(*) FROM relatos
                           WHERE created_at >= %s AND cidade=%s
                           GROUP BY bairro,condicao ORDER BY COUNT(*) DESC LIMIT 6""",
                        (desde, cidade)).fetchall()
                else:
                    linhas = con.execute(
                        """SELECT cidade,condicao,COUNT(*) FROM relatos
                           WHERE created_at >= %s GROUP BY cidade,condicao
                           ORDER BY COUNT(*) DESC LIMIT 6""", (desde,)).fetchall()
        except Exception as exc:
            print(f"[radar] falha ao consultar; usando memoria: {exc}")

    if not linhas:
        with _LOCK:
            recentes = [r for r in _MEMORIA if r["created_at"] >= desde
                        and (not cidade or r["cidade"] == cidade)]
        chave = (lambda r: (r["bairro"], r["condicao"])) if cidade else (
            lambda r: (r["cidade"], r["condicao"]))
        linhas = [(a, b, n) for (a, b), n in Counter(chave(r) for r in recentes).most_common(6)]

    titulo = f"📡 Radar colaborativo — últimas {horas}h"
    if cidade:
        titulo += f" em {cidade}"
    if not linhas:
        return titulo + "\nAinda não há relatos. Envie: BAIRRO + CHUVA, SOL, VENTO ou NUBLADO."
    itens = "\n".join(f"• {lugar}: {condicao} ({qtd})" for lugar, condicao, qtd in linhas)
    return titulo + "\n" + itens + "\nRelatos da comunidade; confirme alertas nos canais oficiais."


def status() -> dict:
    return {"database": "ok" if _DB_OK else ("configurado" if _URL else "memoria"),
            "relatos_em_memoria": len(_MEMORIA)}
