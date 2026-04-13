from __future__ import annotations

import argparse
import csv
import multiprocessing
import re
import unicodedata
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR_CANDIDATES = (
    SCRIPT_DIR / "Base de Dados",
    SCRIPT_DIR.parent / "Base de Dados",
    Path(
        r"C:\Users\paulo\OneDrive\Documentos\Github_Desktop_Arquivos"
        r"\progamacao_concorrente_e_distribuida\TP01_Manipulando_Arquivos\Base de Dados"
    ),
    Path(
        r"C:\Users\paulo\OneDrive\Documentos\Github_Desktop_Arquivos"
        r"\progamacao_concorrente_e_distribuida\Base de Dados"
    ),
)
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "saida"
INPUT_ENCODING = "utf-8-sig"
OUTPUT_ENCODING = "utf-8"

AGGREGATE_FIELDS = (
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
)

SUMMARY_HEADER = (
    "municipio_oj",
    "total_julgados_2026",
    "Meta1",
    "Meta2A",
    "Meta2Ant",
    "Meta4A",
    "Meta4B",
)

RANKING_HEADER = (
    "sigla_tribunal",
    "Meta1",
    "Meta2A",
    "Meta2Ant",
    "Meta4A",
    "Meta4B",
)


def localizar_base_padrao() -> Path:
    for caminho in BASE_DIR_CANDIDATES:
        if caminho.exists():
            return caminho
    return BASE_DIR_CANDIDATES[0]


DEFAULT_BASE_DIR = localizar_base_padrao()


@dataclass
class TempoExecucao:
    funcionalidade: str
    tempo_serial: float
    tempo_paralelo: float

    @property
    def speedup(self) -> float:
        if self.tempo_paralelo == 0:
            return 0.0
        return self.tempo_serial / self.tempo_paralelo


