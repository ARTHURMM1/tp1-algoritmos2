"""
Vamos gerar entregadores de forma aleatoria em torno de cada restaurante.

Cada restaurante vai ter (total_entregadores / num_restaurantes) entregadodes

Vamos usar a distribuição normal para distribuir os entregadores. 
Para gerar para um restaurante especifico, vamos usar como média, 
as suas coordenadas (lati, long).
Para o desvio padrão vamos converter km_para_graus = 1 / 111
E agora escolhermos sigma_km, em que sigma_graus = sigma_km*km_para_graus 
"""

import numpy as np

KM_PARA_GRAUS = 1.0 / 111.0

def _gerar_entregadores(restaurante, numero_de_entregadores: int, sigma_km: float) -> list[list[float]]:
    """
    Gera entregadores próximos a um restaurante.
    Usando distribuição normal, com média (latitude, longetude) do restaurante
    E desvio padrão como sigma_km convertido para graus.
    """

    sigma_graus = sigma_km * KM_PARA_GRAUS
    entregadores = []

    latitudes_simuladas = np.random.normal(loc=restaurante['latitude'], scale=sigma_graus, size=numero_de_entregadores)
    longitudes_simuladas = np.random.normal(loc=restaurante['longitude'], scale=sigma_graus, size=numero_de_entregadores)

    for lati, long in zip(latitudes_simuladas, longitudes_simuladas):
        entregadores.append([lati, long])

    return entregadores

def gerar_entregadores(restaurantes, num_entregadores: int, sigma_km: float) -> list[list[float]]:
    """
    Gera todos os entregadores perto de cada restarante.
    """

    numero_restaurantes = len(restaurantes)

    if numero_restaurantes <= 0: raise ValueError("O numero de restaurantes não pode ser zero")
    if num_entregadores <= 0: raise ValueError("O numero de entregadores precisa ser maior que zero")
    if sigma_km < 0 : raise ValueError("O desvio padrão não pode ser negativo")
  
    entregadores_por_restaurante = num_entregadores // numero_restaurantes
    entregadores_restantes = num_entregadores - entregadores_por_restaurante*numero_restaurantes

    mais_um = 0
    entregadores = []
    for restaurante in restaurantes:

        # Aloca os estregadores restantes
        if entregadores_restantes > 0: 
            mais_um = 1
            entregadores_restantes -= 1
        else: mais_um = 0

        entregadores.extend(_gerar_entregadores(restaurante, entregadores_por_restaurante+mais_um, sigma_km))

    return entregadores

