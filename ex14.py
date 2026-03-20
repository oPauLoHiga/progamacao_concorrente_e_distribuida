import time
from datetime import datetime

inicio = time.time()

Soma = 0

for i in range(10000000):
    x = 2 * i
    Soma += x
fim = time.time()

print(f"Inicio: {datetime.fromtimestamp(inicio)}")
print(f"Fim: {datetime.fromtimestamp(fim)}")
print(f"Tempo: {fim - inicio:.4f} segundos")