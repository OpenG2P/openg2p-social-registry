{
    "name": "OpenG2P Leaflet Map",
    "category": "G2P",
    "version": "17.0.1.5.0",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/g2p_osm_config.xml",
        "views/g2p_show_map.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_leaflet_map/static/src/*",
        ]
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
