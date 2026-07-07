# -*- coding: utf-8 -*-
"""
captions.py -- Geracao automatica de captions para o @previsaosulfluminense.
Tres tipos: manha (06h), noite (18h) e alerta (variacao brusca).
"""

HASHTAGS = (
    "#voltaredonda #resende #barramansa #portoreal #angradosreis "
    "#sulfluminense #previsaodotempo #climarj #tempoagora"
)

# Weathercodes Open-Meteo -> descricao curta
DESCRICAO_TEMPO = {
    0: "ceu limpo", 1: "predominio de sol", 2: "sol entre nuvens",
    3: "ceu nublado", 45: "nevoeiro", 48: "nevoeiro com geada",
    51: "chuvisco fraco", 53: "chuvisco", 55: "chuvisco intenso",
    61: "chuva fraca", 63: "chuva moderada", 65: "chuva forte",
    80: "pancadas isoladas", 81: "pancadas de chuva", 82: "pancadas fortes",
    95: "tempestade", 96: "tempestade com granizo", 99: "tempestade severa",
}


def _emoji_tempo(code: int) -> str:
    if code <= 1:
        return "☀️"
    if code == 2:
        return "🌤️"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if code in (51, 53, 55, 61, 63):
        return "🌧️"
    if code in (65, 80, 81, 82):
        return "🌧️💧"
    if code >= 95:
        return "⛈️"
    return "🌡️"


def caption_manha(data_extenso: str, cidades: list, pergunta: str) -> str:
    """cidades: lista de dicts com nome, tmin, tmax, prob_chuva, weathercode."""
    code_pred = max(c["weathercode"] for c in cidades)
    desc = DESCRICAO_TEMPO.get(code_pred, "tempo variavel")
    emoji = _emoji_tempo(code_pred)

    tmin = min(c["tmin"] for c in cidades)
    tmax = max(c["tmax"] for c in cidades)
    prob = max(c["prob_chuva"] for c in cidades)

    linhas_cidades = "\n".join(
        f"{_emoji_tempo(c['weathercode'])} {c['nome']}: "
        f"{c['tmin']:.0f}C / {c['tmax']:.0f}C"
        + (f" - {c['prob_chuva']:.0f}%" if c["prob_chuva"] >= 30 else "")
        for c in cidades
    )

    aviso_chuva = (
        f"\n\nAtencao: chance de chuva de ate {prob:.0f}% na regiao. "
        "Vale levar o guarda-chuva!" if prob >= 60 else ""
    )

    return (
        f"{emoji} PREVISAO DO TEMPO -- SUL FLUMINENSE\n"
        f"{data_extenso}\n\n"
        f"Hoje o dia sera de {desc}, com minima de {tmin:.0f}C "
        f"e maxima de {tmax:.0f}C na regiao.\n\n"
        f"{linhas_cidades}"
        f"{aviso_chuva}\n\n"
        f"Arrasta pro lado e ve a previsao completa da sua cidade!\n\n"
        f"{pergunta}\n"
        f"Responde aqui nos comentarios!\n\n"
        f"Compartilha com quem precisa saber e ativa as notificacoes.\n\n"
        f"{HASHTAGS}"
    )


def caption_noite(data_extenso: str, cidades: list, pergunta: str) -> str:
    """cidades: dicts com nome, temp_21h, tmin_madrugada, prob_chuva_noite."""
    tmin = min(c["tmin_madrugada"] for c in cidades)
    prob = max(c["prob_chuva_noite"] for c in cidades)

    linhas_cidades = "\n".join(
        f"{c['nome']}: {c['temp_21h']:.0f}C as 21h, "
        f"minima de {c['tmin_madrugada']:.0f}C na madrugada"
        for c in cidades
    )

    aviso = (
        f"\n\nPode chover durante a noite (ate {prob:.0f}% de chance). "
        "Recolhe a roupa do varal!" if prob >= 50 else ""
    )

    frio = (
        f"\n\nMadrugada gelada de {tmin:.0f}C -- separa o cobertor!"
        if tmin <= 14 else ""
    )

    return (
        f"COMO SERA A NOITE NO SUL FLUMINENSE\n"
        f"{data_extenso}\n\n"
        f"{linhas_cidades}"
        f"{aviso}{frio}\n\n"
        f"Arrasta pro lado pra ver os detalhes da sua cidade!\n\n"
        f"{pergunta}\n"
        f"Responde aqui nos comentarios!\n\n"
        f"{HASHTAGS}"
    )


