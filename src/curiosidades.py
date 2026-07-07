# -*- coding: utf-8 -*-
"""
curiosidades.py -- Banco de 52 curiosidades/mitos do clima para o
carrossel "Mito ou Verdade" de domingo do @previsaosulfluminense.
Rotacao sem repeticao (1 por semana = 1 ano completo) via estado.json.
"""

import json
from pathlib import Path

ESTADO_PATH = Path(__file__).parent / "estado.json"

# Cada item: titulo (afirmacao), veredito (MITO/VERDADE), explicacao, regional.
CURIOSIDADES = [
    {
        "titulo": "Raio nunca cai duas vezes no mesmo lugar.",
        "veredito": "MITO",
        "explicacao": "Cai, sim -- e varias vezes. Estruturas altas sao atingidas repetidamente por atrair as descargas.",
        "regional": "O Cristo Redentor, no Rio, leva varios raios todo ano.",
    },
    {
        "titulo": "Da pra saber a distancia de uma tempestade contando os segundos entre o raio e o trovao.",
        "veredito": "VERDADE",
        "explicacao": "A cada 3 segundos entre o clarao e o som, o raio esta a cerca de 1 km. O som viaja ~340 m/s.",
        "regional": "Util nas tardes de verao em Resende e na serra.",
    },
    {
        "titulo": "Neblina e sinal de que vai fazer calor no dia.",
        "veredito": "VERDADE",
        "explicacao": "Neblina de radiacao se forma em madrugadas de ceu limpo, que costumam anteceder dias ensolarados.",
        "regional": "Comum no Vale do Paraiba e na serra de Resende.",
    },
    {
        "titulo": "Voce pode se molhar mais correndo do que andando na chuva.",
        "veredito": "MITO",
        "explicacao": "Estudos mostram que correr geralmente molha menos, pois voce fica menos tempo exposto a chuva.",
        "regional": "",
    },
    {
        "titulo": "Fazer frio significa que nao vai chover.",
        "veredito": "MITO",
        "explicacao": "Frentes frias trazem justamente frio E chuva ao mesmo tempo. Uma coisa nao exclui a outra.",
        "regional": "Frentes frias que sobem pelo litoral chegam direto em Angra.",
    },
    {
        "titulo": "O ceu vermelho ao entardecer indica bom tempo no dia seguinte.",
        "veredito": "VERDADE",
        "explicacao": "Em geral sim: ceu avermelhado ao por do sol costuma indicar ar seco e estavel chegando pelo oeste.",
        "regional": "",
    },
    {
        "titulo": "Guarda-chuva atrai raio.",
        "veredito": "MITO",
        "explicacao": "O material comum nao atrai raio. O risco real e estar em campo aberto, sendo o ponto mais alto.",
        "regional": "",
    },
    {
        "titulo": "Faz mais calor no verao porque a Terra fica mais perto do Sol.",
        "veredito": "MITO",
        "explicacao": "E a inclinacao do eixo da Terra que causa as estacoes -- nao a distancia ate o Sol.",
        "regional": "",
    },
    {
        "titulo": "Da pra ter queimadura de sol mesmo em dia nublado.",
        "veredito": "VERDADE",
        "explicacao": "Ate 80% dos raios UV atravessam as nuvens. Protetor solar vale mesmo sem sol aparente.",
        "regional": "Vale pra quem vai a praia em Angra em dia encoberto.",
    },
    {
        "titulo": "Relampago e raio sao a mesma coisa.",
        "veredito": "MITO",
        "explicacao": "Raio e a descarga eletrica; relampago e o clarao de luz que ela produz; trovao e o som.",
        "regional": "",
    },
    {
        "titulo": "Umidade alta faz o calor parecer pior do que e.",
        "veredito": "VERDADE",
        "explicacao": "Com muita umidade o suor evapora menos, o corpo esfria pior e a sensacao termica sobe.",
        "regional": "Sensacao abafada e tipica do litoral de Angra no verao.",
    },
    {
        "titulo": "Beber alcool esquenta o corpo no frio.",
        "veredito": "MITO",
        "explicacao": "Da sensacao momentanea de calor, mas dilata os vasos e faz o corpo perder calor mais rapido.",
        "regional": "",
    },
    {
        "titulo": "A friagem no Sul Fluminense vem do ar polar.",
        "veredito": "VERDADE",
        "explicacao": "Massas de ar polar sobem pelo continente e derrubam a temperatura, principalmente no inverno.",
        "regional": "O Vale do Paraiba sente forte por causa do relevo.",
    },
    {
        "titulo": "Chove mais no fim de semana do que nos dias uteis.",
        "veredito": "MITO",
        "explicacao": "E vies de percepcao: a chuva incomoda mais quando atrapalha o lazer, entao voce lembra dela.",
        "regional": "",
    },
    {
        "titulo": "Trovao pode machucar alguem.",
        "veredito": "MITO",
        "explicacao": "O trovao e so o som. Quem causa dano e o raio. Mas o som avisa que ha raios por perto.",
        "regional": "",
    },
    {
        "titulo": "Faz mais frio no alto da serra do que embaixo.",
        "veredito": "VERDADE",
        "explicacao": "A temperatura cai cerca de 6,5 C a cada 1000 m de altitude. Quanto mais alto, mais frio.",
        "regional": "Por isso a serra de Resende e bem mais fria que o vale.",
    },
    {
        "titulo": "Nuvem carregada e escura sempre significa chuva.",
        "veredito": "MITO",
        "explicacao": "Nem toda nuvem escura chove; depende da umidade e das correntes de ar. Mas o risco aumenta.",
        "regional": "",
    },
    {
        "titulo": "Granizo pode cair no verao.",
        "veredito": "VERDADE",
        "explicacao": "Sim: tempestades fortes de verao tem correntes de ar que congelam gotas nas camadas altas.",
        "regional": "Ja houve registros de granizo em cidades do Sul Fluminense.",
    },
    {
        "titulo": "O ar-condicionado gasta menos se ficar ligado o dia todo.",
        "veredito": "MITO",
        "explicacao": "Nao. Desligar quando nao precisa economiza energia, mesmo considerando o gasto de religar.",
        "regional": "",
    },
    {
        "titulo": "A lua influencia as mares.",
        "veredito": "VERDADE",
        "explicacao": "A gravidade da Lua (e do Sol) e a principal responsavel pelo sobe e desce das mares.",
        "regional": "Faz diferenca para quem navega na Baia da Ilha Grande.",
    },
    {
        "titulo": "Sentir dor no joelho preve chuva.",
        "veredito": "VERDADE",
        "explicacao": "Tem base real: a queda de pressao atmosferica antes da chuva pode aumentar dores articulares.",
        "regional": "",
    },
    {
        "titulo": "Abrir a janela do carro gasta menos combustivel que ligar o ar.",
        "veredito": "MITO",
        "explicacao": "Em velocidade de estrada, janela aberta gera arrasto e pode gastar mais que o ar-condicionado.",
        "regional": "Vale lembrar de quem pega a Via Dutra.",
    },
    {
        "titulo": "Existe 'calor de chuva' antes de temporais.",
        "veredito": "VERDADE",
        "explicacao": "O abafamento antes da chuva e real: calor e umidade se acumulam e alimentam a tempestade.",
        "regional": "Sensacao classica das tardes de verao na regiao.",
    },
    {
        "titulo": "Estrelas cintilam porque estao piscando.",
        "veredito": "MITO",
        "explicacao": "Elas nao piscam. A luz e distorcida pela atmosfera turbulenta, criando o efeito de cintilacao.",
        "regional": "",
    },
    {
        "titulo": "Dias mais curtos no inverno significam menos horas de sol.",
        "veredito": "VERDADE",
        "explicacao": "No inverno o Sol nasce mais tarde e se poe mais cedo, reduzindo as horas de luz.",
        "regional": "",
    },
    {
        "titulo": "Arco-iris so aparece depois da chuva.",
        "veredito": "MITO",
        "explicacao": "Aparece sempre que ha gotas de agua e luz do sol no angulo certo -- inclusive em cachoeiras.",
        "regional": "Da pra ver nas cachoeiras de Resende e Itatiaia.",
    },
    {
        "titulo": "Vento forte sempre vem antes da chuva.",
        "veredito": "VERDADE",
        "explicacao": "As rajadas de ar frio que descem das tempestades costumam chegar pouco antes do aguaceiro.",
        "regional": "",
    },
    {
        "titulo": "A cor do ceu azul e reflexo do mar.",
        "veredito": "MITO",
        "explicacao": "O ceu e azul porque a atmosfera espalha mais a luz azul do Sol (espalhamento de Rayleigh).",
        "regional": "",
    },
    {
        "titulo": "Fazer muito frio mata os mosquitos da dengue.",
        "veredito": "VERDADE",
        "explicacao": "O frio reduz muito a atividade e a reproducao do Aedes, mas ele volta com o calor.",
        "regional": "Por isso os casos caem no inverno do Sul Fluminense.",
    },
    {
        "titulo": "Nuvem em formato de 'bigorna' indica tempestade forte.",
        "veredito": "VERDADE",
        "explicacao": "E a cumulonimbus, a nuvem das tempestades, com raios, ventos e as vezes granizo.",
        "regional": "",
    },
    {
        "titulo": "Beber agua gelada no calor 'choca' e faz mal.",
        "veredito": "MITO",
        "explicacao": "Nao faz mal ao corpo saudavel. Hidratar-se no calor e essencial, gelada ou natural.",
        "regional": "",
    },
    {
        "titulo": "A umidade do ar pode chegar a 100%.",
        "veredito": "VERDADE",
        "explicacao": "Sim, e nesse ponto o ar esta saturado -- e quando se forma orvalho, neblina ou chuva.",
        "regional": "Manhas de serra chegam perto disso.",
    },
    {
        "titulo": "Colocar o celular no arroz seca a agua por dentro.",
        "veredito": "MITO",
        "explicacao": "O arroz nao e eficiente e ainda solta po. O ideal e desligar e levar a assistencia.",
        "regional": "",
    },
    {
        "titulo": "Existe neve no Brasil.",
        "veredito": "VERDADE",
        "explicacao": "Neva ocasionalmente na serra do Sul do pais, em altitudes elevadas e frio intenso.",
        "regional": "No Sul Fluminense e rarissimo, mas ha geada em Itatiaia.",
    },
    {
        "titulo": "Temperatura e sensacao termica sao a mesma coisa.",
        "veredito": "MITO",
        "explicacao": "Nao. Vento e umidade mudam como o corpo percebe o calor ou o frio -- a sensacao difere do termometro.",
        "regional": "",
    },
    {
        "titulo": "O ponto mais quente do dia e ao meio-dia.",
        "veredito": "MITO",
        "explicacao": "Costuma ser entre 14h e 16h: o solo continua acumulando e liberando calor depois do meio-dia.",
        "regional": "",
    },
    {
        "titulo": "Geada pode queimar plantas.",
        "veredito": "VERDADE",
        "explicacao": "O congelamento rompe as celulas das folhas, deixando-as escuras como se estivessem queimadas.",
        "regional": "Afeta lavouras na regiao serrana no inverno.",
    },
    {
        "titulo": "Chuva 'limpa' o ar da poluicao.",
        "veredito": "VERDADE",
        "explicacao": "As gotas arrastam poeira e poluentes para o chao, melhorando a qualidade do ar apos a chuva.",
        "regional": "Perceptivel em areas industriais como Volta Redonda.",
    },
    {
        "titulo": "Da pra prever o tempo olhando o comportamento dos animais.",
        "veredito": "VERDADE",
        "explicacao": "Parcialmente: alguns animais reagem a quedas de pressao e umidade antes da chuva.",
        "regional": "",
    },
    {
        "titulo": "Faz mais frio de madrugada porque o sol 'apagou'.",
        "veredito": "VERDADE",
        "explicacao": "Sem sol, a superficie perde calor a noite toda; o ponto mais frio e pouco antes do amanhecer.",
        "regional": "",
    },
    {
        "titulo": "Ceu muito estrelado a noite indica frio pela manha.",
        "veredito": "VERDADE",
        "explicacao": "Ceu limpo deixa o calor escapar a noite, favorecendo madrugadas mais frias.",
        "regional": "Regra pratica que funciona na serra da regiao.",
    },
    {
        "titulo": "Raios sao mais quentes que a superficie do Sol.",
        "veredito": "VERDADE",
        "explicacao": "O canal de um raio pode passar de 27.000 C -- cerca de 5 vezes a superficie do Sol.",
        "regional": "",
    },
    {
        "titulo": "Ventilador esfria o ar do quarto.",
        "veredito": "MITO",
        "explicacao": "Ele nao baixa a temperatura; so movimenta o ar e ajuda o suor a evaporar, dando sensacao de frescor.",
        "regional": "",
    },
    {
        "titulo": "A previsao do tempo e so 'chute'.",
        "veredito": "MITO",
        "explicacao": "E baseada em modelos matematicos e dados de satelite. A precisao de curto prazo e muito alta hoje.",
        "regional": "",
    },
    {
        "titulo": "Chove por causa da evaporacao da agua.",
        "veredito": "VERDADE",
        "explicacao": "A agua evapora, forma nuvens e depois volta como chuva -- e o ciclo da agua.",
        "regional": "Represas e o rio Paraiba do Sul alimentam esse ciclo local.",
    },
    {
        "titulo": "Molhar a cabeca no frio causa gripe.",
        "veredito": "MITO",
        "explicacao": "Gripe e causada por virus, nao pelo frio em si. O frio so facilita a transmissao em ambientes fechados.",
        "regional": "",
    },
    {
        "titulo": "O vento tem 'direcao de onde vem', nao pra onde vai.",
        "veredito": "VERDADE",
        "explicacao": "Vento 'sul' e o que sopra do sul para o norte. Ele e nomeado pela origem.",
        "regional": "",
    },
    {
        "titulo": "Da pra ver o mesmo arco-iris que outra pessoa.",
        "veredito": "MITO",
        "explicacao": "Cada pessoa ve seu proprio arco-iris -- ele depende do angulo exato entre voce, o sol e as gotas.",
        "regional": "",
    },
    {
        "titulo": "Pressao atmosferica alta indica bom tempo.",
        "veredito": "VERDADE",
        "explicacao": "Alta pressao costuma trazer ceu limpo e estavel; baixa pressao favorece nuvens e chuva.",
        "regional": "",
    },
    {
        "titulo": "Faz mais calor na cidade do que no campo.",
        "veredito": "VERDADE",
        "explicacao": "E a 'ilha de calor': asfalto e concreto acumulam calor, deixando centros urbanos mais quentes.",
        "regional": "Sentido no centro de Volta Redonda e Barra Mansa.",
    },
    {
        "titulo": "Neblina e nevoa sao a mesma coisa.",
        "veredito": "MITO",
        "explicacao": "A diferenca e a visibilidade: neblina reduz a menos de 1 km; nevoa e mais leve, acima disso.",
        "regional": "Importante para quem dirige na Dutra de manha.",
    },
    {
        "titulo": "O verao e a estacao mais chuvosa no Sudeste.",
        "veredito": "VERDADE",
        "explicacao": "Sim: o calor e a umidade do verao alimentam as tempestades de fim de tarde tipicas da regiao.",
        "regional": "Dezembro a marco concentram as chuvas no Sul Fluminense.",
    },
]


def _carregar_estado():
    if ESTADO_PATH.exists():
        return json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
    return {}


def _salvar_estado(estado):
    ESTADO_PATH.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def escolher_curiosidade() -> dict:
    """Retorna a proxima curiosidade em rotacao, sem repetir ate esgotar as 52."""
    estado = _carregar_estado()
    indice = estado.get("indice_curiosidade", 0) % len(CURIOSIDADES)
    item = CURIOSIDADES[indice]

    estado["indice_curiosidade"] = indice + 1
    _salvar_estado(estado)

    return item
