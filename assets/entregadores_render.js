window.dashExtensions = window.dashExtensions || {};
window.dashExtensions.default = window.dashExtensions.default || {};

window.dashExtensions.default.pontoEntregador = function(feature, latlng) {
    return window.L.circleMarker(latlng, {
        radius: 3, color: '#64748b', weight: 1,
        fillColor: '#64748b', fillOpacity: 0.75
    });
};

window.dashExtensions.default.pontoResultado = function(feature, latlng) {
    const p = feature.properties || {};
    const dentro = Boolean(p.dentro);
    const cor = dentro ? '#dc2626' : '#f59e0b';
    const marcador = window.L.circleMarker(latlng, {
        radius: dentro ? 6 : 5, color: cor, weight: 1.5,
        fillColor: cor, fillOpacity: 0.95
    });
    if (p.distancia_km != null) {
        marcador.bindTooltip('Entregador ' + p.id + ' — ' + Number(p.distancia_km).toFixed(3) + ' km');
    }
    return marcador;
};
