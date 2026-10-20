import pandas as pd
import dash_leaflet as dl
from osmnx.distance import great_circle

def carrega_entregadores_corrigidos():
    try:
        df_entregadores = pd.read_csv("data/entregadores_corrigidos.csv")
        df_bares = pd.read_csv("data/bares.csv").dropna(subset=["LATITUDE", "LONGITUDE"])
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        df_entregadores = pd.DataFrame()
        df_bares = pd.DataFrame()

    return df_entregadores, df_bares

def filtrar_entregadores_por_raio(df_entregadores, restaurante, raio_metros):
    if df_entregadores.empty:
        return df_entregadores

    distancias = great_circle(
        restaurante["LATITUDE"], restaurante["LONGITUDE"],
        df_entregadores["latitude_rua_graus"].to_numpy(),
        df_entregadores["longitude_rua_graus"].to_numpy(),
    )
    return df_entregadores.loc[distancias <= raio_metros]

def plota_mapa_interface(
    df_entregadores, df_bares, indice_restaurante_selecionado=None,
    raio_metros=1000, exibir_raio=False, exibir_restaurantes=False,
):
    restaurante = None
    if indice_restaurante_selecionado is not None:
        restaurante = df_bares.iloc[int(indice_restaurante_selecionado)]

    df_entregadores = df_entregadores.assign(dentro_raio=False)
    if restaurante is not None:
        entregadores_no_raio = filtrar_entregadores_por_raio(
            df_entregadores, restaurante, raio_metros
        )
        df_entregadores["dentro_raio"] = df_entregadores.index.isin(entregadores_no_raio.index)

    marcadores = []
    for entregador in df_entregadores.to_dict("records"):
        cor = "red"
        opacidade = 0.8
        if restaurante is not None:
            cor = "green" if entregador["dentro_raio"] else "#dc3545"
            opacidade = 0.8 if entregador["dentro_raio"] else 0.75
        marcador = dl.CircleMarker(
            center=[entregador["latitude_rua_graus"], entregador["longitude_rua_graus"]],
            radius=7, color=cor, fillColor=cor, weight=1,
            opacity=opacidade, fillOpacity=opacidade,
            children=dl.Tooltip(str(entregador["id_entregador"])),
        )
        marcadores.append(marcador)

    if exibir_restaurantes:
        for indice, bar in df_bares.iterrows():
            if indice == indice_restaurante_selecionado:
                continue
            marcador = dl.CircleMarker(
                center=[bar["LATITUDE"], bar["LONGITUDE"]], radius=5,
                children=dl.Tooltip(str(bar.get("NOME", "Restaurante"))),
            )
            marcadores.append(marcador)

    if restaurante is not None:
        centro = [restaurante["LATITUDE"], restaurante["LONGITUDE"]]
        if exibir_raio:
            marcadores.append(dl.Circle(
                center=centro, radius=raio_metros, weight=1,
                fillOpacity=0.1, interactive=False,
            ))
        marcadores.append(dl.Marker(
            position=centro,
            children=dl.Tooltip(str(restaurante.get("NOME", "Restaurante"))),
        ))
    return marcadores