import re

from django.template import engines
from django.test import SimpleTestCase


PICO_CSS_URL = "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"


def render_child(source):
    """Render a template string that extends base.html."""
    return engines["django"].from_string('{% extends "base.html" %}' + source).render()


def render_nav():
    """Return the <nav> element of the rendered base layout ("" if there is none)."""
    match = re.search(r"<nav\b.*?</nav>", render_child(""), re.DOTALL)
    return match.group(0) if match else ""


class HomePageTests(SimpleTestCase):
    def test_home_page_returns_200_for_anonymous_visitor(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_home_page_renders_home_template_extending_base(self):
        response = self.client.get("/")

        self.assertTemplateUsed(response, "home.html")
        self.assertTemplateUsed(response, "base.html")

    def test_home_page_title_contains_app_name(self):
        response = self.client.get("/")

        self.assertRegex(response.content.decode(), r"<title>[^<]*Learning Companion[^<]*</title>")


class BaseLayoutTests(SimpleTestCase):
    def test_child_template_fills_title_and_content_blocks(self):
        html = render_child(
            "{% block title %}Child title{% endblock %}"
            "{% block content %}<p>Child content</p>{% endblock %}"
        )

        self.assertInHTML("<title>Child title</title>", html)
        self.assertInHTML("<p>Child content</p>", html)

    def test_only_stylesheet_is_pico_css_from_cdn(self):
        html = render_child("")

        links = [tag for tag in re.findall(r"<link\b[^>]*>", html) if 'rel="stylesheet"' in tag]
        self.assertEqual(len(links), 1)
        self.assertIn(f'href="{PICO_CSS_URL}"', links[0])

    def test_nav_has_brand_link_to_home(self):
        nav = render_nav()

        self.assertInHTML('<a href="/">Learning Companion</a>', nav)
