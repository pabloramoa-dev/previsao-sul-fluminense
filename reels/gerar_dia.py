#!/usr/bin/env python3
"""
gerar_dia.py — pipeline completo do Reel diário do Seu Ranzinza.

    dados do tempo  ->  roteiro ranzinza  ->  Kokoro  ->  lip sync  ->  Manim  ->  MP4

Uso:
    python gerar_dia.py --dados dia.json --saida REEL.mp4
    python gerar_dia.py --demo                 # usa dados de exemplo

Formato do dia.json (o que o Open-Meteo devolve, já resumido):
{
  "data": "2026-07-29",
  "cidades": [
    {"nome": "Volta Redonda", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0},
    ...
  ],
  "umidade_min": 30
}

O gerador de falas é uma MÁQUINA DE RESMUNGO: cada condição tem várias frases e
ele sorteia usando a data como semente. Assim o texto varia todo dia, mas é
reproduzível (rodar de novo no mesmo dia dá o mesmo vídeo).
"""
import argparse, json, os, random, subprocess, sys, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))


# =====================================================================
#  MÁQUINA DE RESMUNGO — a personalidade do velho
# =====================================================================
ABERTURAS = [
    "Bom dia. Ou nem tanto.",
    "Acordei. Infelizmente vocês também.",
    "Olha eu aqui de novo. Que alegria pra vocês.",
    "Bom dia. Já vou avisando: não melhorou.",
    "Bom dia. Preparados pra decepção?",
    "De novo eu, de novo cedo. Que sorte a de vocês.",
    "Acordei de mau humor. Novidade nenhuma.",
    "Bom dia. Vou ser breve, o tempo não merece.",
    "Olha a hora. E olha esse tempo.",
    "Bom dia. Sentem, porque não é boa notícia.",
    "Levantei cedo pra ver isso. Que desperdício.",
    "Bom dia. Alguém prometeu que hoje seria bom? Mentiu.",
    "Cá estou. Contra a minha vontade, como sempre.",
    "Bom dia. Café na mão que a notícia é longa.",
    "Acordei antes do galo pra reclamar em primeira mão.",
    "Bom dia. Não me olhem assim, a culpa é do céu.",
    "Mais um dia. Já começo cansado só de olhar lá fora.",
    "Bom dia. Vamos logo com isso, tenho mais o que resmungar.",
    "De pé desde cedo. O tempo, esse, continua o mesmo.",
    "Bom dia. Spoiler: não vão gostar.",
    "Cheguei. Tragam paciência, vão precisar.",
    "Bom dia. Hoje eu até tentei sorrir. Não deu.",
    "Aqui estou, pontual como a minha implicância.",
    "Bom dia. O sol nasceu, e o meu humor não.",
    "Levantei. Reclamar é meu exercício matinal.",
    "Bom dia. Preparei a previsão e a bronca junto.",
    "Mais uma manhã. Que emoção conter, não é.",
    "Bom dia. Sentaram? Então vamos ao estrago.",
    "Acordei. O mundo insiste em continuar girando.",
    "Bom dia. Já reclamando, pra não perder o costume.",
]

# CTA de seguir — entra no FIM DE TODO VÍDEO, na voz do personagem. Pedido
# seco funciona mal; no jeito dele (a contragosto) vira piada e as pessoas
# lembram. É a última batida antes do frame limpo que fecha o loop.
CTA = [
    "E segue o perfil. Não que eu me importe.",
    "Aperta o seguir aí. Faz isso por mim, vai.",
    "Se seguir, eu volto amanhã. Se não seguir, também volto.",
    "Segue aí. Custa o quê, um dedo?",
    "Segue o perfil. Já que perdeu tempo até aqui.",
    "Aperta o seguir. Não vai doer, prometo. Quase.",
    "Segue. Faça um velho feliz, pra variar.",
    "Clica no seguir. É de graça, diferente de tudo hoje.",
    "Segue aí, vai. Nem eu aguento repetir isso todo dia.",
    "Aperta o seguir. Depois não diga que não avisei do tempo.",
    "Segue o perfil. Assim divido meu mau humor com mais gente.",
    "Toca no seguir. É o mínimo depois de me ouvir reclamar.",
    "Segue. Prometo continuar rabugento, se é isso que te prende.",
    "Aperta ali no seguir. Um clique, uma boa ação.",
    "Segue o canal. Amanhã tem mais reclamação garantida.",
    "Clica no seguir antes que eu mude de ideia.",
    "Segue aí. Não é pedido, é quase uma ordem.",
    "Aperta o seguir. Faça de conta que gosta de mim.",
    "Segue o perfil. Eu finjo que não ligo, mas ligo.",
    "Toca no seguir. É rápido, ao contrário desse frio.",
    "Segue. Um velho ranzinza também precisa de plateia.",
    "Aperta ali. Seguir é grátis, chorar depois também.",
    "Segue o perfil pra não errar o guarda-chuva amanhã.",
    "Clica no seguir. Vai por mim, que erro pouco.",
    "Segue aí. Depois reclama comigo nos comentários.",
    "Aperta o seguir. Assim você me aguenta oficialmente.",
    "Segue o canal. Previsão certa e mau humor de brinde.",
    "Toca no seguir. Nem custa e ainda me faz companhia.",
    "Segue. Quem avisa tempo ruim merece ser seguido.",
    "Aperta o seguir. Depois não venha dizer que ninguém te avisou.",
]

