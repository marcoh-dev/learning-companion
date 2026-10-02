from django.test import TestCase


PROFILE_URL = "/accounts/profile/"


class AnonymousProfileTests(TestCase):
    def test_anonymous_visitor_is_redirected_to_login_with_next(self):
        response = self.client.get(PROFILE_URL)

        self.assertRedirects(response, "/accounts/login/?next=/accounts/profile/")
