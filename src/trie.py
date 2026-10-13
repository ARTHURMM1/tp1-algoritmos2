class TrieNode :
    def __init__(self, prefix=""):
        self.prefix = prefix
        self.children = {}
        self.deliverers = []


class Trie :
    def __init__(self):
        self.root = TrieNode()

    # comecamos na raiz, e procuramos pelo hashing. se nao existir. trie padrao
    # def add(self, geohash, deliverer) :
        
    #     current = self.root

    #     for char in geohash:
    #         if char not in current.children :
    #             current.children[char] = TrieNode()

    #         current = current.children[char]

    #     self.deliverers.append(deliverer)

    
    
    # implementacao de insercao compacta
    def insert(self, geohash, deliverer):
        current = self.root
        resto = geohash

        while resto:

            # Se nao existe um filho que comece com o primeiro
            # caractere do resto, adicionamos todo o resto.
            if resto[0] not in current.children:
                new_node = TrieNode(resto)
                new_node.deliverers.append(deliverer)

                current.children[resto[0]] = new_node
                return

            # Se existe, ele eh o unico filho que pode
            # compartilhar prefixo com resto.
            c = current.children[resto[0]]

            i = self.common_prefix(resto, c.prefix)

            # O prefixo do no foi completamente consumido.
            if i == len(c.prefix):

                # Geohash e prefixo sao exatamente iguais.
                if i == len(resto):
                    c.deliverers.append(deliverer)
                    return

                # Ainda sobrou parte do geohash.
                # Descemos na Trie e continuamos com o restante.
                current = c
                resto = resto[i:]
                continue

            # O geohash termina no meio do prefixo existente.
            if i == len(resto):
                old_prefix = c.prefix[i:]
                old_children = c.children
                old_deliverers = c.deliverers

                # c passa a representar o novo prefixo comum.
                c.prefix = resto
                c.children = {}
                c.deliverers = [deliverer]

                # O antigo no vira filho de c.
                old_node = TrieNode(old_prefix)
                old_node.children = old_children
                old_node.deliverers = old_deliverers

                c.children[old_prefix[0]] = old_node
                return

            # Os dois prefixos possuem uma parte comum,
            # mas depois divergem.

            common_prefix = c.prefix[:i]
            old_prefix = c.prefix[i:]
            new_prefix = resto[i:]

            old_children = c.children
            old_deliverers = c.deliverers

            # c vira o no intermediario.
            c.prefix = common_prefix
            c.children = {}
            c.deliverers = []

            # Ramo antigo.
            old_node = TrieNode(old_prefix)
            old_node.children = old_children
            old_node.deliverers = old_deliverers

            c.children[old_prefix[0]] = old_node

            # Novo ramo.
            new_node = TrieNode(new_prefix)
            new_node.deliverers.append(deliverer)

            c.children[new_prefix[0]] = new_node

            return
                        

            
    def common_prefix(a, b) :
        i = 0
        while i < len(a) and i < len(b) and a[i] == b[i] :

            i+= 1

        return i

        



