class TrieNode :
    def __init__(self, prefix=""):
        self.prefix = prefix
        self.children = {}
        self.deliverers = []


class Trie :
    def __init__(self):
        self.root = TrieNode()

    # comecamos na raiz, e procuramos pelo hashing. se nao existir 
    def add(self, geohash, deliverer) :
        
        current = self.root

        for char in geohash:
            if char not in current.children :
                current.children[char] = TrieNode()

            current = current.children[char]

        self.deliverers.append(deliverer)

    def insert(self, hash, deliverer) :
        current = self.root

        resto = hash

        while resto :
            #se o no esta vazio, adiciona tudo
            if not current.children :
                new_node = TrieNode(resto)
                new_node.deliverers.append(deliverer)
                current.children[resto[0]] = new_node
                return
        
            encontrou = False #ainda nao encontramos
            
            for c in current.children.values() : #iteramos sobre cada filho para saber qual prefixo eh comum a ele
                i = self.common_prefix(resto, c.prefix)
                if i == 0 : #se nao casar, continue a procurar
                    continue

                encontrou = True #caso contrario ele encontrou algum prefixo comum

                if i == len(c.prefix) : # se conter completamente, atualiza o resto e vai para o proximo
                    current = c
                    resto = resto[i:]
                    break

                #caso contrario, eles diferem em algum sufixo entao deve quebrar. o antigo deve manter as informacoes
                new_prefix = resto[i:]
                old_prefix = c.prefix[i:]
                old_children = c.children
                old_deliverers = c.deliverers

                #limpa o no atual antes de reatribuir os valores
                c.children = {} 
                c.deliverers = []
                

                #realiza a quebra
                c.prefix = c.prefix[:i]
                #carry do no antigo
                c.children[old_prefix[0]] = TrieNode(old_prefix)
                c.children[old_prefix[0]].children = old_children
                c.children[old_prefix[0]].deliverers = old_deliverers

                #adiciona o novo 
                c.children[new_prefix[0]] = TrieNode(new_prefix)
                c.children[new_prefix[0]].deliverers.append(deliverer)

                return

            if not encontrou : 
                new_node = TrieNode(resto)
                new_node.deliverers.append(deliverer)
                current.children[resto[0]] = new_node
                return
                        

            
    def common_prefix(a, b) :
        i = 0
        while i < len(a) and i < len(b) and a[i] == b[i] :

            i+= 1

        return i

        