def caption_alerta(tipo: str, detalhe: str, cidades_afetadas: list) -> str:
    """tipo: queda_temperatura, subida_temperatura, chuva_forte, vento, tempestade."""
    titulos = {
        "queda_temperatura": "ALERTA: QUEDA BRUSCA DE TEMPERATURA",
        "subida_temperatura": "ALERTA: CALOR CHEGANDO COM FORCA",
        "chuva_forte": "ALERTA: CHUVA FORTE A CAMINHO",
        "vento": "ALERTA: RAJADAS DE VENTO",
        "tempestade": "ALERTA: RISCO DE TEMPESTADE",
    }
    dicas = {
        "queda_temperatura": "Separa o casaco e se agasalha bem!",
        "subida_temperatura": "Hidrate-se e evite o sol do meio-dia!",
        "chuva_forte": "Evite areas de alagamento e atencao no transito!",
        "vento": "Cuidado com estruturas soltas e arvores!",
        "tempestade": "Se possivel, evite se deslocar durante a tempestade!",
    }

    lista = ", ".join(cidades_afetadas)

    return (
        f"{titulos.get(tipo, 'ALERTA DE TEMPO')}\n\n"
        f"{detalhe}\n\n"
        f"Cidades afetadas: {lista}\n\n"
        f"{dicas.get(tipo, 'Fique atento as atualizacoes!')}\n\n"
        f"COMPARTILHA agora com quem mora ou trabalha na regiao.\n\n"
        f"Ativa as notificacoes do @previsaosulfluminense.\n\n"
        f"{HASHTAGS} #alertadetempo"
    )
"""
captions.py -- Geracao automatica de captions para o @previsaosulfluminense.
Tres tipos: manha (06h), noite (18h) e alerta (variacao brusca).
"""

HASHTAGS = (
    "#voltaredonda #resende #barramansa #portoreal #angradosreis "
    "#sulfluminense #previsaodotempo #climarj #tempoagora"
)

# Weathercodes Open-Meteo -> descricao curta
DESCRICAO_TEMPO = {
    0: "ceu limpo", 1: "predominio de sol", 2: "sol entre nuvens",
    3: "ceu nublado", 45: "nevoeiro", 48: "nevoeiro com geada",
    51: "chuvisco fraco", 53: "chuvisco", 55: "chuvisco intenso",
    61: "chuva fraca", 63: "chuva moderada", 65: "chuva forte",
    80: "pancadas isoladas", 81: "pancadas de chuva", 82: "pancadas fortes",
    95: "tempestade", 96: "tempestade com granizo", 99: "tempestade severa",
}


def _emoji_tempo(code: int) -> str:
    if code <= 1:
        return "☀️"
    if code == 2:
        return "U0001F324️"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "U0001F32B️"
    if code in (51, 53, 55, 61, 63):
        return "U0001F327️"
    if code in (65, 80, 81, 82):
        return "U0001F327️U0001F4A7"
    if code >= 95:
        return "⛈️"
    return "U0001F321️"


