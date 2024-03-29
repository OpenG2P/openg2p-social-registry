{
    "name": "G2P Self Service Portal",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_social_registry",
        "website",
        "web",
        "auth_oidc",
    ],
    "data": [
        "data/website_form_action_data.xml",
        "views/g2p_self_service_base.xml",
        "views/g2p_self_service_login.xml",
        "views/g2p_self_service_myprofile.xml",
        "views/auth_oauth_provider.xml",
        "views/g2p_self_service_form_page_template.xml",
        "views/g2p_self_service_submitted_forms.xml",
        "views/res_config_settings.xml",
    ],
    "assets": {
        "web.assets_backend": [],
        "web.assets_frontend": [
            "g2p_self_service_portal/static/src/js/self_service_form_action.js"
        ],
        "web.assets_common": [],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
