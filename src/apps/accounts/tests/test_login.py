from django.contrib.auth import get_user_model
from django.test import TestCase


LOGIN_URL = "/accounts/login/"
PASSWORD = "correct-horse-battery-9"


def create_user(username="ada"):
    return get_user_model().objects.create_user(username=username, password=PASSWORD)


class LoginPageTests(TestCase):
    def test_login_page_renders_login_form_in_base_layout(self):
        response = self.client.get(LOGIN_URL)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertTemplateUsed(response, "base.html")
        for field in ("username", "password"):
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')


class LoginTests(TestCase):
    def test_valid_login_authenticates_and_redirects_home(self):
        user = create_user()

        response = self.client.post(LOGIN_URL, {"username": "ada", "password": PASSWORD})

        self.assertRedirects(response, "/")
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))

    def test_login_follows_safe_next_and_ignores_external_next(self):
        create_user()
        cases = {
            "/goals/": "/goals/",
            "https://evil.example/": "/",
        }

        for next_url, expected in cases.items():
            with self.subTest(next=next_url):
                response = self.client.post(
                    f"{LOGIN_URL}?next={next_url}", {"username": "ada", "password": PASSWORD}
                )

                # /goals/ doesn't exist yet, so don't fetch the redirect target.
                self.assertRedirects(response, expected, fetch_redirect_response=False)
