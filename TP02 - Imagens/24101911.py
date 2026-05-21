import os
import threading
import time
from pathlib import Path
from tkinter import Tk, filedialog
from PIL import Image

PASTA_SAIDA = Path(__file__).resolve().parent / "saida_imagens"


def calcular_luminancia(r, g, b):
    return int(0.299 * r + 0.587 * g + 0.114 * b)

def converter_sem_threads(imagem):
    largura, altura = imagem.size
    imagem_preto_branco = Image.new("L", (largura, altura))

    inicio = time.perf_counter()

    for x in range(largura):
        for y in range(altura):
            r, g, b = imagem.getpixel((x, y))
            luminancia = calcular_luminancia(r, g, b)
            imagem_preto_branco.putpixel((x, y), luminancia)

    tempo = time.perf_counter() - inicio
    return imagem_preto_branco, tempo


def converter_faixa(imagem, inicio_y, fim_y, partes, indice):
    largura, _ = imagem.size
    altura_faixa = fim_y - inicio_y
    faixa_pb = Image.new("L", (largura, altura_faixa))

    for x in range(largura):
        for y in range(inicio_y, fim_y):
            r, g, b = imagem.getpixel((x, y))
            luminancia = calcular_luminancia(r, g, b)
            faixa_pb.putpixel((x, y - inicio_y), luminancia)

    partes[indice] = (inicio_y, faixa_pb)


def converter_com_threads(imagem, quantidade_threads):
    largura, altura = imagem.size
    quantidade_threads = max(1, min(quantidade_threads, altura))
    linhas_por_thread = altura // quantidade_threads
    partes = [None] * quantidade_threads
    threads = []

    inicio = time.perf_counter()

    for i in range(quantidade_threads):
        inicio_y = i * linhas_por_thread

        if i == quantidade_threads - 1:
            fim_y = altura
        else:
            fim_y = inicio_y + linhas_por_thread

        thread = threading.Thread(
            target=converter_faixa,
            args=(imagem, inicio_y, fim_y, partes, i),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    imagem_preto_branco = Image.new("L", (largura, altura))

    for inicio_y, faixa_pb in partes:
        imagem_preto_branco.paste(faixa_pb, (0, inicio_y))

    tempo = time.perf_counter() - inicio
    return imagem_preto_branco, tempo, quantidade_threads


def mostrar_tempos(tempo_sem_threads, tempo_com_threads, quantidade_threads):
    print("\nComparacao de desempenho:")
    print(f"Tempo sem threads: {tempo_sem_threads:.4f} segundos")
    print(f"Tempo com {quantidade_threads} thread(s): {tempo_com_threads:.4f} segundos")


def converter_preto_branco():
    try:
        root = Tk()
        root.withdraw()

        caminho_imagem = filedialog.askopenfilename(
            title="Selecione uma imagem",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if not caminho_imagem:
            print("Nenhuma imagem foi selecionada.")
            root.destroy()
            return

        imagem = Image.open(caminho_imagem)
        imagem = imagem.convert("RGB")  # Garante que a imagem esteja no modo RGB

        quantidade_threads = os.cpu_count() or 4

        imagem_sem_threads, tempo_sem_threads = converter_sem_threads(imagem)
        imagem_preto_branco, tempo_com_threads, quantidade_threads = converter_com_threads(
            imagem,
            quantidade_threads,
        )

        PASTA_SAIDA.mkdir(exist_ok=True)
        nome_saida = f"{Path(caminho_imagem).stem}_pb.png"

        caminho_saida = filedialog.asksaveasfilename(
            title="Salvar imagem em preto e branco",
            defaultextension=".png",
            initialdir=str(PASTA_SAIDA),
            initialfile=nome_saida,
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if not caminho_saida:
            print("Operacao de salvamento cancelada.")
            root.destroy()
            return

        imagem_preto_branco.save(caminho_saida)
        caminho_saida = Path(caminho_saida).resolve()

        print(f"Imagem convertida com sucesso! Salva em: {caminho_saida}")
        print(f"Caminho final da imagem salva: {caminho_saida}")

        mostrar_tempos(tempo_sem_threads, tempo_com_threads, quantidade_threads)

        if imagem_sem_threads.tobytes() == imagem_preto_branco.tobytes():
            print("Validacao: a conversao com threads esta correta.")
        else:
            print("Aviso: a conversao com threads ficou diferente da sem threads.")

        root.destroy()

    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")


def main():
    converter_preto_branco()

if __name__ == "__main__":
    main()