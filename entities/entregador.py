class Entregador:
    def __init__(self, id_Entregador, latitude, longitude, x, y, geohash="", aresta_u=None, aresta_v=None, aresta_key=None, posicao_aresta_metros=None):
        self.id_Entregador = id_Entregador
        self.latitude = latitude 
        self.longitude = longitude  
        self.x = x
        self.y = y
        self.geohash = geohash
        self.aresta_u = aresta_u
        self.aresta_v = aresta_v
        self.aresta_key = aresta_key
        self.posicao_aresta_metros = posicao_aresta_metros
        self.distancia_restaurante = 0.0
        self.tempo_estimado = 0.0
        self.filtrado = True # e.g se esta no raio que o usuario filtrar,then :True 
                             #                                           o.w, False