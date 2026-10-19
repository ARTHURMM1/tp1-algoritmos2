window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng, context) {
            return L.circleMarker(latlng, {
                radius: 3,
                color: '#64748b',
                weight: 1,
                fillColor: '#64748b',
                fillOpacity: 0.7
            });
        },
        function1: function(feature, latlng, context) {
            const dentro = feature.properties.dentro;
            const cor = dentro ? '#dc2626' : '#f59e0b';
            return L.circleMarker(latlng, {
                radius: dentro ? 6 : 5,
                color: cor,
                weight: 1.5,
                fillColor: cor,
                fillOpacity: 0.95
            }).bindTooltip(
                'Entregador ' + feature.properties.id +
                ' - ' + feature.properties.distancia_km.toFixed(3) + ' km' +
                (dentro ? ' (dentro do raio)' : ' (candidato fora do raio)')
            );
        }
    }
});