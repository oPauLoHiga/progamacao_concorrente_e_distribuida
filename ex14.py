import time

inicio = time.time()

Soma = 0

for i in range(10000000):
    x = 2 * i
    Soma += x
fim = time.time()
print(f"Tempo: {fim - inicio:.4f} segundos")