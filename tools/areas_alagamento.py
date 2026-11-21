"""Pontos de atenção hidrológica do Sul Fluminense.

Base HISTÓRICA, não sensor de cheia, mapa de inundação em tempo real nem
previsão de bairro. Uso editorial SOMENTE após evento de chuva intensa
corroborado ou aviso oficial de tempestade. Fontes e datas em
docs/areas_inundacao_sulflu.md.

Não transformar menções a estes locais em afirmações de que estão alagando.
"""

# Cada entrada contém (curso d'água / mecanismo, locais documentados, evidência).
PONTOS = {
    "Volta Redonda": [
        ("Córrego Secades", ("Vila Santa Cecília (Rua 41)",), "transbordamento_2026"),
        ("Ribeirão Brandão e Córrego Cachoeirinha",
         ("Siderópolis", "Sessenta", "Vila Santa Cecília"), "historico_inea"),
        ("drenagem urbana", ("Vila Rica (Rua 23)", "Casa de Pedra", "Roma"), "alagamentos_2026"),
    ],
    "Barra Mansa": [
        ("Rio Barra Mansa", ("Nova Esperança", "São Luís", "Boa Sorte"), "historico_inea"),
        ("Rio Bananal", ("Santa Maria II", "Saudade", "Vila Maria"), "historico_inea"),
        ("Rio Bocaina", ("Bocaininha", "Siderlândia"), "historico_inea"),
        ("Córrego Cotiara", ("Roberto Silveira",), "historico_inea"),
        ("Rio Paraíba do Sul", ("Vista Alegre", "Centro", "Vila dos Remédios"), "alagamentos_2026"),
    ],
    "Resende": [
        ("Rio Sesmaria", ("Parque Ipiranga", "Jardim Brasília", "Jalisco"), "historico_inea_e_2026"),
        ("Canal Periférico e Ribeirão Preto",
         ("Alegria", "Baixada de Olaria", "Itapuca", "Liberdade"), "historico_inea"),
    ],
    "Itatiaia": [
        ("Rio Santo Antônio / Córrego da Cazunga",
         ("Nova Conquista", "Vila Martins", "Centro"), "historico_inea"),
    ],
    "Barra do Piraí": [
        ("Rio Piraí", ("Centro", "Chalet", "Muqueca"), "historico_inea_e_2022"),
        ("Rio Paraíba do Sul", ("trechos ribeirinhos da área urbana",), "historico_inea"),
    ],
    "Piraí": [
        ("Rio Piraí", ("Vale Verde I", "Vale Verde II", "Vila Nova Esperança",
                        "Asilo", "Centro", "Santanésia"), "registro_camara_2022"),
    ],
    "Quatis": [
        ("Ribeirão dos Quatis", ("Pilotos",), "transbordamento_2023"),
        ("drenagem urbana", ("Barrinha", "Mirandópolis"), "alagamentos_2023"),
    ],
    "Pinheiral": [
        ("Rio Paraíba do Sul", ("Parque Maíra (Loteamento Novo)",), "suscetibilidade_prefeitura"),
        ("Rio Caximbau / drenagem na Rodovia Benjamin Constant",
         ("km 9, ligação Pinheiral–Arrozal",), "alagamento_via_2026"),
    ],
    "Rio Claro": [
        ("Rio Claro", ("partes baixas da sede municipal",), "transbordamento_2026"),
        ("cursos d'água do distrito de Lídice",
         ("Lídice (moradias ribeirinhas)",), "cheias_defesa_civil_2026"),
    ],
    "Porto Real": [
        ("Rios Paraíba do Sul, Piá e Barreiro",
         ("fundos de vale e trechos ribeirinhos",), "suscetibilidade_plano_saneamento"),
    ],
}


def pontos(cidade: str):
    """Entradas publicáveis só como contexto histórico, sem extrapolar cidade."""
    return PONTOS.get(cidade, [])


def resumo(cidade: str, *, grupos: int = 1, locais_por_grupo: int = 2) -> str:
    """Texto compacto: localidade e curso d'água, SEM afirmar alagamento atual."""
    partes = []
    for rio, locais, _ in pontos(cidade)[:grupos]:
        prep = ('da' if rio.startswith('drenagem ')
                else 'dos' if rio.startswith(('Rios ', "cursos d'água"))
                else 'do')
        partes.append(f"{', '.join(locais[:locais_por_grupo])} (perto {prep} {rio})")
    return "; ".join(partes)


def cidades_com_chuva_intensa(eventos) -> set[str]:
    """Só evento 'chuva' confirmado nos dois modelos libera citação de bairros."""
    return {e["local"] for e in eventos if e.get("tipo") == "chuva"
            and e.get("modelos") and len(set(e["modelos"])) >= 2}
