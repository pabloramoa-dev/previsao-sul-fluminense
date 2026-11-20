# Previsão Sul Fluminense — @previsaosulflu

Automação de previsão do tempo para Instagram. O sistema coleta dados de **10 municípios fixos** do Sul Fluminense e, **às sextas-feiras e aos domingos**, inclui **Angra dos Reis** no boletim. Exibe **exatamente 5 cidades distintas por boletim principal**: a cidade em destaque e quatro municípios de maior audiência, sem duplicação. As cinco têm mínima e máxima no Reel, no card e nas respectivas legendas.

Municípios regulares: Volta Redonda, Barra Mansa, Resende, Porto Real, Barra do Piraí, Piraí, Itatiaia, Quatis, Pinheiral e Rio Claro. **Angra dos Reis** participa da coleta do Open-Meteo e abre a seleção de cinco cidades **nos boletins publicados na sexta-feira e no domingo** (Reel das 06h e card das 18h, ambos pelo dia de publicação, no horário de Brasília). Nos demais dias, a seleção mantém as dez cidades regulares.

## Bairros em foco nos Reels (rodízio por dia e turno)

Os cinco municípios do quadro permanecem identificados pelo nome da cidade,
com **um bairro ou localidade real em destaque por cidade**. O catálogo
`estudio/bairros_foco.py` utiliza nomes já presentes em `dm/dm_bairro.py`.
O sorteio não é aleatório: segue a **data local de publicação** e diferencia
Bira (06h) e Bia (18h), permitindo reproduzir um boletim sem mudar os bairros.
Cada município gira apenas entre os nomes validados do seu próprio cadastro.

A apresentação traz o bairro principal na abertura, identifica o bairro
junto à cidade nas cinco linhas do quadro e lista os bairros na legenda.
O narrador também destaca o município com **maior volume diário de chuva previsto
entre todas as cidades efetivamente coletadas**, inclusive quando não está no
quadro das cinco. Nessa fala, menciona o bairro editorial da vez desse município.
Se não houver ao menos 1 mm previsto, não inventa uma maior chuva.

**Precisão:** os valores meteorológicos atuais são os do Open-Meteo para
as coordenadas **dos municípios**. Bairros são referências de identificação
local, não medições independentes e não significam que aquele bairro terá
mais chuva que os demais do município. Não publicar rankings de bairros
mais chuvosos até existir uma previsão verificável por coordenadas de bairro.
Municípios com apenas um nome local confirmado (por exemplo, Pinheiral no
cadastro atual) não ganham bairros fictícios para forçar alternância.

Validação sem publicar: `python estudio/test_bairros_foco.py`; o mesmo
teste integra `.github/workflows/testes.yml`. A renderização também aplica
`estudio/bairros_visual.patch`, sobre o motor visual do Previsão RJ.

## Programação ativa (horário de Brasília, UTC-3)

| Conteúdo | Horário | Workflow | Observações |
|---|---|---|---|
| Reel do Bira — previsão de hoje | Todos os dias às 06h | `.github/workflows/juarez.yml` | Motor visual do RJ; abre com cidade de destaque, capa informativa, duração-alvo 20–25 s. |
| Reel “amanhã” da Bia | Todos os dias por volta das 18h | `.github/workflows/card_amanha.yml` | Vídeo de 20–25 s com cidade e temperatura em destaque, capa própria e legenda regional. |
| Monitor de alertas | A cada 2h, das 07h às 19h | `.github/workflows/monitor_alertas.yml` | Reels de 14 segundos com cidade e hora de emissão no primeiro quadro; só com gatilho, máximo de dois alertas/dia. |

O detector de alertas continua monitorando as dez cidades regulares, inclusive cidades fora do resumo diário. Angra é uma inclusão editorial no Reel e no card às sextas e domingos, não uma extensão do monitor de alertas. **São previsões, não observações.** O quadro retrospectivo “Choveu quanto?” está suspenso até existir uma fonte de dados realmente observados para as últimas 24h. O monitor também pode ser testado sem publicar: gera MP4, JPG de capa e legenda no artifact. O horário destacado é o da emissão do boletim, não a hora exata da ocorrência prevista.

