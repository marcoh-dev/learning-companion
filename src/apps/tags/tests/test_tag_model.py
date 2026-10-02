from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.tags.models import Tag


class FocusAreaRelationTests(TestCase):
    def test_profile_can_hold_focus_area_tags(self):
        profile = get_user_model().objects.create_user(username="ada").profile
        rust = Tag.objects.create(name="rust")

        profile.focus_areas.add(rust)

        self.assertQuerySetEqual(profile.focus_areas.all(), [rust])
