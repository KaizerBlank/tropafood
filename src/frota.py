from src.geohash import encode_geohash
from src.trie import Trie_Compacta

class Frota:
    def __init__(self, entregadores):
        self.entregadores = list(entregadores)
        self.trie = Trie_Compacta()

        for entregador in self.entregadores:
            entregador.geohash = encode_geohash(
                entregador.latitude,
                entregador.longitude
            )

            self.trie.insert(entregador)

    def buscar_por_prefixo(self, prefixo):
        return self.trie.search(prefixo)