from datetime import datetime
from uuid import uuid4

import pandas as pd
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from shapely import wkt
from src.frota import Frota
from src.grafo import obter_malha
from src.simulador import corrigir_para_ruas, gerar_entregadores_normais
from utilities.constants import (
    CSV_BARES,
    CSV_ENTREGADORES_CORRIGIDOS,
    CSV_ENTREGADORES_MATEMATICOS,
    DATA_DIR,
    DESVIO_PADRAO_METROS,
)
from utilities.files import criar_entregadores
from utilities.indice import obter_trie_entregadores
from utilities.interface import (
    filtrar_entregadores_por_raio,
    montar_tabela_rotas,
    plota_mapa_interface,
)

# Carrega os bares
df_bares = pd.read_csv(CSV_BARES).dropna(
    subset=["GEOMETRIA", "LATITUDE", "LONGITUDE"]
)
df_bares = df_bares.reset_index(drop=True)

app = Dash()
app.title = "Tropafood"

app.layout = html.Main([
    dcc.Store(id="dados-entregadores", data=[]),
    dcc.Store(id="geracao-entregadores", data=None),
    dcc.Graph(
        id="mapa-entregadores",
        figure=plota_mapa_interface(pd.DataFrame(), df_bares),
        config={"scrollZoom": True},
        className="mapa",
        style={"height": "100vh", "width": "100%"},
    ),
    html.Section(
        [
            html.Header(
                [
                    html.H1("Tropafood"),
                    html.P("Belo Horizonte", className="localidade"),
                ],
                className="cabecalho",
            ),
            html.Label("Restaurante"),
            dcc.Dropdown(
                id="busca-restaurante",
                options=[
                    {
                        "label": str(bar.get("NOME", "Restaurante")),
                        "value": idx,
                    }
                    for idx, bar in df_bares.iterrows()
                ],
                placeholder="Buscar restaurante pelo nome",
                clearable=True,
            ),
            html.Label("Raio de busca (metros)"),
            dcc.Input(
                id="raio-busca",
                type="number",
                min=100,
                max=50000,
                step=100,
                value=1000,
                debounce=True,
                className="campo-numero",
            ),
            dcc.Checklist(
                id="exibir-raio",
                options=[{"label": "Exibir raio de busca", "value": "exibir"}],
                value=["exibir"],
                className="opcoes",
            ),
            dcc.Checklist(
                id="exibir-restaurantes",
                options=[
                    {"label": "Exibir todos os restaurantes", "value": "exibir"}
                ],
                value=[],
                className="opcoes",
            ),
            html.P(id="resumo-busca"),
            html.Div(
                [
                    html.H2("Entregadores"),
                    html.Label("Quantidade"),
                    dcc.Input(
                        id="quantidade-entregadores",
                        type="number",
                        min=1,
                        step=1,
                        value=5000,
                        className="campo-numero",
                    ),
                    dcc.Checklist(
                        id="salvar-csv",
                        options=[
                            {
                                "label": "Salvar CSVs desta geração",
                                "value": "salvar",
                            }
                        ],
                        value=[],
                        className="opcoes",
                    ),
                    html.Button(
                        "Gerar entregadores",
                        id="gerar-entregadores",
                        n_clicks=0,
                    ),
                    html.P(id="mensagem-geracao", className="mensagem"),
                ],
                className="geracao",
            ),
            html.Button(
                "Mostrar tabela",
                id="mostrar-tabela",
                n_clicks=0,
            ),
        ],
        className="painel",
        **{"aria-label": "Busca e entregadores"},
    ),

    html.Section([
        html.Div([
            html.H2("Rotas até o restaurante"),
            html.Button(
                "Fechar",
                id="fechar-tabela",
                n_clicks=0,
            ),
        ], className="cabecalho-tabela"),

        html.P("Tempo estimado sem considerar trânsito ou paradas."),

        dcc.Loading(
            html.Div(
                "Selecione um restaurante para consultar os entregadores gerados.",
                id="tabela-rotas",
                className="conteudo-tabela",
            ),
        ),
    ],
        id="painel-tabela",
        className="painel-tabela",
        hidden=True,
        **{"aria-label": "Tabela de rotas dos entregadores"},
    ),
])

@app.callback(
    Output("painel-tabela", "hidden"),
    Input("mostrar-tabela", "n_clicks"),
    Input("fechar-tabela", "n_clicks"),
    prevent_initial_call=True,
)
def controlar_tabela(cliques_mostrar, cliques_fechar):
    return ctx.triggered_id == "fechar-tabela"


