
import osmnx as ox

def projetar_nas_ruas_mais_proximas(
    entregadores: list[list[float]]
) -> dict[int, tuple[float, float]]:
    """
    Projeta os entregadores nos nós mais próximos da rede viária.

    Entrada: [[lat, lon], ...]
    Saída: {id: (lat, lon)}
    """

    grafo_osm = ox.graph_from_place(
        'Belo Horizonte, Minas Gerais, Brazil',
        network_type='drive'
    )

    latitudes = [e[0] for e in entregadores]
    longitudes = [e[1] for e in entregadores]

    nos_proximos = ox.distance.nearest_nodes(
        grafo_osm,
        X=longitudes,
        Y=latitudes
    )

    entregadores_projetados = {}

    for id, no_id in enumerate(nos_proximos):
        lat = grafo_osm.nodes[no_id]['y']
        lon = grafo_osm.nodes[no_id]['x']

        entregadores_projetados[id] = (lat, lon)

    return entregadores_projetados
