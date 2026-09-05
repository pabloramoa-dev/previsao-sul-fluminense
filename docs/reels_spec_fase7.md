# Fase 7 — Reformulação dos Reels (spec executável)

> ## ⚠️ SUPERADO PELO PLANO v3 EM 2026-09-04 — LEIA ANTES DE IMPLEMENTAR
>
> A seção **7.5** manda construir o Juarez Plantão como um **Reel da NOITE, às
> 18h**, substituindo a Dona Maria e mantendo o Seu Ranzinza de manhã. O
> resultado disso são **dois Reels por dia**.
>
> O plano v3 ("Conserto do Motor") decidiu o contrário: **um Reel só, às 06h**,
> na voz do Juarez, em **dois modos** — rotina e alerta, escolhidos pelos
> limiares de `limiares.py`. O Ranzinza e a Dona Maria saem do fluxo diário.
> Quem implementar a 7.5 como está escrita coloca no ar exatamente o formato
> que o experimento de 14 dias (08/09 a 21/09) existe para substituir, e a
> métrica medida não responde por mudança nenhuma.
>
> **O que vale hoje**, e já está no repositório:
>
> | | 7.5 (superado) | plano v3 (em produção) |
> |---|---|---|
> | horário | 18h | 06h |
> | quantos Reels/dia | 2 | 1 |
> | pergunta | "Amanhã presta?" | previsão de hoje, rotina ou alerta |
> | gerador | `reels/gerar_noite.py` (nunca criado) | `reels/gerar_juarez.py` |
> | workflow | `post_noite.yml` | `.github/workflows/juarez.yml` |
> | duração | 15–20s | 18–22s |
>
> As "Pendências de código" no fim deste documento também estão vencidas: os
> itens 1 e 2 foram feitos de outra forma (`reels/juarez_lib.py`, portado da
> skill `juarez-plantao`), e o item 3 virou o desligamento dos dois crons do
> `ranzinza.yml`. O resto do documento — 7.1 a 7.4, 7.6 e a integração com a
> Fase 6 — continua válido e é boa referência.


> Documento de especificação para a Fase 7 do roteiro v2 do @previsaosulflu.
> Faz parte do PR da Fase 6 (branch fix/conversao-e-slot-noturno). NÃO É CÓDIGO
> DE PRODUÇÃO: descreve as mudanças a aplicar em reels/gerar_dia.py,
> reels/gerar_tarde.py, reels/postar_reel.py e no workflow ranzinza.yml.
> Objetivo: transformar alcance em seguidor. Retenção e conversão são o gargalo.

## Estado atual (para referência)

Hoje o projeto gera dois Reels animados (Manim + voz Kokoro, custo zero de API):

| slot | personagem | hora BRT | conteúdo |
|---|---|---|---|
| manhã | Seu Ranzinza | ~06:10 | previsão do dia, resmungando |
| meio-dia | Dona Maria | ~11:20 | varal, sensação térmica, UV, "neste dia" |

Workflow: `.github/workflows/ranzinza.yml` (dois jobs: reel-ranzinza e reel-maria).

A Fase 7 mantém o slot da manhã (ajustado) e SUBSTITUI o slot do meio-dia
(11h20) por um slot da NOITE (18h00). Dona Maria não é apagada — o conteúdo de
varal migra para o alerta condicional da noite (ver src/varal.py da Fase 6).

---

## 7.1 — O primeiro segundo (regra para os dois slots)

O primeiro segundo decide a retenção. Regras:

- 0–1s: TEXTO GRANDE na tela com a informação mais forte do dia (número, palavra
  de choque). Nada de logo, cartela de abertura ou "bom dia".
- Sem intro animada, sem apresentação de personagem antes do gancho.
- O personagem entra DEPOIS que o número já apareceu.
- A informação mais forte vem de src/ganchos.py (fonte única do gancho, criada na
  Fase 6): BANCO_MANHA para o slot da manhã, BANCO_NOITE para o da noite.

Aplicar em: reels/gerar_dia.py e no novo gerador da noite (frame 0 = texto grande,
sem clipe de abertura).

---

## 7.2 — REEL DA MANHÃ (06h13) — "Como está HOJE"

Duração-alvo: 15–22s. Estrutura por segundos:

| tempo | conteúdo |
|---|---|
| 0–2s | número chocante do dia (ex.: "9°C AGORA em Resende") — texto grande, sem logo |
| 2–5s | "Sua cidade:" — chamada de identificação |
| 5–15s | cidade por cidade, rápido, uma tela curta por cidade |
| 15–18s | fecho/loop: gancho que emenda no começo (retenção por replay) |

- Hora do disparo: 06h13 BRT (o workflow já foi ajustado na Fase 6 para o alvo
  09:13 UTC = 06h13 BRT em post_manha.yml).
- CTA da manhã (Fase 8.1): pergunta de identificação local de UMA palavra.

Aplicar em: reels/gerar_dia.py (roteiro/tempos) e ranzinza.yml (cron/alvo do job
da manhã, se o Reel for gerado por esse workflow).

---

## 7.3 — Rotação da ordem das cidades

