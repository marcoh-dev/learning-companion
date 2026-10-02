from django.test import TestCase

from apps.accounts.tests.test_profile_page import PROFILE_URL, create_user
from apps.tags.models import Tag


def tag(name):
    return Tag.objects.get_or_create(name=name)[0]


class FocusAreaDisplayTests(TestCase):
    def test_display_lists_focus_areas_alphabetically(self):
        user = create_user()
        # Created in reverse order, so the listing must really sort by name.
        user.profile.focus_areas.add(tag("rust"), tag("go"))
        self.client.force_login(user)

        response = self.client.get(PROFILE_URL)

        self.assertInHTML("<dt>Focus areas</dt>", response.content.decode())
        self.assertInHTML("<dd>go, rust</dd>", response.content.decode())
