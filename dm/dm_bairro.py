# -*- coding: utf-8 -*-
"""
dm_bairro.py - Resolve o bairro que a pessoa mandou na DM para uma das 14
cidades cobertas pelo @previsaosulflu.

Fonte dos bairros: base dos Correios (cepbrasil.org / ruacep.com.br), consultada
em 21/08/2026. Rio Claro entra por distritos, porque o municipio nao tem bairros
separados na base postal.

CUIDADO COM NOMES REPETIDOS. 23 nomes existem em mais de uma cidade, e "Centro"
existe nas cidades cobertas. Por isso o indice mapeia bairro -> LISTA de cidades, e nao
bairro -> cidade. Um dicionario simples faria o ultimo nome sobrescrever os
outros, e a pessoa de Resende que mandasse "Centro" receberia a previsao de
outra cidade sem ninguem perceber.
"""

from __future__ import annotations

import unicodedata

from rapidfuzz import process, fuzz

CIDADES = [
    "Volta Redonda", "Barra Mansa", "Porto Real", "Resende",
    "Barra do Piraí", "Piraí", "Itatiaia", "Quatis", "Pinheiral", "Rio Claro",
    "Angra dos Reis", "Paraty", "Valença", "Rio das Flores",
]

# Bairros por cidade
BAIRROS = {
"Volta Redonda": """Açude|Aero Clube|Água Limpa|Aterrado|Barreira Cravo|Bela Vista|Belmonte|Belo Horizonte|Bom Jesus|Brasilândia|Caieira|Cailândia|Candelária|Casa de Pedra|Centro|Colorado|Conforto|Coqueiros|Dom Bosco|Eldorado|Eucaliptal|Jardim Amália|Jardim Belvedere|Jardim Cidade do Aço|Jardim Esperança|Jardim Europa|Jardim Normandia|Jardim Paraíba|Jardim Ponte Alta|Jardim Primavera|Jardim Suíça|Jardim Tiradentes|Jardim Veneza|Jardim Vila Rica|Laranjal|Limoeiro|Mariana Torres|Minerlândia|Mirante do Vale|Monte Castelo|Morada do Campo|Morro da Conquista|Morro São Carlos|Niterói|Nossa Senhora das Graças|Nova Esperança|Nova Primavera|Nova São Luiz|Padre Josino|Parque das Ilhas|Parque Vitória|Pinto da Serra|Ponte Alta|Retiro|Rio das Flores|Roma|Rústico|San Remo|Santa Cruz|Santa Rita do Zarur|Santo Agostinho|São Carlos|São Cristóvão|São Geraldo|São João|São João Batista|São Lucas|São Luís|São Sebastião|Sessenta|Siderlândia|Siderópolis|Sidervile|Três Poços|Vale Verde|Vila Americana|Vila Brasília|Vila Mury|Vila Rica|Vila Santa Cecília|Voldac|Volta Grande""",
"Barra Mansa": """Nove de Abril|Abelhas|Água Comprida|Ano Bom|Antônio Rocha|Apóstolo Paulo|Assunção|Barbara|Boa Sorte|Boa Vista|Bocaininha|Bom Pastor|Cajueiro|Cantagalo|Centro|Colônia Santo Antônio|Cotiara|Floriano|Getúlio Vargas|Goiabal|Jardim Alvorada|Jardim América|Jardim Boa Vista|Jardim Central|Jardim Guanabara|Jardim Marilu|Jardim Ponte Alta|Jardim Primavera|Jardim Redentor|Mangueira|Metalúrgico|Minerlândia|Moinho de Vento|Monte Cristo|Morada da Colônia|Morada da Granja|Morada do Vale|Morada Verde|Nossa Senhora Aparecida|Nossa Senhora de Fátima|Nossa Senhora de Lourdes|Nossa Senhora do Amparo|Nossa Senhora dos Remédios|Nova Esperança|Novo Horizonte|Paraíso|Parque Independência|Piteiras|Pombal|Ponte Alta|Recanto do Sol|Rialto|Roberto Silveira|Roselândia|Santa Clara|Santa Inês|Santa Izabel|Santa Lúcia|Santa Maria|Santa Rita|Santa Rita de Cássia|Santa Rosa|São Carlos|São Domingos|São Francisco de Assis|São Genaro|São Judas Tadeu|São Lucas|São Luiz|São Paulo|São Pedro|São Sebastião|São Silvestre|Saudade|Siderlândia|Vale do Paraíba|Verbo Divino|Vila Coringa|Vila Elmira|Vila Independência|Vila Maria|Vila Nova|Vila Orlandélia|Vila Principal|Vila Ursulino|Village do Sol|Vista Alegre""",
"Resende": """Alambari|Alegria|Alto dos Passos|Alvorada|Barbosa Lima|Bela Vista|Boa Vista|Bulhões|Cabral|Campo Belo|Campos Elíseos|Casa da Lua|Castelo Branco|Centro|Cidade Alegria|Comercial|Elite|Eucaliptal|Fazenda Castelo|Fazenda da Barra|Fazenda Penedo|Guararapes|Independência|Itapuca|Jardim Alegria|Jardim Aliança|Jardim Beira Rio|Jardim Brasília|Jardim das Rosas|Jardim do Sol|Jardim Esperança|Jardim Jalisco|Jardim Martinelli|Jardim Primavera|Jardim Tropical|Lava-pés|Liberdade|Manejo|Mirante das Agulhas|Mirante de Serra|Monet|Monte Castelo|Montese|Morada da Barra|Morada da Colina|Morada da Felicidade|Morada da Montanha|Morada das Garças|Morada do Bosque|Morada do Castelo|Morada do Contorno|Nova Alegria|Nova Liberdade|Nova Resende|Novo Surubi|Paraíso|Parque Embaixador|Parque Ipiranga|Pólo Industrial|Residências do Campo|Residências do Vale|Santa Isabel|Santo Amaro|São Caetano|Surubi|Terras Alpha|Toyota|Vale dos Reis|Vicentino|Vila Adelaide|Vila Central|Vila Hulda Rocha|Vila Isabel|Vila Julieta|Vila Moderna|Vila Nossa Senhora de Fátima|Vila Santa Cecília|Vila Verde""",
"Barra do Piraí": """Areal|Arthur Cataldi|Belvedere da Taquara|Boa Sorte|Boca do Mato|Caieira São Pedro|Caieira Velha|Caixa D'Água Velha|Campo Bom|Cantão|Carvão|Centro|Chácara Farani|Chalet|Coimbra|Doutor Mesquita|Lago Azul|Maracanã|Matadouro|Metalúrgica|Morro do Gama|Muqueca|Nossa Senhora de Santana|Oficinas Velhas|Parque Almirante|Parque Santana|Parque São Joaquim|Parque São José|Ponte do Andrade|Ponte Preta|Ponte Vermelha|Química|Represa|Roseira|Santana da Barra|Santo Antônio|Santo Cristo|São João|São Luís|Vale do Ipiranga|Vargem Grande|Vila Helena|Vila Suíça""",
"Piraí": """Arrozal|Centro|Monumento|Ribeirão das Lajes|Rosa Machado""",
"Itatiaia": """Centro|Fazenda Penedo|Vila de Maringá|Vila Odete""",
"Porto Real": """Bulhões|Centro""",
"Quatis": """Alto Paraíso|Barrinha|Bela Vista|Centro|Falcão|Jardim Independência|Jardim Polastri|Loteamento Bondarovshy|Mirandópolis|Nossa Senhora do Rosário|Pilotos|Ribeirão de São Joaquim|Santa Bárbara|São Benedito|São Francisco de Assis|Vila Santo Antônio""",
"Pinheiral": """Centro""",
"Rio Claro": """Centro|Lídice|Passa Três|São João Marcos|Getulândia|Pouso Seco|Fazenda da Grama""",
"Angra dos Reis": """Centro|Balneário|Parque das Palmeiras|Japuíba|Frade|Bracuí|Jacuecanga|Monsuaba|Camorim|Praia da Chácara|Belém|Areal|Nova Angra|Verolme|Garatucaia|Mambucaba|Parque Mambucaba|Perequê|Vila do Abraão|Provetá|Araçatiba|Bonfim|Marinas|Morro da Cruz|Sapinhatuba|Encruzo da Enseada""",
"Paraty": """Centro Histórico|Centro|Jabaquara|Caborê|Portal das Artes|Parque Imperial|Ilha das Cobras|Mangueira|Patitiba|Chácara da Saudade|Pantanal|Corumbê|Penha|Trindade|Tarituba|Paraty-Mirim|Laranjeiras|Graúna|São Gonçalo""",
"Valença": """Centro|Barroso|Benfica|Biquinha|Cambota|Carambita|Canteiro|Esplanada do Cruzeiro|Jardim Valença|Monte D'Ouro|Osório|Parque Pentagna|Ponte Funda|Santa Cruz|São Francisco|São José das Palmeiras|Varginha|Conservatória|Barão de Juparanã|Pentagna|Parapeúna|Santa Isabel do Rio Preto""",
"Rio das Flores": """Centro|Taboas|Abarracamento|Manuel Duarte|Três Ilhas|Fazenda União|Formoso""",
}

