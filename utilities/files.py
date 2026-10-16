import csv

def ler_bares():
    restaurantes = []
    with open('bares.csv', mode="r", encoding="utf-8") as file:
        dados_csv = csv.reader(file)
        for line in dados_csv:
            restaurantes.append(line)
    return restaurantes