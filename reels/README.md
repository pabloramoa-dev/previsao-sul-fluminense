# Seu Ranzinza & Dona Maria — Reels diários do @previsaosulflu

Dois personagens animados, dois horários:

- **Seu Ranzinza (manhã)** — a previsão do tempo, reclamando de tudo. Varanda.
- **Dona Maria (meio-dia)** — o bloco prático: índice de varal, sensação
  térmica, UV e "neste dia". Quintal com varal. Ela cita o velho de propósito —
  quem viu um vídeo quer ver o outro, e é a retenção mais barata do projeto.

Tudo desenhado por código (Manim) e narrado por voz neural local (Kokoro):
**custo zero de API**, personagem sempre idêntico, sem IA de imagem.

## Como roda

```
coletar_tempo.py     Open-Meteo  ->  dia.json
gerar_dia.py         dia.json    ->  roteiro -> voz -> lip sync -> MP4 9:16
postar_reel.py       MP4 público ->  Reels no Instagram
```

O `.github/workflows/ranzinza.yml` encadeia os três todo dia às 06:10 (Brasília).

## Arquivos

| arquivo | o que faz |
|---|---|
| `previsao_lib.py` | O personagem, os cenários por condição de tempo, chuva animada, cartões e a trilha temporal |
| `piloto.py` | A cena Manim. **Orientada a dados** — lê `segs.json` + `conteudo.json`, não tem nada do dia escrito dentro |
| `gerar_dia.py` | Máquina de resmungo + `produzir()`, o pipeline compartilhado pelos dois vídeos |
| `gerar_tarde.py` | Bloco da Dona Maria: índice de varal, sensação térmica, UV, "neste dia" |
| `lipsync_amplitude.py` | Lip sync pela energia do áudio, no mesmo formato JSON do Rhubarb |
| `coletar_tempo.py` | Busca a previsão das 10 cidades numa chamada só, incluindo UV, vento, horas de sol, sensação térmica e a hora da virada da chuva |
| `historico.py` | Constrói (1x) a tabela de recordes "neste dia" e consulta offline depois |
| `postar_reel.py` | Publica na Graph API (container → espera processar → publica) |

## Configuração

Dois secrets no repositório (Settings → Secrets → Actions):

- `IG_USER_ID` — 27148485038175
- `IG_ACCESS_TOKEN` — token de longa duração da conta profissional

## Testar sem publicar

```bash
python gerar_dia.py --demo --saida manha.mp4          # Ranzinza, dados de exemplo
python gerar_tarde.py --demo --saida tarde.mp4        # Dona Maria, dados de exemplo
python coletar_tempo.py --saida dia.json              # previsão de verdade
python postar_reel.py --video URL --dados dia.json --dry-run   # só mostra a legenda
```

## Duas escolhas técnicas que valem lembrar

**Sincronia por relógio, não por encadeamento.** Boca, legenda e painel leem o
mesmo tempo absoluto de cena, vindo do `segs.json` do Kokoro. A primeira versão
encadeava `play`/`wait` e acumulava ~0,4s de atraso na legenda ao longo de 30s,
porque cada animação é arredondada pro frame mais próximo.

**Lip sync sem Rhubarb.** O Rhubarb dá visemas fonéticos melhores, mas exige
compilar C++ (~3 min) em todo job. Neste tamanho de boca, a energia do áudio lê
igualmente bem. O JSON é o mesmo, então dá pra trocar depois sem mexer na cena.

## Custo de execução

Pipeline completo (9 batidas, 30s, 1080x1920): **~2 min** de runner. Com o cache
do modelo Kokoro (~350MB) e do pip, o job diário fica em torno de 4-5 min —
cerca de 150 min/mês. Repositório público tem Actions ilimitado.


## Técnicas de retenção implementadas

1. **Gancho** — abre com o dado mais extremo do dia estalando na tela (o número
   grande), não com o personagem parado dando bom-dia. A decisão de deslizar é
   tomada em ~1,5s.
