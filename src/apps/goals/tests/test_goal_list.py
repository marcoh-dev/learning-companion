from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
