import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html
from osmnx.distance import great_circle

def filtrar_entregadores_por_raio(df_entregadores, restaurante, raio_metros):
    if df_entregadores.empty:
        return df_entregadores

    distancias = great_circle(
        restaurante["LATITUDE"],
        restaurante["LONGITUDE"],
        df_entregadores["latitude_rua_graus"].to_numpy(),
        df_entregadores["longitude_rua_graus"].to_numpy(),
    )
    return df_entregadores.loc[distancias <= raio_metros]

def gerar_circulo(lat, lon, raio_metros, pontos=50):
    r_terra = 6371000.0
    angulos = np.linspace(0, 2 * np.pi, pontos)

    d_lat = (raio_metros / r_terra) * (180.0 / np.pi)
    d_lon = (raio_metros / (r_terra * np.cos(np.radians(lat)))) * (180.0 / np.pi)

    return lat + d_lat * np.sin(angulos), lon + d_lon * np.cos(angulos)

def plota_mapa_interface(
    df_entregadores,
    df_bares,
    indice_restaurante_selecionado=None,
    raio_metros=1000,
    exibir_raio=False,
    exibir_restaurantes=False,
):
    fig = go.Figure()

    restaurante = None
    if (
        indice_restaurante_selecionado is not None
        and not df_bares.empty
        and int(indice_restaurante_selecionado) < len(df_bares)
    ):
        restaurante = df_bares.iloc[int(indice_restaurante_selecionado)]

    # 1. Entregadores (com cor dinâmica)
    if not df_entregadores.empty:
        if restaurante is not None:
            no_raio = filtrar_entregadores_por_raio(
                df_entregadores, restaurante, raio_metros
            )
            cores = np.where(
                df_entregadores.index.isin(no_raio.index), "green", "red"
            )
        else:
            cores = "red"

        fig.add_trace(
            go.Scattermap(
                lat=df_entregadores["latitude_rua_graus"],
                lon=df_entregadores["longitude_rua_graus"],
                mode="markers",
                marker=dict(size=6, color=cores, opacity=0.7),
                text=df_entregadores["id_entregador"],
                hoverinfo="text",
                name="Entregadores",
            )
        )

    if exibir_restaurantes and not df_bares.empty:
        outros = df_bares
        if restaurante is not None:
            outros = df_bares.drop(index=int(indice_restaurante_selecionado))

        fig.add_trace(
            go.Scattermap(
                lat=outros["LATITUDE"],
                lon=outros["LONGITUDE"],
                mode="markers",
                marker=dict(size=7, color="blue"),
                text=outros.get("NOME", "Restaurante"),
                hoverinfo="text",
                name="Restaurantes",
            )
        )

    if restaurante is not None:
        lat_res = restaurante["LATITUDE"]
        lon_res = restaurante["LONGITUDE"]

        if exibir_raio:
            lats_c, lons_c = gerar_circulo(lat_res, lon_res, raio_metros)
            fig.add_trace(
                go.Scattermap(
                    lat=lats_c,
                    lon=lons_c,
                    mode="lines",
                    fill="toself",
                    fillcolor="rgba(0, 100, 255, 0.15)",
                    line=dict(color="blue", width=1),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig.add_trace(
            go.Scattermap(
                lat=[lat_res],
                lon=[lon_res],
                mode="markers",
                marker=dict(size=12, color="orange"),
                text=[str(restaurante.get("NOME", "Restaurante"))],
                hoverinfo="text",
                name="Selecionado",
            )
        )
        centro = dict(lat=lat_res, lon=lon_res)
        zoom = 14
    else:
        lat_c = df_bares["LATITUDE"].mean() if not df_bares.empty else -19.92
        lon_c = df_bares["LONGITUDE"].mean() if not df_bares.empty else -43.94
        centro = dict(lat=lat_c, lon=lon_c)
        zoom = 12

    fig.update_layout(
        map=dict(
            style="basic",
            center=centro,
            zoom=zoom,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        uirevision=str(indice_restaurante_selecionado),
    )

    return fig

def montar_tabela_rotas(resultados):
    if not resultados:
        return html.P("Nenhum entregador para exibir nesta consulta.")

    linhas = []
    for r in resultados:
        dist = (
            f"{r['distancia_metros']:.1f}"
            if r["distancia_metros"] is not None
            else "Sem rota"
        )
        tempo = (
            f"{r['tempo_segundos'] / 60:.2f}"
            if r["tempo_segundos"] is not None
            else "Sem rota"
        )

        linhas.append(
            html.Tr([
                html.Td(r["id_entregador"]),
                html.Td(f"{r['latitude']:.6f}"),
                html.Td(f"{r['longitude']:.6f}"),
                html.Td(dist),
                html.Td(tempo),
            ])
        )

    return html.Table([
        html.Thead(
            html.Tr([
                html.Th("ID"),
                html.Th("Latitude"),
                html.Th("Longitude"),
                html.Th("Distância (m)"),
                html.Th("Tempo (min)"),
            ])
        ),
        html.Tbody(linhas),
    ])