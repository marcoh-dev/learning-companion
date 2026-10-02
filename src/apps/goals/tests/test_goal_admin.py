from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.goals.models import Goal


class GoalAdminTests(TestCase):
    def test_goal_is_registered_with_list_columns_and_status_filter(self):
        self.assertTrue(admin.site.is_registered(Goal))

        model_admin = admin.site.get_model_admin(Goal)
        self.assertEqual(tuple(model_admin.list_display), ("title", "status", "owner", "updated_at"))
        self.assertEqual(tuple(model_admin.list_filter), ("status",))

    def test_superuser_can_open_the_goal_changelist(self):
        root = get_user_model().objects.create_superuser(username="root", password="x")
        Goal.objects.create(owner=root, title="Learn Django")
        self.client.force_login(root)

        response = self.client.get(reverse("admin:goals_goal_changelist"))

        self.assertContains(response, "Learn Django")
