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
            let polygon = null;
            let polygonCenter = null;

            // **Add Polygon**
            if (this.props.polygonCoords?.length) {
                polygon = L.polygon(this.props.polygonCoords).addTo(this.map);
                bounds.extend(polygon.getBounds());

                // **Calculate Polygon Center**
                polygonCenter = polygon.getBounds().getCenter();

                // **Add a Pin at Polygon Center**
                L.marker(polygonCenter, {
                    icon: L.icon({
                        iconUrl: "/g2p_leaflet_map/static/lib/leaflet/images/marker-icon.png",
                        iconSize: [25, 40],
                        iconAnchor: [12, 40],
                    }),
                })
                    .addTo(this.map)
                    .bindPopup("Land Shape");
            } else {
                console.warn("No polygon coordinates received.");
            }

            // **Add Partner Location Marker**
            if (this.props.partnerLatitude !== null && this.props.partnerLongitude !== null) {
                const partnerLocation = [this.props.partnerLatitude, this.props.partnerLongitude];
                L.marker(partnerLocation).addTo(this.map).bindPopup("Data Collection Point").openPopup();

                bounds.extend(partnerLocation);
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
