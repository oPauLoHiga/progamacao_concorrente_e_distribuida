# Programacao Concorrente e Distribuida

Repositorio com materiais da disciplina de Programacao Concorrente e Distribuida.

## Estrutura do repositorio

### `em aula/`

Contem exercicios, exemplos e arquivos usados durante as aulas da disciplina.

Arquivos principais:

- `exemplo12.py` e `exemplo13.py`: exemplos desenvolvidos em aula;
- `ex14.py`, `ex15.py` e `ex16.py`: exercicios praticos;
- `Painel_26.csv`: base de apoio local para as aulas. Esse arquivo e grande e nao deve ser versionado.

### `TP01_Manipulando_Arquivos/`

Contem o Trabalho Pratico 01, cujo objetivo e manipular arquivos CSV da base da Justica Eleitoral usando versoes seriais e paralelas.

Arquivos principais:

- `tp01_arquivos.py`: codigo-fonte principal do TP01;
- `DOCUMENTACAO.md`: relatorio/documentacao do trabalho, com formulas, funcionamento, comandos de execucao e comparacao de tempos;
- `.gitignore`: regras especificas para nao versionar a base, arquivos gerados e caches do TP01;
- `Base de Dados/`: base local usada para executar o trabalho. Nao deve ser enviada como codigo-fonte;
- `TP01 - Manipulando arquivos.pdf`: enunciado do trabalho, mantido localmente para consulta.

A antiga pasta `N1` foi reorganizada: seu conteudo foi incorporado em `TP01_Manipulando_Arquivos`.

## Como executar o TP01

Entre na pasta do trabalho:

```powershell
cd "C:\Users\paulo\OneDrive\Documentos\Github_Desktop_Arquivos\progamacao_concorrente_e_distribuida\TP01_Manipulando_Arquivos"
```

Abrir o menu interativo:

```powershell
python tp01_arquivos.py
```

Executar a comparacao completa entre versoes serial e paralela:

```powershell
python tp01_arquivos.py --acao benchmark --municipio MACAPA
```

Mais comandos e detalhes estao documentados em `TP01_Manipulando_Arquivos/DOCUMENTACAO.md`.

## Observacoes sobre versionamento

As bases CSV, arquivos TXT/CSV gerados, caches do Python, arquivos de IDE e demais saidas locais nao devem ser enviados ao repositorio.

Para a entrega do TP01 pelo AVA, use somente os arquivos-fonte e a documentacao solicitada pelo professor.
