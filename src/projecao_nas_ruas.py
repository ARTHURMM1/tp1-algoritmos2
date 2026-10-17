
from functools import lru_cache
from pathlib import Path

import osmnx as ox


@lru_cache(maxsize=1)
def _carregar_grafo_viario():
    caminho_cache = (
        Path(__file__).resolve().parents[1]
        / "cache"
        / "belo_horizonte_drive.graphml"
    )

    if caminho_cache.exists():
        print(f"Carregando rede viária do cache: {caminho_cache}", flush=True)
        return ox.load_graphml(caminho_cache)

    print("Baixando a rede viária de Belo Horizonte do OpenStreetMap...", flush=True)
    grafo = ox.graph_from_place(
        'Belo Horizonte, Minas Gerais, Brazil',
        network_type='drive'
    )
    caminho_cache.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(grafo, caminho_cache)
    print(f"Rede viária salva em: {caminho_cache}", flush=True)
    return grafo


def projetar_nas_ruas_mais_proximas(
    entregadores: dict[int, tuple[float, float]]
) -> dict[int, tuple[float, float]]:
    """
    Projeta os entregadores nos nós mais próximos da rede viária.

    Entrada: {id: (latitude, longitude), ...}
    Saída: {id: (lat, lon)}
    """

    if not entregadores:
        return {}

    grafo_osm = _carregar_grafo_viario()

    ids = list(entregadores)
    latitudes = [entregadores[id][0] for id in ids]
    longitudes = [entregadores[id][1] for id in ids]

    nos_proximos = ox.distance.nearest_nodes(
        grafo_osm,
        X=longitudes,
        Y=latitudes
    )

    entregadores_projetados = {}

    for id, no_id in zip(ids, nos_proximos):
        lat = grafo_osm.nodes[no_id]['y']
        lon = grafo_osm.nodes[no_id]['x']

        entregadores_projetados[id] = (lat, lon)

    return entregadores_projetados
