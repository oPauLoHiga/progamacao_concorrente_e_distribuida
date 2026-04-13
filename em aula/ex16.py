import time
import pandas as pd
import os
import threading

inicio = time.time()

Arquivo = "Painel_26.csv"
Pasta = "saida_paralela"
os.makedirs(Pasta, exist_ok=True)
df = pd.read_csv(Arquivo, sep=",", encoding="utf-8")

def gravar_csv(tribunal, grupo):
    caminho = os.path.join(Pasta, f"{tribunal}.csv")
    grupo.to_csv(caminho, sep=",", encoding="utf-8")
    print(f"Arquivo gerado: {caminho}")

threads = []
for tribunal, grupo in df.groupby("sigla_tribunal"):
    t = threading.Thread(target=gravar_csv, args=(tribunal, grupo))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

fim = time.time()

print(f"Tempo: {fim - inicio:.4f} segundos")