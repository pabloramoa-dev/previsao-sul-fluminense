# -*- coding: utf-8 -*-
"""
main.py - Orquestrador chamado pelos workflows do GitHub Actions.

Uso:
    python -m src.main manha       [--dry-run]
    python -m src.main noite       [--dry-run]
    python -m src.main alertas     [--dry-run]
    python -m src.main fim_semana  [--dry-run]
    python -m src.main curiosidade [--dry-run]

Cada modo: coleta dados -> gera imagens -> monta caption -> publica.
Em qualquer falha, loga claramente e sai com codigo != 0 (nunca post pela metade).
"""

from __future__ import annotations

import argparse
import sys
import traceback

from . import clima, historico, indices, perguntas, captions
from . import gerar_carrossel as gc
from . import gerar_story, publicar

def _fase_lua() -> str:
    try:
        from . import astronomia
        return astronomia.fase_da_lua().get("nome", "indisponivel")
    except Exception:
        return "indisponivel"


def _coletar():
    cidades = clima.coletar_todas()
    resumo = clima.resumo_regional(cidades)
    return cidades, resumo


def rodar_manha(dry_run: bool) -> None:
    cidades, resumo = _coletar()

    recorde = historico.checar_recorde(
        cidades[0].nome, cidades[0].tmin, cidades[0].tmax)

    umidade_media = sum(c.umidade for c in cidades) / len(cidades)
    aqi_regional = max(c.aqi for c in cidades)
    itens = indices.resumo_indices(resumo, umidade_media, aqi_regional)

    pergunta = perguntas.escolher_pergunta(resumo["tmax"], resumo["weathercode_pred"])
    fase = _fase_lua()

    caption = captions.caption_manha(
        resumo["data_extenso"], [c.como_dict() for c in cidades], pergunta)

    # Fase 6.1/6.6 -- gancho unico do slot (sem repetir os ultimos 10)
    gancho = ganchos.escolher_gancho("manha", resumo, cidades[0].nome)
    # Fase 6.7 -- conjunto de hashtags do slot (manha != noite no mesmo dia)
    condicao = ganchos.condicao_do_dado(resumo)
    tags = hashtags.escolher_conjunto("manha", condicao)
    caption = f"{gancho}\n\n{caption}\n\n{tags}"

    # Fase 6.2 -- legenda minima valida
    travas.validar_caption(caption)
"""
main.py - Orquestrador chamado pelos workflows do GitHub Actions.

Uso:
    python -m src.main manha       [--dry-run]
    python -m src.main noite       [--dry-run]
    python -m src.main alertas     [--dry-run]
    python -m src.main fim_semana  [--dry-run]
    python -m src.main curiosidade [--dry-run]

Cada modo: coleta dados -> gera imagens -> monta caption -> publica.
Em qualquer falha, loga claramente e sai com codigo != 0 (nunca post pela metade).
"""

from __future__ import annotations

import argparse
import sys
import traceback

from . import clima, historico, indices, perguntas, captions
from . import gerar_carrossel as gc
from . import gerar_story, publicar
# Fase 6 -- conversao e slot noturno
from . import ganchos, hashtags, varal, travas, slots_config

def _fase_lua() -> str:
    try:
        from . import astronomia
        return astronomia.fase_da_lua().get("nome", "indisponivel")
    except Exception:
        return "indisponivel"


def _coletar():
    cidades = clima.coletar_todas()
    resumo = clima.resumo_regional(cidades)
    return cidades, resumo


def rodar_manha(dry_run: bool) -> None:
    cidades, resumo = _coletar()

    recorde = historico.checar_recorde(
        cidades[0].nome, cidades[0].tmin, cidades[0].tmax)

    umidade_media = sum(c.umidade for c in cidades) / len(cidades)
    aqi_regional = max(c.aqi for c in cidades)
    itens = indices.resumo_indices(resumo, umidade_media, aqi_regional)

    pergunta = perguntas.escolher_pergunta(resumo["tmax"], resumo["weathercode_pred"])
    fase = _fase_lua()

    caption = captions.caption_manha(
        resumo["data_extenso"], [c.como_dict() for c in cidades], pergunta)

    # Fase 6.1/6.6 -- gancho unico do slot (sem repetir os ultimos 10)
    gancho = ganchos.escolher_gancho("manha", resumo, cidades[0].nome)
    # Fase 6.7 -- conjunto de hashtags do slot (manha != noite no mesmo dia)
    condicao = ganchos.condicao_do_dado(resumo)
    tags = hashtags.escolher_conjunto("manha", condicao)
    caption = f"{gancho}\n\n{caption}\n\n{tags}"

    # Fase 6.2 -- legenda minima valida
    travas.validar_caption(caption)

    # Fase 6.3 -- nao repetir o mesmo conteudo no mesmo dia/slot
    if travas.ja_publicado(resumo["data_extenso"], "manha", caption):
        print("[travas] conteudo ja publicado hoje no slot manha; abortando.")
        return

    # Fase 6.4 -- carrossel no feed desativado; manha vira story
    if slots_config.deve_gerar_carrossel_feed("manha"):
        slides = gc.gerar_carrossel_manha(
            cidades, resumo, itens, pergunta, fase, recorde)
        publicar.publicar_carrossel(slides, caption, dry_run=dry_run)

    a, b = gerar_story.dividir_opcoes(pergunta)
    story = gerar_story.gerar_story_card(pergunta, a, b, "manha")
    publicar.publicar_story(story, dry_run=dry_run)

    if not dry_run:
        travas.registrar_publicacao(resumo["data_extenso"], "manha", caption)

    historico.registrar_dia(cidades)


