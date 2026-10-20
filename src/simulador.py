import numpy as np
import pandas as pd
import osmnx as ox
import geopandas as gpd
from shapely import wkt
from shapely.geometry import LineString, Point
from utilities.constants import (
    CRS_GRAUS,
    CRS_METROS,
    CSV_BARES,
    CSV_ENTREGADORES_CORRIGIDOS,
    CSV_ENTREGADORES_MATEMATICOS,
    DESVIO_PADRAO_METROS,
)
from .grafo import obter_malha

def gerar_entregadores_normais(df_bares, N_entregadores, desvio_padrao_metros=DESVIO_PADRAO_METROS):
    """
    Gera posições de entregadores baseadas numa distribuição normal 
    centrada nas coordenadas dos restaurantes, com um desviao padrao em metros
    para nao gerar todos os entregadores no mesmo ponto.
    """
    bares_metros = df_bares["GEOMETRIA"].apply(wkt.loads)

    num_restaurantes = len(df_bares)
    if num_restaurantes == 0:
        raise ValueError("Erro no database")
    
    entregadores_por_bar = N_entregadores // num_restaurantes
    resto = N_entregadores % num_restaurantes

    indices_com_resto = set(np.random.choice(num_restaurantes, size=resto, replace=False))
    
    lista_entregadores = []
    
    for index, geom in enumerate(bares_metros):
        row = df_bares.iloc[index]

        x_centro = geom.x
        y_centro = geom.y

        n_atual = entregadores_por_bar + (1 if index in indices_com_resto else 0)

        xs_gerados = np.random.normal(loc=x_centro, scale=desvio_padrao_metros, size=n_atual)
        ys_gerados = np.random.normal(loc=y_centro, scale=desvio_padrao_metros, size=n_atual)

        for i in range(n_atual):
            lista_entregadores.append({
                "id_entregador": f"entregador_{len(lista_entregadores) + 1}",
                "restaurante_origem": row.get("NOME", "Desconhecido"),
                "x_matematica_metros": xs_gerados[i],
                "y_matematica_metros": ys_gerados[i],
                "filtrado": True
            })
            
    df_entregadores = pd.DataFrame(lista_entregadores)

    gdf_mat_metros= gpd.GeoDataFrame(
        df_entregadores,
        geometry=gpd.points_from_xy(df_entregadores["x_matematica_metros"], df_entregadores["y_matematica_metros"]),
        crs=CRS_METROS
    )
    gdf_mat_latlon = gdf_mat_metros.to_crs(CRS_GRAUS)

    df_entregadores["latitude_matematica"] = gdf_mat_latlon.geometry.y
    df_entregadores["longitude_matematica"] = gdf_mat_latlon.geometry.x

    return df_entregadores

def corrigir_para_ruas(df_entregadores, G):
    """
    Aloca os entregadores para a aresta (rua) mais próxima do grafo.
    """
    gdf_entregadores_metros = gpd.GeoDataFrame(
        df_entregadores,
        geometry=gpd.points_from_xy(
            df_entregadores["x_matematica_metros"],
            df_entregadores["y_matematica_metros"],
        ),
        crs=CRS_METROS,
    )

    xs_metros_rua = []
    ys_metros_rua = []
    posicoes_arestas_metros = []

    arestas = ox.distance.nearest_edges(
        G, 
        X=gdf_entregadores_metros.geometry.x.values, 
        Y=gdf_entregadores_metros.geometry.y.values
    )

    for i, geom in enumerate(gdf_entregadores_metros.geometry):
        u, v, key = arestas[i]
        edge_data = G.edges[u, v, key]
        
        line = edge_data.get("geometry", LineString([
            (G.nodes[u]["x"], G.nodes[u]["y"]), 
            (G.nodes[v]["x"], G.nodes[v]["y"])
        ]))

        ponto_u = Point(G.nodes[u]["x"], G.nodes[u]["y"])

        inicio = Point(line.coords[0])
        fim = Point(line.coords[-1])

        if ponto_u.distance(fim) < ponto_u.distance(inicio):
            line = LineString(list(line.coords)[::-1])

        posicao_metros = line.project(geom)
        ponto_projetado = line.interpolate(posicao_metros)

        posicoes_arestas_metros.append(float(posicao_metros))
        
        xs_metros_rua.append(ponto_projetado.x)
        ys_metros_rua.append(ponto_projetado.y)

    df_entregadores = df_entregadores.copy()
    df_entregadores["x_rua_metros"] = xs_metros_rua
    df_entregadores["y_rua_metros"] = ys_metros_rua

    df_entregadores["aresta_u"] = [
        int(aresta[0]) for aresta in arestas
    ]

    df_entregadores["aresta_v"] = [
        int(aresta[1]) for aresta in arestas
    ]

    df_entregadores["aresta_key"] = [
        int(aresta  [2]) for aresta in arestas
    ]

    df_entregadores["posicao_aresta_metros"] = posicoes_arestas_metros

    gdf_rua_metros = gpd.GeoDataFrame(
        df_entregadores,
        geometry=gpd.points_from_xy(xs_metros_rua, ys_metros_rua),
        crs=CRS_METROS,
    )
    gdf_rua_latlon = gdf_rua_metros.to_crs(CRS_GRAUS)

    df_entregadores["latitude_rua_graus"] = gdf_rua_latlon.geometry.y
    df_entregadores["longitude_rua_graus"] = gdf_rua_latlon.geometry.x

    return df_entregadores

if __name__ == "__main__":
    print("=== SIMULADOR DE ENTREGADORES ===")
    
    if not CSV_BARES.is_file():
        raise FileNotFoundError(f"Arquivo de bares não encontrado: {CSV_BARES}")

    n_input = input("Número total de entregadores: ").strip()
    N_entregadores = int(n_input) if n_input else 500

    print("\nCarregando bares...")
    df_bares = pd.read_csv(CSV_BARES).dropna(subset=["GEOMETRIA"])

    print(f"Gerando {N_entregadores} entregadores (desvio: {DESVIO_PADRAO_METROS}m)...")
    df_entregadores_matematica = gerar_entregadores_normais(
        df_bares, N_entregadores=N_entregadores, desvio_padrao_metros=DESVIO_PADRAO_METROS
    )
    df_entregadores_matematica.to_csv(CSV_ENTREGADORES_MATEMATICOS, index=False)
    print(f"Salvo: {CSV_ENTREGADORES_MATEMATICOS}")

    print("Carregando Malha Viaria de BH - Grafo")
    G = obter_malha()

    print("Corrigindo coordenadas dos entregadores para as ruas...")
    df_entregadores_corrigido = corrigir_para_ruas(df_entregadores_matematica, G)

    caminho_csv_rua = CSV_ENTREGADORES_CORRIGIDOS
    df_entregadores_corrigido.to_csv(caminho_csv_rua, index=False)

    print(f"Deu bom! Arquivo final em: {caminho_csv_rua}\n")

    cols_exibicao = [
        "id_entregador",
        "restaurante_origem",
        "x_matematica_metros",
        "y_matematica_metros",
        "latitude_matematica",
        "longitude_matematica",
        "x_rua_metros",
        "y_rua_metros",
        "latitude_rua_graus",
        "longitude_rua_graus",
    ]
    print(df_entregadores_corrigido[cols_exibicao].head())