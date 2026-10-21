from datetime import datetime
from uuid import uuid4
from shapely import wkt
from utilities.files import criar_entregadores
from src.frota import Frota
import dash_leaflet as dl
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
from utilities.interface import (
    filtrar_entregadores_por_raio,
    montar_tabela_rotas,
    plota_mapa_interface,
)

df_bares = pd.read_csv(CSV_BARES).dropna(
    subset=["GEOMETRIA", "LATITUDE", "LONGITUDE"]
).reset_index(drop=True)
CENTRO_INICIAL = [df_bares["LATITUDE"].mean(), df_bares["LONGITUDE"].mean()]

def raio_valido(raio):
    return raio is not None and 100 <= raio <= 50000

app = Dash()
app.title = "Tropafood"
app.layout = html.Main([
    dcc.Store(id="dados-entregadores", data=[]),
    dl.Map([
        dl.TileLayer(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        ),
        dl.LayerGroup(id="camadas-mapa"),
        dl.ZoomControl(position="topright"),
    ], id="mapa-entregadores", center=CENTRO_INICIAL, zoom=12,
        zoomControl=False, className="mapa"),
    html.Section([
        html.Header([
            html.H1("Tropafood"),
            html.P("Belo Horizonte", className="localidade"),
        ], className="cabecalho"),
        html.Label("Restaurante", htmlFor="busca-restaurante"),
        dcc.Dropdown(
            id="busca-restaurante",
            options=[
                {"label": str(bar.get("NOME", "Restaurante")), "value": indice}
                for indice, bar in df_bares.iterrows()
            ],
            placeholder="Buscar restaurante pelo nome",
            clearable=True, searchable=True,
        ),
        html.Label("Raio de busca (metros)", htmlFor="raio-busca"),
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
        html.H2("Rotas até o restaurante"),
        html.P("Tempo estimado sem considerar trânsito ou paradas."),
        dcc.Loading(html.Div(
            "Selecione um restaurante para consultar os entregadores gerados.",
            id="tabela-rotas",
            style={"overflowX": "auto"},
        )),
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
    if not raio_valido(raio):
        return no_update, "Raio não aceito. Use de 100 a 50.000 metros."
    
    camadas = plota_mapa_interface(
        pd.DataFrame(entregadores), df_bares,
        indice_restaurante_selecionado=restaurante_indice,
        raio_metros=raio,
        exibir_raio="exibir" in (exibir_raio or []),
        exibir_restaurantes="exibir" in (exibir_restaurantes or []),
    )
    
    quantidade = len(entregadores or [])
    if restaurante_indice is None:
        return camadas, f"{quantidade} entregadores no mapa."
        
    restaurante = df_bares.iloc[int(restaurante_indice)]
    selecionados = filtrar_entregadores_por_raio(pd.DataFrame(entregadores or []), restaurante, raio)
    return camadas, f"{len(selecionados)} de {quantidade} entregadores dentro do raio."


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
    prevent_initial_call=True,
    running=[(Output("gerar-entregadores", "disabled"), True, False)],
)
def atualizar_mapa(n_clicks, quantidade_entregadores, salvar_csv=None):
    if not quantidade_entregadores or quantidade_entregadores < 1 or not float(quantidade_entregadores).is_integer():
        return no_update, "Quantidade não aceita. Use um inteiro maior que zero."

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
        
        if salvar_csv and "salvar" in salvar_csv:
            mat_path, corr_path = salvar_csvs_entregadores(df_entregadores_matematicos, df_entregadores)
            mensagem += f" CSVs salvos: {mat_path.name} e {corr_path.name}."
            
    except Exception:
        return no_update, "Não foi possível gerar os entregadores."

    return df_entregadores.to_dict("records"), mensagem


@app.callback(
    Output("tabela-rotas", "children"),
    Input("dados-entregadores", "data"),
    Input("busca-restaurante", "value"),
    Input("raio-busca", "value"),
)
def atualizar_tabela_rotas(registros, restaurante_indice, raio):
    if restaurante_indice is None:
        return html.P("Selecione um restaurante para consultar as rotas.")

    if not raio_valido(raio):
        return html.P("Raio não aceito. Use de 100 a 50.000 metros.")

    if not registros:
        return html.P("Gere os entregadores antes de consultar as rotas.")

    try:
        restaurante = df_bares.iloc[int(restaurante_indice)]
        selecionados = filtrar_entregadores_por_raio(pd.DataFrame(registros), restaurante, raio)
        resumo = html.P(f"Exibindo {len(selecionados)} de {len(registros)} entregadores dentro do raio.")
        
        if selecionados.empty:
            return html.Div([resumo, montar_tabela_rotas([])])

        ponto = wkt.loads(restaurante["GEOMETRIA"])
        grafo = obter_malha()
        entregadores = criar_entregadores(selecionados.to_dict(orient="records"))
        frota = Frota(entregadores)
        resultados = frota.calcular_rotas(
            grafo, ponto.x, ponto.y, frota.entregadores
        )

        return html.Div([resumo, montar_tabela_rotas(resultados)])
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