# Part of OpenG2P Social Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Registry ID Deduplication",
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
    ],
    "external_dependencies": {},
    "data": [
        "security/ir.model.access.csv",
        "views/deduplication_view.xml",
        "views/group_kind_id_type_mapping_view.xml",
        "views/group_view.xml",
        "views/individual_view.xml",
        "views/res_config_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_registry_id_deduplication/static/src/js/duplicate_button.js",
            "/g2p_registry_id_deduplication/static/src/xml/duplicate_template.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
    "uninstall_hook": "_uninstall_cleanup",
}
