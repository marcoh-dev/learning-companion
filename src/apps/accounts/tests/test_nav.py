import re
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


def nav_of(response):
    """Return the <nav> element of a rendered page ("" if there is none)."""
    match = re.search(r"<nav\b.*?</nav>", response.content.decode(), re.DOTALL)
    return match.group(0) if match else ""


class FormAttrsCollector(HTMLParser):
    """Collect the attributes of every <form> start tag."""

    def __init__(self):
        super().__init__()
        self.forms = []

    def handle_starttag(self, tag, attrs):
        if tag == "form":
            self.forms.append(dict(attrs))


def form_attrs(html):
    collector = FormAttrsCollector()
    collector.feed(html)
    return collector.forms


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
        [attrs] = form_attrs(form.group(0))
        self.assertEqual(attrs.get("method", "").lower(), "post")
        self.assertEqual(attrs.get("action"), reverse("logout"))
        self.assertIn('name="csrfmiddlewaretoken"', form.group(0))
        self.assertInHTML('<button type="submit">Log out</button>', form.group(0))
        self.assertNotIn(">Log in<", nav)
        self.assertNotIn(">Sign up<", nav)
