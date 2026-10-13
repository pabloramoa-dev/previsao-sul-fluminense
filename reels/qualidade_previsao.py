"""Portão de qualidade técnico: nunca inventa afirmações sobre acerto da previsão.

Conferência geométrica de texto/imagens requer render no navegador; aqui são
inspecionados plano, narração, continuidade e metadados do MP4.
"""
from __future__ import annotations
import json
from pathlib import Path


def verificar(batidas, segs, plano, probe):
    erros, alertas = [], []
    if len(batidas) != len(segs) or len(plano) != len(segs) or not batidas:
        erros.append("quantidade de batidas, segmentos e plano divergente")
    for i, (b, s) in enumerate(zip(batidas, segs)):
        if not str(b.get("fala", "")).strip():
            erros.append(f"batida {i}: fala vazia")
        if "legenda" in b and not str(b["legenda"]).strip():
            erros.append(f"batida {i}: legenda vazia")
        if i and float(s["ini"]) < float(segs[i-1]["fim"]) - .002:
            erros.append(f"batida {i}: intervalos sobrepostos")
        if b.get("tipo") == "resumo" and len(str(b["fala"]).split()) > 75:
            alertas.append(f"resumo {i}: muito texto; revisar legibilidade")
    streams = probe.get("streams") or []
    if not any(s.get("codec_type") == "video" for s in streams):
        erros.append("arquivo sem vídeo")
    if not any(s.get("codec_type") == "audio" for s in streams):
        erros.append("arquivo sem áudio")
    if not plano or len({p["gesto"] for p in plano}) == 1:
        alertas.append("pouca variedade de gestos")
    return {
        "aprovado_tecnicamente": not erros,
        "erros": erros, "alertas": alertas,
        "total_batidas": len(batidas),
        "gestos": sorted({p["gesto"] for p in plano}),
        "checagens": ["batidas/timeline", "legenda não vazia", "MP4 com áudio e vídeo"],
        "aviso": "A validação técnica não atesta precisão meteorológica ou ausência de toda sobreposição visual.",
    }


def gravar(caminho, dados):
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
