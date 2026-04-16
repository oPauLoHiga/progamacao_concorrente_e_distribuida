import argparse
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter
import pandas as pd

PASTA_BASE_PADRAO = Path(__file__).parent / "Base de Dados"
PASTA_SAIDA_PADRAO = Path(__file__).parent / "saida"
ENCODING_LEITURA = "utf-8-sig"

COLUNAS_SOMA = [
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

COLUNAS_METAS = ["Meta1", "Meta2A", "Meta2Ant", "Meta4A", "Meta4B"]


def listar_csvs(pasta_base):
    arquivos = sorted(Path(pasta_base).glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em: {pasta_base}")
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
    return pd.read_csv(caminho_csv, dtype=str, encoding=ENCODING_LEITURA)


def carregar_base(pasta_base=PASTA_BASE_PADRAO, paralelo=False, workers=None):
    arquivos = listar_csvs(pasta_base)

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

    for coluna in [coluna for coluna in COLUNAS_SOMA if coluna not in base]:
        base[coluna] = ""
    base[COLUNAS_SOMA] = base[COLUNAS_SOMA].apply(preparar_coluna_numerica)

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
            df["casos_novos_2026"] + df["dessobrestados_2026"] - df["suspensos_2026"],
            100,
        ),
        Meta2A=calcular_meta(
            df["julgm2_a"],
            df["distm2_a"] - df["suspm2_a"],
            1000 / 7,
        ),
        Meta2Ant=calcular_meta(
            df["julgm2_ant"],
            df["distm2_ant"] - df["suspm2_ant"] - df["desom2_ant"],
            100,
        ),
        Meta4A=calcular_meta(
            df["julgm4_a"],
            df["distm4_a"] - df["suspm4_a"],
            100,
        ),
        Meta4B=calcular_meta(
            df["julgm4_b"],
            df["distm4_b"] - df["suspm4_b"],
            100,
        ),
    )


def formatar_metas(df):
    df = df.copy()
    for coluna in COLUNAS_METAS:
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
        .groupby("municipio_oj", as_index=False)[COLUNAS_SOMA]
        .sum()
        .pipe(adicionar_metas)
        .rename(columns={"julgados_2026": "total_julgados_2026"})
        .sort_values("municipio_oj", key=lambda serie: serie.map(normalizar_texto))
        .reset_index(drop=True)
    )

    resumo["total_julgados_2026"] = resumo["total_julgados_2026"].round().astype(int)
    return formatar_metas(resumo[["municipio_oj", "total_julgados_2026", *COLUNAS_METAS]])


def montar_ranking_tribunais(df):
    ranking = (
        preparar_base(df)
        .groupby("sigla_tribunal", as_index=False)[COLUNAS_SOMA]
        .sum()
        .pipe(adicionar_metas)
        .sort_values(["Meta1", "sigla_tribunal"], ascending=[False, True])
        .head(10)
        .reset_index(drop=True)
    )

    return formatar_metas(ranking[["sigla_tribunal", *COLUNAS_METAS]])


def montar_filtro_municipio(df, municipio):
    if "municipio_oj" not in df:
        return df.iloc[0:0].copy()

    municipio_normalizado = normalizar_texto(municipio)
    filtro = df["municipio_oj"].fillna("").map(normalizar_texto) == municipio_normalizado
    return df.loc[filtro].reset_index(drop=True)


def agrupar_municipios(df):
    if "municipio_oj" not in df:
        return []

    base = df.copy()
    base["_municipio_arquivo"] = base["municipio_oj"].fillna("").map(nome_arquivo_municipio)

    grupos = []
    for nome_arquivo, grupo in base.groupby("_municipio_arquivo", sort=True):
        grupos.append((nome_arquivo, grupo.drop(columns=["_municipio_arquivo"]).reset_index(drop=True)))
    return grupos


def salvar_filtros_municipios(df, pasta_saida, paralelo=False, workers=None):
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    grupos = agrupar_municipios(df)

    def salvar_grupo(item):
        nome_arquivo, grupo = item
        salvar_csv(grupo, pasta_saida / f"{nome_arquivo}.csv")

    if paralelo:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            list(executor.map(salvar_grupo, grupos))
    else:
        for item in grupos:
            salvar_grupo(item)

    return pasta_saida


def gerar_arquivo(
    transformar,
    caminho_saida,
    pasta_base=PASTA_BASE_PADRAO,
    paralelo=False,
    workers=None,
    municipio=None,
):
    df = carregar_base(pasta_base, paralelo, workers)
    resultado = transformar(df) if municipio is None else transformar(df, municipio)
    caminho = salvar_csv(resultado, caminho_saida)
    return resultado, caminho


def concatenar_arquivos_serial(pasta_base=PASTA_BASE_PADRAO, caminho_saida=None):
    _, caminho = gerar_arquivo(
        montar_concatenacao,
        caminho_saida or PASTA_SAIDA_PADRAO / "base_concatenada_serial.csv",
        pasta_base=pasta_base,
    )
    return caminho


