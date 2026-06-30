import random
import threading
import time


CAPACIDADE_FILA_LOCAL = 4
ARQUIVO_LOG = "tp04_impressao_3d.log"

PARTICIPANTES = [
    "Professor",
    "Pos-graduacao 1",
    "Pos-graduacao 2",
    "Graduacao 1",
    "Graduacao 2",
]

PRIORIDADES = {
    "professor": 0,
    "pos-graduacao": 1,
    "graduacao": 2,
}

fila_local = []
servidor_central = []

mutex = threading.Lock()
mutex_log = threading.Lock()
sem_reabastecer = threading.Semaphore(0)
sem_fila_pronta = threading.Semaphore(0)

reabastecendo = False
participantes_esperando = 0
encerrar_servidor = False

total_impressoes = 0
total_reabastecimentos = 0
impressoes_por_participante = {}


def escrever_log(texto):
    horario = time.strftime("%H:%M:%S")

    with mutex_log:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"[{horario}] {texto}\n")


def carregar_servidor_central():
    trabalhos = [
        ("ARQ-001", "Prof. Ana", "professor"),
        ("ARQ-002", "Aluno Carlos", "graduacao"),
        ("ARQ-003", "Mestranda Bia", "pos-graduacao"),
        ("ARQ-004", "Aluno Davi", "graduacao"),
        ("ARQ-005", "Prof. Bruno", "professor"),
        ("ARQ-006", "Doutoranda Eva", "pos-graduacao"),
        ("ARQ-007", "Aluno Felipe", "graduacao"),
        ("ARQ-008", "Prof. Carla", "professor"),
        ("ARQ-009", "Aluno Gabi", "graduacao"),
        ("ARQ-010", "Mestrando Hugo", "pos-graduacao"),
        ("ARQ-011", "Aluno Igor", "graduacao"),
        ("ARQ-012", "Prof. Denise", "professor"),
        ("ARQ-013", "Doutorando Joao", "pos-graduacao"),
        ("ARQ-014", "Aluna Lara", "graduacao"),
        ("ARQ-015", "Aluno Mateus", "graduacao"),
    ]

    for trabalho in trabalhos:
        servidor_central.append(trabalho)


def retirar_mais_prioritario(fila):
    indice_melhor = 0

    for indice in range(1, len(fila)):
        tipo_atual = fila[indice][2]
        tipo_melhor = fila[indice_melhor][2]

        if PRIORIDADES[tipo_atual] < PRIORIDADES[tipo_melhor]:
            indice_melhor = indice

    return fila.pop(indice_melhor)


def servidor():
    global reabastecendo
    global total_reabastecimentos

    while True:
        sem_reabastecer.acquire()

        with mutex:
            if encerrar_servidor:
                break

        time.sleep(0.1)
        arquivos_movidos = []

        with mutex:
            while len(fila_local) < CAPACIDADE_FILA_LOCAL and len(servidor_central) > 0:
                trabalho = retirar_mais_prioritario(servidor_central)
                fila_local.append(trabalho)
                arquivos_movidos.append(trabalho[0])

            if len(arquivos_movidos) > 0:
                total_reabastecimentos += 1

            reabastecendo = False
            acordar = participantes_esperando

        if len(arquivos_movidos) > 0:
            escrever_log("Servidor reabasteceu a fila com: " + ", ".join(arquivos_movidos))
        else:
            escrever_log("Servidor foi chamado, mas nao havia arquivos pendentes.")

        for _ in range(acordar):
            sem_fila_pronta.release()

    escrever_log("Servidor central encerrado.")


def pegar_arquivo(nome_participante):
    global reabastecendo
    global participantes_esperando
    global encerrar_servidor

    while True:
        chamar_servidor = False

        with mutex:
            if len(fila_local) > 0:
                return retirar_mais_prioritario(fila_local)

            if len(servidor_central) == 0 and not reabastecendo:
                encerrar_servidor = True
                sem_reabastecer.release()
                return None

            participantes_esperando += 1

            if not reabastecendo:
                reabastecendo = True
                chamar_servidor = True

        if chamar_servidor:
            escrever_log(nome_participante + " encontrou a fila vazia e chamou o servidor.")
            sem_reabastecer.release()
        else:
            escrever_log(nome_participante + " aguardou a fila ser reabastecida.")

        sem_fila_pronta.acquire()

        with mutex:
            participantes_esperando -= 1


def participante(nome):
    global total_impressoes

    impressoes_por_participante[nome] = 0

    while True:
        arquivo = pegar_arquivo(nome)

        if arquivo is None:
            escrever_log(nome + " encerrou porque nao existem mais arquivos.")
            break

        codigo, dono, tipo = arquivo

        escrever_log(f"{nome} iniciou a impressao de {codigo} ({tipo}, {dono}).")
        time.sleep(random.uniform(0.05, 0.2))
        escrever_log(nome + " terminou a impressao de " + codigo + ".")

        with mutex:
            total_impressoes += 1
            impressoes_por_participante[nome] += 1


def mostrar_resumo():
    melhor_participante = max(impressoes_por_participante, key=impressoes_por_participante.get)
    maior_quantidade = impressoes_por_participante[melhor_participante]

    print("Resumo da simulacao")
    print(f"Total de impressoes realizadas: {total_impressoes}")
    print(f"Total de reabastecimentos executados: {total_reabastecimentos}")
    print(f"Participante que mais imprimiu: {melhor_participante} ({maior_quantidade} trabalho(s))")
    print(f"Arquivo de log gerado: {ARQUIVO_LOG}")


def main():
    random.seed(7)

    with open(ARQUIVO_LOG, "w", encoding="utf-8") as arquivo:
        arquivo.write("Log do laboratorio de impressao 3D\n")

    carregar_servidor_central()
    escrever_log("Servidor central recebeu os arquivos pendentes.")

    thread_servidor = threading.Thread(target=servidor)
    threads_participantes = []

    thread_servidor.start()

    for nome in PARTICIPANTES:
        t = threading.Thread(target=participante, args=(nome,))
        threads_participantes.append(t)
        t.start()

    for t in threads_participantes:
        t.join()

    thread_servidor.join()
    mostrar_resumo()


if __name__ == "__main__":
    main()