FECHOS = [
    "Amanhã eu volto. Infelizmente.",
    "Amanhã tem mais. Preparem-se.",
    "É isso. Podem reclamar, não adianta.",
    "Amanhã eu conto o resto. Se eu estiver de bom humor.",
    "Por hoje chega. Já reclamei o suficiente.",
    "Fui. O tempo não melhora, mas o vídeo acaba.",
    "Amanhã volto. Vocês que aguentem.",
    "Acabou. Podem voltar às suas vidas atribuladas.",
    "É tudo por hoje. Não me agradeçam.",
    "Amanhã tem mais previsão e mais resmungo.",
    "Encerro por aqui. Meu joelho pede descanso.",
    "Fui. Guardem o guarda-chuva, vão precisar.",
    "Amanhã eu apareço de novo. Que sina.",
    "É isso, criaturas. Sumam antes que eu reclame mais.",
    "Por hoje é só. O céu que se explique amanhã.",
    "Acabou o sermão. Bom dia, ou o que sobrar dele.",
    "Volto amanhã, no mesmo horário, no mesmo mau humor.",
    "Chega. Já falei demais pra quem não vai ouvir.",
    "É o fim. Do vídeo, não do meu descontentamento.",
    "Amanhã continua. O tempo não tira folga, nem eu.",
    "Fecho por aqui. Levem casaco e levem juízo.",
    "Terminei. Podem discordar em silêncio.",
    "Amanhã eu conto como piorou. Porque vai.",
    "É isso aí. Agora me deixem resmungar em paz.",
    "Por hoje deu. Bebam água e não me irritem.",
    "Volto amanhã. Não por gosto, por teimosia.",
    "Acabou. Que o dia de vocês seja melhor que a previsão.",
    "Fui embora. O tempo que continue sem mim.",
    "Amanhã tem mais. Já peço desculpa adiantado.",
    "É o fim do vídeo. O começo da sua fila no ponto de ônibus.",
]

