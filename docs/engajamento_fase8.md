# Fase 8 — Motor de Engajamento (spec executável)

> Documento da Fase 8 do roteiro v2 do @previsaosulflu. Faz parte do PR da Fase 6
> (branch fix/conversao-e-slot-noturno). Define as regras de CTA e de interação.
> Objetivo: transformar alcance em seguidor via comentário, salvamento e resposta.
> Regra de ouro: NUNCA comentar "segue a gente" — isso queima a conta.

## 8.1 — CTA diferente por slot

O CTA muda conforme o horário, casado com os ganchos da Fase 6 (src/ganchos.py):

| slot | objetivo | CTA |
|---|---|---|
| MANHÃ (06h13) | identificação local | pergunta de UMA palavra: "Sua cidade tá assim? Responde AQUI 👇" — resposta esperada de uma palavra (nome da cidade / "sol" / "frio") |
| NOITE (18h00) | salvamento | "Salva pra conferir amanhã de manhã 📌" |

- O CTA da manhã puxa comentário (sinal forte pro algoritmo e porta de entrada
  pra conversa local).
- O CTA da noite puxa salvamento (o vídeo da noite é utilidade → "guardo pra ver
  amanhã"). Salvamento é a métrica-alvo da Fase 10.
- Wiring: o texto do CTA vem por slot; sugerir constantes CTA_MANHA / CTA_NOITE
  (junto de src/ganchos.py) usadas por captions.py e pelos geradores de Reel.

## 8.2 — Comentar primeiro no próprio post

- Assim que o post sai, a própria conta faz o PRIMEIRO comentário e FIXA ele.
- Conteúdo: a "pergunta do dia" — curta, local, fácil de responder.
  - Manhã: "E na sua cidade, tá como agora? 👇"
  - Noite: "Amanhã você sai cedo? Salva que eu te aviso a hora da chuva 📌"
- Fixar o comentário mantém a pergunta no topo e organiza a conversa.
- IMPORTANTE (regra permanente): comentar e fixar são publicações — só com "ok"
  explícito no chat, um a um. Este doc só define os textos-modelo.

## 8.3 — Responder 100% dos comentários em até 1 hora

- Meta: responder TODO comentário em no máximo 1h enquanto o post está "quente".
- Resposta curta, com nome/cidade da pessoa quando der, e devolve pergunta pra
  manter a conversa ("Aí em Barra Mansa também? Tá firme o dia?").
- Nunca resposta genérica copiada; nunca pedir "segue a gente".
- Operacional: nas primeiras 2h após cada post, checar comentários e responder.

## 8.4 — Rotina diária de interação local (15 min)

- Comentar em ~10 posts/dia de: prefeituras, páginas de notícia local, comércio
  local da região (Volta Redonda, Barra Mansa, Resende, Porto Real, Barra do
  Piraí, Piraí, etc.).
- Comentário genuíno e útil, ligado ao clima quando fizer sentido
  ("Boa! E amanhã a manhã vem fria nessa região 👀"). Presença, não spam.
- NUNCA comentar "segue a gente" / "segue de volta" / autopromoção crua.
- Alvo: virar presença reconhecida na conversa local → seguidor vem por
  reconhecimento, não por pedido.

## Lista-semente de perfis locais (para 8.4 — validar antes de usar)

Perfis a confirmar/ajustar com o dono da conta (candidatos por município):
- Prefeituras: @prefeituravr, @prefeiturabarramansa, @prefeitraresende (conferir handles reais)
- Notícia local: páginas de jornal/rádio da região Sul Fluminense
- Comércio local: feiras, eventos, pontos turísticos da região

> NENHUM comentário/DM é enviado a partir deste doc. Trazer a lista final de
> perfis pro chat e obter "ok" antes de qualquer interação (regra da Fase 9).

## Integração com Fases 6 e 7

- src/ganchos.py (Fase 6) — banco de ganchos manhã/noite; CTAs por slot ficam junto.
- docs/reels_spec_fase7.md (Fase 7) — os CTAs entram no fecho de cada Reel (7.2 e 7.5).
- src/travas.py (Fase 6) — evita post duplicado; não interfere no comentário.

## Métricas que a Fase 8 move (ver Fase 10)

- Comentários/semana: 0 → 20
- Salvamentos: ~1 → 25
- (Resposta rápida melhora tempo de exibição e retorno do algoritmo.)

