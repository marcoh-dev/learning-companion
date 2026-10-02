import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


def nav_of(response):
    """Return the <nav> element of a rendered page ("" if there is none)."""
    match = re.search(r"<nav\b.*?</nav>", response.content.decode(), re.DOTALL)
    return match.group(0) if match else ""


class AnonymousNavTests(TestCase):
    def test_anonymous_nav_links_to_login_and_signup_without_logout(self):
        nav = nav_of(self.client.get("/"))

        self.assertInHTML(f'<a href="{reverse("login")}">Log in</a>', nav)
        self.assertInHTML(f'<a href="{reverse("signup")}">Sign up</a>', nav)
        self.assertNotIn(reverse("logout"), nav)


class LoggedInNavTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user(username="ada"))

    def test_logged_in_nav_shows_username_and_logout_form_instead_of_login_links(self):
        nav = nav_of(self.client.get("/"))

        self.assertIn("Signed in as ada", nav)
        form = re.search(r"<form\b[^>]*>.*?</form>", nav, re.DOTALL)
        self.assertIsNotNone(form)
        self.assertRegex(form.group(0), rf'method="post"[^>]*action="{reverse("logout")}"')
        self.assertIn('name="csrfmiddlewaretoken"', form.group(0))
        self.assertInHTML('<button type="submit">Log out</button>', form.group(0))
        self.assertNotIn(">Log in<", nav)
        self.assertNotIn(">Sign up<", nav)
