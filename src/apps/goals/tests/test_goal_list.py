from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.goals.models import Goal

GOALS_URL = "/goals/"
PASSWORD = "correct-horse-battery-9"


def create_user(username="ada"):
    return get_user_model().objects.create_user(username=username, password=PASSWORD)


class AnonymousGoalListTests(TestCase):
    def test_goal_list_url_is_named_goal_list(self):
        self.assertEqual(reverse("goal-list"), GOALS_URL)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(GOALS_URL)

        self.assertRedirects(response, "/accounts/login/?next=/goals/")


class SignedInGoalListTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    def test_signed_in_user_gets_the_goals_page(self):
        response = self.client.get(GOALS_URL)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "goals/goal_list.html")
        self.assertContains(response, "<title>Goals · Learning Companion</title>", html=True)


class OwnGoalsOnlyTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.bob = create_user("bob")
        self.client.force_login(self.ada)

    def test_list_shows_own_goals_but_not_other_users_goals(self):
        own = Goal.objects.create(owner=self.ada, title="Learn Django")
        Goal.objects.create(owner=self.bob, title="Bob's secret goal")

        response = self.client.get(GOALS_URL)

        self.assertQuerySetEqual(response.context["goal_list"], [own])
        self.assertContains(response, "Learn Django")
        self.assertNotContains(response, "secret goal")