# a piada do personagem: ele reclama de TODO tipo de tempo, inclusive do bom.
# chaves sol/nublado/chuva/tempestade/frio vêm do campo `cond` do Open-Meteo;
# calor/abafado/ameno são DERIVADAS dos números por refinar_cond() — os mesmos
# limiares valem no vídeo da tarde (Dona Maria), então os dois nunca discordam.
RESMUNGO = {
    "sol": [
        "Sol de rachar. Depois não venham chorar com dor de cabeça.",
        "Esse sol não tem hora pra parar. Nem juízo.",
        "Céu limpo demais. Isso não presta, tem coisa vindo.",
        "Sol o dia todo. Ótimo pra queimar a nuca de quem esquece o boné.",
        "Céu azul, azul. Bonito pra quem não precisa sair na rua.",
        "Sol a pino. Vão derreter e a culpa vai sobrar pra mim.",
        "Nem uma nuvem. O sol hoje veio pra castigar.",
        "Sol firme. Aproveitem pra reclamar do calor, já que gostam.",
        "Céu aberto. Bom pra roupa no varal, ruim pro meu humor.",
        "Sol escaldante. Bebam água antes que virem passa.",
        "Dia ensolarado. Isso engana: parece bom, mas cansa.",
        "Sol das antigas. Do tipo que racha o asfalto e a paciência.",
        "Céu limpo. Vão dizer que está lindo. Eu digo que está quente.",
        "Sol sem trégua. Chapéu, protetor e paciência, nessa ordem.",
        "Muito sol. Ótimo pra quem tem piscina. Péssimo pro resto.",
        "Sol o tempo inteiro. Nem uma sombrinha de nuvem pra ajudar.",
        "Dia claro. O problema não é o sol, é vocês na rua ao meio-dia.",
        "Sol pesado. Não digam que eu não avisei da queimadura.",
        "Céu azul o dia todo. Bonito na foto, sofrido na pele.",
        "Sol de doer os olhos. Óculos escuros, e não é frescura.",
        "Sol firme e forte. Guardem energia, vão suar por ela.",
        "Dia de sol. Perfeito pra ficar dentro de casa, na minha opinião.",
        "Sol brabo. Cuidado com criança e com cachorro no sol.",
        "Céu escancarado. Nem uma nuvenzinha pra fazer companhia.",
        "Sol torrando tudo. Regue as plantas, senão elas reclamam mais que eu.",
        "Muito sol e nenhum alívio. Sombra vai ser disputada a tapa.",
        "Sol de verão em pleno dia ruim pra caminhada.",
        "Céu limpo demais pro meu gosto. Prefiro uma nuvem pra xingar.",
        "Sol constante. Passem protetor, ou depois não venham se queixar.",
        "Dia ensolarado. Bonito, sim. Confortável, nem tanto.",
    ],
    "nublado": [
        "Nublado. Nem chove, nem faz sol. Só enrola.",
        "Céu fechado o dia inteiro. Que animação.",
        "Nublado é o tempo dos indecisos.",
        "Cinza por cima, cinza por dentro. Combina comigo.",
        "Esse céu não decide nada. Igual gente que eu conheço.",
        "Nublado. Nem sombra pra reclamar, nem sol pra xingar.",
        "Dia sem graça. Que surpresa, hein.",
        "Céu carregado, mas sem coragem de chover. Frouxo.",
        "Nublado o dia todo. Um cinza sem começo nem fim.",
        "Tempo fechado. O sol tirou folga e não avisou ninguém.",
        "Céu de segunda-feira. Mesmo que seja quinta.",
        "Nublado. Perfeito pra combinar com o meu ânimo.",
        "Sol nenhum à vista. As nuvens tomaram conta e não largam.",
        "Dia encoberto. Nem escuro, nem claro. Uma indecisão só.",
        "Céu pesado. Parece que vai desabar, mas é só drama.",
        "Nublado sem chuva. O pior dos dois mundos, na verdade.",
        "Tempo fechado. Nem pra secar roupa serve direito.",
        "Céu acinzentado. Bonito pra poeta, chato pro resto.",
        "Nublado. Guardem a esperança de sol pra outro dia.",
        "Dia cinzento. Combina com café requentado e mau humor.",
        "Céu tampado. O sol está aí atrás, com preguiça de aparecer.",
        "Nublado firme. Nem sombra faz, de tão parado.",
        "Tempo encoberto. Vão sentir falta do sol, e com razão.",
        "Céu fechado. Um edredom cinza cobrindo a cidade inteira.",
        "Nublado o dia todo. Monótono como discurso comprido.",
        "Sem sol e sem chuva. O tempo hoje é morno de propósito.",
        "Céu carregado. Se decidir chover, eu volto pra avisar.",
        "Nublado. Dia bom pra dormir, ruim pra produzir.",
        "Tempo fechado desde cedo. E vai ficar assim, teimoso.",
        "Céu cinza. Nem preciso reclamar, ele reclama sozinho.",
    ],
    "chuva": [
        "Chuva o dia todo. Levem guarda-chuva, criaturas.",
        "Vai chover. Vai molhar. Vai reclamar. Eu avisei.",
        "Chuva de novo. Meu joelho já tinha avisado ontem.",
        "Chove hoje. Molha, atrasa, irrita. O pacote completo.",
        "Guarda-chuva na mão. Ou vão reclamar molhados depois.",
        "Vai chover. Meu joelho não erra, ao contrário do resto.",
        "Chuva chegando. Já era o cabelo de vocês.",
        "Dia de chuva. Perfeito pra encharcar o sapato novo.",
        "Chove sem parar. Levem capa, guarda-chuva e paciência.",
        "Chuva firme. O trânsito vai ficar pior que o meu humor.",
        "Vem água do céu. Fechem as janelas antes de sair.",
        "Chuva o dia inteiro. Roupa no varal, nem pensar.",
        "Molha hoje, molha bastante. Calçado fechado, criaturas.",
        "Chuva a caminho. Guardem o guarda-chuva perto da porta.",
        "Dia molhado. Quem esquecer a capa vai lembrar de mim.",
        "Chove desde cedo. Vai pingar na cabeça de quem duvidar.",
        "Água no céu e no chão. Cuidado com a poça traiçoeira.",
        "Chuva persistente. Do tipo que não pede licença.",
        "Vai chover forte. Não deixem nada de valor no quintal.",
        "Chuva o dia todo. Guarda-chuva bom, não aquele que vira do avesso.",
        "Molha e refresca. Mas encharca o pé de quem se atrasa.",
        "Chuva garantida. Já avisei: não venham me culpar depois.",
        "Dia chuvoso. Café quente, janela fechada, e me deixem em paz.",
        "Chove sem trégua. O céu hoje resolveu descarregar tudo.",
        "Vai cair água. Segurem o guarda-chuva firme, tem vento junto.",
        "Chuva chegando pra ficar. Planejem o dia por dentro de casa.",
        "Molha tudo hoje. Até quem só ia dar uma saidinha rápida.",
        "Chuva na área. Sapato de couro, guarda pra outro dia.",
        "Dia de chuva. Bom pra plantação, ruim pro passeio.",
        "Chove e não afina. Levem duas meias, por precaução.",
    ],
    "tempestade": [
        "Temporal à vista. Tirem o carro debaixo da árvore.",
        "Tempestade. Desliga o computador, criatura.",
        "Vai vir com tudo. Não digam que eu não falei.",
        "Temporal feio. Tirem o varal, tirem o carro, tirem o juízo da rua.",
        "Vem trovoada. Fiquem em casa, pelo menos hoje me obedeçam.",
        "Raio, vento, estrago. Não digam que o velho não avisou.",
        "Tempestade à vista. Carregue o celular e reze.",
        "Temporal chegando. Guardem tudo que o vento possa levar.",
        "Vem raio e trovão. Desliguem os aparelhos da tomada.",
        "Tempestade das brabas. Fiquem longe de janela e de árvore.",
        "Vento forte com chuva. Segurem o portão e a paciência.",
        "Temporal pesado. Cancelem o passeio, isso não é brincadeira.",
        "Trovoada a caminho. Cachorro pra dentro, gente também.",
        "Vai desabar. Tirem as motos e os vasos do caminho do vento.",
        "Tempestade feia. Não é hora de bancar o corajoso na rua.",
        "Raios à vista. Fora da água, fora do descampado, dentro de casa.",
        "Temporal com vento. Fechem tudo e não subam em laje.",
        "Vem tempestade. Deixem o carro em lugar coberto, se puderem.",
        "Trovão forte hoje. Quem tem medo, já sabe: cobertor na cabeça.",
        "Tempestade séria. Guardem lixeira, cadeira e o que voar.",
        "Vai vir vento e água junto. Redobrem o cuidado na estrada.",
        "Temporal à vista. Se puder adiar a saída, adie mesmo.",
        "Raio e trovão o dia todo. Evitem chuveiro durante o pior.",
        "Tempestade chegando. Prendam bem o guarda-chuva, ou vai voar.",
        "Vem coisa braba do céu. Melhor prevenir que enxugar depois.",
        "Temporal pesado à tarde. Voltem pra casa antes que aperte.",
        "Trovoada forte. Não estacionem embaixo de árvore, por favor.",
        "Tempestade na área. Desliguem o portão eletrônico da tomada.",
        "Vem raio, vento e chuva. O trio que ninguém convidou.",
        "Temporal daqueles. Segurem firme e esperem passar em casa.",
    ],
    "frio": [
        "Frio de rachar. Casaco, e não é sugestão.",
        "Vai fazer frio. Do tipo que dói o osso.",
        "Frio danado. Isso é castigo, só pode.",
        "Frio de renegar a cama. Casaco e cobertor.",
        "Vai gelar. Do tipo que o chuveiro vira melhor amigo.",
        "Frio danado. Guardem o chinelo, criaturas.",
        "Tá frio e vai piorar. Aproveitem pra reclamar comigo.",
        "Frio cortante. Meia grossa e touca, sem vergonha.",
        "Vem friagem. O cobertor pesado vai ganhar o dia.",
        "Frio de manhã cedo. Ninguém merece sair da cama assim.",
        "Gela até o pensamento. Casaco por cima do casaco.",
        "Frio seco e teimoso. Passem hidratante, a pele reclama.",
        "Vai congelar. Deixem o café bem quente e a coberta perto.",
        "Friaca das boas. Do tipo que embaça o vidro do carro.",
        "Frio de doer. Luva, cachecol e cara feia, tudo combina.",
        "Manhã gelada. Quem tem que trabalhar cedo, meus pêsames.",
        "Frio pesado. Aqueçam as mãos antes de reclamar comigo.",
        "Vem frio de verdade. Nada de sair de casaco fininho.",
        "Frio de rachar os lábios. Levem lenço e paciência.",
        "Gelado desde cedo. O sol nem se deu ao trabalho de esquentar.",
        "Friagem forte. Idoso e criança bem agasalhados, ouviram?",
        "Frio de arrepiar. A cama vai ser o lugar mais disputado.",
        "Vai fazer um frio de respeito. Cobertor duplo, sem dó.",
        "Frio úmido, o pior de todos. Entra no osso e não sai.",
        "Manhã congelante. Quem for correr, agasalhe bem antes.",
        "Frio bravo. Chá quente vira questão de sobrevivência.",
        "Vem geada quase. Cuidado com a planta e com o nariz.",
        "Frio daqueles. Até eu, que reclamo de tudo, tenho razão hoje.",
        "Gelado o dia todo. Nem o meio-dia vai dar trégua.",
        "Frio persistente. Guardem a roupa de verão, ela não serve hoje.",
    ],
    "calor": [
        "Calor de derreter. Bebam água antes que virem sombra no chão.",
        "Vai fazer um calor indecente. Ventilador no talo.",
        "Calorão. Do tipo que gruda a roupa no corpo.",
        "Calor sufocante. Nem o vento resolve, se é que vem vento.",
        "Vem calor pesado. Guardem energia, vão suar bastante.",
        "Calor de rachar. Sombra e água fresca, e olhe lá.",
        "Dia escaldante. Evitem o sol do meio-dia, não sejam teimosos.",
        "Calor absurdo. Criança e idoso longe do sol forte.",
        "Vai assar. Boné, protetor e muita, muita água.",
        "Calor sem trégua. O asfalto vai ferver, cuidado com o pé.",
        "Calorão danado. Bebida gelada vai ser disputada em casa.",
        "Vem forno lá de fora. Não deixem bicho no carro nem um minuto.",
        "Calor de suar parado. Roupa leve e clara, por favor.",
        "Dia quentíssimo. Quem trabalha no sol, hidrate a cada pausa.",
        "Calor pesado. Ventilador, leque, o que tiver que abane.",
        "Vai fazer calor de doer. Fujam do sol entre meio-dia e três.",
        "Calorão o dia todo. Nem de noite vai refrescar direito.",
        "Calor abafado. Bebam água mesmo sem sede, ouviram?",
        "Dia de forno. Guardem o esforço físico pra quando esfriar.",
        "Calor extremo. Idoso dentro de casa nas horas piores.",
        "Vem calor de verão raiz. Chapéu na cabeça, sempre.",
        "Calor insuportável. A sombra vai valer ouro hoje.",
        "Dia torrando. Molhem a nuca, molhem os pulsos, se refresquem.",
        "Calor forte. Deixem a garrafa de água sempre por perto.",
        "Vai esquentar demais. Nada de exercício pesado ao meio-dia.",
        "Calorão. Roupa de cama leve, senão a noite vira sauna.",
        "Calor de suar até parado no ponto. Levem um leque.",
        "Dia muito quente. Protetor solar não é luxo, é necessidade.",
        "Calor pra derreter sorvete na mão. Se protejam do sol.",
        "Vem calor pesado. Bebam água antes, durante e depois de tudo.",
    ],
    "abafado": [
        "Abafado. Aquele calor grudento que ninguém aguenta.",
        "Mormaço o dia todo. O ar parece parado de propósito.",
        "Calor úmido. Sua-se sem fazer nada, que beleza.",
        "Abafado demais. Nem o ventilador dá conta desse ar pesado.",
        "Ar pesado e úmido. Dia de camiseta grudando nas costas.",
        "Mormaço danado. Calor que não sobe termômetro, mas incomoda.",
        "Abafado. O tipo de dia que deixa todo mundo de pavio curto.",
        "Umidade alta e calor. A combinação que gruda a roupa no corpo.",
        "Dia abafado. Bebam água, esse mormaço engana e desidrata.",
        "Ar parado e quente. Abram as janelas, se é que adianta.",
        "Mormaço pesado. Do tipo que dá preguiça só de respirar.",
        "Abafado o dia inteiro. Nem a sombra refresca direito hoje.",
        "Calor úmido de grudar. Roupa leve e paciência, muita paciência.",
        "Dia mormacento. O ar tá tão parado que dá pra cortar.",
        "Abafado. Vão suar, e não é do calor seco, é do úmido chato.",
        "Umidade e calor juntos. A pele não seca, o humor não melhora.",
        "Mormaço firme. Ventilador ajuda pouco, mas ligue mesmo assim.",
        "Ar abafado. Dia bom pra ficar quieto e beber água gelada.",
        "Calor de estufa. Úmido, parado e cansativo, o combo completo.",
        "Abafado sem vento. Parece que o ar esqueceu de se mexer.",
        "Dia pesado. Mormaço que dá dor de cabeça em quem é sensível.",
        "Umidade nas alturas. Suor garantido, mesmo na sombra.",
        "Abafado o tempo todo. Nem de noite promete aliviar.",
        "Mormaço de doer. Chá gelado e o mínimo de esforço possível.",
        "Ar grudento. Roupa de algodão, larga, e nada de agito.",
        "Calor úmido chato. Do tipo que cansa antes de começar o dia.",
        "Abafado. O ventilador só empurra ar quente, mas empurre.",
        "Dia de mormaço. Se puder, fique perto de um ventilador.",
        "Umidade pesada. Beba água, que esse abafamento engana o corpo.",
        "Abafado e sem brisa. Um forno mal ventilado, é o que é.",
    ],
    "ameno": [
        "Tempo ameno. Até eu tenho que admitir: está tolerável.",
        "Dia agradável. Não se acostumem, é raro me ver calado.",
        "Clima ameno. Nem frio, nem calor. Quase de propósito.",
        "Temperatura boa. Confesso a contragosto: dá pra sair sem drama.",
        "Dia bom. Pronto, falei. Não me façam repetir.",
        "Ameno e tranquilo. Aproveitem, porque amanhã eu volto a reclamar.",
        "Clima gostoso. Raro, eu sei. Anotem no calendário.",
        "Tempo agradável. Até o meu joelho está em silêncio hoje.",
        "Dia equilibrado. Nem casaco pesado, nem ventilador. Um respiro.",
        "Temperatura amena. Bom pra caminhar, se é que vocês caminham.",
        "Clima ameno. O céu resolveu colaborar. Milagre.",
        "Dia leve. Aproveitem sem exagero, que exagero sempre dá errado.",
        "Tempo bom de verdade. Estranho, mas verdadeiro.",
        "Ameno o dia todo. Nem reclamar direito eu consigo hoje.",
        "Clima agradável. Janela aberta e brisa leve. Até que enfim.",
        "Dia confortável. Roupa leve resolve. Sem sofrimento por uma vez.",
        "Temperatura na medida. Nem eu acho o que criticar. Quase.",
        "Tempo ameno. Bom pra estender roupa e pra respirar fundo.",
        "Dia tranquilo. Sol na conta certa, vento na conta certa.",
        "Clima ameno. Vão gostar. Eu, por princípio, fico neutro.",
        "Temperatura boa o dia todo. Aproveitem antes que eu ache defeito.",
        "Dia gostoso. Camiseta e um casaquinho pra garantir, só isso.",
        "Ameno e estável. O tipo de dia que não dá trabalho a ninguém.",
        "Clima equilibrado. Nem eu, com esforço, acho motivo de bronca.",
        "Tempo bom. Passeiem, respirem, façam o que gente feliz faz.",
        "Dia agradável. Guardem a lembrança, que amanhã pode mudar.",
        "Temperatura amena. Perfeita pra quem não gosta de extremos.",
        "Clima ameno. Céu comportado e brisa educada. Elogio raro meu.",
        "Dia bom e calmo. Aproveitem sem culpa, autorizado pelo velho.",
        "Ameno. Pronto, elogiei o tempo. Agora me deixem em paz.",
    ],
}

