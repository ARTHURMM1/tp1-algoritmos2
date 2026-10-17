import geohash
import trie
import projecao_nas_ruas
import time
import gerar_entregadores
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State
import dash_leaflet as dl
from dash_extensions.enrich import DashProxy
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

ESTILO_SEARCH_BOX = {
    "position": "absolute",
    "top": "15px",      
    "left": "60px",     
    "zIndex": 1000,     
    "backgroundColor": "white",
    "padding": "10px",
    "borderRadius": "5px",
    "boxShadow": "0 2px 5px rgba(0,0,0,0.3)",
    "display": "flex",
    "gap": "5px"
}

RED_MARKER = dict(
            iconUrl="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
            shadowUrl="https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
            iconSize=[25, 41],
            iconAnchor=[12, 41],
            popupAnchor=[1, -34],
            shadowSize=[41, 41]
        )

bares = pd.read_csv('assets/bares_coords.csv',sep=',')
bares = bares.set_index('NOME')
restaurantes = bares[['Y', 'X']].rename(
    columns={'Y': 'latitude', 'X': 'longitude'}).to_dict('records')
entregadores = []
restaurante_atual = 0

app = DashProxy()
app.layout = html.Div([
    
    html.Div([
        html.Div([
            dcc.Input(
                id="input-pesquisa", 
                type="text", 
                placeholder="Pesquisar restaurante", 
                style={"width": "250px", "padding": "5px"}
            ),
            html.Button("Buscar", id="btn-pesquisa", style={"padding": "5px 10px", "cursor": "pointer"})
        ], style={"display": "flex", "alignItems": "center", "gap": "5px"}), 

        html.Div([
            dcc.Input(
                id="input-gerador", 
                type="text", 
                placeholder=" ", 
                style={"width": "50px", "padding": "5px"} 
            ),
            html.Button("Gerar entregadores", id="btn-gerador", style={"padding": "5px 10px", "cursor": "pointer"})
        ], style={"display": "flex", "alignItems": "center", "gap": "5px"})

   
    ], style=dict(ESTILO_SEARCH_BOX, **{"display": "flex", "gap": "20px", "alignItems": "center"})),
    
    dl.Map([dl.TileLayer(),dl.LayerGroup(id="grupo-restaurante"),dl.LayerGroup(id="grupo-marcadores")], id="mapa-principal", center=[-19.922757, -43.945137], zoom=14, style={"height": "100vh"}),

], style={"position": "relative", "width": "100%", "height": "100vh"})
@app.callback(
    [Output("mapa-principal", "center"),
     Output("mapa-principal", "zoom"),
     Output("grupo-restaurante","children")],
    Input("btn-pesquisa", "n_clicks"),
    State("input-pesquisa", "value"),
    prevent_initial_call=True
)
def buscar_local(n_clicks, endereco):
    try:
        register = bares.loc[endereco]
        pos = [register.Y,register.X]
        restaurante_atual = register.GEOHASH
        marcador_restaurante = dl.Marker(
            position=pos,
            icon=RED_MARKER,
            children=dl.Tooltip(f"Restaurante: {endereco}")
        )
        return pos,18, [marcador_restaurante]
    except KeyError:
        print("Endereço não encontrado")

    return dash.no_update,dash.no_update,dash.no_update

@app.callback(
    Output("grupo-marcadores", "children"),
    Input("btn-gerador", "n_clicks"),
    State("input-gerador", "value"),
    prevent_initial_call=True
)
def gerarador_entregadores(n_clicks, num_entregadores):
    if num_entregadores is None or str(num_entregadores).strip() == "":
        return []

    try:
        qtd = int(num_entregadores)
    except (TypeError, ValueError):
        return []

    if qtd <= 0:
        return []

    inicio = time.perf_counter()

    entregadores = gerar_entregadores.gerar_entregadores(restaurantes, qtd, 1.5)
    fim_geracao = time.perf_counter()
    print(
        f"Entregadores gerados: {qtd} em {fim_geracao - inicio:.3f} s. "
        "Iniciando projeção na rede viária...",
        flush=True
    )

    entregadores = projecao_nas_ruas.projetar_nas_ruas_mais_proximas(entregadores)

    fim_projecao = time.perf_counter()
    print(
        f"Projeção concluída em {fim_projecao - fim_geracao:.3f} s. "
        "Criando marcadores...",
        flush=True
    )

    novos_marcadores = [
        dl.Marker(position=pos, children=dl.Tooltip("Entregador"))
        for pos in entregadores.values()
    ]
    print(
        f"Marcadores criados em {time.perf_counter() - fim_projecao:.3f} s; "
        "aguardando atualização do mapa no navegador.",
        flush=True
    )
    return novos_marcadores
    
if __name__ == "__main__":
    app.run()