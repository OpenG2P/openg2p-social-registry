{
    "name": "g2p_leaflet_map",
    "category": "Uncategorized",
    "version": "17.0.0.0.0",
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
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