BAIRROS = {c: [b.strip() for b in s.split("|") if b.strip()]
           for c, s in BAIRROS.items()}

# ---------------------------------------------------------------------------
# Trava de integridade dos dados.
#
# Este arquivo pode ser recriado copiando e colando (pelo GitHub, por um
# agente de navegador). Se um bairro sumir ou vier com o nome trocado, o robo
# passaria a responder a previsao da cidade errada em silencio -- que e
# exatamente o erro que este modulo existe para evitar.
#
# Por isso ele se recusa a carregar se os dados nao baterem. Falhar no deploy
# e barato; responder errado para o seguidor nao e.
BAIRROS_ESPERADOS = 399
CHECKSUM_ESPERADO = "1884781fd7b6"


def _conferir_integridade() -> None:
    import hashlib
    total = sum(len(v) for v in BAIRROS.values())
    if total != BAIRROS_ESPERADOS:
        raise RuntimeError(
            f"dm_bairro.py: esperava {BAIRROS_ESPERADOS} bairros, encontrei {total}. "
            "O arquivo foi copiado de forma incompleta.")
    assinatura = "|".join(f"{c}:{','.join(BAIRROS[c])}" for c in sorted(BAIRROS))
    soma = hashlib.sha256(assinatura.encode()).hexdigest()[:12]
    if soma != CHECKSUM_ESPERADO:
        raise RuntimeError(
            f"dm_bairro.py: checksum {soma}, esperado {CHECKSUM_ESPERADO}. "
            "Algum nome de bairro foi alterado na copia.")