2. **Loop** — primeiro e último frame são a mesma imagem limpa. Nuvens, sol,
   respiração e câmera têm a velocidade ajustada pra completar ciclos inteiros
   na duração exata do vídeo. Diferença medida entre os dois frames: ~1,5/255.
3. **Legenda karaokê** no terço central (o rodapé fica coberto pela interface do
   Instagram), palavra a palavra. A largura é derivada de `larg_segura()` =
   quadro × zoom mínimo da câmera − margem. Sem isso a legenda estoura durante
   o push-in dos 2 primeiros segundos, que é quando mais gente está vendo.
4. **Câmera** — push-in nos primeiros 2s, deriva lenta depois, volta ao
   enquadramento inicial pro loop fechar.

## Rodízio de cidades e o selo na grade

Volta Redonda era sempre a cidade principal — a primeira da lista em
`coletar_tempo.py`. Duas consequências ruins, e a segunda só aparece quando se
olha o perfil em vez do vídeo:

1. As outras nove cidades nunca abriam um vídeo. Quem mora em Quatis ouvia o
   nome do município no meio da terceira batida, se ouvisse.
2. Na **grade**, dez Reels seguidos eram dez miniaturas do mesmo velho na mesma
   varanda. Nada ali dizia de que cidade era cada vídeo.

O conserto tem três partes:

**A lista gira por data.** `ordem_do_dia()` roda a lista de cidades em
`(data.toordinal() + desloca) % 10`. A cidade principal muda todo dia e cada uma
volta a cada dez dias, sem repetir na sequência. Continua determinístico: rodar
duas vezes no mesmo dia dá o mesmo vídeo.

**Os dois vídeos do dia nunca coincidem.** O Ranzinza roda com deslocamento 0 e
a Dona Maria com `DESLOCA_TARDE = 5` — metade exata da volta, então ela está
sempre no lado oposto do rodízio. São duas cidades citadas por dia.

**O nome vai pra tela nas primeiras batidas.** `previsao_lib.selo_cidade()`
desenha "HOJE EM / VOLTA REDONDA" (ou "AMANHÃ EM", no vídeo dela) em `Y_SELO`,
enquanto o gancho está no centro e a faixa do painel está livre. O selo sai
quando o cartão de mínima/máxima ocupa aquele lugar, por volta dos 11s.

**A capa não é o primeiro frame.** O primeiro frame é de propósito limpo, pro
loop fechar sem emenda — se a capa fosse ele, todo esse trabalho não apareceria
na grade. `postar_reel.py` manda `thumb_offset=1500` (ms), um frame de dentro da
janela do selo. `--capa-ms 0` volta ao comportamento antigo.

**A hashtag da cidade da vez entra na frente.** Os cinco conjuntos de hashtags
foram escritos quando Volta Redonda era fixa. Com o rodízio, o vídeo pode ser
inteiro sobre Quatis e o conjunto do dia citar só Volta Redonda e Barra Mansa —
justamente quem procura pelo município não acharia. `engajamento.hashtags()`
agora recebe `destaque` e põe `#quatis` na primeira posição, sem duplicar se a
tag já estiver no conjunto.

Duas medidas que valem lembrar se mexer no selo:

- **`Y_SELO = 3.95`, e não a faixa do painel (4.5).** A grade mostra o Reel
  recortado — hoje 3:4 (|y| ≤ 5.33), já foi 1:1 (|y| ≤ 4.0). Em 3.95 o selo cabe
  nos dois, o que o deixa imune à Meta mexer nisso de novo.
- **Corpo 56 em caixa alta.** Na grade o quadro aparece com ~330px de largura,
  menos de um terço do render. O que não se lê nesse tamanho não existe.

Pra desligar tudo: `coletar_tempo.py --sem-rodizio` volta a ordem fixa, e sem o
campo `destaque` no JSON o `piloto.py` simplesmente não desenha o selo.