def concatenar_arquivos_paralelo(pasta_base=PASTA_BASE_PADRAO, caminho_saida=None, workers=None):
    _, caminho = gerar_arquivo(
        montar_concatenacao,
        caminho_saida or PASTA_SAIDA_PADRAO / "base_concatenada_paralelo.csv",
        pasta_base=pasta_base,
        paralelo=True,
        workers=workers,
    )
    return caminho


def gerar_resumo_municipios_serial(pasta_base=PASTA_BASE_PADRAO, caminho_saida=None):
    _, caminho = gerar_arquivo(
        montar_resumo_municipios,
        caminho_saida or PASTA_SAIDA_PADRAO / "resumo_municipios_serial.csv",
        pasta_base=pasta_base,
    )
    return caminho


def gerar_resumo_municipios_paralelo(pasta_base=PASTA_BASE_PADRAO, caminho_saida=None, workers=None):
    _, caminho = gerar_arquivo(
        montar_resumo_municipios,
        caminho_saida or PASTA_SAIDA_PADRAO / "resumo_municipios_paralelo.csv",
        pasta_base=pasta_base,
        paralelo=True,
        workers=workers,
    )
    return caminho


def gerar_ranking_tribunais_serial(pasta_base=PASTA_BASE_PADRAO, caminho_saida=None):
    _, caminho = gerar_arquivo(
        montar_ranking_tribunais,
        caminho_saida or PASTA_SAIDA_PADRAO / "ranking_tribunais_serial.csv",
        pasta_base=pasta_base,
    )
    return caminho


def gerar_ranking_tribunais_paralelo(pasta_base=PASTA_BASE_PADRAO, caminho_saida=None, workers=None):
    _, caminho = gerar_arquivo(
        montar_ranking_tribunais,
        caminho_saida or PASTA_SAIDA_PADRAO / "ranking_tribunais_paralelo.csv",
        pasta_base=pasta_base,
        paralelo=True,
        workers=workers,
    )
    return caminho


def filtrar_municipio_serial(municipio, pasta_base=PASTA_BASE_PADRAO, caminho_saida=None):
    resultado, caminho = gerar_arquivo(
        montar_filtro_municipio,
        caminho_saida or PASTA_SAIDA_PADRAO / f"{nome_arquivo_municipio(municipio)}.csv",
        pasta_base=pasta_base,
        municipio=municipio,
    )
    if resultado.empty:
        print("Nenhum registro encontrado para o municipio informado.")
    return caminho


def filtrar_municipio_paralelo(municipio, pasta_base=PASTA_BASE_PADRAO, caminho_saida=None, workers=None):
    resultado, caminho = gerar_arquivo(
        montar_filtro_municipio,
        caminho_saida or PASTA_SAIDA_PADRAO / f"{nome_arquivo_municipio(municipio)}.csv",
        pasta_base=pasta_base,
        paralelo=True,
        workers=workers,
        municipio=municipio,
    )
    if resultado.empty:
        print("Nenhum registro encontrado para o municipio informado.")
    return caminho


def gerar_filtros_municipios_serial(pasta_base=PASTA_BASE_PADRAO, pasta_saida=None):
    df = carregar_base(pasta_base, paralelo=False)
    return salvar_filtros_municipios(
        df,
        pasta_saida or PASTA_SAIDA_PADRAO / "filtros_municipios_serial",
        paralelo=False,
    )