def caption_manha(data_extenso: str, cidades: list, pergunta: str) -> str:
    """cidades: lista de dicts com nome, tmin, tmax, prob_chuva, weathercode."""
    code_pred = max(c["weathercode"] for c in cidades)
    desc = DESCRICAO_TEMPO.get(code_pred, "tempo variavel")
    emoji = _emoji_tempo(code_pred)

    tmin = min(c["tmin"] for c in cidades)
    tmax = max(c["tmax"] for c in cidades)
    prob = max(c["prob_chuva"] for c in cidades)

    linhas_cidades = "\n".join(
        f"{_emoji_tempo(c['weathercode'])} {c['nome']}: "
        f"{c['tmin']:.0f}C / {c['tmax']:.0f}C"
        + (f" - {c['prob_chuva']:.0f}%" if c["prob_chuva"] >= 30 else "")
        for c in cidades
    )

    aviso_chuva = (
        f"\n\nAtencao: chance de chuva de ate {prob:.0f}% na regiao. "
        "Vale levar o guarda-chuva!" if prob >= 60 else ""
    )

    return (
        f"{emoji} PREVISAO DO TEMPO -- SUL FLUMINENSE\n"
        f"{data_extenso}\n\n"
        f"Hoje o dia sera de {desc}, com minima de {tmin:.0f}C "
        f"e maxima de {tmax:.0f}C na regiao.\n\n"
        f"{linhas_cidades}"
        f"{aviso_chuva}\n\n"
        f"Arrasta pro lado e ve a previsao completa da sua cidade!\n\n"
        f"{pergunta}\n"
        f"Responde aqui nos comentarios!\n\n"
        f"Compartilha com quem precisa saber e ativa as notificacoes.\n\n"
        f"{HASHTAGS}"
    )


def caption_noite(data_extenso: str, cidades: list, pergunta: str) -> str:
    """cidades: dicts com nome, temp_21h, tmin_madrugada, prob_chuva_noite."""
    tmin = min(c["tmin_madrugada"] for c in cidades)
    prob = max(c["prob_chuva_noite"] for c in cidades)

    linhas_cidades = "\n".join(
        f"{c['nome']}: {c['temp_21h']:.0f}C as 21h, "
        f"minima de {c['tmin_madrugada']:.0f}C na madrugada"
        for c in cidades
    )

    aviso = (
        f"\n\nPode chover durante a noite (ate {prob:.0f}% de chance). "
        "Recolhe a roupa do varal!" if prob >= 50 else ""
    )

    frio = (
        f"\n\nMadrugada gelada de {tmin:.0f}C -- separa o cobertor!"
        if tmin <= 14 else ""
    )

    return (
        f"COMO SERA A NOITE NO SUL FLUMINENSE\n"
        f"{data_extenso}\n\n"
        f"{linhas_cidades}"
        f"{aviso}{frio}\n\n"
        f"Arrasta pro lado pra ver os detalhes da sua cidade!\n\n"
        f"{pergunta}\n"
        f"Responde aqui nos comentarios!\n\n"
        f"{HASHTAGS}"
    )


def caption_alerta(tipo: str, detalhe: str, cidades_afetadas: list) -> str:
    """tipo: queda_temperatura, subida_temperatura, chuva_forte, vento, tempestade."""
    titulos = {
        "queda_temperatura": "ALERTA: QUEDA BRUSCA DE TEMPERATURA",
        "subida_temperatura": "ALERTA: CALOR CHEGANDO COM FORCA",
        "chuva_forte": "ALERTA: CHUVA FORTE A CAMINHO",
        "vento": "ALERTA: RAJADAS DE VENTO",
        "tempestade": "ALERTA: RISCO DE TEMPESTADE",
    }
    dicas = {
        "queda_temperatura": "Separa o casaco e se agasalha bem!",
        "subida_temperatura": "Hidrate-se e evite o sol do meio-dia!",
        "chuva_forte": "Evite areas de alagamento e atencao no transito!",
        "vento": "Cuidado com estruturas soltas e arvores!",
        "tempestade": "Se possivel, evite se deslocar durante a tempestade!",
    }

    lista = ", ".join(cidades_afetadas)

    return (
        f"{titulos.get(tipo, 'ALERTA DE TEMPO')}\n\n"
        f"{detalhe}\n\n"
        f"Cidades afetadas: {lista}\n\n"
        f"{dicas.get(tipo, 'Fique atento as atualizacoes!')}\n\n"
        f"COMPARTILHA agora com quem mora ou trabalha na regiao.\n\n"
        f"Ativa as notificacoes do @previsaosulfluminense.\n\n"
        f"{HASHTAGS} #alertadetempo"
    )
