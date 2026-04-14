import argparse
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter

import pandas as pd

BASE_DIR = Path(__file__).parent / "Base de Dados"
OUTPUT_DIR = Path(__file__).parent / "saida"
READ_ENCODING = "utf-8-sig"

SUM_COLUMNS = [
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

META_COLUMNS = ["Meta1", "Meta2A", "Meta2Ant", "Meta4A", "Meta4B"]


def listar_csvs(base_dir):
    arquivos = sorted(Path(base_dir).glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em: {base_dir}")
    return arquivos


def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return " ".join(texto.strip().upper().split())


def nome_arquivo_municipio(municipio):
    nome = normalizar_texto(municipio)
    nome = "".join(letra if letra.isalnum() or letra in "-_" else "_" for letra in nome)
    while "__" in nome:
        nome = nome.replace("__", "_")
    return nome.strip("_") or "MUNICIPIO"


def ler_csv(caminho_csv):
    return pd.read_csv(caminho_csv, dtype=str, encoding=READ_ENCODING)


def carregar_base(base_dir=BASE_DIR, paralelo=False, workers=None):
    arquivos = listar_csvs(base_dir)

    if paralelo:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            partes = list(executor.map(ler_csv, arquivos))
    else:
        partes = [ler_csv(arquivo) for arquivo in arquivos]

    return pd.concat(partes, ignore_index=True)


def preparar_coluna_numerica(serie):
    serie = (
        serie.fillna("")
        .astype(str)
        .str.strip()
        .str.replace("%", "", regex=False)
        .str.replace(" ", "", regex=False)
    )
    mascara = serie.str.contains(",", regex=False) & ~serie.str.contains(".", regex=False)
    serie = serie.where(~mascara, serie.str.replace(",", ".", regex=False))
    return pd.to_numeric(serie, errors="coerce").fillna(0.0)


def preparar_base(df):
    base = df.copy()

    for coluna in [coluna for coluna in SUM_COLUMNS if coluna not in base]:
        base[coluna] = ""
    base[SUM_COLUMNS] = base[SUM_COLUMNS].apply(preparar_coluna_numerica)

    for coluna in ["municipio_oj", "sigla_tribunal"]:
        if coluna not in base:
            base[coluna] = "SEM_INFORMACAO"
            continue

        texto = base[coluna].fillna("").astype(str).str.strip()
        base[coluna] = texto.mask(texto == "", "SEM_INFORMACAO")

    return base


def calcular_meta(numerador, denominador, multiplicador):
    return numerador.div(denominador.where(denominador != 0)).fillna(0) * multiplicador


def adicionar_metas(df):
    return df.assign(
        Meta1=calcular_meta(
            df["julgados_2026"],
            df["casos_novos_2026"] + df["dessobrestados_2026"] + df["suspensos_2026"],
            100,
        ),
        Meta2A=calcular_meta(
            df["julgm2_a"],
            df["distm2_a"] + df["suspm2_a"],
            1000 / 7,
        ),
        Meta2Ant=calcular_meta(
            df["julgm2_ant"],
            df["distm2_ant"] + df["suspm2_ant"] + df["desom2_ant"],
            100,
        ),
        Meta4A=calcular_meta(
            df["julgm4_a"],
            df["distm4_a"] + df["suspm4_a"],
            100,
        ),
        Meta4B=calcular_meta(
            df["julgm4_b"],
            df["distm4_b"] + df["suspm4_b"],
            100,
        ),
    )


def formatar_metas(df):
    df = df.copy()
    for coluna in META_COLUMNS:
        df[coluna] = df[coluna].map(lambda valor: f"{valor:.4f}")
    return df


def salvar_csv(df, caminho_saida):
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho_saida, index=False, encoding="utf-8")
    return caminho_saida


def montar_concatenacao(df):
    return df


def montar_resumo_municipios(df):
    resumo = (
        preparar_base(df)
        .groupby("municipio_oj", as_index=False)[SUM_COLUMNS]
        .sum()
        .pipe(adicionar_metas)
        .rename(columns={"julgados_2026": "total_julgados_2026"})
        .sort_values("municipio_oj", key=lambda serie: serie.map(normalizar_texto))
        .reset_index(drop=True)
    )

    resumo["total_julgados_2026"] = resumo["total_julgados_2026"].round().astype(int)
    return formatar_metas(resumo[["municipio_oj", "total_julgados_2026", *META_COLUMNS]])


def montar_ranking_tribunais(df):
    ranking = (
        preparar_base(df)
        .groupby("sigla_tribunal", as_index=False)[SUM_COLUMNS]
        .sum()
        .pipe(adicionar_metas)
        .sort_values(["Meta1", "sigla_tribunal"], ascending=[False, True])
        .head(10)
        .reset_index(drop=True)
    )

    return formatar_metas(ranking[["sigla_tribunal", *META_COLUMNS]])


def montar_filtro_municipio(df, municipio):
    if "municipio_oj" not in df:
        return df.iloc[0:0].copy()

    municipio_normalizado = normalizar_texto(municipio)
    filtro = df["municipio_oj"].fillna("").map(normalizar_texto) == municipio_normalizado
    return df.loc[filtro].reset_index(drop=True)


def executar_transformacao(
    transformar,
    caminho_saida,
    base_dir=BASE_DIR,
    paralelo=False,
    workers=None,
    municipio=None,
):
    df = carregar_base(base_dir, paralelo, workers)
    resultado = transformar(df) if municipio is None else transformar(df, municipio)
    return salvar_csv(resultado, caminho_saida)


def concatenar_arquivos_serial(base_dir=BASE_DIR, caminho_saida=None):
    return executar_transformacao(
        montar_concatenacao,
        caminho_saida or OUTPUT_DIR / "base_concatenada_serial.csv",
        base_dir=base_dir,
    )


def concatenar_arquivos_paralelo(base_dir=BASE_DIR, caminho_saida=None, workers=None):
    return executar_transformacao(
        montar_concatenacao,
        caminho_saida or OUTPUT_DIR / "base_concatenada_paralelo.csv",
        base_dir=base_dir,
        paralelo=True,
        workers=workers,
    )


def gerar_resumo_municipios_serial(base_dir=BASE_DIR, caminho_saida=None):
    return executar_transformacao(
        montar_resumo_municipios,
        caminho_saida or OUTPUT_DIR / "resumo_municipios_serial.csv",
        base_dir=base_dir,
    )


def gerar_resumo_municipios_paralelo(base_dir=BASE_DIR, caminho_saida=None, workers=None):
    return executar_transformacao(
        montar_resumo_municipios,
        caminho_saida or OUTPUT_DIR / "resumo_municipios_paralelo.csv",
        base_dir=base_dir,
        paralelo=True,
        workers=workers,
    )


def gerar_ranking_tribunais_serial(base_dir=BASE_DIR, caminho_saida=None):
    return executar_transformacao(
        montar_ranking_tribunais,
        caminho_saida or OUTPUT_DIR / "ranking_tribunais_serial.csv",
        base_dir=base_dir,
    )


def gerar_ranking_tribunais_paralelo(base_dir=BASE_DIR, caminho_saida=None, workers=None):
    return executar_transformacao(
        montar_ranking_tribunais,
        caminho_saida or OUTPUT_DIR / "ranking_tribunais_paralelo.csv",
        base_dir=base_dir,
        paralelo=True,
        workers=workers,
    )


def filtrar_municipio_serial(municipio, base_dir=BASE_DIR, caminho_saida=None):
    return executar_transformacao(
        montar_filtro_municipio,
        caminho_saida or OUTPUT_DIR / f"{nome_arquivo_municipio(municipio)}.csv",
        base_dir=base_dir,
        municipio=municipio,
    )


def filtrar_municipio_paralelo(municipio, base_dir=BASE_DIR, caminho_saida=None, workers=None):
    return executar_transformacao(
        montar_filtro_municipio,
        caminho_saida or OUTPUT_DIR / f"{nome_arquivo_municipio(municipio)}.csv",
        base_dir=base_dir,
        paralelo=True,
        workers=workers,
        municipio=municipio,
    )


def medir_tempo(funcao):
    inicio = perf_counter()
    caminho_saida = funcao()
    fim = perf_counter()
    return caminho_saida, fim - inicio


def comparar_tempos(nome, funcao_serial, funcao_paralela):
    caminho_serial, tempo_serial = medir_tempo(funcao_serial)
    print(f"{nome} serial: {tempo_serial:.4f}s -> {caminho_serial}")

    caminho_paralelo, tempo_paralelo = medir_tempo(funcao_paralela)
    print(f"{nome} paralelo: {tempo_paralelo:.4f}s -> {caminho_paralelo}")

    speedup = tempo_serial / tempo_paralelo if tempo_paralelo else 0.0
    print(f"Speedup: {speedup:.4f}\n")

    return tempo_serial, tempo_paralelo, speedup


def pedir_municipio(municipio):
    municipio = (municipio or "").strip()
    while not municipio:
        municipio = input("Informe o municipio: ").strip()
    return municipio


def criar_operacao(acao, base_dir, output_dir, municipio, workers, separar_filtro=False):
    if acao == "concatenar":
        return (
            "Concatenar arquivos",
            lambda: concatenar_arquivos_serial(base_dir, output_dir / "base_concatenada_serial.csv"),
            lambda: concatenar_arquivos_paralelo(base_dir, output_dir / "base_concatenada_paralelo.csv", workers),
        )

    if acao == "resumo":
        return (
            "Resumo por municipio",
            lambda: gerar_resumo_municipios_serial(base_dir, output_dir / "resumo_municipios_serial.csv"),
            lambda: gerar_resumo_municipios_paralelo(base_dir, output_dir / "resumo_municipios_paralelo.csv", workers),
        )

    if acao == "ranking":
        return (
            "Ranking de tribunais",
            lambda: gerar_ranking_tribunais_serial(base_dir, output_dir / "ranking_tribunais_serial.csv"),
            lambda: gerar_ranking_tribunais_paralelo(base_dir, output_dir / "ranking_tribunais_paralelo.csv", workers),
        )

    municipio_arquivo = nome_arquivo_municipio(municipio)
    if separar_filtro:
        caminho_serial = output_dir / f"{municipio_arquivo}_serial.csv"
        caminho_paralelo = output_dir / f"{municipio_arquivo}_paralelo.csv"
    else:
        caminho_serial = output_dir / f"{municipio_arquivo}.csv"
        caminho_paralelo = output_dir / f"{municipio_arquivo}.csv"

    return (
        "Filtro por municipio",
        lambda: filtrar_municipio_serial(municipio, base_dir, caminho_serial),
        lambda: filtrar_municipio_paralelo(municipio, base_dir, caminho_paralelo, workers),
    )


def gerar_relatorio(base_dir=BASE_DIR, output_dir=OUTPUT_DIR, municipio="", workers=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    municipio = pedir_municipio(municipio)

    resultados = []
    for acao in ["concatenar", "resumo", "ranking", "filtrar"]:
        nome, funcao_serial, funcao_paralela = criar_operacao(
            acao,
            base_dir,
            output_dir,
            municipio,
            workers,
            separar_filtro=True,
        )
        resultados.append((nome, *comparar_tempos(nome, funcao_serial, funcao_paralela)))

    relatorio = pd.DataFrame(
        resultados,
        columns=["funcionalidade", "tempo_serial", "tempo_paralelo", "speedup"],
    )

    for coluna in ["tempo_serial", "tempo_paralelo", "speedup"]:
        relatorio[coluna] = relatorio[coluna].map(lambda valor: f"{valor:.6f}")

    caminho_relatorio = salvar_csv(relatorio, output_dir / "relatorio.csv")
    print(f"Relatorio gravado em: {caminho_relatorio}")


def executar_acao(acao, modo, base_dir, output_dir, municipio, workers):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if acao == "relatorio":
        gerar_relatorio(base_dir, output_dir, municipio, workers)
        return

    if acao == "filtrar":
        municipio = pedir_municipio(municipio)

    nome, funcao_serial, funcao_paralela = criar_operacao(
        acao,
        base_dir,
        output_dir,
        municipio,
        workers,
        separar_filtro=acao == "filtrar" and modo == "ambos",
    )

    if modo == "serial":
        caminho_saida, tempo = medir_tempo(funcao_serial)
        print(f"{nome} serial: {tempo:.4f}s -> {caminho_saida}")
        return

    if modo == "paralelo":
        caminho_saida, tempo = medir_tempo(funcao_paralela)
        print(f"{nome} paralelo: {tempo:.4f}s -> {caminho_saida}")
        return

    comparar_tempos(nome, funcao_serial, funcao_paralela)


def criar_parser():
    parser = argparse.ArgumentParser(description="TP01 - Manipulando arquivos CSV")
    parser.add_argument(
        "--acao",
        choices=["relatorio", "concatenar", "resumo", "ranking", "filtrar"],
        default="relatorio",
    )
    parser.add_argument(
        "--modo",
        choices=["serial", "paralelo", "ambos"],
        default="ambos",
    )
    parser.add_argument("--municipio", default="")
    parser.add_argument("--base-dir", default=str(BASE_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--workers", type=int, default=None)
    return parser


def main():
    args = criar_parser().parse_args()
    executar_acao(
        args.acao,
        args.modo,
        Path(args.base_dir),
        Path(args.output_dir),
        args.municipio,
        args.workers,
    )


if __name__ == "__main__":
    main()
