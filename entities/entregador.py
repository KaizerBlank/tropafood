class Entregador:
    def __init__(self, id_Entregador, latitude, longitude, x, y, geohash=""):
        self.id_Entregador = id_Entregador
        self.latitude = latitude 
        self.longitude = longitude  
        self.x = x
        self.y = y
        self.geohash = geohash
        self.distancia_restaurante = 0.0
        self.tempo_estimado = 0.0
        self.filtrado = True # e.g se esta no raio que o usuario filtrar,then :True 
                             #                                           o.w, False