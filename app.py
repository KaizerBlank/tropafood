from datetime import datetime
from uuid import uuid4
from utilities.files import criar_entregadores
from shapely import wkt

import pandas as pd
from dash import Dash, Input, Output, State, html, dcc, no_update
from utilities.constants import (
    CSV_BARES,
    CSV_ENTREGADORES_CORRIGIDOS,
    CSV_ENTREGADORES_MATEMATICOS,
    DATA_DIR,
    DESVIO_PADRAO_METROS,
)
from src.grafo import obter_malha
from src.simulador import corrigir_para_ruas, gerar_entregadores_normais
from src.frota import Frota
from utilities.interface import plota_mapa_interface, montar_tabela_rotas

df_bares = pd.read_csv(CSV_BARES).dropna(
    subset=["GEOMETRIA", "LATITUDE", "LONGITUDE"]
).reset_index(drop=True)
df_entregadores = pd.DataFrame()

fig = plota_mapa_interface(df_entregadores, df_bares)

app = Dash()

app.layout = html.Div([
    dcc.Store(
        id="dados-entregadores",
        data=[],
        storage_type="memory",
    ),

    html.H1(children='TP1 - ALG2', style={'textAlign':'center'}),
    dcc.Dropdown(
        id="busca-restaurante",
        options=[
            {"label": str(bar.get("NOME", "Restaurante")), "value": indice}
            for indice, bar in df_bares.iterrows()
        ],
        placeholder="Buscar restaurante pelo nome",
        clearable=True,
        searchable=True,
        style={"maxWidth": "520px", "margin": "0 auto 12px"},
    ),
    html.P("Quantidade de entregadores", style={'textAlign':'center'}),
    html.Div([
        dcc.Input(
            id="quantidade-entregadores",
            type="number",
            min=1,
            step=1,
            value=100,
        ),
        html.Button("Gerar entregadores", id="gerar-entregadores", n_clicks=0),
        dcc.Checklist(
            id="salvar-csv",
            options=[{"label": "Salvar CSVs desta geração", "value": "salvar"}],
            value=[],
        ),
    ], style={"display": "flex", "justifyContent": "center", "gap": "8px"}),
    html.P(id="mensagem-geracao", style={"textAlign": "center"}),
    dcc.Graph(id="mapa-entregadores", figure=fig),

    html.H2("Rotas até o restaurante"),
    html.P("Tempo estimado sem considerar transito ou paradas."),
    html.Div(
        "Selecione um restaurante para consultar os entregadores gerados.",
        id="tabela-rotas",
        style={"overflowX": "auto"}
    )
])


@app.callback(
    Output("dados-entregadores", "data"),
    Output("mensagem-geracao", "children"),
    Input("gerar-entregadores", "n_clicks"),
    State("quantidade-entregadores", "value"),
    State("salvar-csv", "value"),
    State("busca-restaurante", "value"),
    prevent_initial_call=True,
)
def atualizar_mapa(
    n_clicks,
    quantidade_entregadores,
    salvar_csv=None,
    restaurante_indice=None,
):
    if quantidade_entregadores is None or quantidade_entregadores < 1 or not float(quantidade_entregadores).is_integer():
        return no_update, "Informe uma quantidade_entregadores inteira maior que zero."
    if restaurante_indice is not None and not 0 <= int(restaurante_indice) < len(df_bares):
        return no_update, "Restaurante não encontrado."

    try:
        df_entregadores_matematicos = gerar_entregadores_normais(
            df_bares,
            N_entregadores=int(quantidade_entregadores),
            desvio_padrao_metros=DESVIO_PADRAO_METROS,
        )
        grafo = obter_malha()
        df_entregadores = corrigir_para_ruas(df_entregadores_matematicos, grafo)
        registros = df_entregadores.to_dict(orient="records")
        entregadores = criar_entregadores(registros)
        frota = Frota(entregadores)

        df_entregadores["geohash"] = [
            entregador.geohash
            for entregador in frota.entregadores
        ]

        mensagem = f"{len(frota.entregadores)} entregadores gerados e indexados na Trie."
        if "salvar" in (salvar_csv or []):
            entregadores_matematico, entregadores_corrigido = salvar_csvs_entregadores(
                df_entregadores_matematicos, df_entregadores
            )
            mensagem += f" CSVs salvos: {entregadores_matematico.name} e {entregadores_corrigido.name}."
    except Exception as erro:
        return no_update, f"Não foi possível gerar os entregadores: {erro}"

    return df_entregadores.to_dict(orient="records"), mensagem

@app.callback(
        Output("mapa-entregadores", "figure"),
        Input("dados-entregadores", "data"),
        Input("busca-restaurante", "value"),
)
def atualizar_visualizacao_mapa(registros, restaurante_indice):
    return plota_mapa_interface(
        pd.DataFrame(registros or []),
        df_bares,
        indice_restaurante_selecionado=(
            int(restaurante_indice)
            if restaurante_indice is not None
            else None
        ),
    )

@app.callback(
    Output("tabela-rotas", "children"),
    Input("dados-entregadores", "data"),
    Input("busca-restaurante", "value"),
)
def atualizar_tabela_rotas(registros, restaurante_indice):
    if restaurante_indice is None:
        return html.P("Selecione um restaurante para consultar as rotas.")

    if not registros:
        return html.P("Gere os entregadores antes de consultar as rotas.")

    try:
        restaurante = df_bares.iloc[int(restaurante_indice)]
        ponto = wkt.loads(restaurante["GEOMETRIA"])

        grafo = obter_malha()
        frota = Frota(criar_entregadores(registros))
        selecionados = frota.entregadores

        resultados = frota.calcular_rotas(
            grafo,
            ponto.x,
            ponto.y,
            selecionados,
        )

        return html.Div([
            html.P(f"Exibindo todos os {len(resultados)} entregadores gerados."),
            montar_tabela_rotas(resultados),
        ])
    except Exception as erro:
        return html.P(f"Não foi possível consultar as rotas: {erro}")


def salvar_csvs_entregadores(df_matematicos, df_corrigidos):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    identificador = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    entregadores_matematico = CSV_ENTREGADORES_MATEMATICOS.with_name(
        f"{CSV_ENTREGADORES_MATEMATICOS.stem}_{identificador}.csv"
    )
    entregadores_corrigido = CSV_ENTREGADORES_CORRIGIDOS.with_name(
        f"{CSV_ENTREGADORES_CORRIGIDOS.stem}_{identificador}.csv"
    )

    df_matematicos.to_csv(entregadores_matematico, index=False, mode="x")
    df_corrigidos.to_csv(entregadores_corrigido, index=False, mode="x")
    return entregadores_matematico, entregadores_corrigido


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)