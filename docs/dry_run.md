# Dry-run — como testar a Fase 6 antes do merge

> A integração da Fase 6 está na branch fix/conversao-e-slot-noturno (PR #4).
> Este roteiro testa TUDO sem publicar nada no Instagram.
> O agente não consegue executar Python no navegador — estes passos são para
> rodar na sua máquina ou no GitHub Actions.

## 1) Teste rápido dos módulos novos (sanity checks)

Cada módulo da Fase 6 tem um _sanity() embutido. Rode:

```bash
python -c "from src import ganchos;      ganchos._sanity_check_bancos(); print('ganchos ok')"
python -c "from src import hashtags;     hashtags._sanity();             print('hashtags ok')"
python -c "from src import varal;        varal._sanity();                print('varal ok')"
python -c "from src import travas;       travas._sanity();               print('travas ok')"
python -c "from src import slots_config; slots_config._sanity();         print('slots ok')"
```

Esperado: cinco linhas "ok", sem exceção.

## 2) Dry-run do pipeline completo (NÃO publica)

O main.py já aceita --dry-run:

```bash
python -m src.main manha --dry-run
python -m src.main noite --dry-run
```

O que conferir na saída:

- [ ] Rodou sem exceção e terminou com "=== Concluido com sucesso ===".
- [ ] A legenda impressa começa com o GANCHO (não com "bom dia"/logo).
- [ ] A legenda termina com um conjunto de HASHTAGS.
- [ ] O conjunto de hashtags da manhã é DIFERENTE do da noite no mesmo dia.
- [ ] O gancho da manhã é diferente do da noite.
- [ ] NÃO aparece publicação de carrossel no feed (Fase 6.4) — só story/reel.
- [ ] Na noite, se a chance de chuva 18h-06h passar do limiar, aparece o aviso
      do varal; se não passar, não aparece.

## 3) Teste das travas (o bug dos 27 carrosséis)

Rode o MESMO slot duas vezes seguidas:

```bash
python -m src.main manha --dry-run
python -m src.main manha --dry-run
```

- Na segunda execução deve aparecer:
  `[travas] conteudo ja publicado hoje no slot manha; abortando.`
- Obs.: o registro só é gravado quando NÃO é dry-run. Para testar de verdade a
  trava de duplicata, rode uma vez sem --dry-run em ambiente de teste, ou
  chame travas.registrar_publicacao(...) manualmente antes da segunda rodada.

Teste do lock (execução simultânea): abra dois terminais e dispare ao mesmo
tempo — o segundo deve falhar com LockError.

## 4) Teste da legenda curta (Fase 6.2)

```bash
python -c "from src import travas; travas.validar_caption('curta')"
```

Esperado: LegendaInvalidaError (legenda com menos de 40 caracteres é rejeitada).

## 5) Só depois disso: merge

Se os itens acima passarem, o PR #4 pode ser mergeado. Sugestão de ordem:

1. Merge do PR #4.
2. Rodar UM dia em modo real observando o resultado.
3. Só então aplicar as mudanças de Reel da Fase 7 (gerar_noite.py, Juarez).

## O que este PR NÃO faz (continua pendente)

- Não cria o Reel da noite (Juarez Plantão) — só documenta (Fase 7).
- Não mexe no ranzinza.yml (cron das 11h20 continua lá) — Fase 7.4.
- Não arquiva os carrosséis antigos (só dá pelo app do celular) — Fase 4.
- Não fixa Reels nem cria Destaques (só pelo app) — Fase 5.
- Não publica comentários nem envia DM (precisa de 'ok') — Fases 8 e 9.

