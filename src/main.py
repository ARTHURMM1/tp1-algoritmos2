import gerar_entregadores #gera uma lista de entregadores, n sendo o numero de entregadores cada um tem {id, lat, lon}
import projecao_nas_ruas #atualiza lat, lon de cada entregador
import geohash #constroi um dict em que cada entregador tem seu geohash entao temos {entregador: geohash}
import trie #constroe a trie inserindo cada um, O(n + m) onde m é o tamanho do geohash que no nosso caso é m = 8. comando: trie.insert(geohash, entregador)

#aplicacao tem caixa de busca usando KMP(?) para procurar em nome do restaurante / nome de rua e retorna (lat, lon) do restaurante

######
#busca = geohash(lat, lon)

#CELULA CENTRAL
#entregadores_candidatos = trie.search(busca[5:]) usamos precisao 5 pois cada celula tem aprox 4km

#VIZINHOS
#vizinhos_hash = geohash_neighbours(busca[5:])
#for v in vizinhos_hash : 
#   entregadores_canditados.extend(trie.search(v))

#aqui damos um zoom nos 9 blocos e colorimos os pontos no mapa de cada entregador, entao temos a primeira lista com id: lat,lon (gerar um ponto no mapa com cor cinza em lat, lon)