def gerar_filtros_municipios_paralelo(pasta_base=PASTA_BASE_PADRAO, pasta_saida=None, workers=None):
    df = carregar_base(pasta_base, paralelo=True, workers=workers)
    return salvar_filtros_municipios(
        df,
        pasta_saida or PASTA_SAIDA_PADRAO / "filtros_municipios_paralelo",
        paralelo=True,
        workers=workers,
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


def criar_operacao(acao, pasta_base, pasta_saida, municipio, workers, separar_filtro=False):
    if acao == "concatenar":
        return (
            "Concatenar arquivos",
            lambda: concatenar_arquivos_serial(pasta_base, pasta_saida / "base_concatenada_serial.csv"),
            lambda: concatenar_arquivos_paralelo(pasta_base, pasta_saida / "base_concatenada_paralelo.csv", workers),
        )

    if acao == "resumo":
        return (
            "Resumo por municipio",
            lambda: gerar_resumo_municipios_serial(pasta_base, pasta_saida / "resumo_municipios_serial.csv"),
            lambda: gerar_resumo_municipios_paralelo(pasta_base, pasta_saida / "resumo_municipios_paralelo.csv", workers),
        )

    if acao == "ranking":
        return (
            "Resumo dos 10 tribunais",
            lambda: gerar_ranking_tribunais_serial(pasta_base, pasta_saida / "ranking_tribunais_serial.csv"),
            lambda: gerar_ranking_tribunais_paralelo(pasta_base, pasta_saida / "ranking_tribunais_paralelo.csv", workers),
        )

    municipio_arquivo = nome_arquivo_municipio(municipio)
    if separar_filtro:
        caminho_serial = pasta_saida / f"{municipio_arquivo}_serial.csv"
        caminho_paralelo = pasta_saida / f"{municipio_arquivo}_paralelo.csv"
    else:
        caminho_serial = pasta_saida / f"{municipio_arquivo}.csv"
        caminho_paralelo = pasta_saida / f"{municipio_arquivo}.csv"

    return (
        "Filtro por municipio",
        lambda: filtrar_municipio_serial(municipio, pasta_base, caminho_serial),
        lambda: filtrar_municipio_paralelo(municipio, pasta_base, caminho_paralelo, workers),
    )


def gerar_relatorio(pasta_base=PASTA_BASE_PADRAO, pasta_saida=PASTA_SAIDA_PADRAO, workers=None):
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    resultados = []
    for acao in ["concatenar", "resumo", "ranking"]:
        nome, funcao_serial, funcao_paralela = criar_operacao(acao, pasta_base, pasta_saida, "", workers)
        resultados.append((nome, *comparar_tempos(nome, funcao_serial, funcao_paralela)))

    resultados.append(
        (
            "Filtro por municipio",
            *comparar_tempos(
                "Filtro por municipio",
                lambda: gerar_filtros_municipios_serial(
                    pasta_base,
                    pasta_saida / "filtros_municipios_serial",
                ),
                lambda: gerar_filtros_municipios_paralelo(
                    pasta_base,
                    pasta_saida / "filtros_municipios_paralelo",
                    workers,
                ),
            ),
        )
    )

    relatorio = pd.DataFrame(
        resultados,
        columns=["funcionalidade", "tempo_serial", "tempo_paralelo", "speedup"],
    )

    for coluna in ["tempo_serial", "tempo_paralelo", "speedup"]:
        relatorio[coluna] = relatorio[coluna].map(lambda valor: f"{valor:.6f}")

    caminho_relatorio = salvar_csv(relatorio, pasta_saida / "relatorio.csv")
    print(f"Relatorio gravado em: {caminho_relatorio}")


def executar_acao(acao, modo, pasta_base, pasta_saida, municipio, workers):
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if acao == "relatorio":
        gerar_relatorio(pasta_base, pasta_saida, workers)
        return

    if acao == "filtrar":
        municipio = pedir_municipio(municipio)

    nome, funcao_serial, funcao_paralela = criar_operacao(
        acao,
        pasta_base,
        pasta_saida,
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


def menu_interativo(pasta_base, pasta_saida, workers):
    opcoes = {
        "1": "concatenar",
        "2": "resumo",
        "3": "ranking",
        "4": "filtrar",
        "5": "relatorio",
    }

    while True:
        print("\nTP01 - Manipulando arquivos CSV")
        print("Todas as opcoes executam a versao serial e a paralela, exibindo o speedup.")
        print("1 - Concatenar arquivos")
        print("2 - Gerar resumo por municipio")
        print("3 - Gerar resumo dos 10 tribunais com maior Meta1")
        print("4 - Filtrar municipio")
        print("5 - Gerar relatorio de tempos")
        print("0 - Sair")

        opcao = input("Escolha uma opcao: ").strip()
        if opcao == "0":
            break
        if opcao not in opcoes:
            print("Opcao invalida.")
            continue

        acao = opcoes[opcao]
        municipio = ""

        if acao == "filtrar":
            municipio = input("Municipio: ").strip()

        executar_acao(acao, "ambos", pasta_base, pasta_saida, municipio, workers)


def criar_parser():
    parser = argparse.ArgumentParser(description="TP01 - Manipulando arquivos CSV")
    parser.add_argument(
        "--acao",
        choices=["menu", "relatorio", "concatenar", "resumo", "ranking", "filtrar"],
        default="menu",
    )
    parser.add_argument(
        "--modo",
        choices=["serial", "paralelo", "ambos"],
        default="ambos",
    )
    parser.add_argument("--municipio", default="")
    parser.add_argument("--base-dir", default=str(PASTA_BASE_PADRAO))
    parser.add_argument("--output-dir", default=str(PASTA_SAIDA_PADRAO))
    parser.add_argument("--workers", type=int, default=None)
    return parser


def main():
    args = criar_parser().parse_args()
    pasta_base = Path(args.base_dir)
    pasta_saida = Path(args.output_dir)

    if args.acao == "menu":
        menu_interativo(pasta_base, pasta_saida, args.workers)
        return

    executar_acao(
        args.acao,
        args.modo,
        pasta_base,
        pasta_saida,
        args.municipio,
        args.workers,
    )

## Start
if __name__ == "__main__":
    main()