def listar_arquivos_csv(base_dir: Path | str) -> list[Path]:
    base_path = Path(base_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"Pasta da base nao encontrada: {base_path}")

    arquivos = sorted(base_path.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em: {base_path}")

    return arquivos


def garantir_pasta_saida(caminho: Path | str) -> Path:
    path = Path(caminho)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def normalizar_texto(texto: str) -> str:
    texto_ascii = unicodedata.normalize("NFKD", texto or "")
    texto_ascii = texto_ascii.encode("ascii", "ignore").decode("ascii")
    texto_ascii = re.sub(r"\s+", " ", texto_ascii.strip())
    return texto_ascii.upper()


def nome_arquivo_municipio(municipio: str) -> str:
    nome = normalizar_texto(municipio)
    nome = re.sub(r"[^A-Z0-9_-]+", "_", nome).strip("_")
    return nome or "MUNICIPIO"


def converter_numero(valor: str | None) -> float:
    if valor is None:
        return 0.0

    texto = valor.strip()
    if not texto:
        return 0.0

    texto = texto.replace("%", "").replace(" ", "")
    if "," in texto and "." not in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0.0


def dividir(numerador: float, denominador: float) -> float:
    if denominador == 0:
        return 0.0
    return numerador / denominador


def formatar_inteiro(valor: float) -> str:
    return str(int(round(valor)))


def formatar_meta(valor: float) -> str:
    return f"{valor:.4f}"


def novos_totais() -> dict[str, float]:
    return {campo: 0.0 for campo in AGGREGATE_FIELDS}


def mesclar_totais(destino: dict[str, float], origem: dict[str, float]) -> None:
    for campo in AGGREGATE_FIELDS:
        destino[campo] = destino.get(campo, 0.0) + origem.get(campo, 0.0)


def calcular_metas(totais: dict[str, float]) -> dict[str, float]:
    meta1_denominador = (
        totais.get("casos_novos_2026", 0.0)
        + totais.get("dessobrestados_2026", 0.0)
        + totais.get("suspensos_2026", 0.0)
    )
    meta2a_denominador = (
        totais.get("distm2_a", 0.0) + totais.get("suspm2_a", 0.0)
    )
    meta2ant_denominador = (
        totais.get("distm2_ant", 0.0)
        + totais.get("suspm2_ant", 0.0)
        + totais.get("desom2_ant", 0.0)
    )
    meta4a_denominador = (
        totais.get("distm4_a", 0.0) + totais.get("suspm4_a", 0.0)
    )
    meta4b_denominador = (
        totais.get("distm4_b", 0.0) + totais.get("suspm4_b", 0.0)
    )

    return {
        "Meta1": dividir(totais.get("julgados_2026", 0.0), meta1_denominador)
        * 100,
        "Meta2A": dividir(totais.get("julgm2_a", 0.0), meta2a_denominador)
        * (1000 / 7),
        "Meta2Ant": dividir(
            totais.get("julgm2_ant", 0.0), meta2ant_denominador
        )
        * 100,
        "Meta4A": dividir(totais.get("julgm4_a", 0.0), meta4a_denominador)
        * 100,
        "Meta4B": dividir(totais.get("julgm4_b", 0.0), meta4b_denominador)
        * 100,
    }


def ler_cabecalho(base_dir: Path | str) -> list[str]:
    arquivos = listar_arquivos_csv(base_dir)
    with arquivos[0].open("r", encoding=INPUT_ENCODING, newline="") as arquivo:
        leitor = csv.reader(arquivo)
        return next(leitor)


def _conteudo_sem_cabecalho(path_str: str) -> str:
    path = Path(path_str)
    with path.open("r", encoding=INPUT_ENCODING, newline="") as arquivo:
        arquivo.readline()
        return arquivo.read()


def concatenar_arquivos_serial(
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
) -> Path:
    arquivos = listar_arquivos_csv(base_dir)
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / "base_concatenada_serial.csv"
    output_path = garantir_pasta_saida(output_path)

    with output_path.open("w", encoding=OUTPUT_ENCODING, newline="") as saida:
        primeiro_arquivo = True
        for path in arquivos:
            with path.open("r", encoding=INPUT_ENCODING, newline="") as entrada:
                cabecalho = entrada.readline()
                if primeiro_arquivo:
                    saida.write(cabecalho)
                    primeiro_arquivo = False
                for bloco in iter(lambda: entrada.read(1024 * 1024), ""):
                    saida.write(bloco)

    return output_path


def concatenar_arquivos_paralelo(
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
    max_workers: int | None = None,
) -> Path:
    arquivos = listar_arquivos_csv(base_dir)
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / "base_concatenada_paralelo.csv"
    output_path = garantir_pasta_saida(output_path)

    with arquivos[0].open("r", encoding=INPUT_ENCODING, newline="") as entrada:
        cabecalho = entrada.readline()

    with output_path.open("w", encoding=OUTPUT_ENCODING, newline="") as saida:
        saida.write(cabecalho)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futuros = [
                executor.submit(_conteudo_sem_cabecalho, str(path))
                for path in arquivos
            ]
            for futuro in futuros:
                saida.write(futuro.result())

    return output_path


def _agrupar_arquivo(args: tuple[str, str]) -> dict[str, dict[str, float]]:
    path_str, campo_chave = args
    grupos: dict[str, dict[str, float]] = {}

    with Path(path_str).open("r", encoding=INPUT_ENCODING, newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            chave = (linha.get(campo_chave) or "SEM_INFORMACAO").strip()
            totais = grupos.setdefault(chave, novos_totais())
            for campo in AGGREGATE_FIELDS:
                totais[campo] += converter_numero(linha.get(campo))

    return grupos


def mapear_paralelo(
    funcao: Callable,
    argumentos: list[tuple[str, str]],
    max_workers: int | None = None,
) -> list:
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(funcao, argumentos))
    except (OSError, PermissionError):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(funcao, argumentos))


def agrupar_serial(
    base_dir: Path | str,
    campo_chave: str,
) -> dict[str, dict[str, float]]:
    grupos: dict[str, dict[str, float]] = {}
    for path in listar_arquivos_csv(base_dir):
        parcial = _agrupar_arquivo((str(path), campo_chave))
        mesclar_grupos(grupos, parcial)
    return grupos


