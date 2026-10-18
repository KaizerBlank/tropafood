# implementar aqui a distribuição normal dos motoboys
import numpy as np
import pandas as pd
import osmnx as ox
from grafo import obter_malha
import geopandas as gpd
from shapely import wkt

CRS_METROS = "EPSG:31983"
CRS_GRAUS = "EPSG:4326"

def gerar_entregadores_normais(df_bares, N_entregadores, desvio_padrao_metros=300.0):
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
    Aloca os entregadores para os nodes mais próximos do grafo
    Gera coordenadas em metros e graus (lat long).
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

    for geom in gdf_entregadores_metros.geometry:
        x_metros, y_metros = geom.x, geom.y
        no_mais_proximo = ox.distance.nearest_nodes(G, X=x_metros, Y=y_metros)

        xs_metros_rua.append(G.nodes[no_mais_proximo]["x"])
        ys_metros_rua.append(G.nodes[no_mais_proximo]["y"])

    df_entregadores["x_rua_metros"] = xs_metros_rua
    df_entregadores["y_rua_metros"] = ys_metros_rua

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
    print("1. Carregando bares...")
    df_bares = pd.read_csv("data/30_bares.csv").dropna(subset=["GEOMETRIA"])

    print("2. Gerando entregadores baseados em metros (normal centrada na geometria do bar)...")
    df_entregadores_matematica = gerar_entregadores_normais(
        df_bares, N_entregadores=100, desvio_padrao_metros=600.0
    )
    df_entregadores_matematica.to_csv("data/entregadores_matematicos.csv", index=False)
    print("   -> Guardado: data/entregadores_matematicos.csv")

    print("3. Carregando Malha Viária de BH - Grafo (SIRGAS 2000 - EPSG:31983)...")
    G = obter_malha()

    print("4. Corrigindo coordenadas dos entregadores para as ruas...")
    df_entregadores_corrigido = corrigir_para_ruas(df_entregadores_matematica, G)

    caminho_csv_rua = "data/entregadores_corrigidos.csv"
    df_entregadores_corrigido.to_csv(caminho_csv_rua, index=False)

    print(f"5. Deu bom! Arquivo final em: {caminho_csv_rua}\n")

    cols_exibicao = [
        "id_entregador",
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