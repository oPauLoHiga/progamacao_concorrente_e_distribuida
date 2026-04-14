from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter

PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_BASE_PADRAO = PASTA_PROJETO / "Base de Dados"
PASTA_SAIDA_PADRAO = PASTA_PROJETO / "saida"

ENCODING_ENTRADA = "utf-8-sig"
ENCODING_SAIDA = "utf-8"

CAMPOS_SOMA = [
    "julgados_2026",
    "casos_novos_2026",
    "suspensos_2026",
    "dessobrestados_2026",
    "distm2_a",
    "julgm2_a",
    "suspm2_a",
    "distm2_ant",
    "julgm2_ant",
    "suspm2_ant",
    "desom2_ant",
    "distm4_a",
    "julgm4_a",
    "suspm4_a",
    "distm4_b",
    "julgm4_b",
    "suspm4_b",
]

CABECALHO_RESUMO = [
    "municipio_oj",
    "total_julgados_2026",
    "Meta1",
    "Meta2A",
    "Meta2Ant",
    "Meta4A",
    "Meta4B",
]

CABECALHO_RANKING = [
    "sigla_tribunal",
    "Meta1",
    "Meta2A",
    "Meta2Ant",
    "Meta4A",
    "Meta4B",
]


def listar_csvs(pasta_base: Path | str) -> list[Path]:
    pasta = Path(pasta_base)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta da base nao encontrada: {pasta}")

    arquivos = sorted(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum CSV encontrado em: {pasta}")

    return arquivos


def preparar_saida(caminho: Path | str) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return caminho


def ler_cabecalho(pasta_base: Path | str) -> list[str]:
    primeiro_csv = listar_csvs(pasta_base)[0]
    with primeiro_csv.open("r", encoding=ENCODING_ENTRADA, newline="") as arquivo:
        return next(csv.reader(arquivo))


def numero(valor: str | None) -> float:
    if valor is None:
        return 0.0

    valor = valor.strip().replace("%", "").replace(" ", "")
    if not valor:
        return 0.0

    if "," in valor and "." not in valor:
        valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return 0.0


def dividir(numerador: float, denominador: float) -> float:
    if denominador == 0:
        return 0.0
    return numerador / denominador


def formatar_meta(valor: float) -> str:
    return f"{valor:.4f}"


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"\s+", " ", texto.strip())
    return texto.upper()


def nome_arquivo_municipio(municipio: str) -> str:
    nome = normalizar_texto(municipio)
    nome = re.sub(r"[^A-Z0-9_-]+", "_", nome).strip("_")
    return nome or "MUNICIPIO"


def totais_vazios() -> dict[str, float]:
    return {campo: 0.0 for campo in CAMPOS_SOMA}


def somar_linha(totais: dict[str, float], linha: dict[str, str]) -> None:
    for campo in CAMPOS_SOMA:
        totais[campo] += numero(linha.get(campo))


def juntar_totais(destino: dict[str, float], origem: dict[str, float]) -> None:
    for campo in CAMPOS_SOMA:
        destino[campo] += origem.get(campo, 0.0)


def calcular_metas(totais: dict[str, float]) -> dict[str, float]:
    meta1_den = ( totais["casos_novos_2026"] + totais["dessobrestados_2026"]+ totais["suspensos_2026"])

    meta2a_den = totais["distm2_a"] + totais["suspm2_a"]

    meta2ant_den = ( totais["distm2_ant"] + totais["suspm2_ant"] + totais["desom2_ant"])

    meta4a_den = totais["distm4_a"] + totais["suspm4_a"]

    meta4b_den = totais["distm4_b"] + totais["suspm4_b"]

    return {
        "Meta1": dividir(totais["julgados_2026"], meta1_den) * 100,
        "Meta2A": dividir(totais["julgm2_a"], meta2a_den) * (1000 / 7),
        "Meta2Ant": dividir(totais["julgm2_ant"], meta2ant_den) * 100,
        "Meta4A": dividir(totais["julgm4_a"], meta4a_den) * 100,
        "Meta4B": dividir(totais["julgm4_b"], meta4b_den) * 100,
    }


