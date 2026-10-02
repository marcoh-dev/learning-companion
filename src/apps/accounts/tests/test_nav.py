import re

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
