from utilities.files import *
from src.trie import Trie_Compacta
from src.geohash import encode_geohash
from src.grafo import obter_malha

grafo = obter_malha()
print(f"{grafo.number_of_nodes()} nós e" f"{grafo.number_of_edges()} arestas.")


