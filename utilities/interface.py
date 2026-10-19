import pandas as pd
import plotly.express as px

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

    if not df_entregadores.empty:
        df_entregadores = df_entregadores.copy()
        df_entregadores["status"] = df_entregadores["filtrado"].map({
            True: "Entregador Filtrado dentro do raio",
            False: "Entregador Fora do raio"
        })
        
        df_entregadores["nome_exibicao"] = df_entregadores["id_entregador"]
        df_entregadores["lat"] = df_entregadores["latitude_rua_graus"]
        df_entregadores["lon"] = df_entregadores["longitude_rua_graus"]
        partes_mapa.append(df_entregadores[["status", "nome_exibicao", "lat", "lon"]])

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

        fig.update_layout(
            map={
                "center": {"lat": lat_centro, "lon": lon_centro},
            },
            margin={"r":0, "t":40, "l":0, "b":0}
        )
        if indice_restaurante_selecionado is not None:
            fig.update_traces(
                marker={"size": 24},
                selector={"name": "Restaurante selecionado"},
            )

    else:
        fig = px.scatter_map(title="Sem dados para exibir no mapa")

    return fig