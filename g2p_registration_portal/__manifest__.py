{
    "name": "G2P Registration Portal Beneficiary Management",
    "category": "G2P",
    "version": "17.0.1.3.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "depends": [
        "g2p_portal_base",
        "g2p_registry_membership",
        "g2p_enumerator",
        "website",
    ],
    "data": [
        "views/dashboard.xml",
        "views/error_page.xml",
        "views/group_template.xml",
        "views/success_page.xml",
        "views/individual_page.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "g2p_registration_portal/static/src/css/style.css",
        ],
        "web.assets_common": [],
        "website.assets_wysiwyg": [],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