AMPLITUDE = [
    "Frio de rachar cedo, forno à tarde. Escolham um, ora bolas.",
    "De manhã casaco, de tarde ventilador. Uma bagunça.",
    "Amanhece congelando e almoça assando. Não tem lógica.",
    "Cedo é inverno, meio-dia é verão. Vistam-se em camadas.",
    "Casaco na ida, camiseta na volta. Levem os dois.",
    "Manhã gelada, tarde escaldante. O termômetro está indeciso.",
    "Começa frio, termina quente. Uma novela de temperatura.",
    "De manhã treme, de tarde derrete. Preparem-se pros dois.",
    "Frio ao acordar, calor no almoço. Bolsa cheia de roupa.",
    "Amplitude grande hoje. Casaco que sai fácil, é o segredo.",
    "Cedo pede cobertor, tarde pede sombra. Vai entender.",
    "Manhã de touca, tarde de boné. Levem o guarda-roupa junto.",
    "Sobe quinze graus do café ao almoço. Um absurdo.",
    "Gela cedo e ferve depois. Roupa em camadas, já disse.",
    "De casaco pra camiseta em poucas horas. Que confusão.",
    "Frio matinal, calorão vespertino. Um dia, duas estações.",
    "Começa tiritando, acaba abanando. Escolham suas batalhas.",
    "Variação enorme hoje. O corpo estranha, o guarda-roupa também.",
    "Manhã siberiana, tarde tropical. Não é exagero meu.",
    "Do cobertor ao ventilador no mesmo dia. Pura zombaria.",
    "Frio de manhã que ninguém acredita à tarde. Mas foi real.",
    "Amplitude térmica das grandes. Vistam-se pra desmontar.",
    "Cedo agasalho, tarde regata. Levem tudo, deixem nada.",
    "Termômetro sobe demais do amanhecer ao meio-dia. Cuidado.",
    "Manhã fria de doer, tarde quente de suar. Os dois no mesmo dia.",
    "Comece de casaco, termine sem ele. É a dica do velho.",
    "Uma manhã e uma tarde que parecem meses diferentes.",
    "Frio ao sair, calor ao chegar. Planejem a mochila.",
    "De congelar a torrar. O dia hoje é bipolar, e eu entendo.",
    "Grande diferença entre cedo e tarde. Camadas, sempre camadas.",
]

