# Fase 10 — Medição (spec)

> Documento da Fase 10 do roteiro v2 do @previsaosulflu. Faz parte do PR da Fase 6
> (branch fix/conversao-e-slot-noturno). Define O QUE medir, as metas de 30 dias e
> as regras de decisão. Rotina: toda SEGUNDA-FEIRA trazer as métricas pro chat.
> Base do diagnóstico: 09/08/2026 (Windsor.ai, últimos 60 dias).

## Metas de 30 dias

| métrica | hoje | meta 30 dias |
|---|---|---|
| Seguidores | 53 | 300 |
| Alcance/dia | ~400 | 1500 |
| Alcance por Reel | ~105 | 300 |
| Tempo médio de exibição | 4,7s | 8s |
| Comentários/semana | 0 | 20 |
| Salvamentos | ~1 | 25 |
| Compartilhamentos | 3 | 30 |

- O gargalo NÃO é alcance (a conta já alcança ~700 contas/dia). É conversão e
  retenção. Por isso as metas de comentário, salvamento, exibição e seguidores
  pesam mais do que alcance bruto.

## 10.1 — Comparação manhã vs noite

- Medir os dois slots SEPARADAMENTE toda semana:

| métrica por slot | manhã (06h13) | noite (18h00) |
|---|---|---|
| alcance médio/Reel | | |
| tempo médio de exibição | | |
| comentários | | |
| salvamentos | | |
| seguidores ganhos atribuíveis | | |

- Preencher a tabela toda segunda e comparar. O slot que converte melhor recebe
  mais investimento de roteiro.

## Regras de decisão (após 14 dias de dados)

- Se um slot tiver tempo de exibição consistentemente maior → replicar a
  estrutura dele no outro slot.
- Se o CTA de salvamento (noite) estiver funcionando (salvamentos subindo) →
  reforçar utilidade; se não, testar outro CTA.
- Se um formato de gancho (BANCO_MANHA/BANCO_NOITE) repetir baixa retenção →
  aposentar esse tipo de gancho.

## Regra dura (o teste do vídeo)

> Se em 14 dias os seguidores NÃO passarem de 120, o problema não é
> distribuição — é o vídeo em si. Nesse caso, parar de mexer em distribuição e
> refazer o vídeo (gancho, primeiro segundo, ritmo), conforme Fase 7.

## De onde tirar os números

- Instagram: insights por post/Reel (alcance, exibição, salvamentos,
  compartilhamentos, comentários) — coleta manual ou via API.
- Windsor.ai (já usado no diagnóstico) para série histórica.
- Sugestão: registrar num CSV semanal (data, slot, métricas) pra ver a tendência.

> Este doc é só o plano de medição. Não coleta nem publica nada sozinho.

