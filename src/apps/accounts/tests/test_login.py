from django.test import TestCase


LOGIN_URL = "/accounts/login/"


class LoginPageTests(TestCase):
    def test_login_page_renders_login_form_in_base_layout(self):
        response = self.client.get(LOGIN_URL)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertTemplateUsed(response, "base.html")
        for field in ("username", "password"):
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')