_conferir_integridade()



def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.lower().replace("-", " ").split())


_CIDADES_NORM = {_norm(c): c for c in CIDADES}

# bairro normalizado -> lista de cidades que tem esse bairro
_INDICE: dict[str, list[str]] = {}
for _cidade, _lista in BAIRROS.items():
    for _b in _lista:
        _INDICE.setdefault(_norm(_b), []).append(_cidade)

# rotulo bonito do bairro, para responder com o nome como a pessoa conhece
_ROTULO = {_norm(b): b for lista in BAIRROS.values() for b in lista}

LIMIAR_CIDADE = 88
LIMIAR_BAIRRO = 86


def _achar(chave: str, universo, limiar: int):
    if not chave:
        return None
    achado = process.extractOne(chave, universo, scorer=fuzz.WRatio)
    if achado and achado[1] >= limiar:
        return achado[0]
    return None


def resolver(texto: str) -> tuple[str, object, object]:
    """Interpreta a mensagem. Devolve uma de tres situacoes:

    ("cidade",  "Resende",              "Jardim Jalisco (Resende)")
    ("ambiguo", ["Barra Mansa", ...],   "Centro")
    ("nao_achou", None, None)
    """
    chave = _norm(texto)
    if not chave:
        return ("nao_achou", None, None)

    # 1) A mensagem ja e o nome de uma cidade? (cobre a resposta a pergunta
    #    "qual cidade?", entao o fluxo funciona sem guardar estado nenhum)
    mc = _achar(chave, list(_CIDADES_NORM), LIMIAR_CIDADE)
    if mc:
        c = _CIDADES_NORM[mc]
        return ("cidade", c, c)

    # 2) A mensagem traz bairro E cidade juntos? ("centro de resende")
    for cn, cidade in _CIDADES_NORM.items():
        if cn in chave:
            sobra = chave.replace(cn, " ").replace(" de ", " ").strip()
            mb = _achar(sobra, list(_INDICE), LIMIAR_BAIRRO)
            if mb and cidade in _INDICE[mb]:
                return ("cidade", cidade, f"{_ROTULO[mb]} ({cidade})")
            # Quando a cidade vem explicita, aceite tambem localidades menores
            # que ainda nao estejam na lista postal. Isso amplia a cobertura sem
            # arriscar associar um bairro desconhecido a cidade errada.
            if sobra:
                conectores = {"de", "da", "do", "das", "dos", "e"}
                partes = [
                    p if p in conectores else p.capitalize()
                    for p in sobra.split()
                ]
                bairro_livre = " ".join(partes)
                return ("cidade", cidade, f"{bairro_livre} ({cidade})")
            return ("cidade", cidade, cidade)

    # 3) E um bairro conhecido?
    mb = _achar(chave, list(_INDICE), LIMIAR_BAIRRO)
    if mb:
        cidades = _INDICE[mb]
        if len(cidades) == 1:
            return ("cidade", cidades[0], f"{_ROTULO[mb]} ({cidades[0]})")
        # nome repetido em varias cidades -> precisa perguntar
        return ("ambiguo", cidades, _ROTULO[mb])

    # 4) Nao achou
    return ("nao_achou", None, None)


