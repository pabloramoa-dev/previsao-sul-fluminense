from datetime import date
from num2words import num2words
from coletar_tempo import resumo_cinco


def preparar_boletim(dia, personagem, destino):
    cidades = [dict(c, vento_kmh=c.get("rajada_kmh")) for c in resumo_cinco(dia["cidades"])]
    if len(cidades) != 5:
        raise ValueError("O boletim requer cinco cidades distintas")
    manha = personagem == "bira"
    quando = "hoje" if manha else "amanhã"
    nome = "Bira do Tempo" if manha else "Bia da Orla"
    destaque = cidades[0]
    condicoes = {"sol": "sol", "chuva": "chuva", "nublado": "céu nublado",
                 "frio": "frio", "tempestade": "tempestade"}
    condicao = condicoes[destaque["cond"]]
    abertura = f"{'Bom dia' if manha else 'Boa tarde'}, Sul Fluminense! Aqui é {nome}."
    chamada = f"Para {quando}, a previsão em {destaque['nome']} é de {condicao}."
    linhas = []
    for c in cidades:
        minima = num2words(c["min"], lang="pt_BR")
        maxima = num2words(c["max"], lang="pt_BR")
        linhas.append(f"{c['nome']}, de {minima} a {maxima} graus.")
    def batida(tipo, fala, **dados):
        return {"tipo": tipo, "fala": fala, "legenda": fala, "dados": dados}
    batidas = [batida("nenhum", abertura), batida("frase", chamada),
               batida("resumo", " ".join(linhas), cidades=cidades, titulo="CINCO CIDADES"),
               batida("cta", "Acompanhe a previsão do Sul Fluminense.", chamada="SIGA A PREVISÃO")]
    bloco = {"date": dia["data"], "locations": [{"max_c": c["max"], "rain_mm": c["chuva_mm"]} for c in cidades]}
    data = date.fromisoformat(dia["data"]).strftime("%d/%m")
    legenda = [f"{nome} | Previsão para {quando}, {data}", chamada, ""]
    legenda.extend(f"{c['nome']}: {c['min']}° a {c['max']}°" for c in cidades)
    legenda.append("\n@previsaosulflu #SulFluminense #PrevisãoDoTempo")
    (destino / "LEGENDA.txt").write_text("\n".join(legenda), encoding="utf-8")
    return {"forecast": {"today": bloco, "tomorrow": bloco}}, cidades, batidas
