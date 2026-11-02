# Preparação do repositório próprio Nina e Zuleide

Este branch experimental registra a especificação de um **novo repositório independente** desejado: `pabloramoa-dev/nina-e-zuleide`. **Ele NÃO É o repositório novo**, e a branch principal nem workflows de produção foram alterados.

Em 2026-11-02 foi preparado um pacote de importação entregue na conversa como `NINA_E_ZULEIDE_REPOSITORIO_50_EPISODIOS.zip`. A conexão GitHub disponível não possui a ação de criar repositórios; o arquivo ZIP está pronto para importar assim que o repositório vazio for criado.

## Canon de personagens e câmera
- Nina adulta atrevida, namoradeira e protagonista de confusões amorosas bem-humoradas no condomínio.
- Zuleide adulta amiga, confidente e fofoqueira, com humor e ótimas reações.
- Exatamente **duas personagens**. Modelo original Nina de `pabloramoa-dev/nina-me-contou:motor/nina_lib.py` e Zuleide de `pabloramoa-dev/previsao-sul-fluminense:reels/previsao_lib.py`.
- Close 3×4, apenas rosto e ombros, Zuleide ampliada. Motor Manim original, **SEM Kugutu**.
- Ilustração de apoio superior e inferior **diferentes** em cada cena, nunca a mesma imagem em ambos os quadros.
- Gerar roteiro, depois prompts de imagens por cena e perspectiva, depois 10 imagens no quadro de Nina + 10 no quadro de Zuleide via SiliconFlow.
- Histórias originais, ~3 minutos, começo, meio e fim, gancho de antecipação na primeira frase, sem parte 1/2.
- Kokoro e risadas, output MP4 H.264/AAC em artifact, **sem postagem automática**.

## Pesquisa e 50 episódios
O pacote contém `data/50_episodios.json`: **50 pautas originais**, cada uma com gancho, situação, virada e atribuição de inspiração. `data/fontes_pesquisadas.json`: dez notícias sobre vídeos/postagens com situações virais + três estudos de tendências. **Não afirmar que foram encontrados 50 vídeos virais individuais.** Não copiar falas, vídeo, nomes reais ou cenas protegidas.

## Configuração depois da criação do repositório
- Configurar segredos `OPENAI_API_KEY` e `SILICONFLOW_API_KEY` no repo novo, sem expor credenciais.
- Copiar para raiz o conteúdo do ZIP. O workflow `.github/workflows/gerar-episodio.yml` é manual, com entrada `episodio` de 1 a 50; não publica por conta própria.
- O pacote teve testes locais de integridade do catálogo e não repetição de imagens demonstrativas. O workflow completo do novo repo **ainda não foi validado por GitHub Actions**, pois o repo ainda não existe.

Referências oficiais de produto e tendência:
- https://ads.tiktok.com/business/pt-BR/next
- https://metricool.com/instagram-trends/
- https://about.fb.com/news/2026/03/social-feeds-are-powering-indias-micro-drama-boom-meta-ormax-report/amp/
- https://siliconflow.readme.io/reference/imagegeneration
