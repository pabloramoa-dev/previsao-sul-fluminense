# Áreas com histórico de inundação e alagamento — @previsaosulflu

Curadoria inicial: **20/11/2026**. Abrange as dez cidades fixas de `src/clima.py`.
**Não é mapa de inundação em tempo real, nem previsão por bairro.**
A lista inclui registros pontuais e estudos históricos. Obras de drenagem,
mudança de leito, barreiras e medidas municipais podem alterar o risco.

## Fonte técnica principal

INEA / COPPETEC, *Diagnóstico de Vulnerabilidades*, anexo 4, tabela 4.5.1,
RH-III, principalmente página 3 do documento (página 5 do PDF):
https://www.inea.rj.gov.br/wp-content/uploads/2021/03/Diagn%C3%B3stico-Vulnerabilidades-Vol.-I-Anexos-4-e-5.pdf

## Cidades e evidências

| Município | Rios, pontos e bairros historicamente associados | Fundamentação |
|---|---|---|
| Volta Redonda | Córrego Cachoeirinha / Ribeirão Brandão — Vila Santa Cecília, Siderópolis e Sessenta; Córrego Secades — Rua 41, Vila Santa Cecília; alagamentos urbanos na Vila Rica (Rua 23), Casa de Pedra e Roma | INEA; ocorrência de 02/11/2026: https://folhadoaco.com.br/2026/11/02/temporal-provoca-alagamentos-em-volta-redonda-e-causa-transtornos-em-outras-cidades-do-sul-fluminense/ |
| Barra Mansa | Rio Barra Mansa — São Luís, Nova Esperança, Boa Sorte; Rio Bananal — Santa Maria II, Saudade, Vila Maria; Rio Bocaina — Bocaininha, Siderlândia; Córrego Cotiara — Roberto Silveira; Rio Paraíba do Sul — Vista Alegre, Centro e Vila dos Remédios (registro de fevereiro de 2026) | INEA; https://www.correiodamanha.com.br/sul-fluminense/cidades/2026/02/262943-nivel-do-rio-paraiba-sobe-com-alto-volume-de-chuvas-no-medio-paraiba.html |
| Resende | Rio Sesmaria — Parque Ipiranga, Jardim Brasília, Jalisco, Centro (INEA); Canal Periférico/Ribeirão Preto — Alegria, Baixada de Olaria, Itapuca e Liberdade. Transbordamento do Rio Sesmaria confirmado em fevereiro de 2026 | INEA; Prefeitura: https://voltaredonda.rio.br/prefeitura-de-resende-divulga-balanco-das-acoes-de-rescaldo-apos-chuvas-intensas/ |
| Itatiaia | Rio Santo Antônio / Córrego da Cazunga — Nova Conquista, Vila Martins e Centro | INEA |
| Barra do Piraí | Rio Piraí, abaixo da Barragem de Santana até sua foz; Rio Paraíba do Sul nas margens urbanas. Registro histórico de cheia do Rio Piraí no Centro, Chalet e Muqueca | INEA; https://www.papagoiaba.com/noticias/moradores-de-barra-do-pirai-cobram-servico-de-desassoreamento-do-rio-pirai |
| Piraí | Rio Piraí — Vale Verde I, Vale Verde II, Vila Nova Esperança, Asilo, Centro e Santanésia, segundo requerimento da Câmara referente à enchente de 30/04/2022 | https://sapl.pirai.rj.leg.br/sessao/342/votacao-nominal-transparencia/1556/13428?materia=ordem |
| Quatis | Ribeirão dos Quatis — Pilotos, onde houve transbordamento; Barrinha e Mirandópolis também atingidos em 2023, sem atribuição a um rio específico | https://avozdacidade.com/wp/rodovia-rj-159-que-liga-quatis-ao-distrito-joaquim-leite-esta-interditada/ |
| Pinheiral | Rio Paraíba do Sul — Parque Maíra (Loteamento Novo), área oficialmente classificada como de alta suscetibilidade; via próximo ao Rio Caximbau / canal na Rodovia Benjamin Constant km 9, ligação Pinheiral–Arrozal (alagamento e obstrução em novembro de 2026) | Prefeitura: https://pinheiral.rj.gov.br/comunicacao/assessoria-de-comunicacao/noticias/prefeitura-de-pinheiral-em-razao-de-acoes-civis-publicas--desocupa-area-de-protecao-ambiental-no-parque-maira/ e https://www.pinheiral.rj.gov.br/comunicacao/assessoria-de-comunicacao/noticias/prefeitura-realiza-desobstrucao-de-canal-na-rodovia-benjamin-constant/ |
| Rio Claro | Rio Claro — parte baixa da sede municipal; distrito de Lídice — moradias ribeirinhas e próximas à rodovia, conforme Defesa Civil local. Registro de transbordamento em janeiro de 2026 | https://rioclaro.rj.gov.br/prefeito-babton-biondi-decreta-situacao-de-emergencia-em-rio-claro-apos-fortes-chuvas/ e https://rioclaro.rj.gov.br/defesa-civil-reforca-alerta-para-riscos-em-encostas-durante-periodo-de-chuvas-em-rio-claro/ |
| Porto Real | Rios Paraíba do Sul, Piá e Barreiro; fundos de vale e trechos ribeirinhos. **Sem bairros nomeados como hotspots de inundação nesta base**: o documento de saneamento descreve suscetibilidade geral, mas não confirma recorrência em cada bairro. | Plano Municipal de Saneamento: https://www.ceivap.org.br/saneamento/pmsb-fluminenses/pmsb-porto-real.pdf |