- A ordem das cidades ROTACIONA a cada dia.
- Os DOIS slots do mesmo dia usam ordens DIFERENTES entre si (quem viu de manhã
  não vê a mesma sequência à noite → menos fadiga, mais retenção no segundo vídeo).
- Sugestão de implementação: seed = data (YYYYMMDD) para a manhã e
  data+"N" para a noite; embaralhar a lista de cidades com esse seed.

Aplicar em: função utilitária compartilhada (ex.: ordem_cidades(data, slot)) usada
por gerar_dia.py e pelo gerador da noite.

---

## 7.4 — SUBSTITUIR o slot 11h23 pelo slot 18h00

- O slot do meio-dia (Dona Maria, ~11:20) SAI da rotação diária.
- Entra o slot da NOITE às 18h00 BRT.
- No ranzinza.yml: remover/desativar o cron das 11h20 (14:20 UTC) do job
  reel-maria e criar o job da noite com alvo 18h00 BRT (21:00 UTC), alinhado ao
  post_noite.yml já existente (cron "20 17", alvo 21:00 UTC).
- Não apagar o código da Dona Maria de imediato: desativar o agendamento e manter
  o módulo até a noite estar validada (reversível).

---

## 7.5 — REEL DA NOITE (18h00) — "Amanhã presta?"

Identidade PRÓPRIA, separada da manhã. Personagem: **Juarez Plantão** (plantonista
de previsão), paleta NOTURNA (azul-escuro/âmbar), trilha/sonoridade distinta da
manhã. O produto do vídeo da noite é a HORA DO EVENTO (quando chove, quando esfria).

Pergunta de abertura DIFERENTE da manhã (ex.: "Amanhã presta pra estender roupa?").

Estrutura-alvo 15–20s:

| tempo | conteúdo |
|---|---|
| 0–2s | gancho da noite (BANCO_NOITE) — texto grande, o evento e a HORA |
| 2–5s | "Amanhã, na sua cidade:" |
| 5–14s | cidade por cidade com a HORA do evento (ordem diferente da manhã, 7.3) |
| 14–18s | alerta condicional do varal + CTA de salvamento |

- Alerta condicional do varal: se a chance de chuva entre 18h e 06h for > 70%,
  entra o aviso "não deixe roupa no varal". Lógica já criada na Fase 6 em
  src/varal.py (alerta_noturno / limiar 70%).
- CTA da noite (Fase 8.1): salvamento → "Salva pra conferir amanhã de manhã 📌".

Aplicar em: novo gerador reels/gerar_noite.py (baseado em gerar_tarde.py, trocando
personagem/paleta/roteiro) + previsao_lib.py (cena e paleta do Juarez).

---

## 7.6 — Tabela resumo executável: manhã vs noite

| item | MANHÃ (06h13) | NOITE (18h00) |
|---|---|---|
| personagem | Seu Ranzinza | Juarez Plantão |
| pergunta | "Como está HOJE?" | "Amanhã presta?" |
| produto | estado atual (número de choque) | hora do evento de amanhã |
| gancho (fonte) | ganchos.BANCO_MANHA | ganchos.BANCO_NOITE |
| paleta | diurna | noturna (azul/âmbar) |
| duração | 15–22s | 15–20s |
| ordem cidades | seed = data | seed = data+"N" (diferente da manhã) |
| CTA | pergunta local de 1 palavra | salvamento ("Salva pra amanhã 📌") |
| alerta varal | não | condicional (chuva 18h–06h > 70%) |
| hashtags | hashtags manhã (Fase 6) | hashtags noite ≠ manhã (Fase 6) |
| formato/slot | ver src/slots_config.py | ver src/slots_config.py |
| workflow | post_manha.yml (alvo 09:13 UTC) | post_noite.yml (alvo 21:00 UTC) |

---

## Integração com a Fase 6 (já no PR)

- src/ganchos.py — fonte única do gancho (BANCO_MANHA / BANCO_NOITE, sem repetir
  últimos 10). Usar no frame 0 dos dois Reels (7.1).
- src/hashtags.py — 5 conjuntos; manhã ≠ noite no mesmo dia (linha da tabela 7.6).
- src/varal.py — alerta condicional da noite (7.5).
- src/slots_config.py — formato por slot (manhã/noite).
- src/travas.py — validação de caption e trava de execução (evita post duplicado).
- .github/workflows/post_manha.yml — alvo já ajustado p/ 06h13 BRT (7.2).

## Pendências de código (NÃO feitas neste PR — só documentadas)

1. Criar reels/gerar_noite.py (Juarez Plantão) a partir de gerar_tarde.py.
2. Adicionar a cena/paleta noturna do Juarez em reels/previsao_lib.py.
3. Ajustar ranzinza.yml: tirar o cron 11h20, criar job da noite alvo 21:00 UTC.
4. Implementar ordem_cidades(data, slot) e ligar nos dois geradores (7.3).
5. Ligar ganchos.py no frame 0 dos geradores (7.1) e os CTAs por slot (Fase 8).

> Recomendação: rodar dry-run (gerar o MP4 sem postar) antes de qualquer merge.
