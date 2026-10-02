import re
from datetime import datetime, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.goals.models import Goal

GOALS_URL = "/goals/"
PASSWORD = "correct-horse-battery-9"


def create_user(username="ada"):
    return get_user_model().objects.create_user(username=username, password=PASSWORD)


def goal_rows(response):
    """Text of each row in the goal list, tags stripped and whitespace collapsed."""
    match = re.search(r'<ul class="goal-list">(.*?)</ul>', response.content.decode(), re.DOTALL)
    if match is None:
        return []
    rows = re.findall(r"<li\b.*?</li>", match.group(1), re.DOTALL)
    return [" ".join(re.sub(r"<[^>]+>", " ", row).split()) for row in rows]


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


class GoalRowTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)

    def test_each_row_shows_title_and_status_label(self):
        Goal.objects.create(owner=self.ada, title="Learn Django", status=Goal.Status.IN_PROGRESS)

        response = self.client.get(GOALS_URL)

        self.assertEqual(goal_rows(response), ["Learn Django In progress"])


class GoalOrderingTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)

    def updated_at(self, goal, day):
        Goal.objects.filter(pk=goal.pk).update(
            updated_at=datetime(2026, 10, day, 12, 0, tzinfo=dt_timezone.utc)
        )

    def test_goals_are_listed_newest_updated_first(self):
        sql = Goal.objects.create(owner=self.ada, title="Learn SQL")
        docker = Goal.objects.create(owner=self.ada, title="Learn Docker")
        django = Goal.objects.create(owner=self.ada, title="Learn Django")
        self.updated_at(sql, 2)
        self.updated_at(docker, 1)
        self.updated_at(django, 3)

        response = self.client.get(GOALS_URL)

        self.assertQuerySetEqual(response.context["goal_list"], [django, sql, docker])
        self.assertEqual(
            goal_rows(response),
            ["Learn Django Planned", "Learn SQL Planned", "Learn Docker Planned"],
        )


class EmptyGoalListTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)

    def test_user_without_goals_sees_empty_state(self):
        response = self.client.get(GOALS_URL)

        self.assertContains(response, "No goals yet")
        self.assertEqual(goal_rows(response), [])

    def test_other_users_goals_do_not_count(self):
        Goal.objects.create(owner=create_user("bob"), title="Learn Rust")

        response = self.client.get(GOALS_URL)

        self.assertContains(response, "No goals yet")
        self.assertEqual(goal_rows(response), [])

    def test_user_with_goals_sees_no_empty_state(self):
        Goal.objects.create(owner=self.ada, title="Learn Django")

        response = self.client.get(GOALS_URL)

        self.assertNotContains(response, "No goals yet")