def juntar_grupos(
    destino: dict[str, dict[str, float]],
    origem: dict[str, dict[str, float]],
) -> None:
    for chave, totais_origem in origem.items():
        if chave not in destino:
            destino[chave] = totais_vazios()
        juntar_totais(destino[chave], totais_origem)


def agrupar_arquivo(caminho_csv: Path | str, campo_chave: str) -> dict[str, dict[str, float]]:
    grupos: dict[str, dict[str, float]] = {}

    with Path(caminho_csv).open("r", encoding=ENCODING_ENTRADA, newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            chave = (linha.get(campo_chave) or "SEM_INFORMACAO").strip()
            if chave not in grupos:
                grupos[chave] = totais_vazios()
            somar_linha(grupos[chave], linha)

    return grupos


def agrupar_serial(pasta_base: Path | str, campo_chave: str) -> dict[str, dict[str, float]]:
    grupos: dict[str, dict[str, float]] = {}

    for arquivo in listar_csvs(pasta_base):
        parcial = agrupar_arquivo(arquivo, campo_chave)
        juntar_grupos(grupos, parcial)

    return grupos


def agrupar_paralelo(
    pasta_base: Path | str,
    campo_chave: str,
    workers: int | None = None,
) -> dict[str, dict[str, float]]:
    grupos: dict[str, dict[str, float]] = {}
    arquivos = listar_csvs(pasta_base)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        resultados = executor.map(lambda arq: agrupar_arquivo(arq, campo_chave), arquivos)

        for parcial in resultados:
            juntar_grupos(grupos, parcial)

    return grupos


def concatenar_arquivos_serial(
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
) -> Path:
    arquivos = listar_csvs(pasta_base)
    caminho_saida = preparar_saida(
        caminho_saida or PASTA_SAIDA_PADRAO / "base_concatenada_serial.csv"
    )

    with caminho_saida.open("w", encoding=ENCODING_SAIDA, newline="") as saida:
        for indice, arquivo_csv in enumerate(arquivos):
            with arquivo_csv.open("r", encoding=ENCODING_ENTRADA, newline="") as entrada:
                cabecalho = entrada.readline()
                if indice == 0:
                    saida.write(cabecalho)
                saida.write(entrada.read())

    return caminho_saida


def ler_sem_cabecalho(caminho_csv: Path | str) -> str:
    with Path(caminho_csv).open("r", encoding=ENCODING_ENTRADA, newline="") as arquivo:
        arquivo.readline()
        return arquivo.read()


def concatenar_arquivos_paralelo(
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
    workers: int | None = None,
) -> Path:
    arquivos = listar_csvs(pasta_base)
    caminho_saida = preparar_saida(caminho_saida or PASTA_SAIDA_PADRAO / "base_concatenada_paralelo.csv")

    with arquivos[0].open("r", encoding=ENCODING_ENTRADA, newline="") as primeiro:
        cabecalho = primeiro.readline()

    with caminho_saida.open("w", encoding=ENCODING_SAIDA, newline="") as saida:
        saida.write(cabecalho)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for conteudo in executor.map(ler_sem_cabecalho, arquivos):
                saida.write(conteudo)

    return caminho_saida


def escrever_resumo_municipios(
    grupos: dict[str, dict[str, float]],
    caminho_saida: Path | str,
) -> Path:
    caminho_saida = preparar_saida(caminho_saida)

    with caminho_saida.open("w", encoding=ENCODING_SAIDA, newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(CABECALHO_RESUMO)

        for municipio in sorted(grupos, key=normalizar_texto):
            totais = grupos[municipio]
            metas = calcular_metas(totais)
            escritor.writerow(
                [
                    municipio,
                    int(round(totais["julgados_2026"])),
                    formatar_meta(metas["Meta1"]),
                    formatar_meta(metas["Meta2A"]),
                    formatar_meta(metas["Meta2Ant"]),
                    formatar_meta(metas["Meta4A"]),
                    formatar_meta(metas["Meta4B"]),
                ]
            )

    return caminho_saida


def gerar_resumo_municipios_serial(
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
) -> Path:
    grupos = agrupar_serial(pasta_base, "municipio_oj")

    return escrever_resumo_municipios(
        grupos,
        caminho_saida or PASTA_SAIDA_PADRAO / "resumo_municipios_serial.csv",
    )


def gerar_resumo_municipios_paralelo(
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
    workers: int | None = None,
) -> Path:
    grupos = agrupar_paralelo(pasta_base, "municipio_oj", workers)

    return escrever_resumo_municipios(
        grupos,
        caminho_saida or PASTA_SAIDA_PADRAO / "resumo_municipios_paralelo.csv",
    )


def escrever_ranking_tribunais(
    grupos: dict[str, dict[str, float]],
    caminho_saida: Path | str,
) -> Path:
    caminho_saida = preparar_saida(caminho_saida)
    ranking = []

    for tribunal, totais in grupos.items():
        metas = calcular_metas(totais)
        ranking.append((metas["Meta1"], tribunal, metas))

    ranking.sort(key=lambda item: (-item[0], item[1]))

    with caminho_saida.open("w", encoding=ENCODING_SAIDA, newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(CABECALHO_RANKING)

        for _, tribunal, metas in ranking[:10]:
            escritor.writerow(
                [
                    tribunal,
                    formatar_meta(metas["Meta1"]),
                    formatar_meta(metas["Meta2A"]),
                    formatar_meta(metas["Meta2Ant"]),
                    formatar_meta(metas["Meta4A"]),
                    formatar_meta(metas["Meta4B"]),
                ]
            )

    return caminho_saida


def gerar_ranking_tribunais_serial(
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
) -> Path:
    grupos = agrupar_serial(pasta_base, "sigla_tribunal")

    return escrever_ranking_tribunais(
        grupos,
        caminho_saida or PASTA_SAIDA_PADRAO / "ranking_tribunais_serial.csv",
    )


def gerar_ranking_tribunais_paralelo(
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
    workers: int | None = None,
) -> Path:
    grupos = agrupar_paralelo(pasta_base, "sigla_tribunal", workers)
    return escrever_ranking_tribunais(
        grupos,
        caminho_saida or PASTA_SAIDA_PADRAO / "ranking_tribunais_paralelo.csv",
    )


def filtrar_arquivo(caminho_csv: Path | str, municipio_normalizado: str) -> list[list[str]]:
    linhas_filtradas = []

    with Path(caminho_csv).open("r", encoding=ENCODING_ENTRADA, newline="") as arquivo:
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor)
        indice_municipio = cabecalho.index("municipio_oj")

        for linha in leitor:
            if normalizar_texto(linha[indice_municipio]) == municipio_normalizado:
                linhas_filtradas.append(linha)

    return linhas_filtradas


def filtrar_municipio_serial(
    municipio: str,
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
) -> Path:
    arquivos = listar_csvs(pasta_base)
    municipio_normalizado = normalizar_texto(municipio)
    caminho_saida = preparar_saida(
        caminho_saida or PASTA_SAIDA_PADRAO / f"{nome_arquivo_municipio(municipio)}.txt"
    )

    with caminho_saida.open("w", encoding=ENCODING_SAIDA, newline="") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(ler_cabecalho(pasta_base))

        for arquivo_csv in arquivos:
            escritor.writerows(filtrar_arquivo(arquivo_csv, municipio_normalizado))

    return caminho_saida


def filtrar_municipio_paralelo(
    municipio: str,
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    caminho_saida: Path | str | None = None,
    workers: int | None = None,
) -> Path:
    arquivos = listar_csvs(pasta_base)
    municipio_normalizado = normalizar_texto(municipio)
    caminho_saida = preparar_saida(
        caminho_saida or PASTA_SAIDA_PADRAO / f"{nome_arquivo_municipio(municipio)}.txt"
    )

    with caminho_saida.open("w", encoding=ENCODING_SAIDA, newline="") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(ler_cabecalho(pasta_base))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            resultados = executor.map(
                lambda arq: filtrar_arquivo(arq, municipio_normalizado), arquivos
            )
            for linhas in resultados:
                escritor.writerows(linhas)

    return caminho_saida


def medir_tempo(funcao):
    inicio = perf_counter()
    caminho = funcao()
    fim = perf_counter()
    return caminho, fim - inicio


def executar_comparacao(nome: str, funcao_serial, funcao_paralela) -> tuple[float, float]:
    caminho_serial, tempo_serial = medir_tempo(funcao_serial)
    print(f"{nome} serial: {tempo_serial:.4f}s -> {caminho_serial}")

    caminho_paralelo, tempo_paralelo = medir_tempo(funcao_paralela)
    print(f"{nome} paralelo: {tempo_paralelo:.4f}s -> {caminho_paralelo}")

    speedup = tempo_serial / tempo_paralelo if tempo_paralelo else 0.0
    print(f"Speedup: {speedup:.4f}\n")
    return tempo_serial, tempo_paralelo


def executar_benchmark(
    pasta_base: Path | str = PASTA_BASE_PADRAO,
    pasta_saida: Path | str = PASTA_SAIDA_PADRAO,
    municipio: str = "MACAPA",
    workers: int | None = None,
) -> None:
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    municipio_arquivo = nome_arquivo_municipio(municipio)

    testes = [
        (
            "Concatenar arquivos",
            lambda: concatenar_arquivos_serial(
                pasta_base, pasta_saida / "base_concatenada_serial.csv"
            ),
            lambda: concatenar_arquivos_paralelo(
                pasta_base, pasta_saida / "base_concatenada_paralelo.csv", workers
            ),
        ),
        (
            "Resumo por municipio",
            lambda: gerar_resumo_municipios_serial(
                pasta_base, pasta_saida / "resumo_municipios_serial.csv"
            ),
            lambda: gerar_resumo_municipios_paralelo(
                pasta_base, pasta_saida / "resumo_municipios_paralelo.csv", workers
            ),
        ),
        (
            "Ranking de tribunais",
            lambda: gerar_ranking_tribunais_serial(
                pasta_base, pasta_saida / "ranking_tribunais_serial.csv"
            ),
            lambda: gerar_ranking_tribunais_paralelo(
                pasta_base, pasta_saida / "ranking_tribunais_paralelo.csv", workers
            ),
        ),
        (
            "Filtro por municipio",
            lambda: filtrar_municipio_serial(
                municipio, pasta_base, pasta_saida / f"{municipio_arquivo}_serial.txt"
            ),
            lambda: filtrar_municipio_paralelo(
                municipio,
                pasta_base,
                pasta_saida / f"{municipio_arquivo}_paralelo.txt",
                workers,
            ),
        ),
    ]

    resultados = []
    for nome, funcao_serial, funcao_paralela in testes:
        tempo_serial, tempo_paralelo = executar_comparacao(
            nome, funcao_serial, funcao_paralela
        )
        resultados.append((nome, tempo_serial, tempo_paralelo))

    caminho_tempos = pasta_saida / "tempos_execucao.csv"
    with caminho_tempos.open("w", encoding=ENCODING_SAIDA, newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["funcionalidade", "tempo_serial", "tempo_paralelo", "speedup"])

        for nome, tempo_serial, tempo_paralelo in resultados:
            speedup = tempo_serial / tempo_paralelo if tempo_paralelo else 0.0
            escritor.writerow(
                [
                    nome,
                    f"{tempo_serial:.6f}",
                    f"{tempo_paralelo:.6f}",
                    f"{speedup:.6f}",
                ]
            )

    print(f"Tempos gravados em: {caminho_tempos}")


def executar_acao(
    acao: str,
    modo: str,
    pasta_base: Path,
    pasta_saida: Path,
    municipio: str,
    workers: int | None,
) -> None:
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if acao == "benchmark":
        executar_benchmark(pasta_base, pasta_saida, municipio, workers)
        return

    municipio_arquivo = nome_arquivo_municipio(municipio)
    acoes = {
        "concatenar": (
            lambda: concatenar_arquivos_serial(
                pasta_base, pasta_saida / "base_concatenada_serial.csv"
            ),
            lambda: concatenar_arquivos_paralelo(
                pasta_base, pasta_saida / "base_concatenada_paralelo.csv", workers
            ),
        ),
        "resumo-municipios": (
            lambda: gerar_resumo_municipios_serial(
                pasta_base, pasta_saida / "resumo_municipios_serial.csv"
            ),
            lambda: gerar_resumo_municipios_paralelo(
                pasta_base, pasta_saida / "resumo_municipios_paralelo.csv", workers
            ),
        ),
        "ranking-tribunais": (
            lambda: gerar_ranking_tribunais_serial(
                pasta_base, pasta_saida / "ranking_tribunais_serial.csv"
            ),
            lambda: gerar_ranking_tribunais_paralelo(
                pasta_base, pasta_saida / "ranking_tribunais_paralelo.csv", workers
            ),
        ),
        "filtrar-municipio": (
            lambda: filtrar_municipio_serial(
                municipio, pasta_base, pasta_saida / f"{municipio_arquivo}.txt"
            ),
            lambda: filtrar_municipio_paralelo(
                municipio, pasta_base, pasta_saida / f"{municipio_arquivo}.txt", workers
            ),
        ),
    }

    funcao_serial, funcao_paralela = acoes[acao]

    if modo == "serial":
        caminho, tempo = medir_tempo(funcao_serial)
        print(f"{acao} serial: {tempo:.4f}s -> {caminho}")
    elif modo == "paralelo":
        caminho, tempo = medir_tempo(funcao_paralela)
        print(f"{acao} paralelo: {tempo:.4f}s -> {caminho}")
    else:
        executar_comparacao(acao, funcao_serial, funcao_paralela)


def menu_interativo(pasta_base: Path, pasta_saida: Path, workers: int | None) -> None:
    opcoes = {
        "1": "concatenar",
        "2": "resumo-municipios",
        "3": "ranking-tribunais",
        "4": "filtrar-municipio",
        "5": "benchmark",
    }

    while True:
        print("\nTP01 - Manipulando arquivos")
        print("1 - Concatenar arquivos")
        print("2 - Gerar resumo por municipio")
        print("3 - Gerar ranking dos tribunais")
        print("4 - Filtrar por municipio")
        print("5 - Executar benchmark completo")
        print("0 - Sair")

        opcao = input("Escolha uma opcao: ").strip()
        if opcao == "0":
            break
        if opcao not in opcoes:
            print("Opcao invalida.")
            continue

        modo = "ambos"
        if opcao != "5":
            modo = input("Modo (serial/paralelo/ambos): ").strip().lower() or "ambos"
            if modo not in {"serial", "paralelo", "ambos"}:
                print("Modo invalido.")
                continue

        municipio = "MACAPA"
        if opcao in {"4", "5"}:
            municipio = input("Municipio: ").strip() or "MACAPA"

        executar_acao(opcoes[opcao], modo, pasta_base, pasta_saida, municipio, workers)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TP01 - Manipulando arquivos CSV.")
    parser.add_argument(
        "--acao",
        choices=[
            "menu",
            "concatenar",
            "resumo-municipios",
            "ranking-tribunais",
            "filtrar-municipio",
            "benchmark",
        ],
        default="menu",
    )
    parser.add_argument(
        "--modo",
        choices=["serial", "paralelo", "ambos"],
        default="ambos",
    )
    parser.add_argument("--base-dir", default=str(PASTA_BASE_PADRAO))
    parser.add_argument("--output-dir", default=str(PASTA_SAIDA_PADRAO))
    parser.add_argument("--municipio", default="MACAPA")
    parser.add_argument("--workers", type=int, default=None)
    return parser


def main() -> None:
    args = criar_parser().parse_args()
    pasta_base = Path(args.base_dir)
    pasta_saida = Path(args.output_dir)

    if args.acao == "menu":
        menu_interativo(pasta_base, pasta_saida, args.workers)
    else:
        executar_acao(
            args.acao,
            args.modo,
            pasta_base,
            pasta_saida,
            args.municipio,
            args.workers,
        )

if __name__ == "__main__":
    main()
