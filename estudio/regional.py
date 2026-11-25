"""Boletins regionais de 6h e 18h, com destaque rotativo entre cinco cidades."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from num2words import num2words
from coletar_tempo import MAIORES, CIDADES
from bairros_foco import bairro_do_dia

TZ = ZoneInfo("America/Sao_Paulo")


def gancho_rotativo(locs, data, quando, *, ancora=None, canal=""):
    """Gancho de retenção por edição, com fatos validados e sem alarmismo."""
    from datetime import date, timedelta
    from math import isfinite
    def num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and isfinite(x)
    def valor(c, *keys):
        return next((c[k] for k in keys if num(c.get(k))), None)
    def nome(c):
        return c.get("name") or c.get("nome") or c.get("point")
    validos = [c for c in locs if nome(c) and valor(c, "max_c", "max") is not None]
    if not validos:
        return "Confira a previsão " + quando + "."
    try:
        dia = date.fromisoformat(str(data)[:10])
    except (ValueError, TypeError):
        dia = date.today()
    noite = quando == "amanhã"
    pub = dia - timedelta(days=int(noite))
    fase = sum(ord(ch) for ch in canal) % 12
    slot = pub.toordinal() * 2 + int(noite) + fase
    c = ancora if ancora in validos else validos[(slot // 2 + int(noite)) % len(validos)]
    n = nome(c)
    mx = round(valor(c, "max_c", "max"))
    mn0 = valor(c, "min_c", "min")
    mn = round(mn0) if mn0 is not None else None
    outros = [x for x in validos if nome(x) != n]
    outro = max(outros, key=lambda x: abs(valor(x, "max_c", "max") - mx), default=None)
    dif = round(valor(outro, "max_c", "max")) if outro else mx
    fato = f"{n}: {mx} graus {quando}."
    faixa = f"{n}: de {mn} a {mx} graus {quando}." if mn is not None else fato
    # 12 famílias: identificação, curiosidade, antecipação, contraste,
    # proteção, urgência, surpresa, pergunta, comparação, benefício,
    # informação específica e expectativa. Condições especiais têm gate.
    familias = {
        0: (f"Mora em {n}? {mx} graus {quando}.", f"Alô, {n}! Máxima de {mx} graus {quando}.", fato, f"{n}, sua máxima: {mx} graus {quando}."),
        1: (f"Quanto vai fazer em {n}? {mx} graus {quando}.", f"{n}: sabe qual a máxima {quando}? {mx} graus.", f"{fato} E na sua cidade?", f"{n}: como fica {quando}? {mx} graus."),
        2: (f"Planeje {quando}: {faixa}", f"Já se programe: {faixa}", f"Para {quando}, {faixa}", f"Antecipe seus planos: {fato}"),
        4: (f"Antes de sair, {fato}", f"Vai sair em {n}? {mx} graus {quando}.", f"Prepare-se: {faixa}", f"De olho na temperatura: {fato}"),
        7: (f"Vai fazer calor em {n}? {mx} graus {quando}.", f"Casaco ou roupa leve? {faixa}", f"Vai sair {quando}? {faixa}", f"Como se vestir em {n}? {faixa}"),
        8: (f"Compare as temperaturas: {fato}", f"Veja os números: {fato}", f"De cidade em cidade: {fato}", f"Compare com a sua rotina: {faixa}"),
        9: (f"Organize seu dia: {faixa}", f"Para planejar a rotina: {fato}", f"Seu dia em {n}: {mx} graus {quando}.", f"Programe sua saída: {fato}"),
        10: (fato, f"Máxima de {mx} graus em {n} {quando}.", faixa, f"{quando.capitalize()}, {n} pode chegar a {mx} graus."),
        11: (f"{fato} E as demais cidades?", f"{fato} Veja as outras temperaturas.", f"Começando por {n}: {mx} graus {quando}.", f"Primeiro, {fato}"),
    }
    if mn is not None and mx - mn >= 7:
        familias[3] = (f"De {mn} a {mx} graus em {n} {quando}.", f"{n}: mínima de {mn}, máxima de {mx} {quando}.", faixa, f"Do mínimo de {mn} ao máximo de {mx} graus em {n} {quando}.")
    if outro and abs(dif - mx) >= 4:
        familias[6] = (f"{n}: {mx} graus. {nome(outro)}: {dif} {quando}.", f"Olha a diferença {quando}: {n}, {mx}; {nome(outro)}, {dif} graus.", f"Temperaturas bem diferentes: {n}, {mx}; {nome(outro)}, {dif} graus {quando}.", f"{n} e {nome(outro)}: {mx} e {dif} graus {quando}.")
        familias[8] = familias[6][::-1]
    rajada = valor(c, "wind_gust_max_kmh", "gust_kmh", "wind_gust_kmh", "rajada_kmh")
    if rajada is not None and rajada >= 60:
        familias[5] = (f"Atenção em {n}: rajadas fortes {quando}.", f"Vento forte previsto em {n} {quando}.", f"{n}: cuidado com as rajadas {quando}.", f"De olho no vento forte em {n} {quando}.")
    elif mx >= 38:
        familias[5] = (f"Atenção em {n}: máxima de {mx} graus {quando}.", f"{n}: calor intenso, {mx} graus {quando}.", f"Cuidado com o calor em {n}: {mx} graus {quando}.", f"{mx} graus previstos em {n} {quando}: cuide-se.")
    # Se um fenômeno não existe, mantém a alternância sem fabricar o fato.
    k = slot % 12
    fallback = {3: 9, 5: 11, 6: 0}
    k = k if k in familias else fallback.get(k, 10)
    frase = familias[k][(slot // 12) % 4]
    # Mantém a abertura curta mesmo com nomes compostos.
    if len(frase.split()) > 12:
        frase = fato
    return frase


def engajamento_rotativo(data, quando, local="", canal=""):
    """Um pedido útil por edição, com rodízio independente do gancho."""
    from datetime import date, timedelta
    try:
        dia = date.fromisoformat(str(data)[:10])
    except (ValueError, TypeError):
        dia = date.today()
    noite = quando == "amanhã"
    pub = dia - timedelta(days=int(noite))
    slot = pub.toordinal() * 2 + int(noite) + sum(ord(ch) for ch in canal)
    familias = (
        ("Envie a previsão a quem vai sair.", "Compartilhe com quem mora na região.", "Manda pra quem precisa dessa previsão.", "Envie para quem vai viajar."),
        ("Qual sua cidade? Comente aqui.", "Como está o tempo aí? Comente.", "De qual bairro você nos acompanha?", "Qual cidade quer ver por aqui?"),
        ("Salve para consultar antes de sair.", "Guarde esta previsão para seu dia.", "Salve o boletim para planejar.", "Salve para conferir mais tarde."),
        ("Siga para acompanhar a previsão diária.", "Siga e acompanhe o tempo na região.", "Acompanhe o perfil para novos boletins.", "Siga para conferir a próxima previsão."),
    )
    if local and slot % len(familias) == 0:
        return (f"Envie a previsão para alguém de {local}.",
                f"Manda pra quem mora em {local} conferir a previsão.",
                f"Compartilhe com quem vai sair em {local}.",
                f"Envie para quem conhece alguém de {local}.")[(slot // len(familias)) % 4]
    return familias[slot % len(familias)][(slot // len(familias)) % 4]


def escolher_destaque(cidades, data_publicacao=None, personagem="bira"):
    """Alterna a abertura entre os dez municípios, distinguindo manhã e tarde.

    Mantém as maiores audiências no quadro de cinco cidades, sem duplicações.
    A escolha é determinística por data de publicação e personagem.
    """
    if len(cidades) < 5:
        raise ValueError("São necessárias cinco cidades distintas")
    data_publicacao = data_publicacao or datetime.now(TZ).date()
    por_nome = {c["nome"]: c for c in cidades}
    disponiveis = [nome for nome, _, _ in CIDADES if nome in por_nome]
    if len(disponiveis) != len(CIDADES):
        raise ValueError("Ausência de município regular; publicação bloqueada")

    if personagem not in ("bira", "bia"):
        raise ValueError("Personagem desconhecido")
    deslocamento = 5 if personagem == "bia" else 0
    nome = disponiveis[(data_publicacao.toordinal() + deslocamento) % len(disponiveis)]
    # A cidade principal abre. As outras quatro priorizam as maiores audiências.
    escolhidas = [dict(por_nome[nome], vento_kmh=por_nome[nome].get("rajada_kmh"))]
    for candidata in MAIORES:
        if len(escolhidas) == 5:
            break
        if candidata in por_nome and candidata != nome:
            c = por_nome[candidata]
            escolhidas.append(dict(c, vento_kmh=c.get("rajada_kmh")))
    if len(escolhidas) < 5:
        for candidata in disponiveis:
            if len(escolhidas) == 5:
                break
            if candidata not in {c["nome"] for c in escolhidas}:
                c = por_nome[candidata]
                escolhidas.append(dict(c, vento_kmh=c.get("rajada_kmh")))
    return escolhidas

def preparar_boletim(dia, personagem, destino):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    data_publicacao = datetime.now(TZ).date()
    cidades = escolher_destaque(dia["cidades"], data_publicacao, personagem)
    manha = personagem == "bira"
    for cidade in cidades:
        cidade["bairro"] = bairro_do_dia(cidade["nome"], data_publicacao, personagem)
    quando = "hoje" if manha else "amanhã"
    nome = "Bira do Tempo" if manha else "Bia"
    destaque = cidades[0]
    temperatura = round(destaque["max"])
    bairro = destaque.get("bairro")
    # Temperatura municipal no primeiro segundo; bairro apenas como referência.
    abertura = gancho_rotativo(cidades, dia["data"], quando, ancora=destaque, canal="sulflu")
    if bairro:
        abertura += f" Bairro em foco: {bairro}."
    # Minima e maxima continuam visiveis; fala resumida abre espaco para os bairros.
    outras = [f"{c['nome']}, {num2words(round(c['max']), lang='pt_BR')}"
              for c in cidades[1:]]
    previsoes = "; ".join(outras) + " graus."
    # Compara TODAS as cidades coletadas, nao apenas as cinco mostradas.
    # Um bairro em foco nao e uma estacao meteorologica: o dado e municipal.
    valores = [(c, float(c.get("chuva_mm") or 0)) for c in dia["cidades"]]
    pico, chuva_max = max(valores, key=lambda v: v[1])
    bairro_chuva = bairro_do_dia(pico["nome"], data_publicacao, personagem)
    tem_chuva = chuva_max >= 1.0
    mm = int(round(chuva_max))
    if tem_chuva:
        frase_chuva = (f"Maior chuva prevista em {pico['nome']}: "
                       f"{num2words(mm, lang='pt_BR')} milímetros. "
                       f"Bairro da vez: {bairro_chuva}.")
        texto_chuva = (f"Maior volume municipal previsto: {pico['nome']}, "
                       f"cerca de {mm} mm. Bairro em foco: {bairro_chuva}.")
    else:
        frase_chuva = "Sem chuva significativa prevista entre as cidades monitoradas."
        texto_chuva = frase_chuva
    # CTA único, útil e atrelado aos dados reais do boletim.
    if tem_chuva and pico["nome"] == destaque["nome"]:
        chamada = f"Envia pra quem mora em {destaque['nome']} e precisa se preparar pra chuva."
    elif tem_chuva:
        chamada = f"Envia pra quem conhece alguém em {pico['nome']}."
    elif temperatura >= 32:
        chamada = f"Envia pra quem vai sair no calor de {destaque['nome']}."
    elif temperatura <= 17:
        chamada = f"Envia pra quem vai sair cedo em {destaque['nome']}."
    else:
        chamada = f"Envia pra alguém de {destaque['nome']} conferir a previsão."
    chamada = engajamento_rotativo(dia["data"], quando, destaque["nome"], "sulflu")
    def batida(tipo, fala, **dados):
        return {"tipo": tipo, "fala": fala, "legenda": fala, "dados": dados}
    batidas = [
        batida("frase", abertura),
        batida("resumo", previsoes, cidades=cidades, titulo="CIDADES E BAIRROS"),
        batida("frase", frase_chuva),
        batida("cta", chamada, chamada="ACOMPANHE A PREVISÃO"),
    ]
    bloco = {"date": dia["data"], "locations": [
        {"max_c": c["max"], "rain_mm": c.get("chuva_mm", 0)} for c in cidades
    ]}
    data = datetime.fromisoformat(dia["data"]).strftime("%d/%m")
    tag = "#" + "".join(destaque["nome"].split())
    legenda = [
        f"{destaque['nome']}: {temperatura} graus {quando}! {tag}",
        f"{nome} | Previsão de {quando}, {data}",
        "",
    ]
    legenda.extend(
        f"{c['nome']} — {c['bairro']}: {round(c['min'])}° a {round(c['max'])}°"
        if c.get("bairro") else f"{c['nome']}: {round(c['min'])}° a {round(c['max'])}°"
        for c in cidades
    )
    legenda.extend(["", "☔ " + texto_chuva,
                    "Bairros são referências locais; a chuva é prevista para o município."])
    legenda += ["", chamada, "", "@previsaosulflu #SulFluminense #PrevisãoDoTempo"]
    (destino / "LEGENDA.txt").write_text("\n".join(legenda) + "\n", encoding="utf-8")
    ficha = {
        "formato": "manha_sulflu_20_25" if manha else "amanha_sulflu_20_25",
        "gancho": abertura,
        "cidade_destaque": destaque["nome"],
        "bairro_destaque": bairro,
        "cidade_maior_chuva": pico["nome"] if tem_chuva else None,
        "bairro_maior_chuva": bairro_chuva if tem_chuva else None,
        "maior_chuva_mm": round(chuva_max, 1),
        "temperatura_destaque": temperatura,
        "dia_previsao": dia["data"],
        "quando": quando,
        "cta": chamada,
        "horario_brt": "06:00" if manha else "18:00",
        "estrategia": "rodizio_10_municipios_gancho_numero_cta_contextual",
    }
    (destino / "REEL.metadata.json").write_text(
        json.dumps(ficha, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"forecast": {"today": bloco, "tomorrow": bloco}}, cidades, batidas
