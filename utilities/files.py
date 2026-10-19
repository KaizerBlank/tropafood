import csv
from pathlib import Path
from entities.entregador import Entregador
from entities.restaurante import Restaurante

def ler_entregadores() -> list[Entregador]:
    arquivo = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "entregadores_corrigidos.csv"
    )

    entregadores = []

    with arquivo.open(
        mode="r",
        encoding="utf-8",
        newline=""
    ) as file:
        dados_csv = csv.DictReader(file)

        for linha in dados_csv:
            entregador = Entregador(
                id_Entregador=linha["id_entregador"],
                latitude=float(linha["latitude_rua_graus"]),
                longitude=float(linha["longitude_rua_graus"]),
                x=float(linha["x_rua_metros"]),
                y=float(linha["y_rua_metros"]),
            )

            entregadores.append(entregador)

    return entregadores

def ler_bares()->list[Restaurante]:
    arquivo = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "bares.csv"
    )
    restaurantes = []

    with arquivo.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        restaurantes_csv = csv.DictReader(file)

        for linha in restaurantes_csv:
            restaurante = Restaurante(
                id_restaurante=linha["_id"],
                nome=linha["NOME"],
                latitude=float(linha["LATITUDE"]),
                longitude=float(linha["LONGITUDE"]),
                desc_logradouro=linha["DESC_LOGRADOURO"],
                nome_logradouro=linha["NOME_LOGRADOURO"],
                numero=linha["NUMERO_IMOVEL"],
                complemento=linha["COMPLEMENTO"],
                nome_bairro=linha["NOME_BAIRRO"]
            )
            restaurantes.append(restaurante)
    
    return restaurantes