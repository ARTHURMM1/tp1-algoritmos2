BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
def bin_to_base32(binary) :
    return "".join(
        BASE32[int(binary[i:i+5], 2)]
        for i in range(0, len(binary), 5)
    )


def geohash(x, y, precision=8) :
    if (precision > 8) : 
        return ValueError
    
    s = ""
    
    latDown, latUp = -90, 90
    lonDown, lonUp = -180, 180

    
    for _ in range(20) :

        lonMid = (lonUp + lonDown) / 2
        latMid = (latUp + latDown) / 2
        
        if (x >= lonMid) :
            s = s + '1'
            lonDown = lonMid
        else :
            s = s + '0'
            lonUp = lonMid
        

        if (y >= latMid) :
            s = s + '1'
            latDown = latMid
        else :
            s = s + '0'
            latUp = latMid
        
    return bin_to_base32(s)[:precision]

def geohash_neighbors(hash): # retorna um dict de vizinhos para busca
    # Converte Base32 para binário
    bits = "".join(
        f"{BASE32.index(c):05b}" for c in hash
    )

    # Separa longitude e latitude
    lon_bits = bits[::2]
    lat_bits = bits[1::2]

    lon = int(lon_bits, 2)
    lat = int(lat_bits, 2)

    n_lon = 1 << len(lon_bits)
    n_lat = 1 << len(lat_bits)

    directions = {
        "N":  (0, 1),
        "S":  (0, -1),
        "E":  (1, 0),
        "W":  (-1, 0),
        "NE": (1, 1),
        "NW": (-1, 1),
        "SE": (1, -1),
        "SW": (-1, -1)
    }

    neighbors = {}

    for direction, (dx, dy) in directions.items():
        # Longitude dá a volta no globo
        new_lon = (lon + dx) % n_lon
        new_lat = lat + dy

        # Não ultrapassa os polos
        if not 0 <= new_lat < n_lat:
            continue

        # Reconstrói os bits intercalados
        x = f"{new_lon:0{len(lon_bits)}b}"
        y = f"{new_lat:0{len(lat_bits)}b}"

        new_bits = "".join(
            x[i // 2] if i % 2 == 0 else y[i // 2]
            for i in range(len(bits))
        )

        # Converte novamente para Base32
        neighbors[direction] = "".join(
            BASE32[int(new_bits[i:i+5], 2)]
            for i in range(0, len(new_bits), 5)
        )

    return neighbors

def decode_geohash(hash): #decodifica o geohash em latitude e longitude
    bits = "".join(
        f"{BASE32.index(c):05b}" for c in hash
    )

    lon_min, lon_max = -180.0, 180.0
    lat_min, lat_max = -90.0, 90.0

    for i, bit in enumerate(bits):
        if i % 2 == 0:
            mid = (lon_min + lon_max) / 2
            if bit == "1":
                lon_min = mid
            else:
                lon_max = mid
        else:
            mid = (lat_min + lat_max) / 2
            if bit == "1":
                lat_min = mid
            else:
                lat_max = mid

    return lat_min, lat_max, lon_min, lon_max


from collections import deque
from math import radians, sin, cos, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):#calcula distancia entre 2 pontos considerando a terra esferica 
    R = 6371  # km - raio da terra

    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2)**2
        + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    )

    return 2 * R * asin(sqrt(a))

def distancia_celula(lat, lon, hash): #calcula distancia geodesica minima até a origem, considerando a terra esferica
    R = 6371 #km - raio da terra
    lat_min, lat_max, lon_min, lon_max = decode_geohash(hash)

    # Distância angular mínima até o retângulo.
    # Considera também a continuidade na longitude ±180°.
    phi = radians(lat)
    a = radians(lat_min)
    b = radians(lat_max)

    dlon = min(
        abs((lon - lon_min + 180) % 360 - 180),
        abs((lon - lon_max + 180) % 360 - 180)
    )

    if lon_min <= lon <= lon_max:
        dlon = 0.0

    delta = radians(dlon)

    # Maximiza o cosseno da distância angular
    # em relação à latitude da célula.
    from math import atan2
    phi_ideal = atan2(sin(phi), cos(phi) * cos(delta))
    phi_ideal = max(a, min(b, phi_ideal))

    c = (
        sin(phi) * sin(phi_ideal)
        + cos(phi) * cos(phi_ideal) * cos(delta)
    )
    c = max(-1.0, min(1.0, c))

    from math import acos
    return R * acos(c)

def buscar_celulas(lat, lon, raio_km, precision=5):#retorna as celulas dentro do raio 
    origem = geohash(lon, lat, precision)

    visitados = {origem}
    fila = deque([origem])
    celulas = []

    while fila:
        atual = fila.popleft()
        celulas.append(atual)

        for vizinho in geohash_neighbors(atual).values():
            if vizinho in visitados:
                continue

            visitados.add(vizinho)

            if distancia_celula(lat, lon, vizinho) <= raio_km:
                fila.append(vizinho)

    return celulas



