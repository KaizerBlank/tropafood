# implementar aqui a distribuição normal dos motoboys
import numpy as np
import pandas as pd
import osmnx as ox
from grafo import obter_malha
import geopandas as gpd

def gerar_entregadores_normais(df_bares, N_entregadores, desvio_padrao=0.01): # desvio padrao pequeno para nao gerar todos no mesmo ponto
    """
    Gera posições de entregadores baseadas numa distribuição normal 
    centrada nas coordenadas dos restaurantes, com um desviao padrao pequeno
    para nao gerar todos os entregadores no mesmo ponto.
    """

    num_restaurantes = len(df_bares)
    if num_restaurantes == 0:
        raise ValueError("Erro no database")
    
    entregadores_por_bar = N_entregadores // num_restaurantes
    resto = N_entregadores % num_restaurantes

    indices_com_resto = set(np.random.choice(num_restaurantes, size=resto, replace=False))
    
    lista_entregadores = []
    
    for index, row in df_bares.iterrows():
        lat_centro = row["LATITUDE"]
        lon_centro = row["LONGITUDE"]

        n_atual = entregadores_por_bar + (1 if index in indices_com_resto else 0)
            
        # centra a geração em cada bar
        lats_geradas = np.random.normal(loc=lat_centro, scale=desvio_padrao, size=n_atual)
        lons_geradas = np.random.normal(loc=lon_centro, scale=desvio_padrao, size=n_atual)

        for i in range(n_atual):
            lista_entregadores.append({
                "id_entregador": f"entregador_{len(lista_entregadores) + 1}",
                "restaurante_origem": row.get("NOME", "Desconhecido"),
                "latitude_matematica": lats_geradas[i],
                "longitude_matematica": lons_geradas[i]
            })
            
    df_entregadores = pd.DataFrame(lista_entregadores)
    return df_entregadores

def corrigir_para_ruas(df_entregadores, G):
    """
    Aloca os entregadores para os nodes mais proximos do grafo (EPSG:31983 metros).
    Gera coordenadas em metros e graus (lat long)
    """
    # cria uma coluna geometry nova com decimal lat e long
    gdf_entregadores = gpd.GeoDataFrame(
        df_entregadores,
        geometry=gpd.points_from_xy(
            df_entregadores.longitude_matematica,
            df_entregadores.latitude_matematica,
        ),
        crs="EPSG:4326",
    )

    # Converte para metros igual o Grafo (EPSG:31983)
    gdf_entregadores_proj = gdf_entregadores.to_crs("EPSG:31983")

    xs_proj_rua = []
    ys_proj_rua = []

    # Busca o node da rua mais proxima no grafo
    for geom in gdf_entregadores_proj.geometry:
        x_proj, y_proj = geom.x, geom.y
        no_mais_proximo = ox.distance.nearest_nodes(G, X=x_proj, Y=y_proj)

        xs_proj_rua.append(G.nodes[no_mais_proximo]["x"])
        ys_proj_rua.append(G.nodes[no_mais_proximo]["y"])

    # salvaas coordenadas em metros
    df_entregadores["x_rua_metros"] = xs_proj_rua
    df_entregadores["y_rua_metros"] = ys_proj_rua

    # Converte as posições das ruas em metros de volta para graus dec long lat
    gdf_rua_proj = gpd.GeoDataFrame(
        df_entregadores,
        geometry=gpd.points_from_xy(xs_proj_rua, ys_proj_rua),
        crs="EPSG:31983",
    )
    gdf_rua_latlon = gdf_rua_proj.to_crs("EPSG:4326")

    # Guarda as coordenadas geográficas em graus decimais
    df_entregadores["latitude_rua_graus"] = gdf_rua_latlon.geometry.y
    df_entregadores["longitude_rua_graus"] = gdf_rua_latlon.geometry.x

    return df_entregadores


if __name__ == "__main__":
    print("1. Carregando bares...")
    df_bares = pd.read_csv("data/30_bares.csv").dropna(
        subset=["LATITUDE", "LONGITUDE"]
    )

    print("2. Entregadores com long lat matematica...")
    df_frota_matematica = gerar_entregadores_normais(
        df_bares, N_entregadores=100
    )
    df_frota_matematica.to_csv("data/entregadores_matematicos.csv", index=False)
    print("   -> Guardado: data/entregadores_matematicos.csv")

    print("3. Carregando Malha Viária de BH - Grafo (SIRGAS 2000 - EPSG:31983)...")
    G = obter_malha()

    print("4. Corringindo coordenadas dos entregadores para as ruas...")
    df_frota_corrigida = corrigir_para_ruas(df_frota_matematica, G)

    caminho_csv_rua = "data/entregadores_corrigidos.csv"
    df_frota_corrigida.to_csv(caminho_csv_rua, index=False)

    print(
        f"5.Deu bom! Arquivo final em: {caminho_csv_rua}\n"
    )

    cols_exibicao = [
        "id_entregador",
        "latitude_matematica",
        "longitude_matematica",
        "x_rua_metros",
        "y_rua_metros",
        "latitude_rua_graus",
        "longitude_rua_graus",
    ]
    print(df_frota_corrigida[cols_exibicao].head())