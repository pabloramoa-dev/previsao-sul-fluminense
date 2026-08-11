# Fase 9 — Distribuição fora do algoritmo (spec)

> Documento da Fase 9 do roteiro v2 do @previsaosulflu. Faz parte do PR da Fase 6
> (branch fix/conversao-e-slot-noturno). Estratégia para alcançar gente NOVA sem
> depender do feed/algoritmo. NADA aqui é enviado automaticamente.
> Regra permanente: NENHUM DM é enviado sem 'ok' explicito no chat, e a lista de
> perfis vem pro chat ANTES de qualquer envio.

## 9.1 — Alertas uteis em eventos reais

- Quando houver evento climático real (chuva forte, frente fria, calor extremo,
  risco de alagamento), publicar um alerta CURTO e ÚTIL na hora certa.
- Formato: uma frase com o QUÊ + ONDE + QUANDO ("Barra Mansa: chuva forte a
  partir das 16h, tire a roupa do varal"). Sem enrolação.
- Canal: post/story do slot + possível repost por páginas locais (utilidade
  pública viaja sozinha).
- Fonte do gatilho: reaproveitar o monitor_alertas.yml já existente no repo.

## 9.2 — Colabs (parcerias) — SEM DM sem ok

- Objetivo: aparecer para o público de páginas locais complementares (não
  concorrentes): guias da cidade, eventos, comércio, rádios, esporte local.
- Fluxo OBRIGATÓRIO:
  1. Montar a LISTA de perfis-alvo (handle + por que faz sentido).
  2. Trazer a lista pro chat.
  3. Só depois do 'ok', preparar a mensagem de abordagem.
  4. Só depois do 'ok' de novo, enviar — um a um.
- NUNCA enviar DM em massa. NUNCA 'segue a gente'.
- Ideia de colab: post conjunto de previsão para um evento local (feira, jogo,
  festa da cidade) — os dois perfis ganham.

## 9.3 — Marcação de localização rotativa

- Cada post marca UMA cidade da região, alternando a cada dia:
  Volta Redonda → Barra Mansa → Resende → Porto Real → Barra do Piraí → Piraí → (repete).
- Marcar localização coloca o post no mapa/explorar daquela cidade → alcance
  local novo, fora dos seguidores atuais.
- Casar com a rotação de cidades dos Reels (Fase 7.3) quando possível.

## 9.4 — Cross-post no Facebook

- Republicar o mesmo Reel/alerta na página do Facebook (público diferente,
  costuma ser mais velho e mais local).
- Custo marginal ~zero (mesmo vídeo). Bom para alertas de utilidade pública.
- Operacional: se houver página no Facebook, ligar o cross-post no fluxo de
  publicação (publicar.py) OU fazer manual no início.

## Pendências que dependem de 'ok' / ação humana

1. Lista final de perfis para colab (handles reais) → trazer pro chat.
2. Autorização de cada DM, um a um.
3. Definir se o cross-post no Facebook é automático (código) ou manual.

> Este doc NÃO envia DM, NÃO publica e NÃO marca ninguém. É só o plano.

