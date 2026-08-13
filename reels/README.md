# Seu Ranzinza & Dona Maria — Reels diários do @previsaosulfluminense

Dois personagens animados, dois horários — e, principalmente, **dois dias**:

- **Seu Ranzinza (06:10)** — a previsão de **hoje**, reclamando de tudo. Varanda.
- **Dona Maria (18:00)** — a previsão de **amanhã**, pra dar tempo de se
  preparar: mínima e máxima, o que separar hoje à noite, sensação térmica e UV.
  Quintal com varal, ao entardecer. Ela cita o velho de propósito — quem viu um
  vídeo quer ver o outro, e é a retenção mais barata do projeto.

Tudo desenhado por código (Manim) e narrado por voz neural local (Kokoro):
**custo zero de API**, personagem sempre idêntico, sem IA de imagem.

## Como roda

```
06:10  coletar_tempo.py                  ->  dia.json      (hoje)
       gerar_dia.py    dia.json          ->  roteiro -> voz -> lip sync -> MP4 9:16
       postar_reel.py  MP4 público       ->  Reels no Instagram

18:00  coletar_tempo.py --quando amanha  ->  amanha.json   (amanhã)
       gerar_tarde.py  amanha.json       ->  ... -> MP4 9:16
       postar_reel.py  --voz maria --quando amanha
```

O `.github/workflows/ranzinza.yml` encadeia os três às 06:10 (Ranzinza, com
`dia.json`) e de novo às 18:00 (Dona Maria, com `amanha.json`, de
`coletar_tempo.py --quando amanha`). Horários de Brasília.

## Arquivos

| arquivo | o que faz |
|---|---|
| `previsao_lib.py` | O personagem, os cenários por condição de tempo, chuva animada, cartões e a trilha temporal |
| `piloto.py` | A cena Manim. **Orientada a dados** — lê `segs.json` + `conteudo.json`, não tem nada do dia escrito dentro |
| `gerar_dia.py` | Máquina de resmungo + `produzir()`, o pipeline compartilhado pelos dois vídeos |
| `gerar_tarde.py` | Bloco da Dona Maria: previsão de amanhã, o que separar, sensação térmica, UV |
| `lipsync_amplitude.py` | Lip sync pela energia do áudio, no mesmo formato JSON do Rhubarb |
| `coletar_tempo.py` | Busca a previsão das 10 cidades numa chamada só, incluindo UV, vento, horas de sol, sensação térmica e a hora da virada da chuva |
| `postar_reel.py` | Publica na Graph API (container → espera processar → publica). `--voz` e `--quando` mudam a legenda |
| `historico.py` | Tabela de recordes "neste dia". **Fora do pipeline** desde que o bloco saiu do roteiro dela; fica como ferramenta avulsa |

## Configuração

Dois secrets no repositório (Settings → Secrets → Actions):

- `IG_USER_ID` — 27148485038175
- `IG_ACCESS_TOKEN` — token de longa duração da conta profissional

## Testar sem publicar

```bash
python gerar_dia.py --demo --saida manha.mp4          # Ranzinza, dados de exemplo
python gerar_tarde.py --demo --saida tarde.mp4        # Dona Maria, dados de exemplo
python gerar_tarde.py --demo-chuva --so-roteiro       # só as falas, sem renderizar
python coletar_tempo.py --saida dia.json                    # hoje  (Ranzinza)
python coletar_tempo.py --quando amanha --saida amanha.json # amanhã (Dona Maria)
python postar_reel.py --video URL --dados amanha.json --voz maria --quando amanha --dry-run
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

## Horários — e a divisão de dias

| | horário | quem | fala do dia | dados | job |
|---|---|---|---|---|---|
| manhã | 06:10 | Seu Ranzinza | **hoje** | `dia.json` | `reel` |
| fim de tarde | 18:00 | Dona Maria | **amanhã** | `amanha.json` | `tarde` |

Os dois jobs são independentes: se o das 18h falhar, o da manhã do dia seguinte
roda normalmente.

As 18h existem por um motivo: é a hora em que dá pra fazer alguma coisa com a
informação — separar o casaco, deixar o guarda-chuva na porta, encher a garrafa.
Uma previsão do dia seguinte às 11h da manhã não muda o comportamento de
ninguém.

## Como os dois não se contradizem

Os dois vídeos vão pro mesmo perfil com poucas horas de diferença, então a
coerência entre eles é requisito, não detalhe. Quatro regras sustentam isso:

1. **Cada um tem o seu dia.** O velho só fala de hoje, ela só fala de amanhã.
   Por isso a linha dele "Chuva? Nenhuma, nem hoje nem amanhã" foi trocada: era
   a única fala em que ele opinava sobre o dia dela — com dados 12h mais velhos.
2. **Mesmos limiares.** Ela importa `LIMIAR_CHUVA_MM` e `chove_de_verdade()` do
   `gerar_dia.py`. "Chove" quer dizer a mesma coisa nos dois roteiros.
3. **Ela não afirma, ela adianta.** O fecho dela sempre hedgeia e passa o bastão
   ("é o que está previsto até agora; amanhã cedo o velho confere"). Previsão de
   D+1 muda mesmo — e quando muda, o par continua fazendo sentido: ele é a
   confirmação, não a contradição.
4. **O cenário dela não é o tempo de amanhã.** O quintal é sempre de
   entardecer, porque é a hora em que ela está falando. O tempo de amanhã vive
   nos cards. Sem isso, um dia de chuva colocaria chuva caindo em cima dela às
   18h de um dia seco — e é por isso também que ela não usa mais guarda-chuva.

## O bloco útil dela: o que separar

Substituiu o índice de varal, que respondia "dá pra estender AGORA?" — pergunta
do dia de hoje, que não cabe mais num vídeo sobre amanhã. A pergunta das 18h é
"o que eu deixo pronto?", e a resposta é um cartaz só, escolhido por prioridade
do que dói mais esquecer: **guarda-chuva** (chove amanhã em alguma cidade) >
**casaco** (mínima ≤ 13° na cidade mais fria) > **protetor** (UV ≥ 8) >
**garrafa de água** (umidade ≤ 30%) > dia tranquilo.

A varredura é em TODAS as cidades, não só na principal: quem mora em Resende
passa frio numa manhã em que Volta Redonda está amena, e errar pra mais aqui
custa muito menos que deixar alguém no ponto de ônibus sem agasalho.

O bloco de UV não entra em dia de chuva — "leve guarda-chuva" seguido de "passe
protetor e chapéu" no mesmo vídeo é a contradição mais fácil de cometer aqui.


## Guarda-chuva — só o Seu Ranzinza

A Dona Maria não usa mais: o cenário dela é o entardecer de hoje, e a chuva de
que ela fala é a de amanhã, então não há água caindo pra ela se proteger
(`vestir(..., com_guarda_chuva=False)`). No velho ele continua, e três coisas
valem lembrar se mexer nele:

- **Raio 2.05** — precisa ultrapassar a silhueta dos dois lados (corpo ~2.7 a
  3.0 de largura), senão lê como chapéu e a chuva passa rente ao rosto.
- **Domo achatado em 0.62** — guarda-chuva não é meia-esfera, e sem o
  achatamento a cúpula sobe e invade a faixa do painel de dados (y 3.5–5.5).
- **Pingos só pelas duas pontas** — antes eram distribuídos por toda a largura
  da cúpula, inclusive pelo centro: caíam no rosto do personagem e pareciam
  suor. Água de guarda-chuva escorre pela borda.

O personagem é abaixado automaticamente o necessário pro domo não passar de
`TETO_CENA` — o Ranzinza desce 0.76.

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