UMIDADE = [
    "E a umidade despencando pra {u} por cento. Bebe água, criatura.",
    "Umidade em {u} por cento. Isso resseca até o mau humor.",
    "{u} por cento de umidade. Bebam água, não me façam repetir.",
    "Umidade lá embaixo, {u} por cento. Nariz vai reclamar.",
    "Ar seco, {u} por cento de umidade. Hidratem a garganta.",
    "Só {u} por cento de umidade. Isso racha lábio e paciência.",
    "Umidade em {u} por cento. Deserto tem mais água que isso.",
    "Ar seco demais, {u} por cento. Copo de água sempre à mão.",
    "{u} por cento de umidade. Olho seco, garganta seca, tudo seco.",
    "Umidade despencou pra {u} por cento. Umidificador, se tiverem.",
    "Ar ressecado, {u} por cento. Planta murcha, gente também.",
    "Umidade em {u} por cento. Molhem o ambiente, molhem a garganta.",
    "Apenas {u} por cento de umidade. Cuidado com quem tem asma.",
    "Ar seco, {u} por cento. Beba água antes que a sede avise.",
    "Umidade baixa, {u} por cento. Sangramento de nariz é risco real.",
    "{u} por cento de umidade. Toalha molhada no quarto ajuda.",
    "Umidade nas alturas ao contrário, {u} por cento. Hidratante já.",
    "Ar seco de rachar, {u} por cento. Idoso e criança, atenção redobrada.",
    "Só {u} por cento no ar. Garganta arranhando o dia todo.",
    "Umidade em {u} por cento. Evitem esforço físico ao sol.",
    "Ar seco, {u} por cento. Bacia de água pela casa não faz mal.",
    "Umidade despencando a {u} por cento. Bebam mesmo sem sede.",
    "{u} por cento de umidade. A pele pede hidratante, atendam.",
    "Ar ressecado, {u} por cento. Olhos ardendo? É isso mesmo.",
    "Umidade em {u} por cento. Não é hora de queimar mato, atenção.",
    "Baixíssima umidade, {u} por cento. Redobrem a água hoje.",
    "Ar seco, {u} por cento. Fechem a garganta com água, não com café.",
    "Umidade em {u} por cento. Lábio rachado é aviso pra hidratar.",
    "{u} por cento de umidade no ar. Um copo d'água a cada hora, vai.",
    "Ar seco danado, {u} por cento. Cuidem de quem respira com dificuldade.",
]

