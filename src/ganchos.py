# -*- coding: utf-8 -*-
"""
ganchos.py -- Fonte unica de verdade para o GANCHO (primeira linha/frame).

Regras (Fase 6, itens 6.1 e 6.6):
- O gancho e SEMPRE derivado do mesmo objeto de dados que gera chuva/icones.
  Se nao ha chuva (chuva_mm == 0 e nenhum icone de chuva), nenhum gancho de
  chuva pode ser selecionado -- e vice-versa. Isso elimina o caso
  "Vai chover" + "Chuva: nenhuma".
- Dois bancos SEPARADOS, sem nenhum gancho compartilhado:
    BANCO_MANHA -> fala do HOJE, por condicao, nomeando a cidade.
    BANCO_NOITE -> veredito sobre AMANHA ("Amanha chove.", etc.).
- Rotacao real: nao repete um gancho usado nos ultimos 10 posts do mesmo slot.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HIST_PATH = Path(__file__).parent / "ganchos_estado.json"

# Codigos Open-Meteo considerados "chuva" (chuvisco em diante).
CODIGOS_CHUVA = set(range(51, 100))


def condicao_do_dado(dado: dict[str, Any]) -> str:
    """Deriva a condicao a partir do MESMO objeto de dados dos cards.

    Espera as chaves: weathercode, chuva_mm (ou prob_chuva), tmax.
    Retorna uma das: 'chuva', 'calor', 'frio', 'sol', 'nublado'.
    """
    code = int(dado.get("weathercode", 0))
    chuva_mm = float(dado.get("chuva_mm", 0) or 0)
    prob = float(dado.get("prob_chuva", 0) or 0)
    tmax = float(dado.get("tmax", 20) or 20)

    tem_chuva = code in CODIGOS_CHUVA or chuva_mm > 0 or prob >= 60
    if tem_chuva:
        return "chuva"
    if tmax >= 30:
        return "calor"
    if tmax < 18:
        return "frio"
    if code <= 1:
        return "sol"
    return "nublado"


# BANCO MANHA -- fala do HOJE, por condicao, nomeando a cidade ({cidade}).
BANCO_MANHA = {
    "chuva": [
        "Leva o guarda-chuva: hoje chove em {cidade}.",
        "Hoje o dia amanhece molhado em {cidade}.",
        "Chuva na area de {cidade} a partir de hoje cedo.",
        "Sai de casa com capa: {cidade} tem chuva hoje.",
        "Dia de chao molhado em {cidade}. Se prepara.",
        "Hoje a chuva chega em {cidade} -- e nao e fininha.",
        "Guarda-chuva na mochila: {cidade} vai molhar hoje.",
        "Previsao de chuva o dia todo em {cidade}.",
    ],
    "calor": [
        "Hoje o calor aperta em {cidade}. Bebe agua.",
        "Dia de rachar em {cidade}: sol forte o dia inteiro.",
        "Calorao em {cidade} hoje -- protetor e sombra.",
        "Hoje {cidade} ferve. Evite o sol do meio-dia.",
        "Termometro subindo em {cidade}. Hidrata!",
        "Sol pesado hoje em {cidade}. Bone e agua na mao.",
        "Hoje e dia de ar-condicionado em {cidade}.",
        "Calor de verao em {cidade} hoje, mesmo fora dele.",
    ],
    "frio": [
        "Casaco pesado hoje: {cidade} amanhece gelada.",
        "Frio de verdade em {cidade} hoje cedo.",
        "Hoje {cidade} pede cobertor ate mais tarde.",
        "Manha gelada em {cidade}. Se agasalha bem.",
        "Hoje o frio nao da tregua em {cidade}.",
        "Termometro la embaixo em {cidade} hoje.",
        "Dia de sopa quente em {cidade}: frio chegou.",
        "Hoje {cidade} acorda no friozinho. Blusa na mao.",
    ],
    "sol": [
        "Sol firme o dia todo em {cidade} hoje.",
        "Hoje {cidade} tem ceu limpo de manha a noite.",
        "Dia bonito em {cidade}: sol sem chuva hoje.",
        "Hoje da pra estender a roupa em {cidade}.",
        "Sol e ceu azul em {cidade} o dia inteiro.",
        "Hoje {cidade} aproveita um dia seco e ensolarado.",
        "Nada de chuva hoje: {cidade} fica no sol.",
        "Dia de rua em {cidade}: sol garantido hoje.",
    ],
    "nublado": [
        "Hoje o ceu fecha em {cidade}, mas sem chuva firme.",
        "Dia nublado em {cidade}, so encoberto.",
        "Hoje {cidade} amanhece cinza, mas nao chove.",
        "Ceu carregado em {cidade} hoje -- fica de olho.",
        "Hoje {cidade} tem mais nuvem que sol.",
        "Tempo fechado em {cidade} hoje, sem molhar.",
        "Hoje o sol se esconde em {cidade}.",
        "Dia abafado e nublado em {cidade} hoje.",
    ],
}

# BANCO NOITE -- veredito sobre AMANHA. Nenhuma frase aqui aparece na manha.
BANCO_NOITE = {
    "chuva": [
        "Amanha chove. Ja deixa o guarda-chuva na porta.",
        "Ja adianto: amanha o dia comeca molhado.",
        "Amanha tem chuva -- planeja sem pressa.",
        "Se depender do tempo, amanha e dia de ficar em casa.",
        "Amanha a chuva volta. Roupa no varal, nem pensar.",
        "Prepara: amanha promete chuva na regiao.",
        "Amanha nao presta pra sol: vem chuva.",
        "O recado de hoje: amanha leva capa.",
    ],
    "calor": [
        "Amanha esquenta. Ja separa a garrafa de agua.",
        "Aviso pra amanha: calor forte de novo.",
        "Amanha o sol castiga -- protetor desde cedo.",
        "Ja adianto: amanha e dia de rachar.",
        "Amanha promete calorao na regiao.",
        "Se preparando pra amanha: vem dia quente.",
        "Amanha o termometro sobe. Roupa leve.",
        "O recado da noite: amanha e dia de sombra.",
    ],
    "frio": [
        "Amanha amanhece gelado. Casaco a postos.",
        "Ja adianto: amanha o frio aperta.",
        "Aviso pra amanha: manha bem fria.",
        "Amanha pede cobertor ate mais tarde.",
        "Se prepara: amanha comeca no friozinho.",
        "Amanha o dia comeca gelado na regiao.",
        "O recado da noite: amanha leva blusa.",
        "Amanha nao esquece o casaco ao sair.",
    ],
    "sol": [
        "Boa noticia: amanha e dia de sol.",
        "Ja adianto: amanha o ceu abre.",
        "Amanha promete sol e ceu limpo.",
        "Se planeja: amanha da pra sair sem chuva.",
        "Amanha e dia de estender a roupa.",
        "O recado da noite: amanha o sol volta.",
        "Amanha presta: sol firme na regiao.",
        "Amanha da praia ou cachoeira: vem sol.",
    ],
    "nublado": [
        "Amanha o ceu fica fechado, mas sem chuva firme.",
        "Ja adianto: amanha e dia cinza.",
        "Amanha promete mais nuvem que sol.",
        "Se prepara: amanha o tempo fecha, sem molhar.",
        "Amanha o sol se esconde na regiao.",
        "O recado da noite: amanha e dia encoberto.",
        "Amanha fica abafado e nublado.",
        "Amanha o ceu carrega, mas segura a chuva.",
    ],
}


def _sanity_check_bancos() -> None:
    manha = [f for lst in BANCO_MANHA.values() for f in lst]
    noite = [f for lst in BANCO_NOITE.values() for f in lst]
    assert len(manha) >= 40, f"BANCO_MANHA tem {len(manha)} ganchos (<40)"
    assert len(noite) >= 40, f"BANCO_NOITE tem {len(noite)} ganchos (<40)"
    assert not (set(manha) & set(noite)), "Ha ganchos compartilhados entre os bancos"


def _carregar_hist() -> dict[str, list[str]]:
    if HIST_PATH.exists():
        try:
            return json.loads(HIST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"manha": [], "noite": []}


def _salvar_hist(hist: dict[str, list[str]]) -> None:
    HIST_PATH.write_text(json.dumps(hist, ensure_ascii=False, indent=2),
                         encoding="utf-8")


def escolher_gancho(slot: str, dado: dict[str, Any], cidade: str = "") -> str:
    """Escolhe um gancho coerente com o dado, sem repetir os ultimos 10 do slot."""
    if slot not in ("manha", "noite"):
        raise ValueError("slot deve ser 'manha' ou 'noite'")

    banco = BANCO_MANHA if slot == "manha" else BANCO_NOITE
    condicao = condicao_do_dado(dado)
    candidatos = list(banco[condicao])

    hist = _carregar_hist()
    usados = set(hist.get(slot, [])[-10:])
    disponiveis = [g for g in candidatos if g not in usados] or candidatos
    escolhido = disponiveis[0]

    hist.setdefault(slot, []).append(escolhido)
    hist[slot] = hist[slot][-30:]
    _salvar_hist(hist)

    return escolhido.replace("{cidade}", cidade) if cidade else escolhido


_sanity_check_bancos()
