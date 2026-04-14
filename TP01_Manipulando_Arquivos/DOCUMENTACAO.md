# TP01 - Manipulando arquivos CSV

## 1. Objetivo

Este trabalho foi desenvolvido para a disciplina de Programacao Concorrente e
Distribuida.

A proposta foi trabalhar com os arquivos CSV da base de dados, implementar as
quatro funcionalidades pedidas no enunciado e comparar uma versao serial com
uma versao paralela em cada caso.

Nesta versao final, o codigo foi simplificado com o uso da biblioteca `pandas`,
que deixou a leitura, a concatenacao, os agrupamentos e a gravacao dos arquivos
mais diretos.

## 2. Funcionalidades implementadas

Foram implementadas as seguintes funcionalidades:

1. concatenar todos os arquivos CSV da base em um unico arquivo;
2. gerar um resumo por `municipio_oj` com `julgados_2026`, `Meta1`, `Meta2A`,
   `Meta2Ant`, `Meta4A` e `Meta4B`;
3. gerar um resumo com os 10 tribunais de maior `Meta1`, em ordem decrescente;
4. filtrar a base a partir de um municipio informado pelo usuario e gerar um
   arquivo CSV somente com as ocorrencias desse municipio.

Para cada funcionalidade existe uma versao serial e uma versao paralela.

## 3. Arquivos da entrega

Os arquivos principais da entrega sao:

- `tp01_arquivos.py`
- `DOCUMENTACAO.md`

O `.gitignore` foi mantido para evitar envio acidental da base de dados,
arquivos de saida e outros arquivos temporarios.

## 4. Estrutura do codigo

O codigo foi deixado de forma propositalmente simples.

As funcoes principais sao:

- `concatenar_arquivos_serial`
- `concatenar_arquivos_paralelo`
- `gerar_resumo_municipios_serial`
- `gerar_resumo_municipios_paralelo`
- `gerar_ranking_tribunais_serial`
- `gerar_ranking_tribunais_paralelo`
- `filtrar_municipio_serial`
- `filtrar_municipio_paralelo`

As outras funcoes do arquivo servem apenas como apoio para:

- listar os CSVs;
- ler os arquivos com `pandas`;
- converter valores numericos;
- calcular as metas;
- medir tempo de execucao;
- gerar o `relatorio.csv`.

## 5. Base de dados

O programa considera, por padrao, que a base esta dentro da pasta:

```text
TP01_Manipulando_Arquivos\Base de Dados
```

Tambem e possivel informar outra pasta com `--base-dir`.

## 6. Arquivos gerados

Dependendo da execucao, o programa pode gerar:

- `base_concatenada_serial.csv`
- `base_concatenada_paralelo.csv`
- `resumo_municipios_serial.csv`
- `resumo_municipios_paralelo.csv`
- `ranking_tribunais_serial.csv`
- `ranking_tribunais_paralelo.csv`
- `NOME_DO_MUNICIPIO.csv`
- `NOME_DO_MUNICIPIO_serial.csv`
- `NOME_DO_MUNICIPIO_paralelo.csv`
- `relatorio.csv`

Quando o filtro e executado em apenas um modo, o nome do arquivo fica no
formato `NOME_DO_MUNICIPIO.csv`.

Quando o filtro e comparado nos dois modos, os arquivos ficam separados em
`_serial.csv` e `_paralelo.csv`.

## 7. Formulas usadas

No enunciado foi considerado que as subtracoes deveriam ser trocadas por
adicoes. Por isso, os denominadores ficaram assim:

### Meta1

```text
sum(julgados_2026)
------------------------------------------------------------- * 100
sum(casos_novos_2026) + sum(dessobrestados_2026) + sum(suspensos_2026)
```

### Meta2A

```text
sum(julgm2_a)
------------------------------------ * (1000 / 7)
sum(distm2_a) + sum(suspm2_a)
```

### Meta2Ant

```text
sum(julgm2_ant)
-------------------------------------------------- * 100
sum(distm2_ant) + sum(suspm2_ant) + sum(desom2_ant)
```

### Meta4A

