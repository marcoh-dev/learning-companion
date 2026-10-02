from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.tags.models import Tag


class FocusAreaRelationTests(TestCase):
    def test_profile_can_hold_focus_area_tags(self):
        profile = get_user_model().objects.create_user(username="ada").profile
        rust = Tag.objects.create(name="rust")

        profile.focus_areas.add(rust)

        self.assertQuerySetEqual(profile.focus_areas.all(), [rust])


class TagRuleTests(TestCase):
    def test_tag_names_are_unique(self):
        Tag.objects.create(name="rust")

        with self.assertRaises(IntegrityError):
            Tag.objects.create(name="rust")

    def test_tag_names_are_at_most_30_chars(self):
        self.assertEqual(Tag._meta.get_field("name").max_length, 30)

    def test_deleting_the_profile_keeps_its_tags(self):
        user = get_user_model().objects.create_user(username="ada")
        user.profile.focus_areas.add(Tag.objects.create(name="rust"))

        user.delete()

        self.assertTrue(Tag.objects.filter(name="rust").exists())
