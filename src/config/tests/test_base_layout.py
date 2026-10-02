import re
from html.parser import HTMLParser

from django.contrib import messages
from django.contrib.messages import constants
from django.contrib.messages.storage import default_storage
from django.contrib.messages.storage.base import Message
from django.template import engines
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.views.generic import TemplateView


PICO_CSS_URL = "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"

# Hard-coded until the tickets that build these pages replace them with {% url %}.
PLACEHOLDER_NAV_LINKS = [
    ("Goals", "/goals/"),
    ("Sessions", "/sessions/"),
    ("Dashboard", "/dashboard/"),
]


def render_child(source, context=None):
    """Render a template string that extends base.html."""
    return engines["django"].from_string('{% extends "base.html" %}' + source).render(context)


class StylesheetCollector(HTMLParser):
    """Collect the href of every <link> whose rel includes "stylesheet"."""

    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "stylesheet" in (attrs.get("rel") or "").lower().split():
            self.hrefs.append(attrs.get("href"))


def stylesheet_hrefs(html):
    collector = StylesheetCollector()
    collector.feed(html)
    return collector.hrefs


def render_nav():
    """Return the <nav> element of the rendered base layout ("" if there is none)."""
    match = re.search(r"<nav\b.*?</nav>", render_child(""), re.DOTALL)
    return match.group(0) if match else ""


def messages_section(html):
    """Return the <section class="messages"> element of a rendered page ("" if there is none)."""
    match = re.search(r'<section class="messages">.*?</section>', html, re.DOTALL)
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

    def test_home_page_shows_heading_and_intro(self):
        response = self.client.get("/")

        html = response.content.decode()
        self.assertInHTML("<h1>Learning Companion</h1>", html)
        intro = " ".join(re.findall(r"(?s)<p\b[^>]*>(.*?)</p>", html)).lower()
        for topic in ("goals", "sessions", "resources", "ai summaries"):
            with self.subTest(topic=topic):
                self.assertIn(topic, intro)

    # Cookie storage keeps the messages framework off the session, so no DB is needed.
    @override_settings(MESSAGE_STORAGE="django.contrib.messages.storage.cookie.CookieStorage")
    def test_message_added_via_messages_framework_appears_on_home_page(self):
        request = RequestFactory().get("/")
        request._messages = default_storage(request)
        messages.success(request, "Goal saved.")

        response = TemplateView.as_view(template_name="home.html")(request).render()

        self.assertIn("Goal saved.", messages_section(response.content.decode()))


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

        self.assertEqual(stylesheet_hrefs(html), [PICO_CSS_URL])
        self.assertNotIn("@import", html)

    def test_nav_has_brand_link_to_home(self):
        nav = render_nav()

        self.assertInHTML('<a href="/">Learning Companion</a>', nav)

    def test_nav_has_placeholder_links_for_upcoming_pages(self):
        nav = render_nav()

        for label, href in PLACEHOLDER_NAV_LINKS:
            with self.subTest(label=label):
                self.assertInHTML(f'<a href="{href}">{label}</a>', nav)

    def test_messages_are_rendered_in_messages_container(self):
        html = render_child("", {"messages": [Message(constants.SUCCESS, "Goal saved.")]})

        self.assertIn("Goal saved.", messages_section(html))

    def test_no_messages_container_without_messages(self):
        html = render_child("", {"messages": []})

        self.assertNotIn('class="messages"', html)
