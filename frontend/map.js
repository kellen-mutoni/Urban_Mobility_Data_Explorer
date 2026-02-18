/**
 * map.js - Leaflet map with taxi zone heatmap
 * --------------------------------------------
 * Renders an interactive choropleth map of NYC taxi zones
 * colored by pickup density.
 * Depends on: api.js (fetchAPI, formatCurrency)
 * Depends on: app.js (map, geoLayer globals)
 */

// =========================================
//  Map - Leaflet with zone heatmap
// =========================================
async function loadMap() {
    // Initialize map centered on NYC
    map = L.map("map").setView([40.7128, -73.95], 11);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        maxZoom: 18,
    }).addTo(map);

    // Load heatmap data and geojson in parallel
    const [heatmapData, geojsonData] = await Promise.all([
        fetchAPI("/zone-heatmap"),
        fetchAPI("/zones/geojson"),
    ]);

    if (!heatmapData || !geojsonData) return;

    // Create a lookup for pickup counts
    const countLookup = {};
    let maxCount = 0;
    heatmapData.forEach(d => {
        countLookup[d.location_id] = d;
        if (d.pickup_count > maxCount) maxCount = d.pickup_count;
    });

    // Color function based on pickup count
    function getColor(count) {
        const ratio = count / maxCount;
        if (ratio > 0.7) return "#f7c948";
        if (ratio > 0.5) return "#f39c12";
        if (ratio > 0.3) return "#e67e22";
        if (ratio > 0.15) return "#d35400";
        if (ratio > 0.05) return "#c0392b";
        return "#2c3e50";
    }

    // Add GeoJSON layer
    geoLayer = L.geoJSON(geojsonData, {
        style: function (feature) {
            const locId = feature.properties.location_id;
            const info = countLookup[locId];
            const count = info ? info.pickup_count : 0;
            return {
                fillColor: getColor(count),
                weight: 1,
                opacity: 0.7,
                color: "#1a2a3a",
                fillOpacity: 0.7,
            };
        },
        onEachFeature: function (feature, layer) {
            const props = feature.properties;
            const info = countLookup[props.location_id];
            const count = info ? info.pickup_count.toLocaleString() : "0";
            const avgFare = info ? formatCurrency(info.avg_fare) : "N/A";

            layer.bindPopup(
                `<div style="font-family: sans-serif; color: #333;">
                    <strong>${props.zone_name}</strong><br>
                    Borough: ${props.borough}<br>
                    Pickups: ${count}<br>
                    Avg Fare: ${avgFare}
                </div>`
            );

            layer.on("mouseover", function () {
                layer.setStyle({ weight: 3, color: "#f7c948", fillOpacity: 0.9 });
            });
            layer.on("mouseout", function () {
                geoLayer.resetStyle(layer);
            });
        },
    }).addTo(map);
}
