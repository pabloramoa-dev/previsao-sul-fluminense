"""Boletins regionais de 6h e 18h, com destaque rotativo entre cinco cidades."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from num2words import num2words
from coletar_tempo import resumo_cinco, MAIORES, CIDADES
from bairros_foco import bairro_do_dia

TZ = ZoneInfo("America/Sao_Paulo")

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
    abertura = (f"{destaque['nome']}, bairro {bairro}: {temperatura} graus {quando}."
                if bairro else f"{destaque['nome']}: {temperatura} graus {quando}.")
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
    chamada = f"Manda pra quem mora em {destaque['nome']}."
    def batida(tipo, fala, **dados):
        return {"tipo": tipo, "fala": fala, "legenda": fala, "dados": dados}
    batidas = [
        batida("frase", abertura),
        batida("resumo", previsoes, cidades=cidades, titulo="CIDADES E BAIRROS"),
        batida("frase", frase_chuva),
        batida("cta", chamada, chamada="ENVIE PARA A REGIÃO"),
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
    }
    (destino / "REEL.metadata.json").write_text(
        json.dumps(ficha, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"forecast": {"today": bloco, "tomorrow": bloco}}, cidades, batidas
