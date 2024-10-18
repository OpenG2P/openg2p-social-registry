from unittest.mock import patch

from odoo.tests import TransactionCase


class TestFallbackTable(TransactionCase):
    def setUp(self):
        super().setUp()
        self.fallback_table = self.env["g2p.pending.reference_id"].create(
            {
                "registrant_id": self.env["res.partner"].create({"name": "Test Partner"}).id,
                "ref_id": "",
                "status": "failed",
            }
        )

    @patch("odoo.addons.g2p_social_registry.models.registrant.ResPartner.generate_ref_id")
    def test_retry_generate_ref_id_success(self, mock_generate_ref_id):
        mock_generate_ref_id.return_value = None
        self.fallback_table.registrant_id.ref_id = "some_ref_id"
        self.fallback_table.retry_generate_ref_id()
        self.assertEqual(self.fallback_table.status, "success")
        self.assertEqual(self.fallback_table.ref_id, "some_ref_id")

    @patch("odoo.addons.g2p_social_registry.models.registrant.ResPartner.generate_ref_id")
    def test_retry_generate_ref_id_failure(self, mock_generate_ref_id):
        mock_generate_ref_id.return_value = False
        self.fallback_table.retry_generate_ref_id()
        self.assertEqual(self.fallback_table.status, "failed")

    @patch("odoo.addons.g2p_social_registry.models.registrant.ResPartner.generate_ref_id")
    def test_generate_ref_id_for_selected_failure(self, mock_generate_ref_id):
        mock_generate_ref_id.return_value = False
        self.env.context = {"active_ids": [self.fallback_table.registrant_id.id]}
        self.fallback_table.generate_ref_id_for_selected()
        self.assertEqual(self.fallback_table.status, "failed")

    @patch("odoo.addons.g2p_social_registry.models.registrant.ResPartner.generate_ref_id")
    @patch("odoo.addons.g2p_social_registry.models.pending_ref_id.FallbackTable.search")
    def test_generate_ref_id_for_selected_no_registrant(self, mock_search, mock_generate_ref_id):
        mock_search.return_value = False
        mock_generate_ref_id.return_value = True
        self.env.context = {"active_ids": [self.fallback_table.registrant_id.id]}
        self.fallback_table.generate_ref_id_for_selected()
        mock_search.assert_called_once_with(
            [("registrant_id", "=", self.fallback_table.registrant_id.id)], limit=1
        )
