# TP1 - Algoritmos 2: Busca Espacial de Entregadores

Trabalho prático focado em indexação espacial e busca por prefixo. 
Essa aplicação simula a distribuição de entregadores em torno de restaurantes a partir de uma base real de bares e restaurantes (~20,8 mil estabelecimentos) e permite consultar quais entregadores estão dentro de um raio de busca, ordenando os resultados pelo tempo estimado de deslocamento na malha viária.

## Como executar

Crie e ative um ambiente virtual (opcional, mas recomendado) e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Depois, rode o arquivo principal na raiz do projeto:

```bash
python main.py
```

Na primeira execução, se o arquivo `cache/belo_horizonte_drive.graphml` ainda não existir, o `osmnx` fará o download da malha viária de Belo Horizonte e salvará no diretório `cache/` para acelerar as execuções seguintes.

Quando o servidor iniciar, acesse `http://127.0.0.1:8050` no navegador. Pela interface é possível:
- Pesquisar um restaurante pelo nome ou buscar uma rua para visualizar os estabelecimentos próximos;
- Definir a quantidade de entregadores e gerá-los no mapa;
- Ajustar o raio em quilômetros para visualizar os entregadores dentro do alcance (em vermelho), os candidatos das células inspecionadas que ficaram fora do raio (em laranja) e a tabela ordenada pelo tempo estimado de percurso.

## Como funciona

1. **Geração e projeção dos entregadores**: os entregadores são gerados ao redor dos restaurantes seguindo uma distribuição normal ($\sigma = 1{,}5\text{ km}$) (passado como parametro) corrigida pela latitude e, em seguida, projetados para o nó mais próximo da rede viária de Belo Horizonte obtida via OpenStreetMap (`osmnx`).
2. **Indexação espacial (Geohash + Trie Compacta)**: cada entregador tem sua coordenada convertida para um Geohash de precisão 8 e inserida em uma Trie Compacta. Na busca por raio, a árvore é percorrida podando subárvores cuja distância geodésica mínima até a célula passa o raio buscado e coletando diretamente subárvores cujos quatro cantos já estão inteiramente contidos no raio (com granularidade de células de precisão 6). Os candidatos retornados passam pelo filtro final de distância via fórmula de Haversine.
3. **Busca textual por prefixo**: uma Trie padrão (`SearchTrie`) indexa os nomes normalizados dos estabelecimentos e dos logradouros da cidade para autocompletar a barra de pesquisa na interface. Na busca por rua, um buffer de 100 metros sobre a geometria da via recupera os estabelecimentos próximos usando índice espacial (`sindex`).
4. **Estimativa de rota e tempo**: para os entregadores dentro do raio, executa-se um Dijkstra no grafo viário a partir do nó do restaurante, calculando em uma única busca a distância viária e o tempo estimado de chegada de cada entregador.

## Estrutura do projeto

```text
.
├── main.py                    # Aplicação Dash/Leaflet, callbacks e cálculo de rotas
├── requirements.txt           # Dependências do projeto
├── assets/
│   ├── bares_coords.csv       # Base de bares e restaurantes de BH
│   ├── dashExtensions_default.js
│   └── entregadores_render.js
├── cache/
│   └── belo_horizonte_drive.graphml  # Cache local do grafo viário (gerado na 1ª execução)
└── src/
    ├── geohash.py             # Codificação/decodificação Geohash, Haversine e distância ponto-célula
    ├── gerar_entregadores.py  # Sorteio de coordenadas com distribuição normal em torno dos restaurantes
    ├── projecao_nas_ruas.py   # Download/cache da malha do OSM e projeção nos nós das vias
    ├── search_trie.py         # Trie para autocompletar nomes de restaurantes e ruas
    └── trie_compacta.py       # Trie compacta para indexação dos hashes e busca espacial com poda
```


