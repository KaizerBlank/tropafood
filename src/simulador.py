# implementar aqui a distribuição normal dos motoboys
import numpy as np
import pandas as pd

df_bares = pd.read_csv("data/30_bares.csv").dropna(subset=["LATITUDE", "LONGITUDE"])

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

if __name__ == "__main__":
    df_frota = gerar_entregadores_normais(df_bares, 100)
    
    print(f"Total de entregadores gerados: {len(df_frota)}")
    print(df_frota.head(10))

# df_bares = pd.read_csv("bares.csv").dropna(subset=["latitude", "longitude"])
# df_frota = gerar_entregadores_normais(df_bares, N_entregadores=150)
# print(df_frota.head())