Os workflows antigos, carrosséis e pilotos fora de produção foram movidos para `arquivo/workflows/`. Para reativar um experimento, faça revisão e restaure-o deliberadamente em `.github/workflows/`.

## Como funciona

1. `reels/coletar_tempo.py` consulta o Open-Meteo em lote para os dez municípios regulares e adiciona Angra dos Reis na sexta e no domingo. Em falhas transitórias (incluindo 429 e 5xx), tenta até três vezes; dados com contagem incorreta de cidades são rejeitados.
2. `reels/coletar_tempo.py:resumo_cinco()` seleciona as cinco cidades exibidas. `estudio/regional.py` exige cinco cidades e alterna a abertura entre os dez municípios regulares, separando Bira e Bia por cinco posições no ciclo; o monitor de alerta continua cobrindo os dez municípios.
3. O motor do RJ produz áudio e vídeo; `tools/finalizar_reel_sulflu.py` insere o destaque numérico no início, verifica área segura e duração, e gera `CAPA.jpg`.
4. `reels/postar_reel.py` publica os vídeos, registra formato/gancho/ID confirmado em `data/registro_formatos.json` e publica uma pergunta curta no primeiro comentário.
5. O workflow publica com a Instagram Graph API, verifica o processamento da mídia e executa limpeza de arquivos temporários.

O sistema bloqueia a geração do boletim quando faltam cidades ou dados essenciais: é preferível registrar falha a publicar uma previsão parcial. Os gatilhos de alerta vêm do `limiares.py`. O monitor legado obtém dados via `src/clima.py`.

## Testes seguros (sem publicar)

- Em **GitHub Actions → Testes**, rode o workflow `testes.yml`, que valida os roteiros e as regras sem rede.
- Em **Actions → Bira do Tempo — manhã (06h) → Run workflow**, mantenha **Publicar no Instagram?** desmarcado. O MP4 aparece como artifact temporário para avaliação visual.
- Em **Actions → Bia — tarde (18h) → Run workflow**, mantenha **Publicar no Instagram?** desmarcado.
- Em **Actions → Monitor de Alertas → Run workflow**, deixe **dry_run = true** (padrão manual). O cron automático permite publicação quando há alerta.

Não acione o modo de publicação manual para testar se você não quer enviar conteúdo à conta.

## Credenciais

No GitHub, em **Settings → Secrets and variables → Actions**, configure `IG_USER_ID` e `IG_ACCESS_TOKEN` para as publicações. Nunca inclua tokens no repositório. O token pode precisar de renovação periódica. Os workflows usam `MAIL_USERNAME` e `MAIL_PASSWORD` para avisos de falha por e-mail, quando configurados.

## Manutenção

- Para ajustar o rodízio e os dias fixos de Angra, edite `reels/coletar_tempo.py` (`DIAS_ANGRA` e `cidades_para_publicacao`). A lista de dez municípios para alertas continua em `src/clima.py`.
- Para controlar os critérios de alerta, revise `limiares.py` e `src/alertas.py` e execute os testes antes de publicar.
- Para suspender qualquer publicação automática, desabilite o workflow específico em **Actions → Workflow → ⋯ → Disable workflow**.
- Use o arquivo de diagnóstico das execuções do GitHub Actions para confirmar o sucesso de cada publicação; código correto não comprova postagem já realizada.
\n## Experimento de retenção / mensuração\n\nOs Reels das 06h e 18h convivem; não substituir a manhã. Cada publicação registra cidade de abertura, gancho, CTA, formato e ID. O workflow `channel-metrics.yml` associa os dados aos recibos. O campo original `comments` é preservado; `comments_organic_estimate` desconta até um comentário automático por post, **como estimativa** (não é uma identificação verificada do autor do comentário).\n\nA política atual exige duração de 20 a 25 segundos, capa e destaque dentro de área segura. A geração falha, sem publicar, se o vídeo não passar no QA. Não publicar números sem previsão válida.\n
## Vozes e encerramento dos Reels