```text
sum(julgm4_a)
------------------------------------ * 100
sum(distm4_a) + sum(suspm4_a)
```

### Meta4B

```text
sum(julgm4_b)
------------------------------------ * 100
sum(distm4_b) + sum(suspm4_b)
```

Quando o denominador fica zero, o programa retorna `0.0000`.

## 8. Como executar

Antes de executar, e necessario ter o `pandas` instalado:

```powershell
python -m pip install pandas
```

Depois disso, abra o terminal na pasta do trabalho:

```powershell
cd TP01_Manipulando_Arquivos
```

Para gerar todos os arquivos e o `relatorio.csv`:

```powershell
python tp01_arquivos.py --acao relatorio --municipio NOME_DO_MUNICIPIO
```

Para executar apenas uma funcionalidade:

```powershell
python tp01_arquivos.py --acao concatenar --modo ambos
python tp01_arquivos.py --acao resumo --modo ambos
python tp01_arquivos.py --acao ranking --modo ambos
python tp01_arquivos.py --acao filtrar --modo serial --municipio NOME_DO_MUNICIPIO
```

Tambem e possivel mudar a pasta da base e a pasta de saida:

```powershell
python tp01_arquivos.py --acao relatorio --municipio NOME_DO_MUNICIPIO --base-dir "C:\caminho\para\Base de Dados"
python tp01_arquivos.py --acao relatorio --municipio NOME_DO_MUNICIPIO --output-dir "C:\temp\saida_tp01"
```

Se o municipio nao for informado no filtro ou no relatorio, o programa pede esse
valor no terminal.

## 9. Relatorio de tempos

O arquivo `relatorio.csv` guarda, para cada funcionalidade:

- tempo serial;
- tempo paralelo;
- speedup.

O speedup foi calculado assim:

```text
speedup = tempo_serial / tempo_paralelo
```

Interpretacao:

- speedup maior que 1: paralelo mais rapido;
- speedup igual a 1: tempos muito proximos;
- speedup menor que 1: paralelo mais lento.

## 10. Resultado da execucao de teste

Na validacao final do programa, os tempos obtidos foram:

| Funcionalidade | Serial (s) | Paralelo (s) | Speedup |
|---|---:|---:|---:|
| Concatenar arquivos | 1.8084 | 1.6791 | 1.0770 |
| Resumo por municipio | 4.2492 | 4.1985 | 1.0121 |
| Ranking de tribunais | 4.1493 | 4.0602 | 1.0220 |
| Filtro por municipio | 0.8958 | 0.8224 | 1.0892 |

As saidas seriais e paralelas tiveram o mesmo conteudo nas quatro
funcionalidades.

## 11. Pros e contras

### Versao serial

Pros:

- codigo mais simples;
- menor sobrecarga;
- leitura mais facil;
- depuracao mais tranquila.

Contras:

- processa um arquivo por vez;
- tende a aproveitar menos a maquina quando a carga cresce.

### Versao paralela

Pros:

- processa varios arquivos ao mesmo tempo;
- pode melhorar o tempo em cenarios com mais leitura e mais volume de dados;
- com `pandas`, o codigo continua enxuto mesmo com a comparacao entre os modos.

Contras:

- tem mais sobrecarga;
- em bases menores pode ficar mais lenta;
- exige mais cuidado para juntar os resultados parciais.

## 12. Observacao sobre a biblioteca usada

O uso do `pandas` deixou o codigo menor, mais legivel e mais facil de manter.

Por outro lado, ele adiciona uma dependencia externa ao projeto. Entao, para
executar o trabalho em outro computador, e necessario instalar essa biblioteca
antes.

## 13. Conclusao

O trabalho ficou atendendo exatamente as quatro funcionalidades pedidas, com
versao serial e versao paralela para cada uma.

Na validacao final desta versao com `pandas`, a versao paralela ficou levemente
melhor nas quatro funcionalidades. Mesmo assim, as diferencas foram pequenas em
alguns casos, o que mostra que a paralelizacao precisa ser avaliada junto com a
sobrecarga criada no processamento.
