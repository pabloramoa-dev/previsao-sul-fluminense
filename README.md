# Previsão Sul Fluminense — @previsaosulflu

Automação de previsão do tempo para Instagram. O sistema coleta dados de **10 municípios** do Sul Fluminense e exibe **exatamente 5 cidades distintas por boletim principal**: a cidade do rodízio diário e as cidades de maior audiência, sem duplicação. As cinco têm mínima e máxima no Reel, no card e nas respectivas legendas.

Municípios monitorados: Volta Redonda, Barra Mansa, Resende, Porto Real, Barra do Piraí, Piraí, Itatiaia, Quatis, Pinheiral e Rio Claro. Angra dos Reis **não** pertence à lista de coleta atual.

## Programação ativa (horário de Brasília, UTC-3)

| Conteúdo | Horário | Workflow | Observações |
|---|---|---|---|
| Reel do Juarez — previsão de hoje | Todos os dias às 06h | `.github/workflows/juarez.yml` | HyperFrames, acabamento Remotion, Antonio Neural com fallback Kokoro. Publica Reel e tenta Story. |
| Card da previsão de amanhã | Todos os dias por volta das 18h | `.github/workflows/card_amanha.yml` | Foto com cinco cidades, mesma seleção na legenda. |
| Monitor de alertas | A cada 2h, das 07h às 19h | `.github/workflows/monitor_alertas.yml` | Só publica se houver gatilho; máximo de dois alertas por dia, sem repetição do mesmo tipo em 6h. |

O detector de alertas monitora a região toda (10 cidades), inclusive cidades fora do resumo diário. **São previsões, não observações.** O quadro retrospectivo “Choveu quanto?” está suspenso até existir uma fonte de dados realmente observados para as últimas 24h. O monitor também pode ser testado sem publicar.

Os agendamentos antigos de Seu Ranzinza e Dona Maria (`ranzinza.yml`), carrosséis (`post_manha.yml`, `post_noite.yml`, `fim_de_semana.yml`) e formatos experimentais estão desligados; seus arquivos continuam disponíveis para execução manual.

## Como funciona

1. `reels/coletar_tempo.py` consulta o Open-Meteo em lote para os dez municípios. Em falhas transitórias (incluindo 429 e 5xx), tenta até três vezes; dados com contagem incorreta de cidades são rejeitados.
2. `reels/coletar_tempo.py:resumo_cinco()` seleciona as cinco cidades exibidas. `reels/gerar_juarez.py` exige cinco cidades mesmo em dia de alerta.
3. `hyperframes/gerar_hf.py` produz áudio e vídeo, e `lab/remotion-juarez/finalizar.py` realiza acabamento e validação antes da publicação.
4. `reels/postar_reel.py` e `reels/gerar_card_amanha.py` reutilizam a mesma seleção, mantendo legenda e quadro coerentes.
5. O workflow publica com a Instagram Graph API, verifica o processamento da mídia e executa limpeza de arquivos temporários.

O sistema bloqueia a geração do boletim quando faltam cidades ou dados essenciais: é preferível registrar falha a publicar uma previsão parcial. Os gatilhos de alerta vêm do `limiares.py`. O monitor legado obtém dados via `src/clima.py`.

## Testes seguros (sem publicar)

- Em **GitHub Actions → Testes**, rode o workflow `testes.yml`, que valida os roteiros e as regras sem rede.
- Em **Actions → Reel diario — Juarez Plantao (06h) → Run workflow**, mantenha **Publicar no Instagram?** desmarcado. O MP4 aparece como artifact temporário para avaliação visual.
- Em **Actions → Card das 18h → Run workflow**, mantenha **Publicar no Instagram?** desmarcado.
- Em **Actions → Monitor de Alertas → Run workflow**, deixe **dry_run = true** (padrão manual). O cron automático permite publicação quando há alerta.

Não acione o modo de publicação manual para testar se você não quer enviar conteúdo à conta.

## Credenciais

No GitHub, em **Settings → Secrets and variables → Actions**, configure `IG_USER_ID` e `IG_ACCESS_TOKEN` para as publicações. Nunca inclua tokens no repositório. O token pode precisar de renovação periódica. Os workflows usam `MAIL_USERNAME` e `MAIL_PASSWORD` para avisos de falha por e-mail, quando configurados.

## Manutenção

- Para ajustar a ordem do rodízio e a lista de cidades, edite `reels/coletar_tempo.py`. Mantenha também `src/clima.py` alinhado para a cobertura de alertas.
- Para controlar os critérios de alerta, revise `limiares.py` e `src/alertas.py` e execute os testes antes de publicar.
- Para suspender qualquer publicação automática, desabilite o workflow específico em **Actions → Workflow → ⋯ → Disable workflow**.
- Use o arquivo de diagnóstico das execuções do GitHub Actions para confirmar o sucesso de cada publicação; código correto não comprova postagem já realizada.
