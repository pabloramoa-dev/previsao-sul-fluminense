# -*- coding: utf-8 -*-
"""
perguntas.py -- Banco de perguntas fechadas para o slide de engajamento
do @previsaosulfluminense. Rotacao sem repeticao via estado.json.
"""

import json
from pathlib import Path

ESTADO_PATH = Path(__file__).parent / "estado.json"

PERGUNTAS_FRIO_CHUVA = [
    "Voce esta gostando do frio ou prefere o calor?",
    "Quer que o frio acabe ou esta bom assim?",
    "Dia de chuva: melhor ficar em casa ou voce nem liga?",
    "Frio de manha pede: cafe ou chocolate quente?",
    "Noite fria pede: cobertor ou pizza quente?",
    "Chuva no fim de semana: estraga tudo ou e desculpa pra descansar?",
    "Frio assim: edredom ate tarde ou coragem pra levantar?",
    "Prefere frio seco ou chuva fininha o dia todo?",
    "Dia gelado: sopa ou fondue?",
    "Chuva a noite: melhor som pra dormir ou atrapalha seus planos?",
    "Frio no Sul Fluminense: casaco pesado ou aguenta de moletom?",
    "Voce e time inverno ou time verao?",
    "Manha de neblina na serra: acha bonito ou so atrapalha?",
    "Chuva forte chegando: prefere aviso antes ou nem se importa?",
    "Frio de 10 graus: perfeito ou insuportavel?",
    "Dia nublado: acha aconchegante ou fica desanimado?",
    "Chuva de fim de tarde: charme ou transtorno no transito?",
    "Frio pede: churrasco mesmo assim ou fica pra depois?",
    "Prefere acordar com chuva no telhado ou com sol na janela?",
    "Friozinho pra dormir: janela aberta ou tudo fechado?",
]

PERGUNTAS_CALOR_SOL = [
    "Calor assim pede: piscina ou ar-condicionado?",
    "Prefere sol de 35 graus ou chuva o dia todo?",
    "Voce esta gostando do calor ou ja quer que refresque?",
    "Dia quente: bebida gelada ou agua de coco?",
    "Calorao: ventilador resolve ou so ar-condicionado?",
    "Sol forte no fim de semana: cachoeira ou piscina?",
    "Verao no Sul Fluminense: praia em Angra ou sombra em casa?",
    "Calor a noite: dorme de ventilador ligado ou desliga de madrugada?",
    "Dia de 30 graus ou mais: acai ou sorvete?",
    "Sol o dia todo: aproveita ou prefere um tempo mais fresco?",
    "Calor pede: chinelo o dia inteiro ou mantem o tenis?",
    "Voce e time verao ou time inverno?",
    "Domingo de sol: churrasco ou rio/cachoeira?",
    "Calor de meio-dia: almoco quente ou so uma salada?",
    "Sol forte: protetor sempre ou so quando lembra?",
    "Noite quente: banho gelado antes de dormir ou aguenta firme?",
    "Prefere calor seco ou calor umido?",
    "Fim de tarde quente: sorvete ou milk-shake?",
    "Calorao chegando: janela aberta ou cortina fechada o dia todo?",
    "Verao: acorda cedo pra aproveitar ou espera o sol baixar?",
]

CODIGOS_CHUVA = set(range(51, 100))


def _carregar_estado():
    if ESTADO_PATH.exists():
        return json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
    return {}


def _salvar_estado(estado):
    ESTADO_PATH.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def escolher_pergunta(temp_max_regional: float, weathercode: int) -> str:
    """Escolhe a categoria pela condicao do dia e rotaciona sem repetir."""
    estado = _carregar_estado()

    if temp_max_regional < 22 or weathercode in CODIGOS_CHUVA:
        categoria, banco = "frio_chuva", PERGUNTAS_FRIO_CHUVA
    else:
        categoria, banco = "calor_sol", PERGUNTAS_CALOR_SOL

    chave = f"indice_pergunta_{categoria}"
    indice = estado.get(chave, 0) % len(banco)
    pergunta = banco[indice]

    estado[chave] = indice + 1
    _salvar_estado(estado)

    return pergunta
