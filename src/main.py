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


