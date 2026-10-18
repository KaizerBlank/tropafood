from utilities.files import *
from src.grafo import obter_malha

# Lemos os bares, lista de listas. Provavelmente não é a melhor maneira, mas é só para visualizarmos os dados
print(ler_bares())

grafo = obter_malha()
print(f"{grafo.number_of_nodes()} nós e" f"{grafo.number_of_edges()} arestas.")