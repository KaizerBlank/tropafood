class Entregador:
    def __init__(self, id_Entregador, latitute, longitute, geohash=""):
        self.id_Entregador = self.id_Entregador
        self.latitute = latitute 
        self.longitute = longitute  
        self.geohash = geohash
        self.distancia_restaurante = 0.0
        self.tempo_estimado = 0.0
        self.filtrado = True #e.g se esta no raio que o usuario filtrar