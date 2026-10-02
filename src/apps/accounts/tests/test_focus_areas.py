from html.parser import HTMLParser

from django.test import TestCase

from apps.accounts.tests.test_profile_page import PROFILE_URL, create_user
from apps.tags.models import Tag


STARTER_TAGS = ["devops", "django", "javascript", "python", "sql", "testing"]


def tag(name):
    return Tag.objects.get_or_create(name=name)[0]


class FocusAreaCheckboxes(HTMLParser):
    """Collect the focus_areas checkboxes as {tag name: checked}."""

    def __init__(self):
        super().__init__()
        self.checked_by_id = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("type") == "checkbox" and attrs.get("name") == "focus_areas":
            self.checked_by_id[int(attrs["value"])] = "checked" in attrs


def focus_area_checkboxes(response):
    parser = FocusAreaCheckboxes()
    parser.feed(response.content.decode())
    names = dict(Tag.objects.filter(pk__in=parser.checked_by_id).values_list("pk", "name"))
    return {names[pk]: checked for pk, checked in parser.checked_by_id.items()}


class FocusAreaDisplayTests(TestCase):
    def test_display_lists_focus_areas_alphabetically(self):
        user = create_user()
        # Created in reverse order, so the listing must really sort by name.
        user.profile.focus_areas.add(tag("rust"), tag("go"))
        self.client.force_login(user)

        response = self.client.get(PROFILE_URL)

        self.assertInHTML("<dt>Focus areas</dt>", response.content.decode())
        self.assertInHTML("<dd>go, rust</dd>", response.content.decode())


class FocusAreaFormTests(TestCase):
    def test_form_offers_starter_and_own_tags_with_current_ones_checked(self):
        user = create_user()
        user.profile.focus_areas.add(tag("python"), tag("rust"))
        self.client.force_login(user)

        checkboxes = focus_area_checkboxes(self.client.get(PROFILE_URL))

        expected = {name: name == "python" for name in STARTER_TAGS} | {"rust": True}
        self.assertEqual(checkboxes, expected)

    def test_another_users_private_tag_is_not_offered_or_shown(self):
        bob = create_user("bob")
        bob.profile.focus_areas.add(tag("secret-b"))
        self.client.force_login(create_user("ada"))

        response = self.client.get(PROFILE_URL)

        self.assertNotIn("secret-b", focus_area_checkboxes(response))
        self.assertNotContains(response, "secret-b")
