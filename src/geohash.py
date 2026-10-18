#implementar aqui a conversão das coordenadas para Geohash32

#Vamos considerar a base 32, com todos os números de 0-9 e letras do alfabeto - (a, l, i, o)
#Note que 5 bits representam 1 caractere na base 32
base32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encoding_geohash(lat, long):
    #Nossos bits serão armazenados em bits_z
    bits_Z = []

    #Esses são os limites iniciais para latitude e longitude. Vamos ir estreitando os limites a cada iteração do algoritmo.
    #Intervalos consideram o zero para cima.
    lat_lower, lat_upper = -90.0, 90.0
    long_lower, long_upper = -180.0, 180.0

    for i in range(8):
        long_mid = (long_upper + long_lower)/2
        if long_mid <= long:
            bits_Z.append('1')
            long_lower = long_mid 
        else:
            bits_Z.append('0')
            long_upper = long_mid

        lat_mid = (lat_upper + lat_lower)/2
        if lat_mid <= lat:
            bits_Z.append('1')
            lat_lower = lat_mid 
        else:
            bits_Z.append('0')
            lat_upper = lat_mid

    #O geohash será uma string na base32
    #Como teremos 16 bits de informação, os bits 0-4, 5-9, 10-14 resultam em 3 caracteres e o 15 bit forma o último, com 0000 à direita
    #Nosso geohash terá 4 caracteres
    geohash = ""
    print(bits_Z)
    bits_Z_str = "".join(bits_Z)

    for index in range(0, 16, 5):
        bloco = bits_Z_str[index:index+5]
        if len(bloco) < 5:
            bloco = bloco.ljust(5, '0')
            
        index_base32 = int(bloco, 2)
        geohash += base32[index_base32]

    return geohash

print(encoding_geohash(23.3, 42.3))