Bira usa `pm_alex:0.82+pm_santa:0.18` e Bia usa `pf_dora:0.85+af_heart:0.15`. Cada apresentador mantém seu timbre quando aparece nos dois canais.

A narração termina com um único convite de envio ligado ao assunto do vídeo.

## Rodízio editorial e estratégia de compartilhamento (novembro de 2026)

O primeiro destaque alterna entre **os dez municípios regulares**, um novo por dia
para cada apresentador, com diferença de cinco posições entre os turnos.
Os cinco municípios do quadro são o destaque do turno e quatro cidades
priorizadas pelo histórico de audiência; nunca há cidade duplicada.
A edição considera todos os municípios coletados para o maior acumulado de
chuva previsto. Angra dos Reis permanece no conjunto de previsões de sexta e
domingo, mas não substitui a rotação regular de abertura.

Os primeiros segundos mostram **cidade, temperatura e referência de dia**;
o bairro editorial (quando cadastrado) serve para identificação, não para
afirmar medições meteorológicas específicas do bairro. A capa, a primeira
linha da legenda e o vídeo compartilham a mesma cidade. Há **um CTA final**,
adaptado ao assunto: chuva (cidade do maior volume), calor, frio ou previsão
local. É proibido fabricar alertas ou volumes de chuva para aumentar alcance.

A renderização mantém o motor do RJ com HyperFrames, as vozes e o QA:
formato 9:16, 1080×1920, 20–25 segundos e área segura. Não se substitui
a trilha editorial ou os dados do SulFlu pelos do Rio.

**Validação:** `python estudio/test_regional_rodizio.py` (requer `num2words`);
o CI executa este teste junto dos demais. Os resultados publicados são
monitorados pelo workflow `channel-metrics.yml` em janelas de 24h/72h.
Para avaliar a melhoria, comparar alcance, compartilhamentos por mil pessoas
alcançadas e seguidores conquistados por Reel quando disponíveis. Os
insights existentes não comprovam retenção nos três primeiros segundos nem
a causa do crescimento do perfil do Rio.

### Plantão diário das 14h (Brasília)

`monitor_alertas.yml` consulta diariamente às 17h UTC (14h BRT), nas dez cidades
regulares, os modelos DWD ICON e NOAA GFS via Open-Meteo. O GitHub pode atrasar
inícios agendados. Publica **um plantão com Bia no Reels e nos Stories**, somente
se ambos os modelos indicarem o mesmo risco com janelas sobrepostas nas próximas
24 horas. Os demais boletins de 6h/18h continuam independentes.

Critérios editoriais conservadores (não equivalem a aviso oficial): temporal
WMO 95/96/99; granizo somente 96/99 nos dois modelos; chuva >=20 mm/1h,
>=30 mm/3h ou >=50 mm/24h; rajadas >=60 km/h. Temperatura, calor e chuva comum
não liberam este plantão. Dados incompletos, falha na API, divergência ou consulta
com mais de duas horas bloqueiam a publicação. A narração distingue previsão
de certeza, com cidade, data e janela do evento. Uma possibilidade de granizo
em apenas um modelo não é anunciada como granizo corroborado.

As evidências e os arquivos ficam no artifact da execução. Os recibos separados
em `data/alertas_14h_publicados.json` permitem retomar o Story sem duplicar o
Reel. Falhas de Story fazem o job falhar. Disparo manual começa em `dry_run=true`;
push roda testes e consulta real, sem render nem publicação. O monitor
experimental de mudanças bruscas continua apenas produzindo relatórios.

Documentação da fonte: https://open-meteo.com/en/docs