## Índice de varal

Não existe índice oficial. É uma composição própria de umidade (35%), vento
(25%), horas de sol (28%) e temperatura (12%), com a chuva anulando tudo. O
balanço das roupas no varal ao fundo escala com a nota — o cenário mostra o que
ela está dizendo.


## Dona Maria em dia de chuva

O caso traiçoeiro do varal não é o dia de temporal — é a manhã seca com chuva
chegando às 15h. O índice sozinho diria "pode estender" e a roupa tomaria chuva.
Por isso `chuva_hora` (primeira hora da tarde com chuva prevista) limita a nota
a 6 e dispara a batida `recolher`, com cartaz vermelho e o horário.


## Guarda-chuva

Três coisas que precisaram de ajuste e valem lembrar se mexer nele:

- **Raio 2.05** — precisa ultrapassar a silhueta dos dois lados (corpo ~2.7 a
  3.0 de largura), senão lê como chapéu e a chuva passa rente ao rosto.
- **Domo achatado em 0.62** — guarda-chuva não é meia-esfera, e sem o
  achatamento a cúpula sobe e invade a faixa do painel de dados (y 3.5–5.5).
- **Pingos só pelas duas pontas** — antes eram distribuídos por toda a largura
  da cúpula, inclusive pelo centro: caíam no rosto do personagem e pareciam
  suor. Água de guarda-chuva escorre pela borda.

O personagem é abaixado automaticamente em dia de chuva, só o necessário pro
domo não passar de `TETO_CENA` — o Ranzinza desce 0.76, a Dona Maria não precisa
descer (ela já fica mais baixa no quadro).


## "Neste dia" — a tabela histórica

A API de arquivo do Open-Meteo tem série desde 1940. Baixar isso todo dia seria
desperdício — o passado não muda. Por isso:

```bash
python historico.py --construir        # 1x, gera historico.json (~60 KB)
python historico.py --consultar 07-29  # confere
```

O workflow guarda o arquivo em cache e só reconstrói se sumir. O
`gerar_tarde.py` consulta offline; se o arquivo não existir, a batida
simplesmente não entra e o vídeo sai um pouco mais curto.

**Qual recorde contar:** comparar "distância até cada recorde" não funciona. Num
dia de 12°/27° o número diz que estamos mais perto do recorde de calor (35°) que
do de frio (2°) — mas quem mora aqui viveu uma manhã fria. Mínima e máxima não
são grandezas comparáveis assim. A regra é a que uma pessoa usaria: mínima ≤ 14
conta o frio, máxima ≥ 31 conta o calor, e dia morno segue a estação (maio a
setembro é a seca fria daqui).

## Horários

| | horário | quem | job |
|---|---|---|---|
| manhã | 06:10 | Seu Ranzinza | `reel` |
| meio-dia | 11:20 | Dona Maria | `tarde` |

Os dois jobs são independentes: se o da tarde falhar, o da manhã do dia seguinte
roda normalmente.


## CTA de seguir

Todo vídeo termina com uma batida `cta`: o personagem PEDE pra seguir, com voz,
e um cartaz no centro da tela com a pílula azul "TOCA NO SEGUIR" e o @ escrito
por extenso.

Três decisões:

- **No centro, não na faixa do topo.** É a última coisa antes do loop
  reiniciar, e o topo do quadro é justo onde o dedo já está indo pra deslizar.
- **O @ por extenso.** Quem chegou por compartilhamento muitas vezes não viu de
  qual perfil é o vídeo.
- **Na voz de cada um.** Pedido seco funciona mal. O Ranzinza pede a
  contragosto ("Segue aí. Custa o quê, um dedo?"), a Dona Maria pede com jeito
  ("Aperta o seguir, meu bem. É rapidinho."). Quatro variações cada, sorteadas
  pela data.

O cartaz sai de cena nos últimos 0.3s, junto com todo o resto, pro frame limpo
que fecha o loop.