def agrupar_paralelo(
    base_dir: Path | str,
    campo_chave: str,
    max_workers: int | None = None,
) -> dict[str, dict[str, float]]:
    arquivos = listar_arquivos_csv(base_dir)
    grupos: dict[str, dict[str, float]] = {}

    argumentos = [(str(path), campo_chave) for path in arquivos]
    for parcial in mapear_paralelo(_agrupar_arquivo, argumentos, max_workers):
        mesclar_grupos(grupos, parcial)

    return grupos


def mesclar_grupos(
    destino: dict[str, dict[str, float]],
    origem: dict[str, dict[str, float]],
) -> None:
    for chave, totais_origem in origem.items():
        totais_destino = destino.setdefault(chave, novos_totais())
        mesclar_totais(totais_destino, totais_origem)


def escrever_resumo_municipios(
    grupos: dict[str, dict[str, float]],
    output_path: Path | str,
) -> Path:
    output_path = garantir_pasta_saida(output_path)

    with output_path.open("w", encoding=OUTPUT_ENCODING, newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(SUMMARY_HEADER)
        for municipio in sorted(grupos, key=normalizar_texto):
            totais = grupos[municipio]
            metas = calcular_metas(totais)
            escritor.writerow(
                [
                    municipio,
                    formatar_inteiro(totais.get("julgados_2026", 0.0)),
                    formatar_meta(metas["Meta1"]),
                    formatar_meta(metas["Meta2A"]),
                    formatar_meta(metas["Meta2Ant"]),
                    formatar_meta(metas["Meta4A"]),
                    formatar_meta(metas["Meta4B"]),
                ]
            )

    return output_path


def gerar_resumo_municipios_serial(
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
) -> Path:
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / "resumo_municipios_serial.csv"
    grupos = agrupar_serial(base_dir, "municipio_oj")
    return escrever_resumo_municipios(grupos, output_path)


def gerar_resumo_municipios_paralelo(
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
    max_workers: int | None = None,
) -> Path:
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / "resumo_municipios_paralelo.csv"
    grupos = agrupar_paralelo(base_dir, "municipio_oj", max_workers)
    return escrever_resumo_municipios(grupos, output_path)


def escrever_ranking_tribunais(
    grupos: dict[str, dict[str, float]],
    output_path: Path | str,
) -> Path:
    output_path = garantir_pasta_saida(output_path)
    linhas = []

    for tribunal, totais in grupos.items():
        metas = calcular_metas(totais)
        linhas.append((metas["Meta1"], normalizar_texto(tribunal), tribunal, metas))

    linhas.sort(key=lambda item: (-item[0], item[1]))

    with output_path.open("w", encoding=OUTPUT_ENCODING, newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(RANKING_HEADER)
        for _, _, tribunal, metas in linhas[:10]:
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

    return output_path


def gerar_ranking_tribunais_serial(
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
) -> Path:
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / "ranking_tribunais_serial.csv"
    grupos = agrupar_serial(base_dir, "sigla_tribunal")
    return escrever_ranking_tribunais(grupos, output_path)


def gerar_ranking_tribunais_paralelo(
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
    max_workers: int | None = None,
) -> Path:
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / "ranking_tribunais_paralelo.csv"
    grupos = agrupar_paralelo(base_dir, "sigla_tribunal", max_workers)
    return escrever_ranking_tribunais(grupos, output_path)


def _filtrar_arquivo(args: tuple[str, str]) -> list[list[str]]:
    path_str, municipio_normalizado = args
    linhas_filtradas: list[list[str]] = []

    with Path(path_str).open("r", encoding=INPUT_ENCODING, newline="") as arquivo:
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor)
        indice_municipio = cabecalho.index("municipio_oj")
        for linha in leitor:
            if (
                len(linha) > indice_municipio
                and normalizar_texto(linha[indice_municipio]) == municipio_normalizado
            ):
                linhas_filtradas.append(linha)

    return linhas_filtradas


def filtrar_municipio_serial(
    municipio: str,
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
) -> Path:
    arquivos = listar_arquivos_csv(base_dir)
    cabecalho = ler_cabecalho(base_dir)
    municipio_normalizado = normalizar_texto(municipio)

    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / f"{nome_arquivo_municipio(municipio)}.txt"
    output_path = garantir_pasta_saida(output_path)

    with output_path.open("w", encoding=OUTPUT_ENCODING, newline="") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(cabecalho)
        for path in arquivos:
            for linha in _filtrar_arquivo((str(path), municipio_normalizado)):
                escritor.writerow(linha)

    return output_path


def filtrar_municipio_paralelo(
    municipio: str,
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_path: Path | str | None = None,
    max_workers: int | None = None,
) -> Path:
    arquivos = listar_arquivos_csv(base_dir)
    cabecalho = ler_cabecalho(base_dir)
    municipio_normalizado = normalizar_texto(municipio)

    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / f"{nome_arquivo_municipio(municipio)}.txt"
    output_path = garantir_pasta_saida(output_path)

    with output_path.open("w", encoding=OUTPUT_ENCODING, newline="") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(cabecalho)
        argumentos = [(str(path), municipio_normalizado) for path in arquivos]
        for linhas in mapear_paralelo(_filtrar_arquivo, argumentos, max_workers):
            escritor.writerows(linhas)

    return output_path


def medir_tempo(funcao: Callable[[], Path]) -> tuple[Path, float]:
    inicio = perf_counter()
    resultado = funcao()
    fim = perf_counter()
    return resultado, fim - inicio


def executar_comparacao(
    nome: str,
    funcao_serial: Callable[[], Path],
    funcao_paralela: Callable[[], Path],
) -> TempoExecucao:
    caminho_serial, tempo_serial = medir_tempo(funcao_serial)
    print(f"{nome} serial: {tempo_serial:.4f}s -> {caminho_serial}")

    caminho_paralelo, tempo_paralelo = medir_tempo(funcao_paralela)
    print(f"{nome} paralelo: {tempo_paralelo:.4f}s -> {caminho_paralelo}")

    resultado = TempoExecucao(nome, tempo_serial, tempo_paralelo)
    print(f"Speedup: {resultado.speedup:.4f}\n")
    return resultado


def executar_benchmark(
    base_dir: Path | str = DEFAULT_BASE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    municipio: str = "MACAPA",
    max_workers: int | None = None,
) -> list[TempoExecucao]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    nome_municipio = nome_arquivo_municipio(municipio)
    resultados = [
        executar_comparacao(
            "Concatenar arquivos",
            lambda: concatenar_arquivos_serial(
                base_dir, output_dir / "base_concatenada_serial.csv"
            ),
            lambda: concatenar_arquivos_paralelo(
                base_dir, output_dir / "base_concatenada_paralelo.csv", max_workers
            ),
        ),
        executar_comparacao(
            "Resumo por municipio",
            lambda: gerar_resumo_municipios_serial(
                base_dir, output_dir / "resumo_municipios_serial.csv"
            ),
            lambda: gerar_resumo_municipios_paralelo(
                base_dir, output_dir / "resumo_municipios_paralelo.csv", max_workers
            ),
        ),
        executar_comparacao(
            "Ranking de tribunais",
            lambda: gerar_ranking_tribunais_serial(
                base_dir, output_dir / "ranking_tribunais_serial.csv"
            ),
            lambda: gerar_ranking_tribunais_paralelo(
                base_dir, output_dir / "ranking_tribunais_paralelo.csv", max_workers
            ),
        ),
        executar_comparacao(
            "Filtro por municipio",
            lambda: filtrar_municipio_serial(
                municipio, base_dir, output_dir / f"{nome_municipio}_serial.txt"
            ),
            lambda: filtrar_municipio_paralelo(
                municipio,
                base_dir,
                output_dir / f"{nome_municipio}_paralelo.txt",
                max_workers,
            ),
        ),
    ]

    tempos_path = output_dir / "tempos_execucao.csv"
    with tempos_path.open("w", encoding=OUTPUT_ENCODING, newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            ["funcionalidade", "tempo_serial", "tempo_paralelo", "speedup"]
        )
        for item in resultados:
            escritor.writerow(
                [
                    item.funcionalidade,
                    f"{item.tempo_serial:.6f}",
                    f"{item.tempo_paralelo:.6f}",
                    f"{item.speedup:.6f}",
                ]
            )

    print(f"Tempos gravados em: {tempos_path}")
    return resultados


def executar_acao(
    acao: str,
    modo: str,
    base_dir: Path,
    output_dir: Path,
    municipio: str,
    max_workers: int | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if acao == "benchmark":
        executar_benchmark(base_dir, output_dir, municipio, max_workers)
        return

    acoes: dict[str, tuple[Callable[[], Path], Callable[[], Path]]] = {
        "concatenar": (
            lambda: concatenar_arquivos_serial(
                base_dir, output_dir / "base_concatenada_serial.csv"
            ),
            lambda: concatenar_arquivos_paralelo(
                base_dir, output_dir / "base_concatenada_paralelo.csv", max_workers
            ),
        ),
        "resumo-municipios": (
            lambda: gerar_resumo_municipios_serial(
                base_dir, output_dir / "resumo_municipios_serial.csv"
            ),
            lambda: gerar_resumo_municipios_paralelo(
                base_dir, output_dir / "resumo_municipios_paralelo.csv", max_workers
            ),
        ),
        "ranking-tribunais": (
            lambda: gerar_ranking_tribunais_serial(
                base_dir, output_dir / "ranking_tribunais_serial.csv"
            ),
            lambda: gerar_ranking_tribunais_paralelo(
                base_dir, output_dir / "ranking_tribunais_paralelo.csv", max_workers
            ),
        ),
        "filtrar-municipio": (
            lambda: filtrar_municipio_serial(
                municipio, base_dir, output_dir / f"{nome_arquivo_municipio(municipio)}.txt"
            ),
            lambda: filtrar_municipio_paralelo(
                municipio,
                base_dir,
                output_dir / f"{nome_arquivo_municipio(municipio)}.txt",
                max_workers,
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


def menu_interativo(
    base_dir: Path,
    output_dir: Path,
    max_workers: int | None,
) -> None:
    municipio_padrao = "MACAPA"

    while True:
        print("\nTP01 - Manipulando arquivos")
        print(f"Base: {base_dir}")
        print(f"Saida: {output_dir}")
        print("1 - Concatenar arquivos")
        print("2 - Gerar resumo por municipio")
        print("3 - Gerar ranking dos 10 tribunais")
        print("4 - Filtrar por municipio")
        print("5 - Executar benchmark completo")
        print("0 - Sair")
        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "0":
            break
        if opcao not in {"1", "2", "3", "4", "5"}:
            print("Opcao invalida.")
            continue

        modo = "ambos"
        if opcao != "5":
            modo = input("Modo (serial/paralelo/ambos): ").strip().lower() or "ambos"
            if modo not in {"serial", "paralelo", "ambos"}:
                print("Modo invalido.")
                continue

        municipio = municipio_padrao
        if opcao in {"4", "5"}:
            municipio = input("Municipio: ").strip() or municipio_padrao

        mapa_acoes = {
            "1": "concatenar",
            "2": "resumo-municipios",
            "3": "ranking-tribunais",
            "4": "filtrar-municipio",
            "5": "benchmark",
        }

        executar_acao(
            mapa_acoes[opcao],
            modo,
            base_dir,
            output_dir,
            municipio,
            max_workers,
        )


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TP01 - Manipulacao de arquivos CSV em versoes serial e paralela."
    )
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
        help="Funcionalidade a executar.",
    )
    parser.add_argument(
        "--modo",
        choices=["serial", "paralelo", "ambos"],
        default="ambos",
        help="Versao a executar quando a acao nao for menu ou benchmark.",
    )
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Pasta que contem os arquivos CSV da base de dados.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Pasta onde os arquivos gerados serao gravados.",
    )
    parser.add_argument(
        "--municipio",
        default="MACAPA",
        help="Municipio usado na acao filtrar-municipio e no benchmark.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Quantidade de workers nas versoes paralelas.",
    )
    return parser


def main() -> None:
    args = criar_parser().parse_args()
    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)

    if args.acao == "menu":
        menu_interativo(base_dir, output_dir, args.workers)
    else:
        executar_acao(
            args.acao,
            args.modo,
            base_dir,
            output_dir,
            args.municipio,
            args.workers,
        )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
