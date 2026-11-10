# Agendamento externo para @previsaosulflu

Os workflows `.github/workflows/juarez.yml` e `.github/workflows/card_amanha.yml` agora aceitam `repository_dispatch`. Os agendamentos redundantes do GitHub continuam como reserva e `boletim-regional.yml` verifica recibos de publicações anteriores, evitando repetição por turno.

## Configuração no cron-job.org

Crie duas tarefas diárias no fuso `America/Sao_Paulo`:

| Horário do disparo | event_type | Publicação |
| --- | --- | --- |
| 05:15 | `sulflu_bira` | Bira, previsão de hoje às 06:00 |
| 17:15 | `sulflu_bia` | Bia, previsão de amanhã às 18:00 |

Método: `POST`.
URL: `https://api.github.com/repos/pabloramoa-dev/previsao-sul-fluminense/dispatches`.
Headers: `Accept: application/vnd.github+json`, `Content-Type: application/json`, `Authorization: Bearer SEU_TOKEN`, `X-GitHub-Api-Version: 2022-11-28`.
Body JSON: `{"event_type":"sulflu_bira"}` ou `{"event_type":"sulflu_bia"}`.

Use token fine-grained restrito ao repositório, com Contents: Read and write. Resposta esperada HTTP 204. Nunca compartilhe o token em documentação pública.

Os jobs aguardam o horário de publicação se disparados antecipadamente e não publicam se muito fora da janela. O registro por dia e turno evita duplicatas após uma publicação confirmada.

**Situação:** é necessário criar as duas tarefas no cron-job.org; editar o repositório não configura essa conta externa.
