from pathlib import Path
import sys
import time
import math
import heapq
import unicodedata

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from dash import Dash, html, dcc, Input, Output, State, ALL, ctx, no_update
import dash_leaflet as dl

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "src"))

import geohash
import gerar_entregadores
import projecao_nas_ruas
import search_trie
import trie_compacta

PRECISAO_INDICE = 8
PRECISAO_CELULAS = 6
SIGMA_KM = 1.5
DISTANCIA_RUA_M = 100
LIMITE_TABELA = 100

ASSETS = BASE / "assets"
CSV = ASSETS / "bares_coords.csv"
bares = pd.read_csv(CSV).dropna(subset=['NOME', 'Y', 'X']).copy().reset_index(drop=True)
bares['NOME'] = bares['NOME'].astype(str)
bares['Y'] = pd.to_numeric(bares['Y'], errors='coerce')
bares['X'] = pd.to_numeric(bares['X'], errors='coerce')
bares = bares.dropna(subset=['Y', 'X']).reset_index(drop=True)
restaurantes = bares[['Y', 'X']].rename(columns={'Y': 'latitude', 'X': 'longitude'}).to_dict('records')


def normalizar(nome):
    sem_acentos = ''.join(c for c in unicodedata.normalize('NFKD', str(nome)) if not unicodedata.combining(c))
    return ' '.join(sem_acentos.upper().split())


arvore_nomes = search_trie.SearchTrie()
unidades_por_nome = {}
for identificador, registro in bares.iterrows():
    chave = normalizar(registro['NOME'])
    if chave not in unidades_por_nome:
        arvore_nomes.add(chave)
        unidades_por_nome[chave] = []
    unidades_por_nome[chave].append(int(identificador))

arvore_ruas = search_trie.SearchTrie()
ruas_por_nome = {}
rotulos_ruas = {}
crs_metrico = None
pontos_restaurantes = None
indice_restaurantes = None


def carregar_ruas():
    global crs_metrico, pontos_restaurantes, indice_restaurantes
    if crs_metrico is not None:
        return
    grafo = projecao_nas_ruas._carregar_grafo_viario()
    import osmnx as ox
    arestas = ox.graph_to_gdfs(grafo, nodes=False, fill_edge_geometry=True)
    if arestas.crs is None:
        arestas = arestas.set_crs('EPSG:4326')
    crs_metrico = arestas.estimate_utm_crs()
    arestas = arestas.to_crs(crs_metrico)
    for _, aresta in arestas.iterrows():
        nomes = aresta.get('name')
        if isinstance(nomes, str):
            nomes = [nomes]
        if not isinstance(nomes, (list, tuple)):
            continue
        for nome in nomes:
            if not isinstance(nome, str) or not nome.strip():
                continue
            chave = normalizar(nome)
            if chave not in ruas_por_nome:
                ruas_por_nome[chave] = []
                rotulos_ruas[chave] = nome
                arvore_ruas.add(chave)
            ruas_por_nome[chave].append(aresta.geometry)
    pontos_restaurantes = gpd.GeoDataFrame(
        bares[['NOME']].copy(),
        geometry=gpd.points_from_xy(bares['X'], bares['Y']),
        crs='EPSG:4326',
    ).to_crs(crs_metrico)
    indice_restaurantes = pontos_restaurantes.sindex
    print(f'{len(ruas_por_nome)} nomes de ruas indexados.', flush=True)


entregadores = {}
arvore_espacial = trie_compacta.Trie()


def construir_indice(posicoes):
    arvore = trie_compacta.Trie()
    for identificador, (lat, lon) in posicoes.items():
        arvore.insert(geohash.geohash(lon, lat, PRECISAO_INDICE), identificador)
    return arvore


def consultar_entregadores(lat, lon, raio_km):
    celulas, candidatos = arvore_espacial.search_radius(
        lat, lon, raio_km, precision=PRECISAO_CELULAS
    )
    proximos = {}
    for identificador in candidatos:
        lat_e, lon_e = entregadores[identificador]
        distancia = geohash.haversine(lat, lon, lat_e, lon_e)
        if distancia <= raio_km:
            proximos[identificador] = distancia
    return celulas, candidatos, proximos


grafo_tempos = None