def rodar_noite(dry_run: bool) -> None:
    cidades, resumo = _coletar()
    pergunta = perguntas.escolher_pergunta(resumo["tmax"], resumo["weathercode_pred"])
    fase = _fase_lua()
    caption = captions.caption_noite(
        resumo["data_extenso"], [c.como_dict() for c in cidades], pergunta)

    # Fase 6.1/6.6 -- gancho do slot da noite (banco separado da manha)
    gancho = ganchos.escolher_gancho("noite", resumo, cidades[0].nome)
    condicao = ganchos.condicao_do_dado(resumo)
    tags = hashtags.escolher_conjunto("noite", condicao)

    # Fase 6.5 -- alerta condicional do varal (chuva 18h-06h acima do limiar)
    aviso = varal.alerta_varal([c.como_dict() for c in cidades])
    partes = [gancho, caption]
    if aviso:
        partes.append(aviso)
    partes.append(tags)
    caption = "\n\n".join(partes)

    travas.validar_caption(caption)

    if travas.ja_publicado(resumo["data_extenso"], "noite", caption):
        print("[travas] conteudo ja publicado hoje no slot noite; abortando.")
        return

    # Fase 6.4 -- sem carrossel no feed; a noite e slot de Reel/story
    if slots_config.deve_gerar_carrossel_feed("noite"):
        slides = gc.gerar_carrossel_noite(cidades, resumo, pergunta, fase)
        publicar.publicar_carrossel(slides, caption, dry_run=dry_run)

    a, b = gerar_story.dividir_opcoes(pergunta)
    story = gerar_story.gerar_story_card(pergunta, a, b, "noite")
    publicar.publicar_story(story, dry_run=dry_run)

    if not dry_run:
        travas.registrar_publicacao(resumo["data_extenso"], "noite", caption)


def rodar_alertas(dry_run: bool) -> None:
    from . import alertas
    cidades, _ = _coletar()

    for a in alertas.detectar_alertas(cidades):
        img = gc.gerar_card_alerta(
            a["tipo"], a["titulo"], a["detalhe"], a["cidades"])
        cap = captions.caption_alerta(a["tipo"], a["detalhe"], a["cidades"])
        publicar.publicar_imagem(img, cap, dry_run=dry_run)

    chuva = alertas.checar_chuva_acumulada(cidades)
    if chuva:
        linhas = " | ".join(f"{r['nome']}: {r['mm']:.0f}mm" for r in chuva["ranking"])
        img = gc.gerar_card_alerta("chuva_acumulada", "CHOVEU QUANTO?", linhas,
                              [r["nome"] for r in chuva["ranking"][:3]])
        cap = captions.caption_alerta("chuva_forte", "Acumulados das ultimas 24h: " + linhas,
                                      [r["nome"] for r in chuva["ranking"]])
        publicar.publicar_imagem(img, cap, dry_run=dry_run)


def rodar_fim_semana(dry_run: bool) -> None:
    cidades, resumo = _coletar()
    pergunta = "Fim de semana: praia em Angra ou cachoeira em Resende?"
    slides = gc.gerar_carrossel_fim_de_semana(cidades, resumo, pergunta)
    cap = captions.caption_manha(
        resumo["data_extenso"], [c.como_dict() for c in cidades], pergunta)
    publicar.publicar_carrossel(slides, cap, dry_run=dry_run)


def rodar_curiosidade(dry_run: bool) -> None:
    from . import curiosidades
    item = curiosidades.escolher_curiosidade()
    corpo = item.get("explicacao", "")
    if item.get("regional"):
        corpo = corpo + " " + item["regional"]
    slides = gc.gerar_carrossel_curiosidade(
        item, "Você já sabia dessa? Conta pra gente!")
    cap = (f"MITO OU VERDADE? {item.get('titulo','')}\n\n"
           f"{item.get('veredito','')}: {corpo}\n\n"
           "#sulfluminense #previsaodotempo #curiosidades")
    publicar.publicar_carrossel(slides, cap, dry_run=dry_run)


MODOS = {
    "manha": rodar_manha,
    "noite": rodar_noite,
    "alertas": rodar_alertas,
    "fim_semana": rodar_fim_semana,
    "curiosidade": rodar_curiosidade,
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("modo", choices=list(MODOS.keys()))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    print(f"=== {args.modo.upper()} | {'DRY-RUN' if args.dry_run else 'REAL'} ===")
    try:
        # Fase 6.3 -- lock de execucao: impede dois jobs publicando o mesmo slot
        with travas.lock_execucao(args.modo):
            MODOS[args.modo](args.dry_run)
        print("=== Concluido com sucesso ===")
        return 0
    except Exception as e:
        print("=== FALHA ===", file=sys.stderr)
        print(str(e), file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


