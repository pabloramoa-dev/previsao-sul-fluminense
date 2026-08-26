# Pablo Guru V2

Modulo experimental e isolado para evolucao visual e sonora do Pablo Guru.

## Isolamento

- Nao importa nem altera `reels/piloto.py`, `reels/dvh_lib.py`, `gerar_dia.py`, `gerar_tarde.py` ou o workflow automatico do Ranzinza/Dona Maria.
- Dependencias proprias em `pablo_guru/requirements.txt`.
- Render de teste deve ser manual e produzir apenas artifact; nunca publica no Instagram.
- A base usa Manim Community 0.21.0 e Python 3.12.

## Estrutura

- `characters/`: rigs, personagens e expressoes
- `motion/`: gestos, reacoes, camera e transicoes
- `audio/`: voz, lipsync, ambiencia e masterizacao
- `scenes/`: episodios
- `assets/`: recursos exclusivos do Pablo Guru
- `scripts/`: orquestracao de render
- `tests/`: testes de regressao e sanidade

Primeiro episodio de validacao: **PABLO GURU — A ESTACAO**.
