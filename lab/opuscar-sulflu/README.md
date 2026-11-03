# Laboratório Lemo Opuscar — Previsão SulFlu

Experimento independente e **sem publicação automática**: duas direções gráficas inspiradas nas técnicas documentadas em [Broadcast News Package](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/news-package/STYLE.md) e [Data Storytelling](https://github.com/lemomo-ai/lemo-opuscar/blob/main/styles/dataviz/STYLE.md).

O código usa Pillow e ffmpeg, ambos compatíveis com CPU. **Não copia os filmes de demonstração nem instala o motor inteiro do Opuscar.** A escolha é intencional: reaproveitar a gramática de composição e ritmo sem introduzir dependências WebGL/GPU no pipeline existente de HyperFrames + Remotion. Código e roteiro novos para o SulFlu.

## Como testar sem publicar

```bash
python -m pip install pillow
python -m unittest discover -s lab/opuscar-sulflu -p 'test_*.py' -v
python lab/opuscar-sulflu/piloto.py --estilo noticiario --saida output/opuscar-noticiario.mp4
python lab/opuscar-sulflu/piloto.py --estilo dados --saida output/opuscar-dados.mp4
```

Os exemplos usam dados fictícios identificados em todos os quadros; **não publicar essas prévias**. Com dados reais já preparados em JSON, passar `--dados reels/dia.json` (desde que contenha `cidades` com `nome`, `min`, `max`, `cond` e `chuva_mm`). A marca de demonstração continua presente: o experimento ainda não é um Reel de produção. A workflow `opuscar-sulflu-piloto.yml` salva os dois MP4 de teste em *Artifacts*.

## Melhorias analisadas

- **Pacote de telejornal:** cards animados, hierarquia visual, cores por tipo de tempo e marca consistente.
- **História com dados:** escala de precipitação igual para todas as cidades, barras que crescem, cada valor exibido em milímetros, sem inventar previsão.
- **Cidades:** até 20, cinco por página, para não omitir municípios após a primeira tela.
- **Performance:** composição 540x960/15fps por CPU como prova de viabilidade; produção 1080x1920/30fps somente após medir desempenho.
- **Segurança editorial:** valida temperatura mínima/máxima, chuva não negativa e números finitos. Não acessa API nem token e não publica.

## Próximos passos condicionados à avaliação

Migrar partes aprovadas para `lab/remotion-juarez/src/WeatherCast.tsx` como componente opcional, sincronizar transições às batidas reais de `pacote.json`, preservar a narração original do Juarez e as margens seguras do Instagram. Adicionar QA de quadros pretos, duração, áudio e legibilidade antes de considerar ativar no `juarez.yml`.

Outras direções úteis para futuros pilotos: Pictogram Motion (ícones climáticos), Transit Map (mapa por municípios, somente com geometria fiel e licenciada) e Caption News (ganchos de alertas). Evitar 3D pesado e manipulação de mapas não validados no runner gratuito.
