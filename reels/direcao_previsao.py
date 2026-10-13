"""Direção gratuita dos personagens do Sul Fluminense.

A fala e os dados da previsão NÃO são modificados: só a linguagem corporal,
os enquadramentos e um plano de edição auditável. Não usa nenhuma API.
"""
from __future__ import annotations
import math
import os
import re

GESTOS = ("repouso", "explicar", "apontar", "enfatizar", "alertar", "acolher", "perguntar")
DESLOCAMENTOS = {
    "repouso": (0.0, 0.0),
    "explicar": (-0.18, 0.15),
    "apontar": (-0.26, 0.34),
    "enfatizar": (-0.32, 0.29),
    "alertar": (-0.34, 0.39),
    "acolher": (-0.16, 0.13),
    "perguntar": (-0.26, 0.23),
}


def ativo() -> bool:
    return os.environ.get("PREVISAO_DIRECAO", "1").strip().lower() not in ("0", "false", "nao", "não")


def gesto_da_fala(b: dict, indice: int, personagem: str) -> str:
    custom = str(b.get("gesto") or "").lower()
    if custom in GESTOS:
        return custom
    tipo = str(b.get("tipo") or "nenhum")
    fala = str(b.get("fala") or "")
    dados = b.get("dados") if isinstance(b.get("dados"), dict) else {}
    if tipo in ("alerta", "gancho") and (dados.get("cor") == "alerta" or "atenção" in fala.lower()):
        return "alertar"
    if tipo == "gancho":
        return "enfatizar"
    if tipo == "resumo":
        return "apontar"
    if tipo == "cta":
        return "perguntar" if "?" in fala else "acolher"
    if tipo in ("chuva", "frio", "calor", "sem_chuva"):
        return "explicar" if personagem == "maria" else "enfatizar"
    if "?" in fala:
        return "perguntar"
    if re.search(r"\b(cuidado|atenção|tempestade|alerta)\b", fala, re.I):
        return "alertar"
    return ("explicar", "repouso", "acolher")[indice % 3]


def planejar(batidas: list[dict], segmentos: list[dict], personagem="ranzinza") -> list[dict]:
    if not batidas or len(batidas) != len(segmentos):
        raise ValueError("Direção: número de batidas e segmentos diferente")
    anterior = -1.0
    plano = []
    for i, (b, s) in enumerate(zip(batidas, segmentos)):
        a, z = float(s["ini"]), float(s["fim"])
        if not math.isfinite(a) or not math.isfinite(z) or z <= a or a < anterior - .002:
            raise ValueError(f"Direção: timeline inválida na batida {i}")
        tipo = str(b.get("tipo") or "nenhum")
        gesto = gesto_da_fala(b, i, personagem)
        camera = ("aproximar" if tipo in ("gancho", "alerta") else
                  "abrir" if tipo == "resumo" else
                  "estabilizar" if tipo == "cta" else
                  "aproximar_suave" if gesto in ("alertar", "enfatizar") else "manter")
        # A personagem não pode tapar o painel com gestos largos. Movimento é limitado.
        plano.append({"i": i, "inicio": round(a, 3), "fim": round(z, 3),
                      "tipo": tipo, "gesto": gesto, "camera": camera,
                      "energia": .85 if personagem == "maria" else 1.0,
                      "personagem": personagem})
        anterior = z
    return plano


def deslocamento(gesto: str, tempo: float, inicio: float, fim: float, energia=1.0):
    if gesto not in DESLOCAMENTOS or not inicio <= tempo < fim:
        return (0., 0.)
    rampa = min(.34, (fim - inicio)/3.)
    if rampa <= 0:
        return (0., 0.)
    u = min(1.0, max(0.0, (tempo - inicio)/rampa), max(0.0, (fim - tempo)/rampa))
    peso = u*u*(3-2*u)
    pulso = 1.0 + 0.035 * math.sin(4*tempo)
    x, y = DESLOCAMENTOS[gesto]
    return (x*peso*energia*pulso, y*peso*energia*pulso)


def camera(item: dict):
    tipo = item["camera"]
    if tipo == "aproximar":
        return (1.065, 0)
    if tipo == "aproximar_suave":
        return (1.038, -7 if item["i"] % 2 else 7)
    if tipo in ("abrir", "estabilizar"):
        return (1., 0)
    return (1.015, -5 if item["i"] % 2 else 5)