Fontes adicionais para o contexto regional:
- CEMADEN-RJ, painel municipal hidrológico (situação dinâmica; nunca interpretar
  automaticamente como transbordamento confirmado):
  https://painelcemadenrj.defesacivil.rj.gov.br/monitoramento/v2/municipio/?action=2
- Dados de 2026 sobre o Rio Paraíba do Sul, Rio Sesmaria e áreas ribeirinhas:
  https://diariodovale.com.br/cidade/nivel-do-rio-paraiba-sobe-e-causa-alagamentos-no-sul-fluminense/

## Regras obrigatórias para o plantão

1. A base `tools/areas_alagamento.py` é apenas contexto estático geográfico.
   Ela **nunca inicia publicação** ou muda o gatilho de tempestade.
2. Nos alertas gerados por dois modelos, o vídeo pode nomear áreas de atenção
   apenas se existir evento **chuva intensa** corroborado para a MESMA cidade.
   Um código meteorológico de tempestade, sozinho, não comprova alto volume.
3. Se houver aviso oficial INMET de tempestade, referir-se à base apenas como
   histórico/suscetibilidade para as cidades efetivamente cobertas.
4. Dizer “atenção a áreas com histórico de alagamento”, **não**
   “esses bairros vão alagar”, “o rio transbordou” ou “evacue”, salvo
   informação oficial atual e específica que justifique outra linguagem.
5. Previsão meteorológica municipal **não é** previsão do nível do rio nem
   do alagamento em uma rua ou bairro. Cheias do Paraíba do Sul podem depender
   de precipitação a montante e operação de reservatórios, não só da chuva local.
6. Evitar detalhes excessivos na narração: no máximo um grupo de pontos
   para a cidade em destaque. Usar legenda para referências adicionais.
7. Dar instruções seguras: não atravessar ruas alagadas; Defesa Civil 199 e
   Bombeiros 193 em situações de emergência. Não divulgar dados de réguas,
   cota de transbordo ou vazões sem medição atual autenticada.

## Manutenção

Revalidar periodicamente com setorização SGB, planos de contingência municipais,
INEA e ocorrências da Defesa Civil. Preferir informações oficiais recentes a
notícias isoladas; remover pontos quando intervenções descaracterizarem os riscos.
