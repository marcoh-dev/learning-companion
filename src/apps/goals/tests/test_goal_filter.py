from datetime import datetime, timezone as dt_timezone

from django.test import TestCase

from apps.goals.models import Goal
from apps.goals.tests.test_goal_list import GOALS_URL, create_user


def create_goal(owner, title, status, day):
    """Create a goal with a fixed updated_at (2026-10-<day>) so ordering is deterministic."""
    goal = Goal.objects.create(owner=owner, title=title, status=status)
    Goal.objects.filter(pk=goal.pk).update(
        updated_at=datetime(2026, 10, day, 12, 0, tzinfo=dt_timezone.utc)
    )
    return goal


class StatusFilterTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.bob = create_user("bob")
        self.client.force_login(self.ada)
        sql = create_goal(self.ada, "Learn SQL", Goal.Status.PLANNED, 1)
        django = create_goal(self.ada, "Learn Django", Goal.Status.IN_PROGRESS, 2)
        git = create_goal(self.ada, "Learn Git", Goal.Status.DONE, 3)
        rust = create_goal(self.ada, "Learn Rust", Goal.Status.PLANNED, 4)
        python = create_goal(self.ada, "Learn Python", Goal.Status.DONE, 5)
        create_goal(self.bob, "Bob's secret goal", Goal.Status.DONE, 6)
        # Newest updated first within each status.
        self.expected = {
            "planned": [rust, sql],
            "in_progress": [django],
            "done": [python, git],
        }

    def test_valid_status_lists_only_own_goals_with_that_status_newest_first(self):
        for status, expected in self.expected.items():
            with self.subTest(status=status):
                response = self.client.get(GOALS_URL, {"status": status})

                self.assertQuerySetEqual(response.context["goal_list"], expected)

    def test_filter_never_shows_another_users_goals(self):
        response = self.client.get(GOALS_URL, {"status": "done"})

        self.assertNotContains(response, "secret goal")
