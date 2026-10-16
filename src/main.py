import gerar_entregadores #gera uma lista de entregadores, n sendo o numero de entregadores cada um tem {id, lat, lon}
import projecao_nas_ruas #atualiza lat, lon de cada entregador
import geohash #constroi um dict em que cada entregador tem seu geohash entao temos {entregador: geohash}
import trie #constroe a trie inserindo cada um, O(n + m) onde m é o tamanho do geohash que no nosso caso é m = 8. comando: trie.insert(geohash, entregador)

#aplicacao tem caixa de busca usando KMP(?) para procurar em nome do restaurante / nome de rua e retorna (lat, lon) do restaurante

# Raio máximo garantido (km), aproximadamente para BH
PRECISOES = {
    3: 147.0,
    4: 19.5,
    5: 4.6,
    6: 0.61,
    7: 0.144,
    8: 0.019
}

def celula_busca(raio_km=2):
    if raio_km <= 0:
        raise ValueError("O raio deve ser positivo")

    for precision in reversed(PRECISOES):
        if PRECISOES[precision] >= raio_km:
            return precision

    raise ValueError("Raio maior que o suportado")

#CELULA_BUSCA = celula_busca() <-raio da caixa de busca aqui, dafault 2km

#busca = geohash(lat, lon)

# id_candidatos = set(trie.search(busca[:CELULA_BUSCA])) #usamos set pra evitar repeticao de id

# for vizinho in geohash_neighbors(busca[:CELULA_BUSCA]).values():
#     id_candidatos.update(trie.search(vizinho))

#id_candidatos tem o ID dos entregadores

#aqui damos um zoom nos 9 blocos e colorimos os pontos no mapa de cada entregador, no ponto entregadores[id] para cada id em id_candidatos.values()
#pintar de vermelho os que estao a RAIO de distancia do restaurante
