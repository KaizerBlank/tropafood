from src.geohash import encode_geohash, vizinhos_adjacentes
from src.trie import Trie_Compacta
from src.rotas import localizar_na_via, calcular_rotas_osmnx

class Frota:
    def __init__(self, entregadores):
        self.entregadores = list(entregadores)


    # def buscar_por_prefixo(self, prefixo):
    #     lista_geohashes_busca = []
    #     lista_geohashes_busca.append(prefixo)

    #     return self.trie.search(prefixo)

    def _localizar_entregador(self, grafo, entregador):
        aresta = (
            entregador.aresta_u,
            entregador.aresta_v,
            entregador.aresta_key,
        )

        if all(valor is None for valor in aresta):
            aresta = None
        elif any(valor is None for valor in aresta):
            raise ValueError("Entregador com dados incompletos da aresta")

        return localizar_na_via(
            grafo,
            entregador.x,
            entregador.y,
            aresta=aresta,
        )

    def calcular_rotas(self, grafo, x_restaurante, y_restaurante, selecionados):
        selecionados = list(selecionados)
        if not selecionados:
            return []

        destino = localizar_na_via(grafo, x_restaurante, y_restaurante)

        origens = [
            self._localizar_entregador(grafo, entregador)
            for entregador in selecionados
        ]

        rotas = calcular_rotas_osmnx(grafo, origens, destino)
        resultados = []

        for entregador, rota in zip(selecionados, rotas):
            resultados.append({
                "id_entregador": entregador.id_Entregador,
                "latitude": entregador.latitude,
                "longitude": entregador.longitude,
                "distancia_metros": rota["distancia_metros"],
                "tempo_segundos": rota["tempo_segundos"],
            })

        return sorted(
            resultados,
            key=lambda resultado:(
                float("inf")
                if resultado["distancia_metros"] is None
                else resultado["distancia_metros"]
            ),
        )