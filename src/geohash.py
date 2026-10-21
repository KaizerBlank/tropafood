#Vamos considerar a base 32, com todos os números de 0-9 e letras do alfabeto - (a, l, i, o)
#Note que 5 bits representam 1 caractere na base 32
base32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode_geohash(lat, long):
    #Nossos bits serão armazenados em bits_z
    bits_Z = []

    #Escolhemos o número 20 de intercalações porque 20+20 = 40, que é o equivalente a 8 níveis de geohash
    numero_intercalacoes = 20

    #Esses são os limites iniciais para latitude e longitude. Vamos ir estreitando os limites a cada iteração do algoritmo.
    #Intervalos consideram o zero para cima.
    lat_lower, lat_upper = -90.0, 90.0
    long_lower, long_upper = -180.0, 180.0

    for i in range(numero_intercalacoes):
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
    #Nosso geohash terá 8 caracteres
    geohash = ""
    bits_Z_str = "".join(bits_Z)

    for index in range(0, numero_intercalacoes*2, 5):
        bloco = bits_Z_str[index:index+5]
        if len(bloco) < 5:
            bloco = bloco.ljust(5, '0')
            
        index_base32 = int(bloco, 2)
        geohash += base32[index_base32]

    return geohash

def decode_geohash(geohash):
    #Vamos reconstruir a string binária e então descobrir a coordenada
    bits_Z = []
    for char in geohash:
        index = base32.find(char)
        temp_bin = bin(index)[2:].zfill(5)
        bits_Z.extend(temp_bin)

    #Esses são os limites iniciais para latitude e longitude que usamos no encoding
    lat_lower, lat_upper = -90.0, 90.0
    long_lower, long_upper = -180.0, 180.0

    # Longitude ocupa os bits pares; latitude, os ímpares.
    # Processar um bit por vez preserva o último bit dos prefixos ímpares.
    for i, bit in enumerate(bits_Z):
        if i % 2 == 0:
            long_mid = (long_upper + long_lower) / 2
            if bit == '1':
                long_lower = long_mid
            else:
                long_upper = long_mid
        else:
            lat_mid = (lat_upper + lat_lower) / 2
            if bit == '1':
                lat_lower = lat_mid
            else:
                lat_upper = lat_mid

    #Aqui nós calculamos o centro geográfico da malha em que estávamos
    lat_centro = (lat_upper + lat_lower) / 2
    long_centro = (long_upper + long_lower) / 2
    
    # O erro é a distância do centro até as bordas da malha
    lat_erro = lat_upper - lat_centro
    long_erro = long_upper - long_centro
    
    return lat_centro, long_centro, lat_erro, long_erro

#Essa função vai cobrir o caso depontos  vizinhos muito próximos um dos outros, temos que lembrar de dar o append do geohash e calcular no total, 9 buscas na árvore. 
def vizinhos_adjacentes(geohash):

    lat_centro, long_centro, lat_erro, long_erro = decode_geohash(geohash)

    #Essa é a variação de latitude e longitude para chegar nas outras mlahas adjacentes. Temos que cobrir as 8 possibilidades usando dessa variação.
    delta_lat = lat_erro * 2
    delta_long = long_erro * 2
    
    direcoes = [
        (delta_lat, 0),           # Norte
        (-delta_lat, 0),          # Sul
        (0, delta_long),          # Leste
        (0, -delta_long),         # Oeste
        (delta_lat, delta_long),  # Nordeste
        (delta_lat, -delta_long), # Noroeste
        (-delta_lat, delta_long), # Sudeste
        (-delta_lat, -delta_long) # Sudoeste
    ]
    
    vizinhos = []
    
    for var_lat, var_long in direcoes:
        nova_lat = lat_centro + var_lat
        nova_long = long_centro + var_long
            
        vizinho_hash = encode_geohash(
            nova_lat, nova_long
            )[:len(geohash)]
        vizinhos.append(vizinho_hash)
        
    return vizinhos