import gerar_entregadores #gera uma lista de entregadores, n sendo o numero de entregadores cada um tem {id, lat, lon}
import projecao_nas_ruas #atualiza lat, lon de cada entregador
import geohash #constroi um dict em que cada entregador tem seu geohash entao temos {entregador: geohash}
import trie #constroe a trie inserindo cada um, O(n + m) onde m é o tamanho do geohash que no nosso caso é m = 8. comando: trie.insert(geohash, entregador)

#aplicacao tem caixa de busca usando KMP(?) para procurar em nome do restaurante / nome de rua e retorna (lat, lon) do restaurante



#aqui damos um zoom nos 9 blocos e colorimos os pontos no mapa de cada entregador, no ponto entregadores[id] para cada id em id_candidatos.values()
#pintar de vermelho os que estao a RAIO de distancia do restaurante