def obter_grafo_tempos():
    global grafo_tempos
    if grafo_tempos is None:
        import osmnx as ox
        grafo = projecao_nas_ruas._carregar_grafo_viario()
        grafo_tempos = grafo.copy()
        grafo_tempos = ox.routing.add_edge_speeds(grafo_tempos, fallback=30)
        grafo_tempos = ox.routing.add_edge_travel_times(grafo_tempos)
    return grafo_tempos


# calcula distancia e tempo viario dos entregadores ate o restaurante usando dijkstra reverso
def estimar_rotas(restaurante, proximos):
    if not proximos:
        return {}
    import osmnx as ox
    grafo = obter_grafo_tempos()
    ids = list(proximos)
    latitudes = [entregadores[i][0] for i in ids]
    longitudes = [entregadores[i][1] for i in ids]
    origens = ox.distance.nearest_nodes(grafo, X=longitudes, Y=latitudes)
    destino = ox.distance.nearest_nodes(grafo, X=restaurante['lon'], Y=restaurante['lat'])
    por_no = {}
    for i, no in zip(ids, origens):
        por_no.setdefault(no, []).append(i)
    pendentes = set(por_no)
    melhores = {destino: (0.0, 0.0)}
    fila = [(0.0, 0.0, destino)]
    saida = {}
    while fila and pendentes:
        tempo, metros, no = heapq.heappop(fila)
        if (tempo, metros) != melhores.get(no):
            continue
        if no in pendentes:
            for i in por_no[no]:
                saida[i] = (metros / 1000, tempo / 60)
            pendentes.remove(no)
        for anterior, arestas in grafo.pred[no].items():
            for atributos in arestas.values():
                t = float(atributos.get('travel_time', math.inf))
                d = float(atributos.get('length', math.inf))
                if not (math.isfinite(t) and math.isfinite(d)):
                    continue
                proposta = (tempo + t, metros + d)
                if proposta < melhores.get(anterior, (math.inf, math.inf)):
                    melhores[anterior] = proposta
                    heapq.heappush(fila, (*proposta, anterior))
    return saida


def dados_restaurante(identificador):
    registro = bares.loc[identificador]
    return {'id': int(identificador), 'nome': str(registro['NOME']),
            'lat': float(registro['Y']), 'lon': float(registro['X'])}


def marcador_restaurante(identificador):
    r = dados_restaurante(identificador)
    return dl.Marker(
        id={'type': 'pin-restaurante', 'index': int(identificador)},
        position=[r['lat'], r['lon']],
        children=[dl.Tooltip(f"{r['nome']} (ID {identificador})"),
                  dl.Popup(f"{r['nome']} - clique no pin para selecionar")],
    )


def restaurantes_proximos_rua(chave):
    geometria = unary_union(ruas_por_nome[chave])
    buffer = geometria.buffer(DISTANCIA_RUA_M)
    candidatos = indice_restaurantes.query(buffer, predicate='intersects')
    ids = sorted(int(i) for i in candidatos)
    geometria_wgs84 = gpd.GeoSeries([geometria], crs=crs_metrico).to_crs('EPSG:4326').iloc[0]
    return ids, geometria_wgs84


def linhas_leaflet(geom):
    if geom.geom_type == 'LineString':
        return [dl.Polyline(positions=[[y, x] for x, y in geom.coords],
                            color='#2563eb', weight=5)]
    if geom.geom_type == 'MultiLineString':
        return [dl.Polyline(positions=[[y, x] for x, y in linha.coords],
                            color='#2563eb', weight=5)
                for linha in geom.geoms]
    return []


PONTO_ENTREGADOR = {"variable": "dashExtensions.default.pontoEntregador"}
PONTO_RESULTADO = {"variable": "dashExtensions.default.pontoResultado"}


def geojson_resultados(candidatos, proximos, lat, lon):
    features = []
    for identificador in candidatos:
        lat_e, lon_e = entregadores[identificador]
        distancia = proximos.get(identificador)
        dentro = distancia is not None
        if distancia is None:
            distancia = geohash.haversine(lat, lon, lat_e, lon_e)
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(lon_e), float(lat_e)]
            },
            'properties': {
                'id': int(identificador),
                'dentro': dentro,
                'distancia_km': float(distancia),
            },
        })
    return {'type': 'FeatureCollection', 'features': features}


def geojson_entregadores(posicoes):
    return {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [float(lon), float(lat)]},
                'properties': {'id': int(identificador)},
            }
            for identificador, (lat, lon) in posicoes.items()
        ],
    }


