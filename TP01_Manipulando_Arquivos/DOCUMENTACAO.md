# TP01 - Manipulando arquivos CSV

## 1. Sobre o trabalho

Este trabalho foi desenvolvido para a disciplina de Programacao Concorrente e
Distribuida. A ideia principal foi ler varios arquivos CSV da base da Justica
Eleitoral, juntar e resumir esses dados, e comparar uma solucao serial com uma
solucao paralela.

## 2. O que foi implementado

O enunciado pediu quatro funcionalidades. No codigo, cada uma delas tem uma
versao serial e uma versao paralela:

1. concatenar todos os arquivos CSV da base;
2. gerar um resumo por `municipio_oj`;
3. gerar um ranking com os 10 tribunais de maior `Meta1`;
4. filtrar os registros de um municipio informado pelo usuario e gravar em
   arquivo `.txt`.

Tambem foi incluida uma opcao de benchmark para medir os tempos das versoes
seriais e paralelas e calcular o speedup.

## 3. Arquivos do projeto

Os arquivos principais para entrega sao:

- `tp01_arquivos.py`: codigo-fonte do trabalho;
- `DOCUMENTACAO.md`: esta documentacao.

Tambem existe um `.gitignore`.
Os arquivos CSV da base, arquivos de saida e o PDF do
enunciado nao foram enviados como parte do codigo.

## 4. Base de dados

A base usada nos testes ficou na pasta:

```text
TP01_Manipulando_Arquivos\Base de Dados
```

Durante a verificacao, a base tinha:

- 27 arquivos CSV;
- 205.122 linhas de dados;
- o mesmo cabecalho em todos os arquivos.

O codigo procura automaticamente a pasta `Base de Dados` dentro do projeto. Se a
base estiver em outro lugar, basta passar o caminho usando `--base-dir`.

## 5. Como o codigo foi organizado

O arquivo `tp01_arquivos.py` foi separado nessas partes:

- funcoes auxiliares para abrir arquivos, converter numeros e normalizar texto;
- funcao de calculo das metas;
- funcoes da concatenacao;
- funcoes do resumo por municipio;
- funcoes do ranking por tribunal;
- funcoes do filtro por municipio;
- funcoes para medir tempo e executar o benchmark;
- menu interativo e argumentos de linha de comando.

Essa divisao foi feita para deixar mais  bem estruturado com facil acesso para encontrar cada parte do trabalho
e para separar a versao serial da versao paralela.

## 6. Funcionalidades

### 6.1 Concatenacao dos arquivos

Na versao serial, o programa abre um CSV por vez. Ele grava o cabecalho apenas
do primeiro arquivo e depois copia as linhas dos demais arquivos sem repetir o
cabecalho.

Na versao paralela, a leitura dos arquivos e feita em paralelo por arquivo. No
final, o programa grava tudo em um unico CSV.

Arquivos gerados:

- `base_concatenada_serial.csv`;
- `base_concatenada_paralelo.csv`.

### 6.2 Resumo por municipio

Nesta funcionalidade, o programa agrupa as linhas pela coluna `municipio_oj`.
Para cada municipio, ele soma os campos necessarios e calcula:

- total de `julgados_2026`;
- `Meta1`;
- `Meta2A`;
- `Meta2Ant`;
- `Meta4A`;
- `Meta4B`.

Arquivos gerados:

- `resumo_municipios_serial.csv`;
- `resumo_municipios_paralelo.csv`.

### 6.3 Ranking dos tribunais

O ranking agrupa os registros por `sigla_tribunal`, calcula as metas de cada
tribunal e ordena pelo maior valor de `Meta1`.

O arquivo final mostra os 10 tribunais com maior `Meta1`.

Arquivos gerados:

- `ranking_tribunais_serial.csv`;
- `ranking_tribunais_paralelo.csv`.

### 6.4 Filtro por municipio

O usuario informa um municipio, por exemplo `MACAPA`, e o programa grava todas
as linhas em que `municipio_oj` corresponde a esse municipio.

O enunciado primeiro fala em CSV, mas depois corrige para TXT. Por isso, esta
funcionalidade gera arquivo `.txt`.

No benchmark, os nomes ficam assim:

- `MACAPA_serial.txt`;
- `MACAPA_paralelo.txt`.

Quando a funcionalidade e executada sozinha, o arquivo gerado usa o nome do
municipio, por exemplo `MACAPA.txt`.

## 7. Formulas usadas

otodas as subtracoes deveriam ser trocadas por adicoes. 
Por isso, os denominadores abaixo usam soma.

