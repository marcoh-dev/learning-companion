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
