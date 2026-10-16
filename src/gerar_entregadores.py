
import numpy as np

KM_PARA_GRAUS = 1.0 / 111.0

def _gerar_entregadores(
    restaurante,
    numero_de_entregadores: int,
    sigma_km: float
) -> list[tuple[float, float]]:
    """
    Gera entregadores próximos a um restaurante.
    """

    sigma_lat = sigma_km * KM_PARA_GRAUS

    # Corrige a conversão de km para longitude
    sigma_lon = sigma_lat / np.cos(
        np.radians(restaurante.latitude)
    )

    latitudes = np.random.normal(
        loc=restaurante.latitude,
        scale=sigma_lat,
        size=numero_de_entregadores
    )

    longitudes = np.random.normal(
        loc=restaurante.longitude,
        scale=sigma_lon,
        size=numero_de_entregadores
    )

    return list(zip(latitudes, longitudes))


def gerar_entregadores(
    restaurantes,
    num_entregadores: int,
    sigma_km: float
) -> dict[int, tuple[float, float]]:
    """
    Gera entregadores distribuídos entre restaurantes.

    Retorna:
        {id: (latitude, longitude)}
    """

    numero_restaurantes = len(restaurantes)

    if numero_restaurantes <= 0:
        raise ValueError("O numero de restaurantes não pode ser zero")

    if num_entregadores <= 0:
        raise ValueError("O numero de entregadores precisa ser maior que zero")

    if num_entregadores < numero_restaurantes:
        raise ValueError("Não é possivel ter menos entregadores do que restaurantes")

    if sigma_km < 0:
        raise ValueError("O desvio padrão não pode ser negativo")

    entregadores_por_restaurante = (
        num_entregadores // numero_restaurantes
    )

    entregadores_restantes = (
        num_entregadores % numero_restaurantes
    )

    entregadores = {}
    proximo_id = 0

    for restaurante in restaurantes:

        quantidade = entregadores_por_restaurante

        if entregadores_restantes > 0:
            quantidade += 1
            entregadores_restantes -= 1

        gerados = _gerar_entregadores(
            restaurante, quantidade, sigma_km
        )

        for lat, lon in gerados:
            entregadores[proximo_id] = (
                float(lat), float(lon)
            )
            proximo_id += 1

    return entregadores
