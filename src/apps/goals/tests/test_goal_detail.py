from datetime import datetime, timezone as dt_timezone

from django.test import TestCase
from django.urls import reverse

from apps.goals.models import Goal
from apps.goals.tests.test_goal_list import create_user


def detail_url(goal):
    return f"/goals/{goal.pk}/"


class AnonymousGoalDetailTests(TestCase):
    def test_detail_url_is_named_goal_detail(self):
        goal = Goal.objects.create(owner=create_user(), title="Learn Django")

        self.assertEqual(reverse("goal-detail", args=[goal.pk]), detail_url(goal))

    def test_anonymous_user_is_redirected_to_login(self):
        goal = Goal.objects.create(owner=create_user(), title="Learn Django")

        response = self.client.get(detail_url(goal))

        self.assertRedirects(response, f"/accounts/login/?next={detail_url(goal)}")


class OwnGoalDetailTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)
        self.goal = Goal.objects.create(
            owner=self.ada,
            title="Learn Django",
            description="Models, views and templates.",
            status=Goal.Status.IN_PROGRESS,
        )
        Goal.objects.filter(pk=self.goal.pk).update(
            created_at=datetime(2026, 10, 1, 9, 0, tzinfo=dt_timezone.utc),
            updated_at=datetime(2026, 10, 2, 17, 30, tzinfo=dt_timezone.utc),
        )

    def test_detail_shows_title_status_and_description(self):
        response = self.client.get(detail_url(self.goal))

        self.assertTemplateUsed(response, "goals/goal_detail.html")
        self.assertContains(response, "<title>Learn Django · Learning Companion</title>", html=True)
        self.assertContains(response, "<h1>Learn Django</h1>", html=True)
        self.assertContains(response, "In progress")
        self.assertContains(response, "Models, views and templates.")

    def test_detail_shows_created_and_updated_timestamps(self):
        response = self.client.get(detail_url(self.goal))

        self.assertContains(response, 'datetime="2026-10-01T09:00:00+00:00"')
        self.assertContains(response, 'datetime="2026-10-02T17:30:00+00:00"')


class OtherGoalDetailTests(TestCase):
    def setUp(self):
        self.client.force_login(create_user("ada"))

    def test_another_users_goal_is_not_found(self):
        bobs_goal = Goal.objects.create(owner=create_user("bob"), title="Bob's secret goal")

        response = self.client.get(detail_url(bobs_goal))

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "secret goal", status_code=404)

    def test_unknown_goal_is_not_found(self):
        response = self.client.get("/goals/999999/")

        self.assertEqual(response.status_code, 404)
