# implementar aqui a trie compacta

# Devo colocar bool indicando fim e lista com informações dos entregadores associado a determinado geohash?
class TrieNode:
    def __init__(self, rotulo: str):
        self.rotulo = rotulo
        self.filhos = {}
        self.entregadores = []
        self.no_folha = False

# Função auxiliar que retorna o tamanho do maior prefixo em comum entre duas strings
def find_maior_prefixo(string1, string2):
    menor_tamanho = min(len(string1), len(string2))
    for i in range(menor_tamanho):
        if string1[i] != string2[i]:
            # Sintaxe para retornar a string toda até o index i, excluindo o próprio string[i]
            return i
    #Açúcar sintático que aprendemos ser possível fazer em LP
    else: 
        return menor_tamanho
    

class Trie_Compacta:
    def __init__(self):
        self.root = TrieNode("")

    #Eu provavelmente vou só passar o entregador como parâmetro e pegar dele o ID, geohash, etc..
    def insert(self, geohash, entregador):
        current_node = self.root
        temp_geohash = geohash

        while True:
            first_char = temp_geohash[0]

            #Tentamos encontrar um casamento entre o caractere consumido e os filhos já adicionados no nó atual.
            #Se não encontrarmos, isso significa que temos que criar um novo nó folha.
            if first_char not in current_node.filhos:
                new_node = TrieNode(temp_geohash)
                new_node.entregadores.append(entregador)
                new_node.no_folha = True
                
                #Adiciona o novo nó criado como filho do atual
                current_node.filhos[first_char] = new_node
                return new_node
            #Se chegamos até aqui, significa que existe um nó com o o primeiro caractere, agora basta saber quantos caracteres tem em comum:

            next_node = current_node.filhos[first_char]
            rotulo_next_node = next_node.rotulo
            index_maior_prefixo = find_maior_prefixo(temp_geohash, rotulo_next_node)

            #Se o maior prefixo possível entre o que não consumido do geohash e o rótulo do nó filho é exatamente o tamanho do rótulo filho, isso quer dizer que
            # foi completamente consumido. Isso nos leva a dois possíveis cenários: a cadeia sendo processada terminou (adicionamos nó \n como folha) ou ainda há sobra;  
            if index_maior_prefixo == len(rotulo_next_node):
                temp_geohash = temp_geohash[index_maior_prefixo:]

                if len(temp_geohash) == 0:
                    next_node.no_folha = True
                    next_node.entregadores.append(entregador)
                    return next_node

                current_node = next_node

            #Agora, o caso final, é se precisarmos partir o rótulo do nó atual para conseguir adicionar o geohash.
            else:
                #Essa é a parte em comum entre o que havia anteriormente no nó e o geohash que está sendo inserido.
                rotulo_igual = next_node.rotulo[:index_maior_prefixo]

                #Partes sobressalentes
                rotulo_restante_antigo = next_node.rotulo[index_maior_prefixo:]
                rotulo_restante_novo = temp_geohash.rotulo[index_maior_prefixo:]

                #Aqui nós definimos o novo nó intermediário, com a intercessão entre dos rótulos, definimos o rótulo intermediário como filho do nó em que iniciamos a iteração e pai do nó com o restante do rótulo 
                mid_node = TrieNode(rotulo_igual)

                next_node.rotulo = rotulo_restante_antigo
                mid_node.filhos[rotulo_restante_antigo[0]] = next_node

                current_node.filhos[first_char] = mid_node

                #Agora, vamos ver se existe rotulo restante na cadeia a ser consumida:
                if len(rotulo_restante_novo) == 0:
                    mid_node.no_folha = True
                    mid_node.entregadores.append(entregador)
                    return mid_node
                else:
                    new_node = TrieNode(rotulo_restante_novo)
                    new_node.no_folha = True
                    new_node.entregadores.append(entregador)
                    mid_node.filhos[rotulo_restante_novo[0]] = new_node
                    return new_node

                    










            

            


    def search(self, geohash):
        return geohash

    def remove(self, geohash):
        return geohash


    
















# dummy data para simular o hash
DUMMY_DRIVERS = [
    # Ponto Central (Restaurante em '7h6')
    {"id": 1,  "lat": -19.9327, "long": -43.9362, "geohash": "7h6"},
    {"id": 2,  "lat": -19.9250, "long": -43.9300, "geohash": "7h6"},
    {"id": 3,  "lat": -19.9400, "long": -43.9400, "geohash": "7h6"},
    {"id": 4,  "lat": -19.9300, "long": -43.9280, "geohash": "7h6"},
    {"id": 5,  "lat": -19.9380, "long": -43.9320, "geohash": "7h6"},

    # 8 Vizinhos Adjacentes (Bordas)
    {"id": 6,  "lat": -19.8500, "long": -43.9362, "geohash": "7h7"},  # Norte
    {"id": 7,  "lat": -19.8600, "long": -43.9300, "geohash": "7h7"},
    {"id": 8,  "lat": -20.0200, "long": -43.9362, "geohash": "7h4"},  # Sul
    {"id": 9,  "lat": -20.0100, "long": -43.9400, "geohash": "7h4"},
    {"id": 10, "lat": -19.9327, "long": -43.8000, "geohash": "7hk"},  # Leste
    {"id": 11, "lat": -19.9250, "long": -43.8100, "geohash": "7hk"},
    {"id": 12, "lat": -19.9327, "long": -44.1000, "geohash": "7h3"},  # Oeste
    {"id": 13, "lat": -19.9400, "long": -44.0800, "geohash": "7h3"},
    {"id": 14, "lat": -19.8500, "long": -43.8000, "geohash": "7hm"},  # Nordeste
    {"id": 15, "lat": -19.8500, "long": -44.1000, "geohash": "7h5"},  # Noroeste
    {"id": 16, "lat": -20.0200, "long": -43.8000, "geohash": "7hj"},  # Sudeste
    {"id": 17, "lat": -20.0200, "long": -44.1000, "geohash": "7h2"},  # Sudoeste

    # Distantes (Não devem ser retornados na busca do restaurante '7h6')
    {"id": 18, "lat": -19.7000, "long": -43.7000, "geohash": "7he"},
    {"id": 19, "lat": -19.6500, "long": -43.6800, "geohash": "7he"},
    {"id": 20, "lat": -20.3000, "long": -44.3000, "geohash": "7gk"},
    {"id": 21, "lat": -20.3200, "long": -44.3100, "geohash": "7gk"},
    {"id": 22, "lat": -18.5000, "long": -42.5000, "geohash": "7k1"},
    {"id": 23, "lat": -18.5200, "long": -42.5100, "geohash": "7k1"},
    {"id": 24, "lat": -22.9051, "long": -43.1729, "geohash": "775"},
    {"id": 25, "lat": -23.5505, "long": -46.6333, "geohash": "6gy"}
]


