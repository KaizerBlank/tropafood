input_csv = "data/bares.csv"
output_csv = "data/bares_com_coordenadas.csv"
import time
import pandas as pd
import osmnx as ox

def geocodificar_bares(input_csv="data/bares.csv", output_csv="data/bares_com_coordenadas.csv"):
    print("Carregando csv...")
    df = pd.read_csv(input_csv)

    print(f"Achei as colunas {list(df.columns)}")

    latitudes = []
    longitudes = []

    print("Iniciando geocodificação, demora horas.... :<")

    for index, row in df.iterrows():
        logradouro = str(row.get("NOME_LOGRADOURO", "")).strip().replace("AVE ", "AVENIDA ")
        numero = str(row.get("NUMERO_IMOVEL", "")).strip()
        bairro = str(row.get("NOME_BAIRRO", "")).strip()
        nome_bar = str(row.get("NOME", "")).strip()

        endereco_completo = f"{logradouro}, {numero} - {bairro}, Belo Horizonte - MG, Brasil"
        
        if logradouro == "nan" or not logradouro:
            endereco_completo = f"{nome_bar}, {bairro}, Belo Horizonte - MG, Brasil"

        try:
            # busca long lat via openstreetmap
            lat, lon = ox.geocode(endereco_completo)
            latitudes.append(lat)
            longitudes.append(lon)
            print(f"[{index + 1}/{len(df)}] Sucesso: {nome_bar} -> Lat: {lat}, Lon: {lon}")
        except Exception as e:
            latitudes.append(None)
            longitudes.append(None)
            print(f"[{index + 1}/{len(df)}] Erro ao localizar '{nome_bar} ({endereco_completo})': {e}")
        
        time.sleep(1)

    df["latitude"] = latitudes
    df["longitude"] = longitudes

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"Processo concluído! Ficheiro guardado com sucesso como '{output_csv}'.")

if __name__ == "__main__":
    geocodificar_bares()