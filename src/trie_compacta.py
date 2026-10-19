import geohash as gh


class TrieNode :
    def __init__(self, prefix=""):
        self.prefix = prefix
        self.children = {}
        self.deliverers = []


class Trie :
    def __init__(self):
        self.root = TrieNode()
    
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
                        

            
    def common_prefix(self, a, b) :
        i = 0
        while i < len(a) and i < len(b) and a[i] == b[i] :
            i+= 1
        return i

    #busca gulosa a partir do atual:
    def retorna_entregadores(self, node) :
        entregadores = []
        entregadores.extend(node.deliverers)

        for filho in node.children.values() :
            entregadores.extend(self.retorna_entregadores(filho))
        return entregadores


    def search_prefix(self, prefix) :
        atual = self.root
        pref_atual = prefix
        if not prefix:
            return self.retorna_entregadores(self.root)

        while pref_atual:
            filho = atual.children.get(pref_atual[0])
            if filho is None :
                return []
            tamanho_comum = self.common_prefix(pref_atual, filho.prefix)
            if tamanho_comum == len(pref_atual) :
                return self.retorna_entregadores(filho)

            elif tamanho_comum == len(filho.prefix):
                atual = filho
                pref_atual = pref_atual[tamanho_comum:]
            else :
                return []

    # busca entregadores dentro do raio podando ramos da trie fora do alcance
    def search_radius(self, lat, lon, raio_km, precision=6):
        celulas = []
        candidatos = set()

        def coletar_subarvore(node, pref):
            if len(pref) >= precision:
                celulas.append(pref[:precision])
                candidatos.update(self.retorna_entregadores(node))
                return
            if node.deliverers:
                candidatos.update(node.deliverers)
            for filho in node.children.values():
                coletar_subarvore(filho, pref + filho.prefix)

        def dfs(node, pref):
            if pref:
                if len(pref) >= precision:
                    celula = pref[:precision]
                    if gh.distancia_celula(lat, lon, celula) <= raio_km:
                        celulas.append(celula)
                        candidatos.update(self.retorna_entregadores(node))
                    return
                if gh.distancia_celula(lat, lon, pref) > raio_km:
                    return
                if gh.caixa_totalmente_dentro(lat, lon, pref, raio_km):
                    coletar_subarvore(node, pref)
                    return
            if node.deliverers:
                candidatos.update(node.deliverers)
            for filho in node.children.values():
                dfs(filho, pref + filho.prefix)

        dfs(self.root, "")
        return celulas, candidatos
        



