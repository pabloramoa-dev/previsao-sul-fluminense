"""Bairros em foco dos Reels. Curadoria de nomes presentes em dm/dm_bairro.py.

A previsao disponivel no boletim e MUNICIPAL, nao bairro a bairro. Portanto
o bairro e uma referencia editorial de identificacao; nao um ponto de
medicao nem um local onde se comprovou mais chuva.
"""
from datetime import date

BAIRROS_EM_FOCO = {
    "Volta Redonda": ("Retiro", "Aterrado", "Vila Santa Cecília", "Jardim Amália",
                      "Santo Agostinho", "Ponte Alta", "Água Limpa", "Três Poços",
                      "Vila Mury", "Santa Cruz", "Niterói", "São Geraldo"),
    "Barra Mansa": ("Ano Bom", "Vila Nova", "Vila Coringa", "Saudade",
                    "Nove de Abril", "Rialto", "Vista Alegre", "Cotiara",
                    "Jardim Boa Vista", "Centro"),
    "Resende": ("Campos Elíseos", "Cidade Alegria", "Manejo", "Jardim Jalisco",
                "Itapuca", "Paraíso", "Centro", "Morada do Contorno"),
    "Barra do Piraí": ("Areal", "Maracanã", "Ponte Preta", "Parque Santana",
                       "Muqueca", "Roseira", "Centro"),
    "Itatiaia": ("Centro", "Fazenda Penedo", "Vila de Maringá", "Vila Odete"),
    "Porto Real": ("Bulhões", "Centro"),
    "Quatis": ("Mirandópolis", "Alto Paraíso", "Barrinha", "Jardim Polastri",
               "Centro", "São Benedito"),
    "Pinheiral": ("Centro",),  # unica referencia validada no cadastro atual
    "Rio Claro": ("Lídice", "Passa Três", "Getulândia", "Centro",
                  "São João Marcos"),
    "Piraí": ("Arrozal", "Monumento", "Ribeirão das Lajes", "Centro"),
    "Angra dos Reis": ("Japuíba", "Frade", "Bracuí", "Jacuecanga",
                       "Mambucaba", "Parque Mambucaba", "Balneário", "Camorim"),
}


def bairro_do_dia(cidade: str, data_publicacao: date, turno: str = "bira") -> str | None:
    """Giro por data LOCAL de publicacao, com bairro diferente no turno da tarde.

    Para localidades com um unico nome validado, mantemos o dado correto em
    vez de inventar bairros para simular variedade.
    """
    bairros = BAIRROS_EM_FOCO.get(cidade, ())
    if not bairros:
        return None
    deslocamento = 1 if turno == "bia" else 0
    return bairros[(data_publicacao.toordinal() + deslocamento) % len(bairros)]
