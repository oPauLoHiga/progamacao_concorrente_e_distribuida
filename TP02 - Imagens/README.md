# TP02 - Conversao de Imagens para Preto e Branco com Threads

Projeto da disciplina de Programacao Concorrente e Distribuida para converter
imagens coloridas em preto e branco usando processamento sequencial e
processamento com threads.

O programa preserva a estrutura base do enunciado, com selecao de imagem por
janela, conversao manual pixel a pixel, salvamento do resultado e exibicao do
caminho final. A implementacao tambem mede o tempo de execucao das duas
abordagens e valida se a saida gerada com threads e igual a saida sequencial.

## Funcionalidades

- seleciona uma imagem local usando `tkinter.filedialog`;
- converte a imagem para RGB antes do processamento;
- calcula a luminancia com a formula `0.299 * R + 0.587 * G + 0.114 * B`;
- gera uma versao sequencial para comparacao;
- divide a imagem em faixas horizontais para processamento com threads;
- aguarda todas as threads terminarem com `join()`;
- combina as faixas processadas em uma unica imagem final;
- salva a imagem convertida na pasta `saida_imagens`;
- mostra o caminho completo do arquivo salvo;
- compara os tempos com e sem threads.

## Estrutura do projeto

```text
TP02 - Imagens/
├── 24101911.py
├── README.md
├── requirements.txt
├── .gitignore
└── saida_imagens/        # gerada localmente e ignorada pelo Git
```

## Requisitos

- Python 3.10 ou superior;
- Pillow.

Instale a dependencia com:

```bash
pip install -r requirements.txt
```

## Como executar

Execute o script principal:

```bash
python 24101911.py
```

Fluxo do programa:

1. abre uma janela para selecionar a imagem;
2. converte a imagem para RGB;
3. executa a conversao sem threads;
4. executa a conversao com threads;
5. compara os resultados;
6. abre uma janela para escolher o local de salvamento;
7. salva a imagem em preto e branco;
8. exibe o caminho final e os tempos de execucao.

## Organizacao do codigo

| Funcao | Responsabilidade |
|---|---|
| `calcular_luminancia(...)` | Calcula o tom de cinza de um pixel pela formula do enunciado. |
| `converter_sem_threads(...)` | Percorre todos os pixels sequencialmente e mede o tempo de execucao. |
| `converter_faixa(...)` | Processa uma faixa horizontal da imagem dentro de uma thread. |
| `converter_com_threads(...)` | Cria, inicia e sincroniza as threads, depois combina as faixas. |
| `mostrar_tempos(...)` | Exibe a comparacao de desempenho no terminal. |
| `converter_preto_branco()` | Controla o fluxo principal de selecao, conversao, salvamento e validacao. |
| `main()` | Ponto de entrada do programa. |

## Atendimento aos requisitos

| Requisito | Situacao | Implementacao |
|---|---|---|
| Usar `threading` | Atendido | `threading.Thread` em `converter_com_threads(...)`. |
| Dividir a imagem em partes | Atendido | divisao em faixas horizontais. |
| Esperar todas as threads | Atendido | uso de `join()` antes de montar a imagem final. |
| Evitar conflito entre threads | Atendido | cada thread escreve em sua propria imagem parcial. |
| Combinar os resultados | Atendido | uso de `paste(...)` para montar a imagem final. |
| Manter estrutura modular | Atendido | funcoes separadas por responsabilidade. |
| Salvar no formato escolhido | Atendido | `asksaveasfilename(...)` com opcoes de extensao. |
| Exibir caminho salvo | Atendido | mensagens no terminal apos o salvamento. |
| Medir desempenho | Atendido | `time.perf_counter()` nas duas conversoes. |
| Validar a conversao | Atendido | comparacao byte a byte entre a versao sequencial e a versao com threads. |

## Testes realizados

| Imagem | Dimensoes | Tempo sem threads | Tempo com threads | Resultado |
|---|---:|---:|---:|---|
| Captura de tela 2026-03-30 002957.png | 1885x1062 | 2.4202s | 2.4283s | correto |
| ChatGPT Image 9 de mai. de 2026, 00_38_24.png | 1086x1448 | 1.9318s | 1.9334s | correto |
| VacasMagrasPerfil.png | 1024x1024 | 1.2961s | 1.3086s | correto |

Em todos os testes, a imagem gerada com threads foi comparada byte a byte com a
imagem gerada pela versao sequencial. As duas abordagens produziram o mesmo
resultado.

## Observacoes sobre o desempenho

Como o processamento percorre pixels individualmente em Python, o uso de
threads pode nao reduzir o tempo de execucao em relacao a versao sequencial.
Mesmo assim, a implementacao atende ao objetivo do trabalho: dividir a imagem,
processar as partes de forma concorrente, sincronizar as threads e reconstruir a
imagem final corretamente.

## Arquivos ignorados

A pasta `saida_imagens/` e arquivos de imagem sao ignorados pelo Git para evitar
que resultados locais sejam enviados ao GitHub. O PDF do enunciado tambem fica
fora do versionamento por causa do `.gitignore` do repositorio raiz.
