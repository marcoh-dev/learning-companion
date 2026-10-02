import re

from django.test import TestCase
from django.urls import reverse

from apps.goals.models import Goal
from apps.goals.tests.test_goal_list import GOALS_URL, create_user
from config.tests.test_base_layout import messages_section


def delete_url(goal):
    return f"/goals/{goal.pk}/delete/"


class AnonymousGoalDeleteTests(TestCase):
    def setUp(self):
        self.goal = Goal.objects.create(owner=create_user(), title="Learn Django")

    def test_delete_url_is_named_goal_delete(self):
        self.assertEqual(reverse("goal-delete", args=[self.goal.pk]), delete_url(self.goal))

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(delete_url(self.goal))

        self.assertRedirects(response, f"/accounts/login/?next={delete_url(self.goal)}")


class OwnGoalDeleteTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)
        self.goal = Goal.objects.create(owner=self.ada, title="Learn Django")

    def test_get_shows_confirmation_and_deletes_nothing(self):
        response = self.client.get(delete_url(self.goal))

        self.assertTemplateUsed(response, "goals/goal_confirm_delete.html")
        self.assertContains(response, "Delete “Learn Django”?")
        self.assertTrue(Goal.objects.filter(pk=self.goal.pk).exists())

    def test_confirmation_is_a_csrf_protected_post_form(self):
        response = self.client.get(delete_url(self.goal))

        # Search inside <main>: the header's logout form is also a CSRF-protected POST form.
        main = re.search(r"<main\b.*?</main>", response.content.decode(), re.DOTALL).group(0)
        form = re.search(r"<form\b[^>]*>.*?</form>", main, re.DOTALL).group(0)
        self.assertIn('method="post"', form)
        self.assertIn('name="csrfmiddlewaretoken"', form)

    def test_post_deletes_and_redirects_to_list_with_message(self):
        response = self.client.post(delete_url(self.goal), follow=True)

        self.assertRedirects(response, GOALS_URL)
        self.assertIn("Goal deleted.", messages_section(response.content.decode()))
        self.assertFalse(Goal.objects.filter(pk=self.goal.pk).exists())


class OtherGoalDeleteTests(TestCase):
    def setUp(self):
        self.client.force_login(create_user("ada"))
        self.bobs_goal = Goal.objects.create(owner=create_user("bob"), title="Bob's secret goal")

    def test_get_another_users_goal_is_not_found(self):
        response = self.client.get(delete_url(self.bobs_goal))

        self.assertEqual(response.status_code, 404)

    def test_post_another_users_goal_is_not_found_and_keeps_it(self):
        response = self.client.post(delete_url(self.bobs_goal))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Goal.objects.filter(pk=self.bobs_goal.pk).exists())