app = Dash(__name__, assets_folder=str(ASSETS))
app.layout = html.Div([
    dcc.Store(id='restaurante-selecionado'),
    dcc.Store(id='versao-entregadores', data=0),
    html.Div([
      html.Div([
        html.Div([
            dcc.Dropdown(id='input-pesquisa', options=[], searchable=True, clearable=True,
                         placeholder='Restaurante ou rua', style={'width': '100%', 'minWidth': '0', 'flex': '1'}),
            html.Button('Buscar', id='btn-pesquisa'),
        ], style={'display': 'flex', 'gap': '6px', 'alignItems': 'center', 'width': '100%'}),
        html.Div([
            dcc.Input(id='input-gerador', type='number', min=0, step=1, value=500,
                      style={'width': '90px'}),
            html.Button('Gerar entregadores', id='btn-gerador'),
        ], style={'display': 'flex', 'gap': '6px', 'alignItems': 'center'}),
        html.Div([
            html.Span('Raio (km):'),
            dcc.Input(id='input-raio', type='number', min=0, step='any', value=2,
                      style={'width': '75px'}),
            html.Button('Buscar entregadores', id='btn-busca'),
            dcc.Checklist(id='mostrar-raio',
                          options=[{'label': 'Mostrar raio', 'value': 'sim'}],
                          value=['sim'], inline=True),
        ], style={'display': 'flex', 'gap': '6px', 'alignItems': 'center'}),
        html.Div(id='status-rua', style={'fontSize': '12px'}),
        html.Div(id='status', style={'fontSize': '12px'}),
      ], style={
          'backgroundColor': 'white', 'padding': '12px', 'borderRadius': '8px',
          'boxShadow': '0 2px 6px rgba(0,0,0,.25)', 'display': 'flex',
          'flexDirection': 'column', 'gap': '9px'
      }),
      html.Div([
          html.H4('Entregadores dentro do raio', style={'margin': '0 0 8px', 'fontSize': '15px'}),
          html.Div('0 entregadores dentro do raio.', id='metricas-resumo', style={'marginBottom': '9px', 'fontSize': '12px'}),
          html.Div('Nenhum resultado para apresentar.', id='tabela-entregadores', style={'fontSize': '12px'}),
      ], style={
          'backgroundColor': 'white', 'padding': '12px', 'borderRadius': '8px',
          'boxShadow': '0 2px 6px rgba(0,0,0,.25)', 'maxHeight': '42vh',
          'overflowY': 'auto', 'overflowX': 'auto'
      }),
    ], style={
        'position': 'absolute', 'top': '15px', 'left': '60px', 'zIndex': 1000,
        'width': '390px', 'maxWidth': 'calc(100% - 75px)',
        'display': 'flex', 'flexDirection': 'column', 'gap': '10px'
    }),
    dl.Map([
        dl.TileLayer(),
        dl.LayerGroup(id='grupo-rua'),
        dl.LayerGroup(id='grupo-restaurantes'),
        dl.GeoJSON(
            id='geojson-entregadores',
            data={'type': 'FeatureCollection', 'features': []},
            zoomToBounds=False,
            options={'pointToLayer': PONTO_ENTREGADOR},
        ),
        dl.GeoJSON(
            id='geojson-resultados',
            data={'type': 'FeatureCollection', 'features': []},
            zoomToBounds=False,
            options={'pointToLayer': PONTO_RESULTADO},
        ),
        dl.LayerGroup(id='grupo-raio'),
    ], id='mapa-principal', center=[-19.922757, -43.945137], zoom=14,
        preferCanvas=True,
        style={'height': '100%', 'width': '100%'}),
], style={
    "width": "100%",
    "height": "100vh",
})


@app.callback(
    Output('input-pesquisa', 'options'),
    Input('input-pesquisa', 'search_value'),
    State('input-pesquisa', 'value'),
)
def sugerir_opcoes(texto, selecionado):
    if not texto or not texto.strip():
        return no_update
    opcoes = []
    chave = normalizar(texto)
    for nome in arvore_nomes.search(chave):
        for identificador in unidades_por_nome[nome]:
            r = dados_restaurante(identificador)
            opcoes.append({'label': f"[Restaurante] {r['nome']} ({r['lat']:.5f}, {r['lon']:.5f})",
                           'value': f'r:{identificador}'})
            if len(opcoes) >= 20:
                break
        if len(opcoes) >= 20:
            break
    for nome in arvore_ruas.search(chave)[:20]:
        opcoes.append({'label': f"[Rua] {rotulos_ruas[nome]}", 'value': f's:{nome}'})
    if selecionado is not None and not any(o['value'] == selecionado for o in opcoes):
        if selecionado.startswith('r:'):
            identificador = int(selecionado[2:])
            r = dados_restaurante(identificador)
            opcoes.insert(0, {'label': f"[Restaurante] {r['nome']} ({r['lat']:.5f}, {r['lon']:.5f})",
                              'value': selecionado})
        elif selecionado.startswith('s:') and selecionado[2:] in rotulos_ruas:
            opcoes.insert(0, {'label': f"[Rua] {rotulos_ruas[selecionado[2:]]}",
                              'value': selecionado})
    return opcoes


