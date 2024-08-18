# Part of OpenG2P Social Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Registry: G2P Connect REST API",
    "category": "G2P",
    "version": "17.0.1.2.0",
    "author": "OpenG2P",
    "development_status": "Alpha",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "depends": [
        "g2p_registry_membership",
        "fastapi",
        "graphql_base",
    ],
    "data": [
        "data/ir_config_params.xml",
        "data/fastapi_endpoint_g2p_connect.xml",
    ],
    "external_dependencies": {"python": ["python-jose"]},
    "application": True,
    "auto_install": False,
    "installable": True,
}