def _lista_humana(nomes) -> str:
    nomes = list(nomes)
    if len(nomes) == 1:
        return nomes[0]
    return ", ".join(nomes[:-1]) + " ou " + nomes[-1]


def montar_resposta_dm(texto: str, previsao_por_cidade: dict,
                       recomendar_roupa=None) -> str:
    situacao, dado, rotulo = resolver(texto)

    if situacao == "ambiguo":
        return (f"Existe {rotulo} em mais de uma cidade aqui 😅\n"
                f"Me diz qual: {_lista_humana(dado)}.")

    if situacao == "nao_achou":
        return ("Não achei esse bairro por aqui 😅. Me diz a tua CIDADE que eu "
                "já te passo a previsão 🌦️\n"
                f"👉 {_lista_humana(CIDADES)}.")

    p = previsao_por_cidade.get(dado)
    if not p:
        return (f"Ainda não tenho a previsão de {dado} agora. "
                "Tenta de novo daqui a pouco 🙏")

    linha_roupa = ""
    if recomendar_roupa:
        linha_roupa = recomendar_roupa(
            p["tmin"], p["tmax"], p["prob_chuva"], p.get("rajada_kmh", 0)) + "\n"

    return (f"📍 {rotulo} — hoje:\n"
            f"🌡️ {p['tmin']:.0f}° / {p['tmax']:.0f}°  "
            f"☔ chuva {p['prob_chuva']:.0f}%\n"
            f"{linha_roupa}\n"
            "Segue o @previsaosulflu pra receber isso todo dia. 🌦️")
