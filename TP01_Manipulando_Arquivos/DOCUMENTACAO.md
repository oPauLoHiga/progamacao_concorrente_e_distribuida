# TP01 - Manipulando arquivos CSV

## 1. Objetivo

Este codigo foi desenvolvido para a disciplina de Programacao Concorrente e
Distribuida.

A proposta foi trabalhar com os arquivos CSV da base de dados, implementar funcionalidades
e comparar uma versao serial com uma versao paralela em cada caso.

O codigo foi feito com o uso da biblioteca `pandas`,
que deixou a leitura, a concatenacao, os agrupamentos e a gravacao dos arquivos
mais praticos.

## 2. Funcionalidades implementadas

Foram implementadas as seguintes funcionalidades:

1. concatenar todos os arquivos CSV da base em um unico arquivo;
2. gerar um resumo por `municipio_oj` com `julgados_2026`, `Meta1`, `Meta2A`,
   `Meta2Ant`, `Meta4A` e `Meta4B`;
3. gerar um resumo com os 10 tribunais de maior `Meta1`, em ordem decrescente;
4. filtrar a partir de um municipio informado pelo usuario e gerar um
   arquivo CSV somente com as ocorrencias desse municipio.

Para cada funcionalidade existe uma versao serial e uma versao paralela.

O programa tambem possui um menu interativo.

## 3. Arquivos da entrega

Os arquivos principais da entrega sao:

- `tp01_arquivos.py`
- `DOCUMENTACAO.md`

O `.gitignore` foi adcionado para evitar o vasamento de dados,
base de dados, arquivos de saida.

## 4. Estrutura do codigo

As funcoes principais sao:

- `concatenar_arquivos_serial`
- `concatenar_arquivos_paralelo`
- `gerar_resumo_municipios_serial`
- `gerar_resumo_municipios_paralelo`
- `gerar_ranking_tribunais_serial`
- `gerar_ranking_tribunais_paralelo`
- `filtrar_municipio_serial`
- `filtrar_municipio_paralelo`

As outras funcoes do arquivo servem como apoio para:

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

Tambem e possivel informar outra pasta na `--base-dir`.

## 6. Arquivos gerados

Dependendo da execucao, o programa pode gerar:

- `base_concatenada_serial.csv`
- `base_concatenada_paralelo.csv`
- `resumo_municipios_serial.csv`
- `resumo_municipios_paralelo.csv`
- `ranking_tribunais_serial.csv`
- `ranking_tribunais_paralelo.csv`
- `NOME_DO_MUNICIPIO_serial.csv`
- `NOME_DO_MUNICIPIO_paralelo.csv`
- `filtros_municipios_serial`
- `filtros_municipios_paralelo`
- `relatorio.csv`

## 7. Formulas usadas

Os calculos seguem as formulas.

### Meta1

```text
                        sum(julgados_2026)
------------------------------------------------------------- * 100
sum(casos_novos_2026) + sum(dessobrestados_2026) - sum(suspensos_2026)
```

### Meta2A

```text
            sum(julgm2_a)
------------------------------------ * (1000 / 7)
       sum(distm2_a) - sum(suspm2_a)
```

### Meta2Ant

```text
                sum(julgm2_ant)
-------------------------------------------------- * 100
sum(distm2_ant) - sum(suspm2_ant) - sum(desom2_ant)
```

### Meta4A

```text
        sum(julgm4_a)
------------------------------------ * 100
sum(distm4_a) - sum(suspm4_a)
```

### Meta4B

```text
        sum(julgm4_b)
------------------------------------ * 100
sum(distm4_b) - sum(suspm4_b)
```

Quando o denominador fica zero, o programa retorna `0.0`.

## 8. Como executar

Antes de executar, e necessario ter as bibliotecas instaladas:

Depois disso, abra o terminal na pasta do trabalho:

```powershell
cd TP01_Manipulando_Arquivos
```

Para inicar o menu interativo(main):

```powershell
python tp01_arquivos.py
```

No menu, todas as opcoes executam automaticamente a versao serial e a versao paralela
da funcionalidade escolhida, exibindo tambem o speedup.

- concatenar 
- resumo 
- ranking 
- filtrar 
- relatorio


Se o municipio nao for informado no filtro, o programa pede esse valor no
terminal. Concatenar,resumo,ranking e relatorio não tem entrada, porque usa todos os municipios da base.

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

Na validacao final do programa, usando o relatorio completo com todos os
municipios da base, os tempos obtidos foram:

| Funcionalidade | Serial (s) | Paralelo (s) | Speedup |
|---|---:|---:|---:|
| Concatenar arquivos | 1.7117 | 1.5817 | 1.0822 |
| Resumo por municipio | 3.9882 | 3.8965 | 1.0235 |
| Resumo dos 10 tribunais | 3.9647 | 3.9152 | 1.0126 |
| Filtro por municipio | 10.0073 | 10.2656 | 0.9748 |

As saidas seriais e paralelas tiveram o mesmo conteudo, mudando apenas o tempo de execucao. 

## 11. Pros e Contras

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
- com `pandas`, o codigo continua "simples" mesmo com a comparacao entre os modos.

Contras:
- tem mais sobrecarga;
- em bases menores pode ficar mais lenta;
- exige mais cuidado para juntar os resultados parciais.

## 12. Observacao sobre a biblioteca usada

O uso do `pandas` deixou o codigo mais facil.

Por outro lado, ele adiciona uma dependencia externa ao projeto. Entao, para
executar o trabalho em outro computador, e necessario instalar essa biblioteca
antes.

## 13. Conclusao

Na validacao final, a versao paralela ficou melhor em
concatenacao, resumo por municipio e resumo dos 10 tribunais. 

No teste do filtro por municipio, a versao serial ficou ligeiramente melhor.