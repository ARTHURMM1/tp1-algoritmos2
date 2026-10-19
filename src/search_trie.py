
class Node:
    def __init__(self):
        self.children = {}
        self.is_end = False


class SearchTrie:
    def __init__(self):
        self.root = Node()

    def add(self, nome):
        nome = nome.upper()
        current = self.root

        for char in nome:
            if char not in current.children:
                current.children[char] = Node()

            current = current.children[char]

        current.is_end = True

    def search(self, prefix):
        prefix = prefix.upper()
        current = self.root

        # Encontra o nó correspondente ao prefixo
        for char in prefix:
            if char not in current.children:
                return []

            current = current.children[char]

        # Recupera todos os nomes a partir desse nó
        resultados = []

        def dfs(node, palavra):
            if node.is_end:
                resultados.append(palavra)

            for char, filho in node.children.items():
                dfs(filho, palavra + char)

        dfs(current, prefix)

        return resultados
