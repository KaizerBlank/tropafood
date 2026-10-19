class Restaurante:
    def __init__(self, id_restaurante, nome, latitude, longitude, x, y, desc_logradouro,
                 nome_logradouro, numero, complemento, nome_bairro, geohash=""):
        self.id_restaurante = id_restaurante
        self.nome = nome
        self.latitude = latitude
        self.longitude = longitude
        self.x = x
        self.y = y
        self.endereco = f"{desc_logradouro} {nome_logradouro}, {numero} - {nome_bairro}, Belo Horizonte - MG, Brasil".strip()
        self.geohash = geohash