from django.contrib.auth import get_user_model
from django.test import TestCase


LOGOUT_URL = "/accounts/logout/"


class LogoutTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user(username="ada"))

    def test_post_logout_logs_out_and_redirects_to_login_page(self):
        response = self.client.post(LOGOUT_URL)

        self.assertRedirects(response, "/accounts/login/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_get_logout_is_rejected_and_keeps_user_logged_in(self):
        response = self.client.get(LOGOUT_URL)

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
