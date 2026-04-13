# TP01 - Manipulando arquivos CSV

## 1. Identificacao do trabalho

Disciplina: Programacao Concorrente e Distribuida

Tema: manipulacao de arquivos CSV com versoes seriais e paralelas

Linguagem: Python

Sistema operacional alvo: Windows

## 2. Objetivo

O objetivo deste projeto e implementar um sistema capaz de ler, processar e
gerar arquivos a partir da base CSV da Justica Eleitoral disponibilizada para o
trabalho pratico.

O sistema atende as quatro funcionalidades solicitadas no enunciado:

1. concatenar todos os arquivos CSV da base em um unico arquivo;
2. gerar um resumo por `municipio_oj`;
3. gerar um resumo com os 10 tribunais de maior `Meta1`;
4. gerar um arquivo `.txt` com todas as ocorrencias de um municipio informado
   pelo usuario.

Cada funcionalidade foi implementada em duas versoes: uma serial e uma
paralela.

## 3. Arquivos do projeto

O projeto possui os seguintes arquivos principais:

- `tp01_arquivos.py`: codigo-fonte principal do sistema;
- `DOCUMENTACAO.md`: documentacao tecnica e instrucoes de execucao;
- `.gitignore`: lista de arquivos gerados que nao devem ser versionados.

Arquivos CSV, arquivos TXT gerados, caches do Python e pastas de saida nao
fazem parte da entrega do codigo-fonte.

## 4. Base de dados usada

A base usada durante o desenvolvimento possuia:

- 27 arquivos CSV;
- 205.122 registros de dados;
- um mesmo cabecalho em todos os arquivos.

No repositorio da disciplina, a base esta em:

```text
C:\Users\paulo\OneDrive\Documentos\Github_Desktop_Arquivos\progamacao_concorrente_e_distribuida\TP01_Manipulando_Arquivos\Base de Dados
```

O codigo tenta localizar automaticamente a pasta `Base de Dados` em locais
provaveis dentro do projeto. Caso seja necessario usar outro local, o caminho
pode ser substituido na execucao pelo parametro `--base-dir`.

## 5. Requisitos atendidos

O sistema foi implementado com os seguintes pontos do enunciado:

- uso da linguagem Python;
- execucao em ambiente Windows;
- leitura de multiplos arquivos CSV;
- geracao de arquivos de saida;
- uma funcao para cada funcionalidade principal;
- versao serial e versao paralela para cada funcionalidade;
- medicao de tempo de execucao;
- calculo de speedup;
- comparacao entre execucao serial e paralela;
- filtro de municipio gerando arquivo `.txt`, conforme correcao feita no
  enunciado.

## 6. Funcionamento das funcionalidades

### 6.1 Concatenar arquivos

A funcao serial le os arquivos CSV um por vez, grava o cabecalho do primeiro
arquivo e depois copia todas as linhas de dados dos demais arquivos sem repetir
cabecalhos.

A funcao paralela divide a leitura dos arquivos entre workers e depois escreve
o resultado final mantendo a ordem dos arquivos da base.

Saidas principais:

- `base_concatenada_serial.csv`;
- `base_concatenada_paralelo.csv`.

### 6.2 Resumo por municipio

O programa agrupa os registros pela coluna `municipio_oj`. Para cada municipio,
soma os campos numericos necessarios e calcula:

- total de `julgados_2026`;
- `Meta1`;
- `Meta2A`;
- `Meta2Ant`;
- `Meta4A`;
- `Meta4B`.

Saidas principais:

- `resumo_municipios_serial.csv`;
- `resumo_municipios_paralelo.csv`.

### 6.3 Ranking dos tribunais

O programa agrupa os registros pela coluna `sigla_tribunal`, calcula as metas
para cada tribunal e ordena o resultado em ordem decrescente de `Meta1`.

O arquivo final contem somente os 10 tribunais com os maiores valores de
`Meta1`.

Saidas principais:

- `ranking_tribunais_serial.csv`;
- `ranking_tribunais_paralelo.csv`.

### 6.4 Filtro por municipio

O usuario informa um municipio, por exemplo `MACAPA`. O programa procura todas
as linhas em que `municipio_oj` corresponde ao municipio informado e grava o
resultado em arquivo `.txt`.

A comparacao do municipio ignora diferencas de maiusculas, minusculas e acentos,
mas as linhas gravadas mantem o conteudo original da base.

Saida principal:

- `MACAPA.txt`, ou outro nome de municipio informado.

No benchmark completo, os nomes recebem sufixo `_serial` e `_paralelo` para
facilitar a comparacao entre as duas versoes.

## 7. Formulas usadas

O enunciado determina que todas as subtracoes das formulas sejam trocadas por
adicoes. Por isso, os denominadores foram implementados usando soma.

### 7.1 Meta1

```text
sum(julgados_2026)
------------------------------------------------------------- * 100
sum(casos_novos_2026) + sum(dessobrestados_2026) + sum(suspensos_2026)
```

### 7.2 Meta2A

```text
sum(julgm2_a)
------------------------------------ * (1000 / 7)
sum(distm2_a) + sum(suspm2_a)
```

### 7.3 Meta2Ant

```text
sum(julgm2_ant)
-------------------------------------------------- * 100
sum(distm2_ant) + sum(suspm2_ant) + sum(desom2_ant)
```

### 7.4 Meta4A

```text
sum(julgm4_a)
------------------------------------ * 100
sum(distm4_a) + sum(suspm4_a)
```

### 7.5 Meta4B

```text
sum(julgm4_b)
------------------------------------ * 100
sum(distm4_b) + sum(suspm4_b)
```

Quando o denominador e zero, o sistema retorna `0.0000` para evitar erro de
divisao por zero.

