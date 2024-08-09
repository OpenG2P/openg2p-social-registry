import logging
import os
from datetime import datetime

import httpx
from jose import jwt

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ID_GENERATOR_API_BASE_URL = os.getenv(
    "ID_GENERATOR_API_BASE_URL", "https://api-internal.dev.mosip.net/v1/idgenerator/uin"
)
ID_GENERATOR_AUTH_URL = os.getenv(
    "ID_GENERATOR_AUTH_URL",
    "https://api-internal.dev.mosip.net/v1/authmanager/authenticate/clientidsecretkey",
)
ID_GENERATOR_AUTH_CLIENT_ID = os.getenv("ID_GENERATOR_AUTH_CLIENT_ID", "mosip-idrepo-client")
ID_GENERATOR_AUTH_CLIENT_SECRET = os.getenv("ID_GENERATOR_AUTH_CLIENT_SECRET", "")
ID_GENERATOR_AUTH_GRANT_TYPE = os.getenv("ID_GENERATOR_AUTH_GRANT_TYPE", "client_credentials")


class FallbackTable(models.Model):
    _name = "g2p.reference_id.config"
    _description = "G2P Reference ID Configuration"

    name = fields.Char()
    base_api_url = fields.Char(default=ID_GENERATOR_API_BASE_URL)
    auth_url = fields.Char(default=ID_GENERATOR_AUTH_URL)
    auth_client_id = fields.Char(default=ID_GENERATOR_AUTH_CLIENT_ID)
    auth_client_secret = fields.Char(default=ID_GENERATOR_AUTH_CLIENT_SECRET)
    auth_grant_type = fields.Char(default=ID_GENERATOR_AUTH_GRANT_TYPE)
    api_timeout = fields.Integer(default=10)

    access_token = fields.Char()
    access_token_expiry = fields.Datetime()

    @api.model
    def get_config(self):
        return self.search([], limit=1)

    def get_access_token(self):
        self.ensure_one()

        if self.access_token and self.access_token_expiry and self.access_token_expiry > datetime.utcnow():
            return self.access_token

        if not self.auth_url:
            raise UserError(_("Authentication URL is not set"))

        headers = {"Content-Type": "application/json"}
        data = {
            "id": "string",
            "version": "string",
            "requesttime": "2024-07-11T05:10:53.449Z",
            "metadata": {},
            "request": {
                "clientId": self.auth_client_id,
                "secretKey": self.auth_client_secret,
                "appId": "idrepo",
            },
        }

        response = httpx.post(self.auth_url, headers=headers, json=data, timeout=self.api_timeout)
        _logger.debug("ID Generator Authentication API response: %s", response.text)
        response.raise_for_status()

        access_token = response.cookies.get("Authorization")
        token_exp = jwt.get_unverified_claims(access_token).get("exp")

        self.write(
            {
                "access_token": access_token,
                "access_token_expiry": datetime.fromtimestamp(token_exp)
                if isinstance(token_exp, int)
                else datetime.fromisoformat(token_exp)
                if isinstance(token_exp, str)
                else token_exp,
            }
        )
        return access_token
