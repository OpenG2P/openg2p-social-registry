from odoo.tests import TransactionCase
from odoo.exceptions import AccessDenied

class TestResUser(TransactionCase):
    
    def setUp(self):
        super(TestResUser, self).setUp()
        self.user_model = self.env['res.users']
        
        self.valid_user = self.user_model.create({
            'name': 'Valid User',
            'login': 'valid_user@example.com',
            'email': 'valid_user@example.com',
            'password': 'test_password',
            'active': True
        })
        self.valid_user.partner_id.is_registrant = False

        user_group = self.env.ref('base.group_user')
        self.valid_user.groups_id = [(4, user_group.id)]

        self.invalid_user = self.user_model.create({
            'name': 'Invalid User',
            'login': 'invalid_user@example.com',
            'email': 'invalid_user@example.com',
            'password': 'test_password',
            'active': True
        })
        
        self.registrant_user = self.user_model.create({
            'name': 'Registrant User',
            'login': 'registrant_user@example.com',
            'email': 'registrant_user@example.com',
            'password': 'test_password',
            'active': True
        })
        self.registrant_user.partner_id.is_registrant = True

    def test_reset_password_invalid_user(self):
        """Test resetting password for an invalid user (non-existent)."""
        with self.assertRaises(Exception) as context:
            self.invalid_user.reset_password('non_existent@example.com')
        self.assertEqual(str(context.exception), "Incorrect email. Please enter the registered email address.")

    def test_login_access_denied_for_registrant(self):
        """Test that a registrant user is denied access."""
        with self.assertRaises(AccessDenied):
            self.registrant_user._login(db='myTestDB', login='registrant_user@example.com', password='test_password', user_agent_env=None)
