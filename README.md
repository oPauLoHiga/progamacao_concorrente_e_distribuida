# Programacao Concorrente e Distribuida

Repositorio com materiais da disciplina de Programacao Concorrente e Distribuida.

## Estrutura do repositorio

### `em aula/`

Contem exemplos e exercicios praticos usados durante as aulas.

Arquivos principais:

- `exemplo12.py` e `exemplo13.py`: exemplos desenvolvidos em aula;
- `ex14.py`, `ex15.py` e `ex16.py`: exercicios praticos;
- `Painel_26.csv`: base local de apoio para os exemplos com pandas, ignorada pelo Git por ser grande.

Os arquivos dessa pasta foram mantidos no formato original dos exemplos de aula.

### `TP01_Manipulando_Arquivos/`

Contem o Trabalho Pratico 01. O objetivo do TP01 e manipular arquivos CSV da base da Justica Eleitoral usando versoes seriais e paralelas.

Arquivos principais:

- `tp01_arquivos.py`: codigo-fonte principal do TP01;
- `DOCUMENTACAO.md`: relatorio/documentacao com formulas, funcionamento, comandos de execucao e comparacao de tempos;
- `.gitignore`: regras especificas para nao versionar a base e os arquivos gerados pelo TP01;
- `Base de Dados/`: base local usada para executar o trabalho, ignorada pelo Git;
- `TP01 - Manipulando arquivos.pdf`: enunciado local do trabalho, ignorado pelo Git.

## Como executar o TP01

Abrir a pasta do trabalho

Abrir o menu interativo:

```powershell
python tp01_arquivos.py
```

Executar a comparacao completa entre as versoes serial e paralela:

```powershell
python tp01_arquivos.py --acao benchmark --municipio MACAPA
```

Mais comandos e detalhes estao em `TP01_Manipulando_Arquivos/DOCUMENTACAO.md`.

## Versionamento

As bases CSV, arquivos TXT/CSV gerados, caches do Python, arquivos de IDE e demais saidas locais nao devem ser enviados ao repositorio.

Para a entrega do TP01 pelo AVA, use somente os arquivos-fonte e a documentacao solicitada pelo professor.
