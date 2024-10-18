from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase


class TestRegistryConfig(TransactionCase):
    def setUp(self):
        super().setUp()
        self.config = self.env["g2p.reference_id.config"].create(
            {
                "name": "Test Config",
                "base_api_url": "https://idgenerator.sandbox.net/v1/idgenerator/uin",
                "auth_url": "https://keycloak.openg2p.org/realms/master/protocol/openid-connect/token",
                "auth_client_id": "client_id",
                "auth_client_secret": "client_secret",
                "auth_grant_type": "client_credentials",
                "api_timeout": 10,
            }
        )
        self.registry_config = self.env["res.config.settings"].create({})

    @patch("requests.post")
    def test_set_values(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response
        self.registry_config.id_generator_base_api_url = "https://idgenerator.sandbox.net/v1/idgenerator/uin"
        self.registry_config.id_generator_auth_url = (
            "https://keycloak.openg2p.org/realms/master/protocol/openid-connect/token"
        )
        self.registry_config.id_generator_auth_client_id = "new_client_id"
        self.registry_config.id_generator_auth_client_secret = "new_client_secret"
        self.registry_config.id_generator_auth_grant_type = "new_grant_type"
        self.registry_config.id_generator_api_timeout = 20
        self.registry_config.set_values()
        config = self.env["g2p.reference_id.config"].get_config()
        self.assertEqual(config.base_api_url, "https://idgenerator.sandbox.net/v1/idgenerator/uin")
        self.assertEqual(
            config.auth_url, "https://keycloak.openg2p.org/realms/master/protocol/openid-connect/token"
        )
        self.assertEqual(config.auth_client_id, "new_client_id")
        self.assertEqual(config.auth_client_secret, "new_client_secret")
        self.assertEqual(config.auth_grant_type, "new_grant_type")
        self.assertEqual(config.api_timeout, 20)

    @patch("requests.post")
    def test_get_values(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response
        self.registry_config.get_values()
        config = self.env["g2p.reference_id.config"].get_config()
        self.assertEqual(self.registry_config.id_generator_base_api_url, config.base_api_url)
        self.assertEqual(self.registry_config.id_generator_auth_url, config.auth_url)
        self.assertEqual(self.registry_config.id_generator_auth_client_id, config.auth_client_id)
        self.assertEqual(self.registry_config.id_generator_auth_client_secret, config.auth_client_secret)
        self.assertEqual(self.registry_config.id_generator_auth_grant_type, config.auth_grant_type)
        self.assertEqual(self.registry_config.id_generator_api_timeout, config.api_timeout)

    @patch("requests.post")
    def test_add_missing_ref_id_to_retry(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response
        partner_without_ref = self.env["res.partner"].create(
            {"name": "Test Partner", "is_registrant": True, "ref_id": False}
        )
        self.registry_config.add_missing_ref_id_to_retry()
        pending_records = self.env["g2p.pending.reference_id"].search(
            [("registrant_id", "=", partner_without_ref.id)]
        )
        self.assertEqual(len(pending_records), 1)
        self.assertEqual(pending_records.registrant_id.id, partner_without_ref.id)
        self.assertEqual(pending_records.status, "failed")