SEM_CHUVA = [
    "Chuva? Nenhuma. Nem hoje, nem amanhã.",
    "De chuva, nada. Continua tudo seco.",
    "Chuva nem pensar. Poeira até o teto.",
    "Nada de chuva. O céu esqueceu como se faz.",
    "Zero chuva. Quem lavou o carro, acertou por acaso.",
    "Sem uma gota. A terra racha e a planta implora.",
    "Chuva? Só na lembrança. Tudo seco por aqui.",
    "Nem sinal de chuva. Guardem o guarda-chuva no armário.",
    "Chuva nenhuma. Bom pro varal, ruim pro jardim.",
    "Seco de novo. A chuva anda de férias faz tempo.",
    "Nada de água do céu. Reguem as plantas, elas agradecem.",
    "Chuva zero. Poeira pra todo lado, feche as janelas.",
    "Sem chuva à vista. O rio agradece pouco, a horta reclama.",
    "Nem chuvisco. O tempo hoje é seco de propósito.",
    "Chuva? Esqueçam. Nem uma nuvem carregada no horizonte.",
    "Tudo seco. Quem depende de chuva, vai ter que esperar.",
    "Sem pingo de chuva. Aproveitem pra estender tudo no varal.",
    "Nada de molhar. O céu está avarento com a água hoje.",
    "Chuva nenhuma prevista. A poeira vai ser a companhia do dia.",
    "Seco e mais seco. Nem promessa de chuva pra animar.",
    "Chuva? Nem de longe. Regue a plantação, não conte com o céu.",
    "Sem uma gota sequer. Dia bom pra obra, ruim pra lavoura.",
    "Nada de chuva. Guardem energia, não vão precisar de capa.",
    "Chuva zero por aqui. O ar seco vai dominar o dia.",
    "Nem uma nuvenzinha molhada. Tudo firme e seco.",
    "Sem chuva hoje. O guarda-chuva pode dormir no armário.",
    "Chuva? Nem sonhando. A cidade vai continuar empoeirada.",
    "Seco o dia todo. Se ouvir trovão, foi engano seu.",
    "Nada de água caindo. Bom pro passeio, péssimo pro açude.",
    "Chuva nenhuma. Molhem as plantas, que o céu não vai ajudar.",
]


# refina a condição bruta usando os números do dia. Limiares COMPARTILHADOS
# com gerar_tarde.py: se mudar aqui, mude lá, senão os personagens divergem.
# Um dia só é "de chuva" acima deste acumulado. O código WMO marca "chuva" até
# numa garoa de 0,2 mm — e era daí que vinha a contradição do roteiro: a batida
# do resmungo olhava só o código (prometia chuva) e a batida final olhava só o
# acumulado (negava a chuva). Agora as duas leem o MESMO limiar.
LIMIAR_CHUVA_MM = 1.0


def chove_de_verdade(cidade):
    """O dia é de chuva nesta cidade? Código WMO e acumulado precisam concordar."""
    return (cidade.get("cond") in ("chuva", "tempestade")
            and (cidade.get("chuva_mm", 0) or 0) >= LIMIAR_CHUVA_MM)


def cenario_do_dia(cidade):
    """Cenário visual pela MESMA regra da fala: nada de chuva animada na tela
    enquanto a narração diz que não chove."""
    cond = cidade.get("cond", "sol")
    if cond in ("chuva", "tempestade") and not chove_de_verdade(cidade):
        return "nublado"
    return cond


def refinar_cond(cidade, umidade_min):
    """Deriva calor/abafado/ameno a partir da condição bruta + temperatura +
    umidade. Mantém sol/nublado/chuva/tempestade/frio quando fazem sentido."""
    cond = cidade.get("cond", "sol")
    mx = cidade.get("max", 0)
    # garoa de meio milímetro não é dia de chuva: vira nublado e o velho
    # reclama de céu fechado em vez de prometer temporal.
    if cond in ("chuva", "tempestade") and not chove_de_verdade(cidade):
        cond = "nublado"
    if cond in ("chuva", "tempestade", "frio"):
        return cond
    if mx >= 32:
        return "calor"
    if mx >= 28 and (umidade_min or 0) >= 70:
        return "abafado"
    if 22 <= mx <= 27 and cond in ("sol", "nublado"):
        return "ameno"
    return cond


