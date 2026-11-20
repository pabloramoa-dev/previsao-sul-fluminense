"""Aplica a normalização de horários ao motor RJ fixado nos workflows SulFlu.

O SulFlu usa um checkout de um commit específico do estúdio RJ e depois
aplica patches de identidade visual e voz. Este ajuste não troca o commit
fixado nem altera essas customizações.
"""
from pathlib import Path

ALVO = Path("src/previsao_rj/render/characters/kokoro.py")
FUNCAO = r'''
# Apenas a pronúncia muda: "17h" permanece abreviado na legenda e tela.
_HORA_TTS_RE = re.compile(
    r"(?<![\w/])(?P<hora>(?:[01]?\d|2[0-3]))\s*"
    r"(?:[hH](?P<min_h>[0-5]\d)?|:(?P<min_d>[0-5]\d))(?!\w)"
)


def normalizar_horario_para_voz(texto: str) -> str:
    def trocar(match):
        hora = int(match.group("hora"))
        minuto = match.group("min_h") or match.group("min_d")
        unidade = "hora" if hora == 1 else "horas"
        if minuto is None or int(minuto) == 0:
            return f"{hora} {unidade}"
        minuto = int(minuto)
        return f"{hora} {unidade} e {minuto} {'minuto' if minuto == 1 else 'minutos'}"

    return _HORA_TTS_RE.sub(trocar, texto)


'''


def main():
    texto = ALVO.read_text(encoding="utf-8")
    if "def normalizar_horario_para_voz(" in texto:
        print("Pronúncia de horários já normalizada.")
        return
    pontos = (
        "import argparse, json, os, subprocess, sys, wave",
        "def main():",
        "k.create(txt, voice=",
    )
    if any(texto.count(p) != 1 for p in pontos):
        raise RuntimeError("Motor fixado mudou: revisar os pontos de normalização")
    texto = texto.replace(
        pontos[0],
        "import argparse, json, os, re, subprocess, sys, wave",
    )
    texto = texto.replace(pontos[1], FUNCAO + pontos[1])
    texto = texto.replace(
        pontos[2], "k.create(normalizar_horario_para_voz(txt), voice="
    )
    ALVO.write_text(texto, encoding="utf-8")
    print("Normalização de 17h -> 17 horas aplicada ao estúdio fixado.")


if __name__ == "__main__":
    main()
