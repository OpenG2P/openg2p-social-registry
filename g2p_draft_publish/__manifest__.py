{
    "name": "Draft Publish",
    "version": "17.0.0.0.0",
    "summary": "Draft Publish  Module",
    "category": "tools",
    "depends": ["base", "mail", "g2p_social_registry", "g2p_registry_addl_info", "web"],
    "data": [
        "security/rules.xml",
        "security/ir.model.access.csv",
        "views/draft_records.xml",
        "wizards/rejection.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_draft_publish/static/src/**/*.js",
            "g2p_draft_publish/static/src/**/*.css",
            "g2p_draft_publish/static/src/**/*.scss",
            "g2p_draft_publish/static/src/**/*.xml",
        ],
    },
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "",
}
