# implementar aqui a trie compacta

# Devo colocar bool indicando fim e lista com informações dos entregadores associado a determinado geohash?
class TrieNode:
    def __init__(self, rotulo: str):
        self.rotulo = rotulo
        self.filhos = {}
        self.entregadores = []

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
    def insert(self, entregador):
        current_node = self.root
        temp_geohash = entregador.geohash

        while True:
            first_char = temp_geohash[0]

            #Tentamos encontrar um casamento entre o caractere consumido e os filhos já adicionados no nó atual.
            #Se não encontrarmos, isso significa que temos que criar um novo nó folha.
            if first_char not in current_node.filhos:
                new_node = TrieNode(temp_geohash)
                new_node.entregadores.append(entregador)
                
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
                    next_node.entregadores.append(entregador)
                    return next_node

                current_node = next_node

            #Agora, o caso final, é se precisarmos partir o rótulo do nó atual para conseguir adicionar o geohash.
            else:
                #Essa é a parte em comum entre o que havia anteriormente no nó e o geohash que está sendo inserido.
                rotulo_igual = next_node.rotulo[:index_maior_prefixo]

                #Partes sobressalentes
                rotulo_restante_antigo = next_node.rotulo[index_maior_prefixo:]
                rotulo_restante_novo = temp_geohash[index_maior_prefixo:]

                #Aqui nós definimos o novo nó intermediário, com a intercessão entre dos rótulos, definimos o rótulo intermediário como filho do nó em que iniciamos a iteração e pai do nó com o restante do rótulo 
                mid_node = TrieNode(rotulo_igual)

                next_node.rotulo = rotulo_restante_antigo
                mid_node.filhos[rotulo_restante_antigo[0]] = next_node

                current_node.filhos[first_char] = mid_node

                #Agora, vamos ver se existe rotulo restante na cadeia a ser consumida:
                if len(rotulo_restante_novo) == 0:
                    mid_node.entregadores.append(entregador)
                    return mid_node
                else:
                    new_node = TrieNode(rotulo_restante_novo)
                    new_node.entregadores.append(entregador)
                    mid_node.filhos[rotulo_restante_novo[0]] = new_node
                    return new_node

    ##Busca o geohash dentro da trie e retorna a lista de entregadores associada àquele geohash
    def search(self, geohash):
        current_node = self.root
        temp_geohash = geohash
        
        while temp_geohash:
            first_char = temp_geohash[0]

            if first_char not in current_node.filhos:
                return []

            next_node = current_node.filhos[first_char]
            rotulo_next_node = next_node.rotulo
            index_maior_prefixo = find_maior_prefixo(rotulo_next_node, temp_geohash)

            #Geohash todo consumido
            if index_maior_prefixo == len(temp_geohash):
                return self.agregar_entregadores(next_node)

            #Se o rotulo do nó é menor que o geohash 
            elif index_maior_prefixo == len(rotulo_next_node):
                temp_geohash = temp_geohash[index_maior_prefixo:]
                current_node = next_node

            #Geohash não bateu com rótulo
            else:
                return []
        return self.agregar_entregadores(current_node)

    def agregar_entregadores(self, current_node):
        total_entregadores = []

        #Vemos se é nó folha vendo se existe entregador adicionado
        if current_node.entregadores:
            total_entregadores.extend(current_node.entregadores)

        for next_node in current_node.filhos.values():
            total_entregadores.extend(self.agregar_entregadores(next_node))

        return total_entregadores
    

