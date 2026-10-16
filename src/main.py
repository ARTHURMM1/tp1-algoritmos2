import gerar_entregadores #gera uma lista de entregadores, n sendo o numero de entregadores cada um tem {id, lat, lon}
import projecao_nas_ruas #atualiza lat, lon de cada entregador
import geohash #constroi um dict em que cada entregador tem seu geohash entao temos {entregador: geohash}
import trie #constroe a trie inserindo cada um, O(n + m) onde m é o tamanho do geohash que no nosso caso é m = 8. comando: trie.insert(geohash, entregador)

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
import geohash
import trie
import projecao_nas_ruas
import gerar_entregadores
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State
import dash_leaflet as dl
from dash_extensions.enrich import DashProxy



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

bares = pd.read_csv('assets\\bares_coords.csv',sep=',')
bares = bares.set_index('NOME')
markers = [dl.TileLayer()]

app = DashProxy()
app.layout = html.Div([
    html.Div([
            dcc.Input(
                id="input-pesquisa", 
                type="text", 
                placeholder="Pesquisar restaurante  ", 
                style={"width": "250px", "padding": "5px"}
            ),
            html.Button("Buscar", id="btn-pesquisa", style={"padding": "5px 10px", "cursor": "pointer"})
        ], style=ESTILO_SEARCH_BOX),
    dl.Map(markers,id="mapa-principal", center=[-19.922757, -43.945137], zoom=14, style={"height": "100vh"}),
], style={"position": "relative", "width": "100%", "height": "100vh"})


@app.callback(
    [Output("mapa-principal", "center"),
     Output("mapa-principal", "zoom")],
    Input("btn-pesquisa", "n_clicks"),
    State("input-pesquisa", "value"),
    prevent_initial_call=True
)
def buscar_local(n_clicks, endereco):
    try:
        register = bares.loc[endereco]
        print("achou")
        return [register.Y,register.X],18
    except KeyError:
        print("Endereço não encontrado")

    return dash.no_update,dash.no_update

if __name__ == "__main__":
    app.run()


