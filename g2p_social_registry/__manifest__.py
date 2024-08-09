# Part of OpenG2P Social Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Social Registry",
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
        "data/cron_job.xml",
        "data/default_ref_id_config.xml",
        "views/main_view.xml",
        "views/region.xml",
        "views/registrant_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