# o gancho: a decisão de deslizar acontece em ~1,5s, então o Reel abre pelo
# dado mais EXTREMO do dia, dito curto — nunca pelo cumprimento.
GANCHO_FRIO = ["{t} graus. {t}!", "{t} graus em {c}. {t}!"]
GANCHO_CALOR = ["{t} graus hoje. {t}!", "{t} graus em {c}. Prepare-se."]
GANCHO_CHUVA = ["{v} milímetros de chuva hoje.", "Vem chuva. {v} milímetros."]
GANCHO_SECO = ["Umidade em {u} por cento. Isso é deserto."]


def escolher_gancho(cid, umidade, rnd):
    """Devolve (fala, numero_grande, subtitulo, cor) do gancho do dia.

    Prioridade pelo que mais choca quem mora aqui: frio extremo > calor
    extremo > chuva forte > ar seco. Se nada for extremo, usa a máxima da
    cidade principal — sempre há um número pra mostrar.
    """
    mais_frio = min(cid, key=lambda c: c["min"])
    mais_quente = max(cid, key=lambda c: c["max"])
    mais_chuva = max(cid, key=lambda c: c.get("chuva_mm", 0))

    if mais_frio["min"] <= 11:
        t = mais_frio["min"]
        return (rnd.choice(GANCHO_FRIO).format(t=num_extenso(t), c=mais_frio["nome"]),
                f"{t}°", mais_frio["nome"].upper(), "frio")
    if mais_quente["max"] >= 32:
        t = mais_quente["max"]
        return (rnd.choice(GANCHO_CALOR).format(t=num_extenso(t), c=mais_quente["nome"]),
                f"{t}°", mais_quente["nome"].upper(), "calor")
    if mais_chuva.get("chuva_mm", 0) >= 10:
        v = round(mais_chuva["chuva_mm"])
        return (rnd.choice(GANCHO_CHUVA).format(v=num_extenso(v)),
                f"{v}mm", mais_chuva["nome"].upper(), "chuva")
    if umidade and umidade <= 30:
        return (rnd.choice(GANCHO_SECO).format(u=num_extenso(umidade)),
                f"{umidade}%", "UMIDADE", "seco")
    c = cid[0]
    return (f"{num_extenso(c['max'])} graus hoje em {c['nome']}.",
            f"{c['max']}°", c["nome"].upper(), "normal")


