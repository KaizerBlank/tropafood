from utilities.files import *
from src.grafo import obter_malha

# Lemos os bares, lista de listas. Provavelmente não é a melhor maneira, mas é só para visualizarmos os dados
restaurantes=ler_bares()
print(f"restaurantes carregados: {len(restaurantes)}")

grafo = obter_malha()
print(f"{grafo.number_of_nodes()} nós e" f"{grafo.number_of_edges()} arestas.")

entregadores = ler_entregadores()
print(f"entregadores carregados: {len(entregadores)}")
