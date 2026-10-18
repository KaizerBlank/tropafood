from utilities.files import *
from src.trie import Trie_Compacta
from src.geohash import encode_geohash
# from src.grafo import obter_malha

# Lemos os bares, lista de listas. Provavelmente não é a melhor maneira, mas é só para visualizarmos os dados


restaurantes=ler_bares()
print(f"restaurantes carregados: {len(restaurantes)}")

entregadores = ler_entregadores()
print(f"entregadores carregados: {len(entregadores)}")


trie_entregadores = Trie_Compacta()

for entregador in entregadores:
    entregador.geohash = encode_geohash(entregador.latitude, entregador.longitude)
    trie_entregadores.insert(entregador)










# grafo = obter_malha()
# print(f"{grafo.number_of_nodes()} nós e" f"{grafo.number_of_edges()} arestas.")


