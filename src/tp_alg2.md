`Fazer a distribuição uniforme de motoristas em volta dos restaurantes.`
`E projetar na rua mais proxima. E montar o site?`

Para gerar os entregadores: 
	-Entreda: N numero de entregadores.
As coordenadas dos entregadores deve ter uma distribuição normal 
em torno dos reutarantes. N/#restaurantes por restaurante.
	-Ao gerar os integradores:
gerar lati,long provavelmente eles vão cair em lugares não validos 
(no meio de quarteiores)
deve projetar eles para a rua mais proxima, usando Openstreetmaps(osmnx),
assim os pinos no mapa vão aparecer exatamente em cima das ruas. 

	-Conseguir fazer as consultas por restaurante:
Para restaurante X pegue seus entregadores de raio até 5km.

### Para gerar a distribuição normal de um restaurante,
(1 grau em lat/long resulta em, mais ou menos, 111km) 
Vamos fazer km_para_graus = 1 / 111
sigma_graus = sigma_km * km_para_graus

vamos usar como média as suas coordenadas (lat, long). 

É sabido que 68% das pessoas vão ficar dentro de 1*sigma,
95% dentro de 2*sigma e 99,7% dentro de 3*sigma.
Assim podemos usar sigma_km = 1.5 (ou algo em torno disso)
pois fica dentro dos razoaveis 2km definidos no enunciado.
