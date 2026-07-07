# previsao-sul-fluminense

Automacao 100% automatica de previsao do tempo para o Instagram
**@previsaosulfluminense**, cobrindo 5 cidades do Sul Fluminense:
Volta Redonda, Barra Mansa, Resende, Porto Real e Angra dos Reis.

## O que ele publica

| Post | Quando (BRT) | Workflow |
|------|--------------|----------|
| Carrossel do dia | 06h diario | `post_manha.yml` |
| Carrossel da noite | 18h diario | `post_noite.yml` |
| Alertas de tempo | a cada 2h (7h-19h) | `monitor_alertas.yml` |
| Fim de semana | quinta 18h30 | `fim_de_semana.yml` |
| Mito ou Verdade | domingo 12h | `curiosidade.yml` |
| Lembrete de token | dia 1o do mes | `renovar_token.yml` |

Todos os carrosseis terminam com uma pergunta fechada de engajamento, e
apos manha/noite e publicado um Story com a mesma pergunta.

## Arquitetura

- **Dados:** Open-Meteo (previsao, sol/UV e qualidade do ar) - gratuito, sem chave.
- **Imagens:** geradas com Pillow em `assets/output/` e servidas via raw URL.
- **Publicacao:** Instagram Graph API v22.0 (carrossel, imagem unica e story).
- **Orquestrador:** `src/main.py`, chamado pelos workflows.
- **Estado:** `src/estado.json` (rotacao de perguntas + anti-spam de alertas) e
  `src/historico.json` (recordes e comparacoes), commitados de volta pelo Action.

## Configuracao dos Secrets (obrigatorio)

Em **Settings > Secrets and variables > Actions**, crie:

- `IG_ACCESS_TOKEN` - token de longa duracao do Instagram (~60 dias de validade)
- `IG_USER_ID` - ID da conta Instagram (27148485038175)

> Por seguranca, esses valores devem ser inseridos por voce diretamente na
> tela de Secrets do GitHub. Nunca coloque o token em arquivos do repositorio.

Opcional: `RAW_BASE_URL` se as imagens forem servidas de outro local.

## Como renovar o token

O token expira em ~60 dias. Todo dia 1o o workflow `renovar_token.yml` abre
uma issue de lembrete. Para renovar:

1. Gere um novo token de longa duracao no Facebook Developers.
2. Atualize o Secret `IG_ACCESS_TOKEN`.
3. Rode qualquer workflow em modo dry-run para validar (ver abaixo).

## Como testar sem publicar (dry-run)

Cada workflow tem `workflow_dispatch` com a opcao **dry_run**. Em
**Actions > (workflow) > Run workflow**, marque `dry_run = true`. O sistema
gera imagens e captions e loga tudo, sem publicar no Instagram.

Localmente:

```bash
pip install -r requirements.txt
python -m src.main manha --dry-run
```

## Como pausar a automacao

Va em **Actions**, selecione o workflow desejado e clique em
**"..." > Disable workflow**. Para pausar tudo, desabilite os 6 workflows.
Para retomar, use **Enable workflow**.

## Como adicionar uma cidade

Edite a lista `CIDADES` em `src/clima.py` adicionando um dict com
`nome`, `lat` e `lon`. Os templates ja se ajustam ao numero de cidades.
Confira o layout gerando uma amostra em dry-run antes de publicar.

## Como adicionar perguntas ou curiosidades

- Perguntas: edite as listas em `src/perguntas.py`.
- Curiosidades: edite o banco em `src/curiosidade.py`.

A rotacao (sem repeticao) e controlada por indices salvos em `src/estado.json`.

## Notas tecnicas

- A Graph API publica a imagem do Story, mas o sticker interativo de enquete
  nao e suportado via API; o layout simula a enquete e direciona aos comentarios.
- Falhas de API sao logadas e o job sai com erro, evitando post pela metade.
- BRT = UTC-3, por isso os crons usam o horario UTC correspondente.