## 8. Estrategia serial

Na versao serial, os arquivos sao processados em sequencia. O programa termina
o processamento de um arquivo antes de iniciar o proximo.

Vantagens:

- implementacao simples;
- menor sobrecarga de controle;
- comportamento mais previsivel;
- bom desempenho em bases pequenas ou medias.

Desvantagens:

- nao aproveita multiplos nucleos de processamento;
- pode ser menos eficiente em bases muito grandes.

## 9. Estrategia paralela

Na versao paralela, o problema e dividido por arquivo. Cada worker processa um
CSV e gera um resultado parcial. Ao final, os resultados parciais sao unidos.

Para tarefas de agregacao e filtro, o codigo tenta usar `ProcessPoolExecutor`,
que executa trabalho em processos separados. Se o Windows bloquear a criacao de
processos no ambiente de execucao, o programa usa `ThreadPoolExecutor` como
alternativa para manter a funcionalidade paralela disponivel.

Vantagens:

- divide o processamento entre varios workers;
- pode reduzir o tempo em bases maiores;
- aproveita a independencia natural entre os arquivos CSV da base.

Desvantagens:

- possui sobrecarga de criacao e coordenacao de workers;
- pode ficar mais lenta que a serial quando a base nao e grande o bastante;
- depende das permissoes do ambiente para usar multiprocessamento.

## 10. Como executar

Abra o terminal na pasta do projeto:

```powershell
cd "C:\Users\paulo\OneDrive\Documentos\Estudos\codGPT\TP01_Manipulando_Arquivos"
```

Executar o menu interativo:

```powershell
python tp01_arquivos.py
```

Executar o benchmark completo:

```powershell
python tp01_arquivos.py --acao benchmark --municipio MACAPA
```

Concatenar arquivos:

```powershell
python tp01_arquivos.py --acao concatenar --modo serial
python tp01_arquivos.py --acao concatenar --modo paralelo
python tp01_arquivos.py --acao concatenar --modo ambos
```

Gerar resumo por municipio:

```powershell
python tp01_arquivos.py --acao resumo-municipios --modo ambos
```

Gerar ranking dos tribunais:

```powershell
python tp01_arquivos.py --acao ranking-tribunais --modo ambos
```

Filtrar por municipio:

```powershell
python tp01_arquivos.py --acao filtrar-municipio --modo ambos --municipio MACAPA
```

Usar outra pasta de base:

```powershell
python tp01_arquivos.py --acao benchmark --base-dir "C:\caminho\para\Base de Dados"
```

Usar outra pasta de saida:

```powershell
python tp01_arquivos.py --acao benchmark --output-dir "C:\temp\saida_tp01"
```

Definir quantidade de workers:

```powershell
python tp01_arquivos.py --acao benchmark --workers 4
```

## 11. Arquivos gerados

Por padrao, os arquivos sao gravados na pasta `saida`.

Principais saidas:

- `base_concatenada_serial.csv`;
- `base_concatenada_paralelo.csv`;
- `resumo_municipios_serial.csv`;
- `resumo_municipios_paralelo.csv`;
- `ranking_tribunais_serial.csv`;
- `ranking_tribunais_paralelo.csv`;
- `MUNICIPIO.txt`;
- `tempos_execucao.csv`, quando o benchmark completo e executado.

Esses arquivos sao produtos da execucao e nao devem ser enviados como
codigo-fonte.

## 12. Calculo de speedup

O speedup foi calculado pela formula:

```text
speedup = tempo_serial / tempo_paralelo
```

Interpretacao:

- `speedup > 1`: a versao paralela foi mais rapida;
- `speedup = 1`: as duas versoes tiveram desempenho equivalente;
- `speedup < 1`: a versao paralela foi mais lenta.

## 13. Medicao realizada

Foi executado um benchmark completo com a base informada e municipio `MACAPA`.
Os tempos obtidos foram:

| Funcionalidade | Serial (s) | Paralelo (s) | Speedup |
|---|---:|---:|---:|
| Concatenar arquivos | 0.1054 | 0.0899 | 1.1725 |
| Resumo por municipio | 1.5902 | 1.9669 | 0.8085 |
| Ranking de tribunais | 1.5685 | 1.9458 | 0.8061 |
| Filtro por municipio | 0.6617 | 0.8129 | 0.8139 |

Os tempos podem variar de acordo com o computador, disco, quantidade de workers
e permissoes do sistema operacional.

## 14. Analise dos resultados

A concatenacao apresentou speedup maior que 1, indicando ganho na versao
paralela. Esse ganho e explicado pelo fato de a tarefa ser fortemente baseada em
leitura de arquivos, permitindo sobrepor parte das operacoes de entrada.

Nas funcionalidades de resumo, ranking e filtro, a versao paralela ficou mais
lenta na medicao realizada. Isso ocorreu porque a base tem cerca de 205 mil
linhas, e a sobrecarga de criar, coordenar e combinar os resultados dos workers
foi maior que o ganho obtido com a divisao do processamento.

Mesmo assim, a implementacao paralela e relevante porque a base e naturalmente
dividida em arquivos independentes. Em cenarios com arquivos maiores ou mais
registros, a tendencia e que a paralelizacao tenha mais oportunidade de reduzir
o tempo total de execucao.

## 15. Conclusao

O projeto atende aos requisitos do trabalho, pois implementa as quatro
funcionalidades solicitadas em versoes serial e paralela, gera os arquivos de
saida definidos no enunciado, calcula as metas com as formulas adaptadas e mede
os tempos de execucao para comparacao.

Durante a verificacao, os arquivos gerados pelas versoes serial e paralela
tiveram o mesmo conteudo, indicando que a paralelizacao nao alterou os
resultados, apenas a forma de processamento.
