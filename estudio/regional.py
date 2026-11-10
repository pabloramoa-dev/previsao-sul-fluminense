"""Boletins regionais de 6h e 18h, com destaque rotativo entre cinco cidades."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from num2words import num2words
from coletar_tempo import resumo_cinco, MAIORES

TZ = ZoneInfo("America/Sao_Paulo")

def escolher_destaque(cidades, data_publicacao=None):
    """Cinco maiores do cadastro editorial; gira por data local, sem inventar audiência."""
    if len(cidades) < 5:
        raise ValueError("São necessárias cinco cidades distintas")
    data_publicacao = data_publicacao or datetime.now(TZ).date()
    por_nome = {c["nome"]: c for c in cidades}
    disponiveis = [nome for nome in MAIORES if nome in por_nome]
    if len(disponiveis) != 5:
        raise ValueError("Ausência de cidade de maior audiência; publicação bloqueada")
    nome = disponiveis[data_publicacao.toordinal() % 5]
    resumo = [dict(c, vento_kmh=c.get("rajada_kmh")) for c in resumo_cinco(cidades)]
    # Mantém cinco cidades sem duplicar e garante a escolhida no primeiro quadro.
    restantes = [c for c in resumo if c["nome"] != nome]
    escolhidas = [dict(por_nome[nome], vento_kmh=por_nome[nome].get("rajada_kmh"))] + restantes[:4]
    return escolhidas

def preparar_boletim(dia, personagem, destino):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    cidades = escolher_destaque(dia["cidades"])
    manha = personagem == "bira"
    quando = "hoje" if manha else "amanhã"
    nome = "Bira do Tempo" if manha else "Bia"
    destaque = cidades[0]
    temperatura = round(destaque["max"])
    abertura = f"{destaque['nome']}: {temperatura} graus {quando}."
    # Narrar em blocos curtos, preservando os cinco municípios na tela.
    outras = []
    for c in cidades[1:]:
        mn = num2words(round(c["min"]), lang="pt_BR")
        mx = num2words(round(c["max"]), lang="pt_BR")
        outras.append(f"{c['nome']}, {mn} a {mx}.")
    previsoes = " ".join(outras)
    chamada = f"Manda pra quem passa por {destaque['nome']} {quando}."
    def batida(tipo, fala, **dados):
        return {"tipo": tipo, "fala": fala, "legenda": fala, "dados": dados}
    batidas = [
        batida("frase", abertura),
        batida("resumo", previsoes, cidades=cidades, titulo="CINCO CIDADES"),
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
    legenda.extend(f"{c['nome']}: {round(c['min'])}° a {round(c['max'])}°" for c in cidades)
    legenda += ["", chamada, "", "@previsaosulflu #SulFluminense #PrevisãoDoTempo"]
    (destino / "LEGENDA.txt").write_text("\n".join(legenda) + "\n", encoding="utf-8")
    ficha = {
        "formato": "manha_sulflu_20_25" if manha else "amanha_sulflu_20_25",
        "gancho": abertura,
        "cidade_destaque": destaque["nome"],
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
