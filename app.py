from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

try:
    df_entregadores = pd.read_csv("data/entregadores_corrigidos.csv")
    df_bares = pd.read_csv("data/30_bares.csv").dropna(subset=["LATITUDE", "LONGITUDE"])
except Exception as e:
    print(f"Erro db!")
    df_entregadores = pd.DataFrame()
    df_bares = pd.DataFrame()

if not df_entregadores.empty and not df_bares.empty:
    df_bares["status"] = "Restaurante"
    df_bares["nome_exibicao"] = df_bares.get("NOME", "Bar")
    df_bares["lat"] = df_bares["LATITUDE"]
    df_bares["lon"] = df_bares["LONGITUDE"]

    df_entregadores["status"] = df_entregadores["filtrado"].map({
        True: "Entregador Filtrato dentro do raio x",
        False: "Entregador Fora do raio x"
    })
    df_entregadores["status"] = "Entregador"
    df_entregadores["nome_exibicao"] = df_entregadores["id_entregador"]
    df_entregadores["lat"] = df_entregadores["latitude_rua_graus"]
    df_entregadores["lon"] = df_entregadores["longitude_rua_graus"]

    df_mapa = pd.concat([
        df_bares[["status", "nome_exibicao", "lat", "lon"]],
        df_entregadores[["status", "nome_exibicao", "lat", "lon"]]
    ], ignore_index=True)

    lat_centro = df_bares["LATITUDE"].mean()
    lon_centro = df_bares["LONGITUDE"].mean()

    cores_status = {
        "ntregador Filtrato dentro do raio x": "red",
        "Entregador Fora do raio x": "gray",
        "Restaurante": "blue"
    }

    fig = px.scatter_map(
        df_mapa,
        lat="lat",
        lon="lon",
        color="status",
        hover_name="nome_exibicao",
        zoom=12,
        height=650,
        title="Mapa",
        map_style="basic"
    )

    fig.update_layout(
        map={
            "center": {"lat": lat_centro, "lon": lon_centro},
        },
        margin={"r":0, "t":40, "l":0, "b":0}
    )

else:
    fig = px.scatter_map(title="No data")

app = Dash()

app.layout = [
    html.H1(children='TP1 - ALG2', style={'textAlign':'center'}),
    html.P("MAPA", style={'textAlign':'center'}),
    
    dcc.Graph(figure=fig)
]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)