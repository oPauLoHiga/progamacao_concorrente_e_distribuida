# Programacao Concorrente e Distribuida

Repositorio com materiais, exercicios e trabalhos praticos da disciplina de Programacao Concorrente e Distribuida.

## Visao geral

Este repositorio esta organizado por conteudo de aula e por trabalhos praticos. Os arquivos grandes, bases de dados, imagens de teste, PDFs de enunciado e saidas geradas localmente ficam fora do versionamento por meio dos arquivos `.gitignore`.

## Estrutura do repositorio

```text
.
|-- em aula/
|   |-- exemplo12.py
|   |-- exemplo13.py
|   |-- ex14.py
|   |-- ex15.py
|   `-- ex16.py
|-- TP01_Manipulando_Arquivos/
|   |-- tp01_arquivos.py
|   |-- DOCUMENTACAO.md
|   `-- .gitignore
|-- TP02 - Imagens/
|   |-- 24101911.py
|   |-- README.md
|   `-- .gitignore
|-- .gitignore
`-- README.md
```

## Conteudo

### `em aula/`

Contem exemplos e exercicios desenvolvidos durante as aulas.

Arquivos principais:

- `exemplo12.py` e `exemplo13.py`: exemplos praticos de aula;
- `ex14.py`, `ex15.py` e `ex16.py`: exercicios praticos.

### `TP01_Manipulando_Arquivos/`

Trabalho pratico sobre manipulacao de arquivos CSV da base da Justica Eleitoral, com comparacao entre versoes seriais e paralelas.

Arquivos principais:

- `tp01_arquivos.py`: codigo-fonte principal;
- `DOCUMENTACAO.md`: documentacao do trabalho, com objetivo, funcoes implementadas, comandos de execucao e comparacao de desempenho;
- `.gitignore`: regras especificas para ignorar base de dados e saidas locais.

A documentacao completa esta em [`TP01_Manipulando_Arquivos/DOCUMENTACAO.md`](TP01_Manipulando_Arquivos/DOCUMENTACAO.md).

### `TP02 - Imagens/`

Trabalho pratico sobre conversao de imagens coloridas para preto e branco usando processamento sequencial e processamento com threads.

Arquivos principais:

- `24101911.py`: codigo-fonte principal;
- `README.md`: documentacao do TP02, com funcionalidades, fluxo de execucao, organizacao do codigo e testes realizados;
- `.gitignore`: regras para ignorar imagens locais e saidas geradas.

A documentacao completa esta em [`TP02 - Imagens/README.md`](TP02%20-%20Imagens/README.md).

## Requisitos

- Python 3.10 ou superior;
- `pandas`, usado no TP01;
- `Pillow`, usado no TP02.

Instalacao sugerida das dependencias:

```powershell
python -m pip install pandas pillow
```

## Como executar

### TP01

Entre na pasta do trabalho:

```powershell
cd "TP01_Manipulando_Arquivos"
```

Abra o menu interativo:

```powershell
python tp01_arquivos.py
```

Execute a comparacao completa entre as versoes serial e paralela:

```powershell
python tp01_arquivos.py --acao benchmark --municipio MACAPA
```

Tambem e possivel informar outra pasta de base com o parametro `--base-dir`.

### TP02

Entre na pasta do trabalho:

```powershell
cd "TP02 - Imagens"
```

Execute o script principal:

```powershell
python 24101911.py
```

O programa abre janelas para selecionar a imagem de entrada e escolher o local de salvamento da imagem convertida.

## Arquivos ignorados

O repositorio ignora arquivos locais que nao devem ser enviados ao GitHub, incluindo:

- bases CSV;
- arquivos TXT, PDFs e saidas geradas;
- pastas de cache do Python;
- pastas de IDE;
- imagens usadas em testes ou geradas pelo TP02;
- pastas locais como `Base de Dados/`, `saida/`, `saida_serial/`, `saida_paralela/` e `saida_imagens/`.

## Observacoes

- Para executar o TP01, mantenha os arquivos CSV da base dentro de `TP01_Manipulando_Arquivos/Base de Dados/` ou informe outro caminho com `--base-dir`.
- Para executar o TP02, use uma imagem local nos formatos aceitos pelo programa, como PNG, JPG, JPEG, BMP ou GIF.
