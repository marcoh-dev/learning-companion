from django.test import TestCase


SIGNUP_URL = "/accounts/signup/"


class SignUpPageTests(TestCase):
    def test_signup_page_renders_user_creation_form_in_base_layout(self):
        response = self.client.get(SIGNUP_URL)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")
        self.assertTemplateUsed(response, "base.html")
        for field in ("username", "password1", "password2"):
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')
