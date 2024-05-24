# Part of OpenG2P Social Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Social Registry Deduplication",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_registry_group",
        "g2p_registry_individual",
        "g2p_registry_membership",
        "g2p_programs",
    ],
    "external_dependencies": {},
    "data": [
        "data/data.xml",
        "views/registrant_view.xml",
        "views/registrant_action_view.xml",
        "views/menu.xml",
        "views/id_deduplication_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_social_registry_deduplication/static/src/js/deduplication_program.js",
            "/g2p_social_registry_deduplication/static/src/xml/deduplication_template.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
