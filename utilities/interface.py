import pandas as pd
from dash import html
import dash_leaflet as dl
from osmnx.distance import great_circle

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

    if restaurante is not None:
        entregadores_no_raio = filtrar_entregadores_por_raio(df_entregadores, restaurante, raio_metros)
        dentro = df_entregadores.index.isin(entregadores_no_raio.index)
        df_entregadores = df_entregadores.assign(
            cor="green" if len(dentro) > 0 else "#dc3545", # fallback
            opacidade=0.8
        )
        df_entregadores["cor"] = "green"
        df_entregadores["cor"] = df_entregadores["cor"].where(dentro, "#dc3545")
        df_entregadores["opacidade"] = 0.8
        df_entregadores["opacidade"] = df_entregadores["opacidade"].where(dentro, 0.75)
    else:
        df_entregadores = df_entregadores.assign(cor="red", opacidade=0.8)

    marcadores = []
    for entregador in df_entregadores.to_dict("records"):
        marcador = dl.CircleMarker(
            center=[entregador["latitude_rua_graus"], entregador["longitude_rua_graus"]],
            radius=7, color=entregador["cor"], fillColor=entregador["cor"], weight=1,
            opacity=entregador["opacidade"], fillOpacity=entregador["opacidade"],
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


def montar_tabela_rotas(resultados):
    if not resultados:
        return html.P("Nenhum entregador para exibir nesta consulta.")

    linhas = []

    for resultado in resultados:
        distancia = resultado["distancia_metros"]
        tempo = resultado["tempo_segundos"]

        linhas.append(html.Tr([
            html.Td(resultado["id_entregador"]),
            html.Td(f'{resultado["latitude"]:.6f}'),
            html.Td(f'{resultado["longitude"]:.6f}'),
            html.Td(
                "Sem rota"
                if distancia is None
                else f"{distancia:.1f}"
            ),
            html.Td(
                "Sem rota"
                if tempo is None
                else f"{tempo / 60:.2f}"
            ),
        ]))

    return html.Table([
        html.Thead(html.Tr([
            html.Th("ID"),
            html.Th("Latitude"),
            html.Th("Longitude"),
            html.Th("Distância pelas ruas (m)"),
            html.Th("Tempo estimado (min)"),
        ])),
        html.Tbody(linhas),
    ], style={
        "width": "100%",
        "textAlign": "left",
        "borderCollapse": "collapse",
    })
