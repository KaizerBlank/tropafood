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

def plota_mapa_interface(df_entregadores, df_bares, indice_restaurante_selecionado=None):
    partes_mapa = []

    if not df_bares.empty:
        df_bares = df_bares.copy()
        df_bares["status"] = "Restaurante"
        if indice_restaurante_selecionado is not None:
            df_bares.loc[indice_restaurante_selecionado, "status"] = "Restaurante selecionado"
        df_bares["nome_exibicao"] = df_bares.get("NOME", "Bar")
        df_bares["lat"] = df_bares["LATITUDE"]
        df_bares["lon"] = df_bares["LONGITUDE"]
        partes_mapa.append(df_bares[["status", "nome_exibicao", "lat", "lon"]])

def plota_mapa_interface(
    df_entregadores, df_bares, indice_restaurante_selecionado=None,
    raio_metros=1000, exibir_raio=False, exibir_restaurantes=False,
):
    restaurante = None
    if indice_restaurante_selecionado is not None:
        restaurante = df_bares.iloc[int(indice_restaurante_selecionado)]

    if partes_mapa:
        df_mapa = pd.concat(partes_mapa, ignore_index=True)

        if indice_restaurante_selecionado is not None and not df_bares.empty:
            restaurante_selecionado = df_bares.iloc[indice_restaurante_selecionado]
            lat_centro = restaurante_selecionado["LATITUDE"]
            lon_centro = restaurante_selecionado["LONGITUDE"]
        elif not df_bares.empty:
            lat_centro = df_bares["LATITUDE"].mean()
            lon_centro = df_bares["LONGITUDE"].mean()
        else:
            lat_centro = df_entregadores["latitude_rua_graus"].mean()
            lon_centro = df_entregadores["longitude_rua_graus"].mean()

        cores_status = {
            "Entregador Filtrado dentro do raio": "red",
            "Entregador Fora do raio": "gray",
            "Restaurante": "blue",
            "Restaurante selecionado": "green",
        }

        fig = px.scatter_map(
            df_mapa,
            lat="lat",
            lon="lon",
            color="status",
            color_discrete_map=cores_status,
            hover_name="nome_exibicao",
            zoom=15 if indice_restaurante_selecionado is not None else 12,
            height=650,
            title="Mapa de Bares e Entregadores",
            map_style="basic"
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
        if indice_restaurante_selecionado is not None:
            fig.update_traces(
                marker={"size": 24},
                selector={"name": "Restaurante selecionado"},
            )

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