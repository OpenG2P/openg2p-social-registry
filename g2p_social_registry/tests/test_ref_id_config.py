from unittest.mock import MagicMock, patch

import requests

from odoo.tests import TransactionCase


class TestG2PReferenceIdconfig(TransactionCase):
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

    @patch("requests.post")
    def test_get_access_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
                "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            )
        }
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response
        access_token = self.config.get_access_token()
        self.assertEqual(
            access_token,
            (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
                "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            ),
        )

    @patch("requests.post")
    def test_get_access_token_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_response
        with self.assertRaises(requests.exceptions.HTTPError):
            self.config.get_access_token()

    @patch("requests.post")
    def test_write_access_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
                "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            )
        }
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response
        self.config.get_access_token()
        self.assertIsNotNone(self.config.access_token)
        self.assertIsNotNone(self.config.access_token_expiry)
