from django.contrib.auth import get_user_model
from django.test import TestCase


class ProfileCreationTests(TestCase):
    def test_create_user_creates_one_empty_profile(self):
        user = get_user_model().objects.create_user(username="ada")

        user.refresh_from_db()
        self.assertEqual(user.profile.name, "")
        self.assertEqual(user.profile.cohort, "")
        self.assertEqual(type(user.profile).objects.filter(user=user).count(), 1)