def num_extenso(n):
    """Kokoro lê melhor número por extenso em PT-BR."""
    u = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito",
         "nove", "dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis",
         "dezessete", "dezoito", "dezenove"]
    d = {20: "vinte", 30: "trinta", 40: "quarenta", 50: "cinquenta"}
    n = int(n)
    if n < 20:
        return u[n]
    dez, resto = (n // 10) * 10, n % 10
    base = d.get(dez, str(n))
    return base if resto == 0 else f"{base} e {u[resto]}"


def montar_roteiro(dados):
    """Devolve a lista de BATIDAS do vídeo.

    Cada batida é um dict: {"fala", "legenda", "tipo", "dados"}.
    - `fala`    -> vai pro Kokoro (números por extenso, pontuação pra respiro)
    - `legenda` -> vai pra tela (curta, com números em algarismo)
    - `tipo`    -> diz ao piloto.py QUAL painel desenhar acima da cabeça
    - `dados`   -> o que aquele painel precisa

    Separar fala de legenda é de propósito: a boca lê "vinte e sete", a tela
    mostra "27°". Um texto só não serviria bem aos dois.
    """
    semente = int(dados["data"].replace("-", ""))
    rnd = random.Random(semente)
    cid = dados["cidades"]
    principal = cid[0]
    batidas = []

    def maiusculizar(t):
        """Primeira letra da frase E depois de cada ponto — os templates
        repetem o número ('{t} graus. {t}!') e a 2ª ocorrência vinha minúscula."""
        if not t:
            return t
        saida, novo = [], True
        for ch in t:
            saida.append(ch.upper() if novo and ch.isalpha() else ch)
            if ch.isalpha():
                novo = False
            elif ch in ".!?":
                novo = True
        return "".join(saida)

    def add(fala, legenda=None, tipo="nenhum", **dd):
        fala = maiusculizar(fala)
        batidas.append({"fala": fala,
                        "legenda": legenda if legenda is not None else fala,
                        "tipo": tipo, "dados": dd})

    fala_g, num_g, sub_g, cor_g = escolher_gancho(cid, dados.get("umidade_min"), rnd)
    add(fala_g, num_g, tipo="gancho", numero=num_g, sub=sub_g, cor=cor_g)

    add(rnd.choice(ABERTURAS))

    cond = refinar_cond(principal, dados.get("umidade_min"))
    add(rnd.choice(RESMUNGO.get(cond, RESMUNGO["sol"])))

    add(f"{principal['nome']}: mínima de {num_extenso(principal['min'])} graus, "
        f"máxima de {num_extenso(principal['max'])}.",
        f"Mínima de {principal['min']}°, máxima de {principal['max']}°.",
        tipo="cidade", cidade=principal)

    if principal["max"] - principal["min"] >= 12 and principal["min"] <= 15:
        add(rnd.choice(AMPLITUDE), "Frio de rachar cedo, forno à tarde.",
            tipo="amplitude", cidade=principal,
            acao="abanar" if principal["max"] >= 30 else None)

    if len(cid) > 2:
        add(f"{cid[1]['nome']} e {cid[2]['nome']}, a mesma bagunça.",
            f"{cid[1]['nome']} e {cid[2]['nome']}: a mesma bagunça.",
            tipo="duas_cidades", a=cid[1], b=cid[2])

    if len(cid) > 3:
        c = cid[3]
        extra = " e neblina" if c.get("cond") in ("frio", "nublado") else ""
        add(f"{c['nome']} amanhece com {num_extenso(c['min'])} graus{extra}.",
            f"{c['min']} graus{extra} em {c['nome']}.",
            tipo="cidade", cidade=c, nevoa=bool(extra),
            acao="tremer" if c["min"] <= 12 else None)

    u = dados.get("umidade_min")
    if u and u <= 40:
        add(rnd.choice(UMIDADE).format(u=num_extenso(u)),
            "Umidade despencando. Bebe água, criatura.",
            tipo="umidade", umidade=u, acao="beber")

    # mesma regra do resmungo (ver chove_de_verdade): ou o vídeo inteiro
    # promete chuva, ou o vídeo inteiro nega. Nunca os dois.
    if not any(chove_de_verdade(c) for c in cid):
        add(rnd.choice(SEM_CHUVA), tipo="sem_chuva")
    else:
        pico = max(cid, key=lambda c: c.get("chuva_mm", 0))
        add(f"E chuva, viu. Até {num_extenso(round(pico['chuva_mm']))} "
            f"milímetros em {pico['nome']}.",
            f"Chuva: até {pico['chuva_mm']}mm em {pico['nome']}.",
            tipo="chuva", cidade=pico)

    add(rnd.choice(FECHOS), tipo="fecho")
    add(rnd.choice(CTA), tipo="cta", chamada="TOCA NO SEGUIR")
    return batidas


# =====================================================================
#  ORQUESTRAÇÃO
# =====================================================================
def rodar(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, **kw)


def produzir(batidas, saida, cenario="sol", calor=False, personagem="ranzinza",
             cenario_tipo="varanda", quality="m", fps=30, voz="pm_alex",
             pitch=0.88, extra=None):
    """Do roteiro ao MP4. Compartilhado pelos dois vídeos do dia.

    `batidas` já vem pronta de quem chamou (previsão do tempo ou bloco da
    Dona Maria) — esta função só executa: voz, lip sync, render e montagem.
    `pitch` < 1 abaixa o tom (0.88 envelhece o Ranzinza; 0.94 assenta a voz
    da Dona Maria sem deixá-la rouca).
    """
    trab = os.path.join(AQUI, "_trab")
    os.makedirs(trab, exist_ok=True)
    falas = [b["fala"] for b in batidas]

    print(f"[1/5] roteiro — {len(batidas)} batidas ({personagem})")
    rot = os.path.join(trab, "roteiro.txt")
    open(rot, "w").write("\n".join(falas) + "\n")

    print("[2/5] narração (Kokoro, local)")
    bruta = os.path.join(trab, "voz_bruta.wav")
    segs = os.path.join(trab, "segs.json")
    rodar([sys.executable, os.path.join(AQUI, "gerar_voz_kokoro.py"),
           rot, "--voz", voz, "--speed", "0.95", "--gap", "0.30",
           "--out", bruta, "--seg-json", segs])

    print(f"[3/5] ajustando o timbre (pitch {int((pitch-1)*100)}%)")
    narr = os.path.join(trab, "narracao.wav")
    rodar(["ffmpeg", "-y", "-v", "error", "-i", bruta, "-af",
           f"asetrate=44100*{pitch},aresample=44100,atempo={1/pitch:.5f},"
           "vibrato=f=5.5:d=0.09,highpass=f=90,"
           "acompressor=threshold=-18dB:ratio=3:attack=8:release=180,volume=1.15",
           "-ar", "44100", "-ac", "1", narr])

    print("[4/5] lip sync por amplitude")
    lip = os.path.join(trab, "lip_full.json")
    rodar([sys.executable, os.path.join(AQUI, "lipsync_amplitude.py"),
           narr, lip, "--fps", "22"])

    print("[5/5] render Manim + montagem")
    conteudo = {"batidas": batidas, "cenario": cenario, "calor": calor,
                "personagem": personagem, "cenario_tipo": cenario_tipo}
    conteudo.update(extra or {})
    json.dump(conteudo, open(os.path.join(trab, "conteudo.json"), "w"),
              ensure_ascii=False)
    env = dict(os.environ, DVH_LIP_JSON=lip, RANZINZA_TRAB=trab)
    rodar(["manim", f"-q{quality}", "--fps", str(fps),
           os.path.join(AQUI, "piloto.py"), "Piloto"], env=env)

    mp4 = f"media/videos/piloto/1920p{fps}/Piloto.mp4"
    rodar(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-i", narr,
           "-c:v", "libx264", "-crf", "22", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-shortest", saida])
    print(f"pronto: {saida}")
    return saida


def gerar(dados, saida, quality="m"):
    """Vídeo da manhã: previsão do tempo com o Seu Ranzinza."""
    batidas = montar_roteiro(dados)
    for b in batidas:
        print(f'     [{b["tipo"]:13s}] {b["fala"]}')
    return produzir(batidas, saida,
                    cenario=cenario_do_dia(dados["cidades"][0]),
                    calor=max(c["max"] for c in dados["cidades"]) >= 31,
                    personagem="ranzinza", cenario_tipo="varanda",
                    quality=quality, voz="pm_alex", pitch=0.88,
                    extra={"data": dados["data"]})


DEMO = {
    "data": "2026-07-29",
    "cidades": [
        {"nome": "Volta Redonda", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0},
        {"nome": "Barra Mansa", "min": 11, "max": 28, "cond": "sol", "chuva_mm": 0},
        {"nome": "Porto Real", "min": 12, "max": 27, "cond": "sol", "chuva_mm": 0},
        {"nome": "Resende", "min": 9, "max": 25, "cond": "frio", "chuva_mm": 0},
    ],
    "umidade_min": 30,
}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados")
    ap.add_argument("--saida", default="REEL.mp4")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--quality", default="m")
    a = ap.parse_args()
    d = DEMO if a.demo or not a.dados else json.load(open(a.dados))
    gerar(d, a.saida, a.quality)
