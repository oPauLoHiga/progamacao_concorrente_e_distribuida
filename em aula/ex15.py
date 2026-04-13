import time
import pandas as pd
import os

inicio = time.time()

Arquivo = "Painel_26.csv"
Pasta = "saida_serial"
os.makedirs(Pasta, exist_ok=True)
df = pd.read_csv(Arquivo, sep=",", encoding="utf-8")

for tribunal, grupo in df.groupby("sigla_tribunal"):
    caminho = os.path.join(Pasta,f"{tribunal}.csv")
    grupo.to_csv(caminho, sep=",", encoding="utf-8")
    print(f"Arquivo gerado: {caminho}")

fim = time.time()

print(f"Tempo: {fim - inicio:.4f} segundos")