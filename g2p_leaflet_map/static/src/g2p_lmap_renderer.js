/** @odoo-module */
/* global L */

import {Component, onMounted, onWillStart, useRef} from "@odoo/owl";
import {loadCSS, loadJS} from "@web/core/assets";

export class G2PLeafletMapRenderer extends Component {
    static template = "g2p_leaflet_map.MapRenderer";
    static props = {
        polygonCoords: {type: Array, optional: true, default: []},
        partnerLatitude: {type: Number, optional: true},
        partnerLongitude: {type: Number, optional: true},
    };

    setup() {
        console.log("Renderer Props:", this.props);
        this.root = useRef("map");
        this.config = {
            tile_server_url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        };

        onWillStart(async () => {
            try {
                const response = await fetch("/osm/config/get", {
                    method: "GET",
                    headers: {"Content-Type": "application/json"},
                });

                if (response.ok) {
                    const data = await response.json();
                    this.config.tile_server_url = data.tile_server_url || this.config.tile_server_url;
                } else {
                    console.warn("Failed to fetch tile server URL, using default.");
                }

                await loadCSS("/g2p_leaflet_map/static/lib/leaflet/leaflet.css");
                await loadJS("/g2p_leaflet_map/static/lib/leaflet/leaflet.js");
            } catch (error) {
                console.error("Error loading OSM config:", error);
            }
        });

        onMounted(() => {
            if (!this.root.el) return;

            if (typeof L === "undefined") {
                console.error("Leaflet JS is not loaded.");
                return;
            }

            const mapCenter = [9.145, 40.489];
            const zoomLevel = 12;
            this.map = L.map(this.root.el).setView(mapCenter, zoomLevel);

            L.tileLayer(this.config.tile_server_url, {
                maxZoom: 19,
                attribution: "&copy; OpenStreetMap contributors",
            }).addTo(this.map);

            const bounds = L.latLngBounds([]);

            // Define a set of colors for polygons
            const colors = ["blue", "green", "red", "purple", "orange", "yellow"];

            // **Add Polygons from Land Data**
            if (this.props.polygonCoords?.length) {
                this.props.polygonCoords.forEach((land, index) => {
                    const polygonColor = colors[index % colors.length];
                    const polygon = L.polygon(land.polygon_data, {
                        color: polygonColor,
                        fillColor: polygonColor,
                        fillOpacity: 0.5,
                    }).addTo(this.map);

                    bounds.extend(polygon.getBounds());

                    // **Show information on hover**
                    polygon.on("mouseover", (e) => {
                        const popupContent = `
                            <b>Land Information</b><br>
                            Area: ${land.total_land_area} sq km<br>
                            Owner: ${land.ownership_type}
                        `;
                        const tooltip = L.tooltip({
                            permanent: false,
                            direction: "top",
                            opacity: 0.9,
                        })
                            .setContent(popupContent)
                            .setLatLng(e.latlng);
                        polygon.bindTooltip(tooltip).openTooltip();
                    });

                    polygon.on("mouseout", () => {
                        polygon.unbindTooltip();
                    });
                });
            } else {
                console.warn("No land data received.");
            }

            // **Fit Map to Show Everything**
            if (bounds.isValid()) {
                this.map.fitBounds(bounds.pad(0.2));
            } else {
                this.map.setView(mapCenter, zoomLevel);
            }
        });
    }
}
