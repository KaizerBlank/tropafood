from datetime import datetime
from uuid import uuid4
from utilities.files import criar_entregadores

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
from utilities.interface import plota_mapa_interface

df_bares = pd.read_csv(CSV_BARES).dropna(
    subset=["GEOMETRIA", "LATITUDE", "LONGITUDE"]
).reset_index(drop=True)
df_entregadores = pd.DataFrame()

fig = plota_mapa_interface(df_entregadores, df_bares)

app = Dash()

app.layout = html.Div([
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
            id="raio-busca", type="number", min=100, max=50000,
            step=100, value=1000, debounce=True, className="campo-numero",
        ),
        dcc.Checklist(
            id="exibir-raio",
            options=[{"label": "Exibir raio de busca", "value": "exibir"}],
            value=[], className="opcoes",
        ),
        dcc.Checklist(
            id="exibir-restaurantes",
            options=[{"label": "Exibir todos os restaurantes", "value": "exibir"}],
            value=[], className="opcoes",
        ),
        html.P(id="resumo-busca", role="status"),
        html.Div([
            html.H2("Entregadores"),
            html.Label("Quantidade", htmlFor="quantidade-entregadores"),
            dcc.Input(
                id="quantidade-entregadores", type="number", min=1,
                step=1, value=100, className="campo-numero",
            ),
            dcc.Checklist(
                id="salvar-csv",
                options=[{"label": "Salvar CSVs desta geração", "value": "salvar"}],
                value=[], className="opcoes",
            ),
            html.Button("Gerar entregadores", id="gerar-entregadores", n_clicks=0),
            html.P(id="mensagem-geracao", role="status", className="mensagem"),
        ], className="geracao"),
    ], className="painel", **{"aria-label": "Busca e entregadores"}),
])


@app.callback(
    Output("camadas-mapa", "children"),
    Output("resumo-busca", "children"),
    Input("dados-entregadores", "data"),
    Input("busca-restaurante", "value"),
    Input("raio-busca", "value"),
    Input("exibir-raio", "value"),
    Input("exibir-restaurantes", "value"),
)
def atualizar_busca(entregadores, restaurante_indice, raio, exibir_raio, exibir_restaurantes):
    if raio is None or not 100 <= raio <= 50000:
        return no_update, "Raio não aceito. Use de 100 a 50.000 metros."
    camadas = plota_mapa_interface(
        pd.DataFrame(entregadores), df_bares,
        indice_restaurante_selecionado=restaurante_indice,
        raio_metros=raio,
        exibir_raio="exibir" in (exibir_raio or []),
        exibir_restaurantes="exibir" in (exibir_restaurantes or []),
    )
    quantidade = len(entregadores or [])
    resumo = f"{quantidade} entregadores no mapa."
    return camadas, resumo


@app.callback(
    Output("mapa-entregadores", "center"),
    Output("mapa-entregadores", "zoom"),
    Input("busca-restaurante", "value"),
    prevent_initial_call=True,
)
def centralizar_restaurante(restaurante_indice):
    if restaurante_indice is None:
        return CENTRO_INICIAL, 12
    restaurante = df_bares.iloc[int(restaurante_indice)]
    return [restaurante["LATITUDE"], restaurante["LONGITUDE"]], 15


@app.callback(
    Output("dados-entregadores", "data"),
    Output("mensagem-geracao", "children"),
    Input("gerar-entregadores", "n_clicks"),
    State("quantidade-entregadores", "value"),
    State("salvar-csv", "value"),
    State("busca-restaurante", "value"),
    prevent_initial_call=True,
    running=[(Output("gerar-entregadores", "disabled"), True, False)],
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

        figura = plota_mapa_interface(
            df_entregadores,
            df_bares,
            indice_restaurante_selecionado=(
                int(restaurante_indice)
                if restaurante_indice is not None
                else None
            ),
        )

        mensagem = f"{len(frota.entregadores)} entregadores gerados e indexados na Trie."
        if "salvar" in (salvar_csv or []):
            entregadores_matematico, entregadores_corrigido = salvar_csvs_entregadores(
                df_entregadores_matematicos, df_entregadores
            )
            mensagem += f" CSVs salvos: {entregadores_matematico.name} e {entregadores_corrigido.name}."
    except Exception:
        return no_update, "Não foi possível gerar os entregadores."

    return df_entregadores.to_dict("records"), mensagem


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