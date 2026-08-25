# -*- coding: utf-8 -*-
"""
resposta.py - Monta a resposta da DM: previsao de HOJE e de AMANHA do bairro.

Substitui o montar_resposta_dm() do dm_bairro.py (que respondia so o dia de
hoje). A resolucao de bairro continua toda em dm_bairro.py -- aquele arquivo
tem trava de checksum sobre a lista de bairros e nao deve ser editado a toa.
Este modulo so formata a resposta e escolhe o fecho conforme a pessoa segue ou
nao o perfil.

POR QUE A RESPOSTA TRAZ OS DOIS DIAS
------------------------------------
Os Reels do perfil ja contam um dia cada: o Ranzinza fala de hoje as 06h10 e a
Dona Maria fala de amanha as 18h. Uma DM que repetisse um dia so seria
redundante com o video que a pessoa acabou de ver; com hoje E amanha ela sempre
entrega algo que o video nao deu. Os CTAs dos dois personagens prometem
exatamente isso ("te digo como fica hoje e amanha").

O FECHO MUDA COM O FOLLOW
-------------------------
O webhook consulta a API (is_user_follow_business) e passa `segue` para ca:
  - segue          -> agradecimento + pedido de compartilhamento;
  - nao segue      -> a resposta avisa que a proxima so vem seguindo o perfil
                      (a cortesia de responder a primeira e decidida la no
                      webhook; aqui so muda o texto do fecho);
  - None (API nao respondeu) -> trata como seguidor: nunca bloquear por erro
                      nosso.
"""
from __future__ import annotations

from dm_bairro import CIDADES, resolver


def _lista_humana(nomes) -> str:
    nomes = list(nomes)
    if len(nomes) == 1:
        return nomes[0]
    return ", ".join(nomes[:-1]) + " ou " + nomes[-1]


# Mensagem de trava para quem ja usou a cortesia e continua sem seguir.
# Sem previsao nenhuma de proposito: e a troca que o perfil propoe.
MSG_SIGA = (
    "Opa! A previsão do teu bairro agora é só pra quem segue o perfil 😉\n"
    "É de graça: segue o @previsaosulflu e manda o nome do bairro de novo "
    "que eu respondo na hora. 🌦️")

_FECHO_SEGUIDOR = (
    "Amanhã os personagens voltam no perfil. "
    "Compartilha com a vizinhança! 🌦️")

_FECHO_CORTESIA = (
    "🔔 Essa foi por conta da casa. Segue o @previsaosulflu pra continuar "
    "recebendo a previsão do teu bairro sempre que pedir. 🌦️")


def montar_resposta(texto: str, previsao_por_cidade: dict,
                    segue, recomendar_roupa=None) -> tuple[str, bool]:
    """Devolve (resposta, deu_previsao).

    `deu_previsao` diz ao webhook se esta resposta entregou a previsao de fato
    (True) ou foi so uma pergunta de desambiguacao / "nao achei" (False). E por
    ela que o webhook decide se a cortesia do nao-seguidor foi gasta.
    """
    situacao, dado, rotulo = resolver(texto)

    if situacao == "ambiguo":
        return (f"Existe {rotulo} em mais de uma cidade aqui 😅\n"
                f"Me diz qual: {_lista_humana(dado)}.", False)

    if situacao == "nao_achou":
        return ("Não achei esse bairro por aqui 😅. Me diz a tua CIDADE que eu "
                "já te passo a previsão 🌦️\n"
                f"👉 {_lista_humana(CIDADES)}.", False)

    p = previsao_por_cidade.get(dado)
    if not p:
        return (f"Ainda não tenho a previsão de {dado} agora. "
                "Tenta de novo daqui a pouco 🙏", False)

    fallback = p.get("_fonte") == "met_no"
    rotulo_hoje = "Restante de hoje" if fallback else "Hoje"
    linha_roupa = ""
    if recomendar_roupa:
        linha_roupa = recomendar_roupa(
            p["tmin"], p["tmax"], p["prob_chuva"], p.get("rajada_kmh", 0))
        if fallback:
            linha_roupa = linha_roupa.replace(
                "Hoje pede:", "Restante do dia pede:")
        linha_roupa += "\n"

    fecho = _FECHO_SEGUIDOR if segue is not False else _FECHO_CORTESIA

    return (f"📍 {rotulo}\n"
            f"🌡️ {rotulo_hoje}: {p['tmin']:.0f}° / {p['tmax']:.0f}°  "
            f"☔ chuva {p['prob_chuva']:.0f}%\n"
            f"🌅 Amanhã: {p.get('tmin_amanha', p['tmin']):.0f}° / "
            f"{p.get('tmax_amanha', p['tmax']):.0f}°  "
            f"☔ chuva {p.get('prob_chuva_amanha', p['prob_chuva']):.0f}%\n"
            f"{linha_roupa}\n"
            "Dados: Open-Meteo / MET Norway (CC BY 4.0).\n"
            f"{fecho}", True)
