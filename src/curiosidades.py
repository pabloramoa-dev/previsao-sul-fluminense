# -*- coding: utf-8 -*-
"""
curiosidades.py -- Banco de 52 curiosidades/mitos do clima para o
carrossel "Mito ou Verdade" de domingo do @previsaosulflu.
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
        "explicacao": "Cai, sim -- e várias vezes. Estruturas altas são atingidas repetidamente por atrair as descargas.",
        "regional": "O Cristo Redentor, no Rio, leva varios raios todo ano.",
    },
    {
        "titulo": "Dá pra saber a distância de uma tempestade contando os segundos entre o raio e o trovão.",
        "veredito": "VERDADE",
        "explicacao": "A cada 3 segundos entre o clarão e o som, o raio está a cerca de 1 km. O som viaja ~340 m/s.",
        "regional": "Útil nas tardes de verão em Resende e na serra.",
    },
    {
        "titulo": "Neblina é sinal de que vai fazer calor no dia.",
        "veredito": "VERDADE",
        "explicacao": "Neblina de radiação se forma em madrugadas de céu limpo, que costumam anteceder dias ensolarados.",
        "regional": "Comum no Vale do Paraíba e na serra de Resende.",
    },
    {
        "titulo": "Você pode se molhar mais correndo do que andando na chuva.",
        "veredito": "MITO",
        "explicacao": "Estudos mostram que correr geralmente molha menos, pois você fica menos tempo exposto à chuva.",
        "regional": "",
    },
    {
        "titulo": "Fazer frio significa que não vai chover.",
        "veredito": "MITO",
        "explicacao": "Frentes frias trazem justamente frio E chuva ao mesmo tempo. Uma coisa não exclui a outra.",
        "regional": "Frentes frias que sobem pelo litoral chegam direto em Angra.",
    },
    {
        "titulo": "O céu vermelho ao entardecer indica bom tempo no dia seguinte.",
        "veredito": "VERDADE",
        "explicacao": "Em geral sim: céu avermelhado ao pôr do sol costuma indicar ar seco e estável chegando pelo oeste.",
        "regional": "",
    },
    {
        "titulo": "Guarda-chuva atrai raio.",
        "veredito": "MITO",
        "explicacao": "O material comum não atrai raio. O risco real é estar em campo aberto, sendo o ponto mais alto.",
        "regional": "",
    },
    {
        "titulo": "Faz mais calor no verão porque a Terra fica mais perto do Sol.",
        "veredito": "MITO",
        "explicacao": "É a inclinação do eixo da Terra que causa as estações -- não a distância até o Sol.",
        "regional": "",
    },
    {
        "titulo": "Dá pra ter queimadura de sol mesmo em dia nublado.",
        "veredito": "VERDADE",
        "explicacao": "Até 80% dos raios UV atravessam as nuvens. Protetor solar vale mesmo sem sol aparente.",
        "regional": "Vale pra quem vai à praia em Angra em dia encoberto.",
    },
    {
        "titulo": "Relâmpago e raio são a mesma coisa.",
        "veredito": "MITO",
        "explicacao": "Raio é a descarga elétrica; relâmpago é o clarão de luz que ela produz; trovão é o som.",
        "regional": "",
    },
    {
        "titulo": "Umidade alta faz o calor parecer pior do que é.",
        "veredito": "VERDADE",
        "explicacao": "Com muita umidade o suor evapora menos, o corpo esfria pior e a sensação térmica sobe.",
        "regional": "Sensação abafada é típica do litoral de Angra no verão.",
    },
    {
        "titulo": "Beber álcool esquenta o corpo no frio.",
        "veredito": "MITO",
        "explicacao": "Dá sensação momentânea de calor, mas dilata os vasos e faz o corpo perder calor mais rápido.",
        "regional": "",
    },
    {
        "titulo": "A friagem no Sul Fluminense vem do ar polar.",
        "veredito": "VERDADE",
        "explicacao": "Massas de ar polar sobem pelo continente e derrubam a temperatura, principalmente no inverno.",
        "regional": "O Vale do Paraíba sente forte por causa do relevo.",
    },
    {
        "titulo": "Chove mais no fim de semana do que nos dias úteis.",
        "veredito": "MITO",
        "explicacao": "É viés de percepção: a chuva incomoda mais quando atrapalha o lazer, então você lembra dela.",
        "regional": "",
    },
    {
        "titulo": "Trovão pode machucar alguém.",
        "veredito": "MITO",
        "explicacao": "O trovão é só o som. Quem causa dano é o raio. Mas o som avisa que há raios por perto.",
        "regional": "",
    },
    {
        "titulo": "Faz mais frio no alto da serra do que embaixo.",
        "veredito": "VERDADE",
        "explicacao": "A temperatura cai cerca de 6,5 C a cada 1000 m de altitude. Quanto mais alto, mais frio.",
        "regional": "Por isso a serra de Resende é bem mais fria que o vale.",
    },
    {
        "titulo": "Nuvem carregada e escura sempre significa chuva.",
        "veredito": "MITO",
        "explicacao": "Nem toda nuvem escura chove; depende da umidade e das correntes de ar. Mas o risco aumenta.",
        "regional": "",
    },
    {
        "titulo": "Granizo pode cair no verão.",
        "veredito": "VERDADE",
        "explicacao": "Sim: tempestades fortes de verão têm correntes de ar que congelam gotas nas camadas altas.",
        "regional": "Já houve registros de granizo em cidades do Sul Fluminense.",
    },
    {
        "titulo": "O ar-condicionado gasta menos se ficar ligado o dia todo.",
        "veredito": "MITO",
        "explicacao": "Não. Desligar quando não precisa economiza energia, mesmo considerando o gasto de religar.",
        "regional": "",
    },
    {
        "titulo": "A lua influencia as marés.",
        "veredito": "VERDADE",
        "explicacao": "A gravidade da Lua (e do Sol) é a principal responsável pelo sobe e desce das marés.",
        "regional": "Faz diferença para quem navega na Baía da Ilha Grande.",
    },
    {
        "titulo": "Sentir dor no joelho prevê chuva.",
        "veredito": "VERDADE",
        "explicacao": "Tem base real: a queda de pressão atmosférica antes da chuva pode aumentar dores articulares.",
        "regional": "",
    },
    {
        "titulo": "Abrir a janela do carro gasta menos combustível que ligar o ar.",
        "veredito": "MITO",
        "explicacao": "Em velocidade de estrada, janela aberta gera arrasto e pode gastar mais que o ar-condicionado.",
        "regional": "Vale lembrar de quem pega a Via Dutra.",
    },
    {
        "titulo": "Existe 'calor de chuva' antes de temporais.",
        "veredito": "VERDADE",
        "explicacao": "O abafamento antes da chuva é real: calor e umidade se acumulam e alimentam a tempestade.",
        "regional": "Sensação clássica das tardes de verão na região.",
    },
    {
        "titulo": "Estrelas cintilam porque estão piscando.",
        "veredito": "MITO",
        "explicacao": "Elas não piscam. A luz é distorcida pela atmosfera turbulenta, criando o efeito de cintilação.",
        "regional": "",
    },
    {
        "titulo": "Dias mais curtos no inverno significam menos horas de sol.",
        "veredito": "VERDADE",
        "explicacao": "No inverno o Sol nasce mais tarde e se põe mais cedo, reduzindo as horas de luz.",
        "regional": "",
    },
    {
        "titulo": "Arco-íris só aparece depois da chuva.",
        "veredito": "MITO",
        "explicacao": "Aparece sempre que há gotas de água e luz do sol no ângulo certo -- inclusive em cachoeiras.",
        "regional": "Dá pra ver nas cachoeiras de Resende e Itatiaia.",
    },
    {
        "titulo": "Vento forte sempre vem antes da chuva.",
        "veredito": "VERDADE",
        "explicacao": "As rajadas de ar frio que descem das tempestades costumam chegar pouco antes do aguaceiro.",
        "regional": "",
    },
    {
        "titulo": "A cor do céu azul é reflexo do mar.",
        "veredito": "MITO",
        "explicacao": "O céu é azul porque a atmosfera espalha mais a luz azul do Sol (espalhamento de Rayleigh).",
        "regional": "",
    },
    {
        "titulo": "Fazer muito frio mata os mosquitos da dengue.",
        "veredito": "VERDADE",
        "explicacao": "O frio reduz muito a atividade e a reprodução do Aedes, mas ele volta com o calor.",
        "regional": "Por isso os casos caem no inverno do Sul Fluminense.",
    },
    {
        "titulo": "Nuvem em formato de 'bigorna' indica tempestade forte.",
        "veredito": "VERDADE",
        "explicacao": "É a cumulonimbus, a nuvem das tempestades, com raios, ventos e às vezes granizo.",
        "regional": "",
    },
    {
        "titulo": "Beber água gelada no calor 'choca' e faz mal.",
        "veredito": "MITO",
        "explicacao": "Não faz mal ao corpo saudável. Hidratar-se no calor é essencial, gelada ou natural.",
        "regional": "",
    },
    {
        "titulo": "A umidade do ar pode chegar a 100%.",
        "veredito": "VERDADE",
        "explicacao": "Sim, e nesse ponto o ar está saturado -- é quando se forma orvalho, neblina ou chuva.",
        "regional": "Manhãs de serra chegam perto disso.",
    },
    {
        "titulo": "Colocar o celular no arroz seca a água por dentro.",
        "veredito": "MITO",
        "explicacao": "O arroz não é eficiente e ainda solta pó. O ideal é desligar e levar à assistência.",
        "regional": "",
    },
    {
        "titulo": "Existe neve no Brasil.",
        "veredito": "VERDADE",
        "explicacao": "Neva ocasionalmente na serra do Sul do país, em altitudes elevadas e frio intenso.",
        "regional": "No Sul Fluminense é raríssimo, mas há geada em Itatiaia.",
    },
    {
        "titulo": "Temperatura e sensação térmica são a mesma coisa.",
        "veredito": "MITO",
        "explicacao": "Não. Vento e umidade mudam como o corpo percebe o calor ou o frio -- a sensação difere do termômetro.",
        "regional": "",
    },
    {
        "titulo": "O ponto mais quente do dia é ao meio-dia.",
        "veredito": "MITO",
        "explicacao": "Costuma ser entre 14h e 16h: o solo continua acumulando e liberando calor depois do meio-dia.",
        "regional": "",
    },
    {
        "titulo": "Geada pode queimar plantas.",
        "veredito": "VERDADE",
        "explicacao": "O congelamento rompe as células das folhas, deixando-as escuras como se estivessem queimadas.",
        "regional": "Afeta lavouras na região serrana no inverno.",
    },
    {
        "titulo": "Chuva 'limpa' o ar da poluição.",
        "veredito": "VERDADE",
        "explicacao": "As gotas arrastam poeira e poluentes para o chão, melhorando a qualidade do ar após a chuva.",
        "regional": "Perceptível em áreas industriais como Volta Redonda.",
    },
    {
        "titulo": "Dá pra prever o tempo olhando o comportamento dos animais.",
        "veredito": "VERDADE",
        "explicacao": "Parcialmente: alguns animais reagem a quedas de pressão e umidade antes da chuva.",
        "regional": "",
    },
    {
        "titulo": "Faz mais frio de madrugada porque o sol 'apagou'.",
        "veredito": "VERDADE",
        "explicacao": "Sem sol, a superfície perde calor à noite toda; o ponto mais frio é pouco antes do amanhecer.",
        "regional": "",
    },
    {
        "titulo": "Céu muito estrelado à noite indica frio pela manhã.",
        "veredito": "VERDADE",
        "explicacao": "Céu limpo deixa o calor escapar à noite, favorecendo madrugadas mais frias.",
        "regional": "Regra prática que funciona na serra da região.",
    },
    {
        "titulo": "Raios são mais quentes que a superfície do Sol.",
        "veredito": "VERDADE",
        "explicacao": "O canal de um raio pode passar de 27.000 C -- cerca de 5 vezes a superfície do Sol.",
        "regional": "",
    },
    {
        "titulo": "Ventilador esfria o ar do quarto.",
        "veredito": "MITO",
        "explicacao": "Ele não baixa a temperatura; só movimenta o ar e ajuda o suor a evaporar, dando sensação de frescor.",
        "regional": "",
    },
    {
        "titulo": "A previsão do tempo é só 'chute'.",
        "veredito": "MITO",
        "explicacao": "É baseada em modelos matemáticos e dados de satélite. A precisão de curto prazo é muito alta hoje.",
        "regional": "",
    },
    {
        "titulo": "Chove por causa da evaporação da água.",
        "veredito": "VERDADE",
        "explicacao": "A água evapora, forma nuvens e depois volta como chuva -- é o ciclo da água.",
        "regional": "Represas e o rio Paraíba do Sul alimentam esse ciclo local.",
    },
    {
        "titulo": "Molhar a cabeça no frio causa gripe.",
        "veredito": "MITO",
        "explicacao": "Gripe é causada por vírus, não pelo frio em si. O frio só facilita a transmissão em ambientes fechados.",
        "regional": "",
    },
    {
        "titulo": "O vento tem 'direção de onde vem', não pra onde vai.",
        "veredito": "VERDADE",
        "explicacao": "Vento 'sul' é o que sopra do sul para o norte. Ele é nomeado pela origem.",
        "regional": "",
    },
    {
        "titulo": "Dá pra ver o mesmo arco-íris que outra pessoa.",
        "veredito": "MITO",
        "explicacao": "Cada pessoa vê seu próprio arco-íris -- ele depende do ângulo exato entre você, o sol e as gotas.",
        "regional": "",
    },
    {
        "titulo": "Pressão atmosférica alta indica bom tempo.",
        "veredito": "VERDADE",
        "explicacao": "Alta pressão costuma trazer céu limpo e estável; baixa pressão favorece nuvens e chuva.",
        "regional": "",
    },
    {
        "titulo": "Faz mais calor na cidade do que no campo.",
        "veredito": "VERDADE",
        "explicacao": "É a 'ilha de calor': asfalto e concreto acumulam calor, deixando centros urbanos mais quentes.",
        "regional": "Sentido no centro de Volta Redonda e Barra Mansa.",
    },
    {
        "titulo": "Neblina e névoa são a mesma coisa.",
        "veredito": "MITO",
        "explicacao": "A diferença é a visibilidade: neblina reduz a menos de 1 km; névoa é mais leve, acima disso.",
        "regional": "Importante para quem dirige na Dutra de manhã.",
    },
    {
        "titulo": "O verão é a estação mais chuvosa no Sudeste.",
        "veredito": "VERDADE",
        "explicacao": "Sim: o calor e a umidade do verão alimentam as tempestades de fim de tarde típicas da região.",
        "regional": "Dezembro a março concentram as chuvas no Sul Fluminense.",
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