@app.callback(
    Output('grupo-restaurantes', 'children'),
    Output('grupo-rua', 'children'),
    Output('mapa-principal', 'viewport'),
    Output('restaurante-selecionado', 'data'),
    Output('status-rua', 'children'),
    Input('btn-pesquisa', 'n_clicks'),
    Input('input-pesquisa', 'value'),
    Input({'type': 'pin-restaurante', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def buscar_local(_, valor, cliques_pins):
    origem = ctx.triggered_id
    if isinstance(origem, dict) and origem.get('type') == 'pin-restaurante':
        if not ctx.triggered or not ctx.triggered[0].get('value'):
            return (no_update,) * 5
        identificador = int(origem['index'])
        r = dados_restaurante(identificador)
        return no_update, no_update, {'center': [r['lat'], r['lon']], 'zoom': 16}, r, f"Selecionado: {r['nome']} (ID {identificador})"
    if origem not in ('btn-pesquisa', 'input-pesquisa') or not valor:
        return (no_update,) * 5
    if valor.startswith('r:'):
        identificador = int(valor[2:])
        r = dados_restaurante(identificador)
        return [marcador_restaurante(identificador)], [], {'center': [r['lat'], r['lon']], 'zoom': 16}, r, f"Selecionado: {r['nome']} (ID {identificador})"
    if valor.startswith('s:'):
        chave = valor[2:]
        if chave not in ruas_por_nome:
            return (no_update,) * 5
        inicio = time.perf_counter()
        ids, geometria = restaurantes_proximos_rua(chave)
        linhas = linhas_leaflet(geometria)
        if not linhas:
            return [], [], no_update, None, 'Rua sem geometria disponível.'
        x1, y1, x2, y2 = geometria.bounds
        centro = [(y1 + y2) / 2, (x1 + x2) / 2]
        zoom = 14 if max(y2 - y1, x2 - x1) < 0.035 else 12
        return ([marcador_restaurante(i) for i in ids], linhas, {'center': centro, 'zoom': zoom},
                None, f"{rotulos_ruas[chave]}: {len(ids)} restaurantes proximos. "
                      f"Clique em um pin para selecionar. Consulta: {time.perf_counter() - inicio:.3f}s")
    return (no_update,) * 5


@app.callback(
    Output('geojson-entregadores', 'data'),
    Output('versao-entregadores', 'data'),
    Input('btn-gerador', 'n_clicks'),
    State('input-gerador', 'value'),
    State('versao-entregadores', 'data'),
    prevent_initial_call=True,
)
def gerar_e_indexar(_, quantidade, versao):
    global entregadores, arvore_espacial
    try:
        quantidade = int(quantidade)
        if quantidade < 0:
            return no_update, no_update
    except (TypeError, ValueError):
        return no_update, no_update
    inicio = time.perf_counter()
    novos = gerar_entregadores.gerar_entregadores(restaurantes, quantidade, SIGMA_KM)
    novos = projecao_nas_ruas.projetar_nas_ruas_mais_proximas(novos)
    novo_indice = construir_indice(novos)
    entregadores, arvore_espacial = novos, novo_indice
    print(f'{len(novos)} entregadores indexados em {time.perf_counter() - inicio:.3f}s', flush=True)
    return geojson_entregadores(novos), (versao or 0) + 1


def apresentar_resultados(linhas):
    if not linhas:
        return '0 entregadores dentro do raio.', 'Nenhum resultado para apresentar.'
    viaveis = [x for x in linhas if x['tempo_min'] is not None]
    media_tempo = sum(x['tempo_min'] for x in viaveis) / len(viaveis) if viaveis else None
    media_distancia = sum(x['distancia_geografica'] for x in linhas) / len(linhas)
    resumo = (f"{len(linhas)} entregadores no raio | "
              f"distância geográfica média: {media_distancia:.2f} km | "
              f"tempo médio estimado: {media_tempo:.1f} min" if media_tempo is not None
              else f"{len(linhas)} entregadores no raio | nenhum percurso viário encontrado")
    if len(linhas) > LIMITE_TABELA:
        resumo += f" (mostrando os {LIMITE_TABELA} mais rápidos)"
    cabecalho = html.Tr([html.Th(t) for t in ('ID', 'Distância geográfica (km)',
                    'Distância viária (km)', 'Tempo estimado (min)')])
    corpo = [html.Tr([
        html.Td(x['id']), html.Td(f"{x['distancia_geografica']:.3f}"),
        html.Td('Sem rota' if x['distancia_viaria'] is None else f"{x['distancia_viaria']:.3f}"),
        html.Td('Sem rota' if x['tempo_min'] is None else f"{x['tempo_min']:.2f}"),
    ]) for x in linhas[:LIMITE_TABELA]]
    tabela = html.Div(html.Table([html.Thead(cabecalho), html.Tbody(corpo)],
             style={'width': '100%', 'borderCollapse': 'collapse', 'textAlign': 'left'}),
             style={'maxHeight': '30vh', 'overflowY': 'auto', 'overflowX': 'auto'})
    return resumo, tabela


@app.callback(
    Output('geojson-resultados', 'data'),
    Output('status', 'children'),
    Output('metricas-resumo', 'children'),
    Output('tabela-entregadores', 'children'),
    Input('btn-busca', 'n_clicks'),
    Input('versao-entregadores', 'data'),
    Input('restaurante-selecionado', 'data'),
    State('input-raio', 'value'),
    prevent_initial_call=True,
)
def destacar_proximos(_, versao, restaurante, raio):
    vazio = {'type': 'FeatureCollection', 'features': []}
    if not restaurante:
        return vazio, 'Selecione um restaurante para buscar entregadores.', *apresentar_resultados([])
    try:
        raio = float(raio)
        if not 0 < raio <= 100:
            return vazio, 'Informe um raio maior que zero e de até 100 km.', *apresentar_resultados([])
    except (TypeError, ValueError):
        return vazio, 'Informe um raio válido.', *apresentar_resultados([])
    inicio = time.perf_counter()
    celulas, candidatos, proximos = consultar_entregadores(restaurante['lat'], restaurante['lon'], raio)
    dados = geojson_resultados(candidatos, proximos, restaurante['lat'], restaurante['lon'])
    rotas = estimar_rotas(restaurante, proximos)
    linhas = []
    for identificador, distancia_geografica in proximos.items():
        distancia_viaria, tempo_min = rotas.get(identificador, (None, None))
        linhas.append({'id': int(identificador),
                       'distancia_geografica': round(distancia_geografica, 3),
                       'distancia_viaria': round(distancia_viaria, 3) if distancia_viaria is not None else None,
                       'tempo_min': round(tempo_min, 2) if tempo_min is not None else None})
    linhas.sort(key=lambda x: (x['tempo_min'] is None, x['tempo_min'] if x['tempo_min'] is not None else math.inf))
    resumo, tabela = apresentar_resultados(linhas)
    fora = len(candidatos) - len(proximos)
    status = (f'{len(proximos)} dentro do raio (vermelho) | '
              f'{fora} candidatos fora do raio (laranja) | '
              f'{len(celulas)} células consultadas | '
              f'consulta: {time.perf_counter() - inicio:.4f}s')
    return dados, status, resumo, tabela


@app.callback(
    Output('grupo-raio', 'children'),
    Input('restaurante-selecionado', 'data'),
    Input('input-raio', 'value'),
    Input('mostrar-raio', 'value'),
)
def desenhar_raio(restaurante, raio, mostrar):
    if not restaurante or 'sim' not in (mostrar or []):
        return []
    try:
        raio_km = float(raio)
    except (TypeError, ValueError):
        return []
    if not 0 < raio_km <= 100:
        return []
    return [dl.Circle(center=[restaurante['lat'], restaurante['lon']],
                      radius=raio_km * 1000, color='#2563eb', weight=2,
                      fillColor='#60a5fa', fillOpacity=0.12,
                      children=dl.Tooltip(f'Raio: {raio_km * 1000:g} metros'))]

if __name__ == '__main__':
    carregar_ruas()
    app.run(debug=False)
