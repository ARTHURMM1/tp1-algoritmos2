"""
Vamos pegar as coordenadas dos entregadores (que provavelmente estão em cordenadas invalidas) 
e projeta-los em ruas. 
"""
import osmnx as ox

def projetar_nas_ruas_mais_proximas(entregadores: list[list[float]]) -> list[list[float]]:
    """
    Mapeia os pontos dos entregadores para as coordenadas validas (ruas).
    """

    # Manda a osmnx montar o grafo de ruas de BH
    grafo_osm = ox.graph_from_place('Belo Horizonte, Minas Gerais, Brazil', network_type='drive')

    latitudes = [entregador[0] for entregador in entregadores]
    longitudes = [entregador[1] for entregador in entregadores]

    nos_proximos = ox.distance.nearest_nodes(grafo_osm, X=longitudes, Y=latitudes)

    for entregador, no_id in zip(entregadores, nos_proximos):
        entregador[0] = grafo_osm.nodes[no_id]['y']
        entregador[1] = grafo_osm.nodes[no_id]['x']

    return entregadores

