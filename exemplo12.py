import threading
import time
import random

# memoria compartilhada
MemoriaCompartilhada = {
    "contador" : 0,
    "mensagem" : []
}

# mecanismo de sincronização
lock = threading.Lock()

# Para simular uma tarefa
def tarefa(nome_thread, quant_execucoes):
    for i in range(quant_execucoes):
        time.sleep(random.uniform(0.1,0.5))

        valor_antigo = MemoriaCompartilhada["contador"]
        novo_valor = valor_antigo + 1
        MemoriaCompartilhada["contador"] = novo_valor

        mensagem = (
            f"{nome_thread} acessou a memoria compartilhada"
            f"e alterou o contador de {valor_antigo} para {novo_valor}"
        )

        MemoriaCompartilhada["mensagem"].append(mensagem)
        print(mensagem)

def main():
    threads1 = threading.Thread(target=tarefa, args=("texte", 5))
    threads2 = threading.Thread(target=tarefa, args=("texte2", 5))

    threads1.start()
    threads2.start()

    threads1.join()
    threads2.join()

    print("\nPrograma finalizado com sucesso!")
    print(f"valor final: {MemoriaCompartilhada['contador']}")
    print("\nHistorico de acesso")
    for msg in MemoriaCompartilhada['mensagem']:print(" - ", msg)
if __name__ == "__main__":

    main()