### Meta1

```text
(sum(julgados_2026) / (sum(casos_novos_2026) + sum(dessobrestados_2026) + sum(suspensos_2026)) ) * 100
```

### Meta2A

```text
( sum(julgm2_a) / (sum(distm2_a) + sum(suspm2_a)) ) * (1000 / 7)
```

### Meta2Ant

```text
( sum(julgm2_ant) / (sum(distm2_ant) + sum(suspm2_ant) + sum(desom2_ant)) ) * 100
```

### Meta4A

```text
( sum(julgm4_a) / (sum(distm4_a) + sum(suspm4_a)) ) * 100
```

### Meta4B

```text
( sum(julgm4_b) / (sum(distm4_b) + sum(suspm4_b)) ) * 100
```

Quando algum denominador fica igual a zero, o programa retorna `0.0000` para
evitar erro de divisao por zero.

## 8. Execucao serial e paralela

Na execucao serial, os arquivos sao processados um depois do outro. Essa versao
e mais simples e tem menos sobrecarga.

Na execucao paralela, o trabalho e dividido por arquivo. Cada worker processa
uma parte da base e, depois, os resultados parciais sao reunidos.

Na versao paralela foi usado `ThreadPoolExecutor`, dividindo o trabalho entre
os arquivos da base.

## 9. Como executar

Abra o terminal na pasta do trabalho:

```powershell
cd TP01_Manipulando_Arquivos
```

Para abrir o menu:

```powershell
python tp01_arquivos.py
```

Para executar todas as funcionalidades e comparar os tempos:

```powershell
python tp01_arquivos.py --acao benchmark --municipio MACAPA
```

Alguns exemplos de execucao individual:

```powershell
python tp01_arquivos.py --acao concatenar --modo ambos
python tp01_arquivos.py --acao resumo-municipios --modo ambos
python tp01_arquivos.py --acao ranking-tribunais --modo ambos
python tp01_arquivos.py --acao filtrar-municipio --modo ambos --municipio MACAPA
```

Tambem e possivel mudar a pasta da base ou a pasta de saida:

```powershell
python tp01_arquivos.py --acao benchmark --base-dir "C:\caminho\para\Base de Dados"
python tp01_arquivos.py --acao benchmark --output-dir "C:\temp\saida_tp01"
```

## 10. Speedup

O speedup foi calculado assim:

```text
speedup = tempo_serial / tempo_paralelo
```

Interpretacao:

- se o speedup for maior que 1, a versao paralela foi mais rapida;
- se for igual a 1, as duas ficaram praticamente iguais;
- se for menor que 1, a versao paralela foi mais lenta.

## 11. Resultado dos testes

Foi executado um benchmark completo usando a base fornecida e o municipio
`MACAPA`.

| Funcionalidade | Serial (s) | Paralelo (s) | Speedup |
|---|---:|---:|---:|
| Concatenar arquivos | 0.1959 | 0.1176 | 1.6653 |
| Resumo por municipio | 1.7297 | 2.2322 | 0.7749 |
| Ranking de tribunais | 1.6658 | 2.1175 | 0.7867 |
| Filtro por municipio | 0.6769 | 0.8299 | 0.8157 |

Os tempos podem mudar de uma execucao para outra, dependendo do computador, do
disco e da quantidade de workers.

## 12. Analise dos resultados

No texte realizado, a concatenacao ficou mais rapida na versao paralela. Isso
faz sentido porque a tarefa depende bastante de leitura de arquivos.

Nas outras funcionalidades, a versao paralela ficou mais lenta. Acredito que
isso aconteceu porque a base nao e tao grande para compensar a sobrecarga de
criar trabalho, dividir o trabalho e juntar os resultados no final.

a versao paralela  mostra como a base pode ser processada por partes independentes.

## 13. Verificacao

Na ultima verificacao:

- o codigo executou sem erro;
- a base foi encontrada automaticamente;
- foram detectados 27 arquivos CSV;
- as saidas seriais e paralelas tiveram o mesmo conteudo;
- o filtro por `MACAPA` gerou 1.145 registros mais o cabecalho.

## 14. Conclusao

Foram implementadas as quatro funcionalidades, com versoes seriais e paralelas, calculo das metas,
medicao de tempo e calculo de speedup.

A principal observacao dos testes e que paralelizar nem sempre deixa o programa
mais rapido. Para esta base, a paralelizacao ajudou na concatenacao, mas nao no
resumo, ranking e filtro, por causa da sobrecarga da execucao paralela.