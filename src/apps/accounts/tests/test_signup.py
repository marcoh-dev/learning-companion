from django.contrib.auth import get_user_model
from django.test import TestCase

from config.tests.test_base_layout import messages_section


SIGNUP_URL = "/accounts/signup/"
PASSWORD = "correct-horse-battery-9"


def signup_data(username="ada", password1=PASSWORD, password2=PASSWORD):
    return {"username": username, "password1": password1, "password2": password2}


class SignUpPageTests(TestCase):
    def test_signup_page_renders_user_creation_form_in_base_layout(self):
        response = self.client.get(SIGNUP_URL)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")
        self.assertTemplateUsed(response, "base.html")
        for field in ("username", "password1", "password2"):
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')


class ValidSignUpTests(TestCase):
    def test_valid_signup_creates_user_and_redirects_home(self):
        response = self.client.post(SIGNUP_URL, signup_data())

        self.assertTrue(get_user_model().objects.filter(username="ada").exists())
        self.assertRedirects(response, "/")

    def test_valid_signup_logs_the_new_user_in(self):
        self.client.post(SIGNUP_URL, signup_data())

        user = get_user_model().objects.get(username="ada")
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))
        self.assertTrue(self.client.get("/").context["user"].is_authenticated)

    def test_valid_signup_shows_success_message_on_home_page(self):
        response = self.client.post(SIGNUP_URL, signup_data(), follow=True)

        self.assertIn("Welcome, ada! Your account has been created.", messages_section(response.content.decode()))


class InvalidSignUpTests(TestCase):
    def test_invalid_signup_rerenders_form_with_errors_and_creates_no_user(self):
        get_user_model().objects.create_user(username="taken", password=PASSWORD)
        cases = {
            "mismatched passwords": (
                signup_data(password2=PASSWORD + "x"),
                "The two password fields didn’t match.",
            ),
            "password rejected by validators": (
                signup_data(password1="12345678", password2="12345678"),
                "This password is entirely numeric.",
            ),
            "existing username in another case": (
                signup_data(username="TAKEN"),
                "A user with that username already exists.",
            ),
        }

        for case, (data, error) in cases.items():
            with self.subTest(case=case):
                response = self.client.post(SIGNUP_URL, data)

                self.assertContains(response, error, status_code=200)
                self.assertEqual(get_user_model().objects.count(), 1)
                self.assertFalse(response.context["user"].is_authenticated)