@app.callback(
    Output("mapa-entregadores", "figure"),
    Output("resumo-busca", "children"),
    Input("dados-entregadores", "data"),
    Input("busca-restaurante", "value"),
    Input("raio-busca", "value"),
    Input("exibir-raio", "value"),
    Input("exibir-restaurantes", "value"),
    Input("geracao-entregadores", "data"),
)
def atualizar_busca(
    entregadores, restaurante_indice, raio, exibir_raio, exibir_restaurantes, geracao
):
    if raio is None or not 100 <= raio <= 50000:
        return no_update, "Raio não aceito. Use de 100 a 50.000 metros."

    df_entregadores = pd.DataFrame(entregadores or [])
    trie = (
        obter_trie_entregadores(geracao, entregadores)
        if entregadores else None
    )

    figura = plota_mapa_interface(
        df_entregadores,
        df_bares,
        indice_restaurante_selecionado=restaurante_indice,
        raio_metros=raio,
        exibir_raio="exibir" in (exibir_raio or []),
        exibir_restaurantes="exibir" in (exibir_restaurantes or []),
        trie=trie,
    )

    total = len(df_entregadores)
    if restaurante_indice is None:
        return figura, f"{total} entregadores no mapa."

    restaurante = df_bares.iloc[int(restaurante_indice)]
    selecionados = filtrar_entregadores_por_raio(
        df_entregadores, restaurante, raio, trie
    )
    return figura, f"{len(selecionados)} de {total} entregadores dentro do raio."

@app.callback(
    Output("dados-entregadores", "data"),
    Output("mensagem-geracao", "children"),
    Output("geracao-entregadores", "data"),
    Input("gerar-entregadores", "n_clicks"),
    State("quantidade-entregadores", "value"),
    State("salvar-csv", "value"),
    prevent_initial_call=True,
    running=[(Output("gerar-entregadores", "disabled"), True, False)],
)
def atualizar_mapa(n_clicks, quantidade, salvar_csv):
    if quantidade is None or quantidade < 1 or not float(quantidade).is_integer():
        return no_update, "Quantidade não aceita. Use um inteiro maior que zero.", no_update

    try:
        df_mat = gerar_entregadores_normais(
            df_bares,
            N_entregadores=int(quantidade),
            desvio_padrao_metros=DESVIO_PADRAO_METROS,
        )

        grafo = obter_malha()
        df_corr = corrigir_para_ruas(df_mat, grafo)

        msg = f"{len(df_corr)} entregadores gerados."
        if salvar_csv and "salvar" in salvar_csv:
            f_mat, f_corr = salvar_csvs_entregadores(df_mat, df_corr)
            msg += f" Salvo em: {f_mat.name} e {f_corr.name}."

        registros = df_corr.to_dict("records")
        geracao = uuid4().hex
        obter_trie_entregadores(geracao, registros)
        return registros, msg, geracao

    except Exception as erro:
        return no_update, f"Erro ao gerar entregadores: {erro}", no_update

@app.callback(
    Output("tabela-rotas", "children"),
    Input("dados-entregadores", "data"),
    Input("busca-restaurante", "value"),
    Input("raio-busca", "value"),
    Input("geracao-entregadores", "data"),
)
def atualizar_tabela_rotas(registros, restaurante_indice, raio, geracao):
    if restaurante_indice is None:
        return html.P("Selecione um restaurante para consultar as rotas.")

    if raio is None or not 100 <= raio <= 50000:
        return html.P("Raio não aceito. Use de 100 a 50.000 metros.")

    if not registros:
        return html.P("Gere os entregadores antes de consultar as rotas.")

    try:
        restaurante = df_bares.iloc[int(restaurante_indice)]
        trie = obter_trie_entregadores(geracao, registros)
        selecionados = filtrar_entregadores_por_raio(
            pd.DataFrame(registros), restaurante, raio, trie
        )
        resumo = html.P(
            f"Exibindo {len(selecionados)} de {len(registros)} entregadores dentro do raio."
        )

        if selecionados.empty:
            return html.Div([resumo, montar_tabela_rotas([])])

        ponto = wkt.loads(restaurante["GEOMETRIA"])
        grafo = obter_malha()
        entregadores = criar_entregadores(
            selecionados.to_dict(orient="records")
        )
        frota = Frota(entregadores)
        resultados = frota.calcular_rotas(
            grafo, ponto.x, ponto.y, frota.entregadores
        )

        return html.Div([resumo, montar_tabela_rotas(resultados)])

    except Exception as erro:
        return html.P(f"Não foi possível calcular rotas: {erro}")

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
