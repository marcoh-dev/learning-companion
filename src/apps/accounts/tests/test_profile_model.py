from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Profile


class ProfileCreationTests(TestCase):
    def test_create_user_creates_one_empty_profile(self):
        user = get_user_model().objects.create_user(username="ada")

        user.refresh_from_db()
        self.assertEqual(user.profile.name, "")
        self.assertEqual(user.profile.cohort, "")
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)

    def test_create_superuser_creates_one_profile_and_resaving_adds_none(self):
        admin = get_user_model().objects.create_superuser(username="root", password="x")

        admin.first_name = "Grace"
        admin.save()

        self.assertEqual(Profile.objects.filter(user=admin).count(), 1)
