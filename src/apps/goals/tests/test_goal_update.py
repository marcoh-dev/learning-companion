from django.test import TestCase
from django.urls import reverse

from apps.goals.models import Goal
from apps.goals.tests.test_goal_create import INVALID_GOAL_CASES
from apps.goals.tests.test_goal_list import create_user
from config.tests.test_base_layout import messages_section


def edit_url(goal):
    return f"/goals/{goal.pk}/edit/"


class AnonymousGoalUpdateTests(TestCase):
    def setUp(self):
        self.goal = Goal.objects.create(owner=create_user(), title="Learn Django")

    def test_edit_url_is_named_goal_update(self):
        self.assertEqual(reverse("goal-update", args=[self.goal.pk]), edit_url(self.goal))

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(edit_url(self.goal))

        self.assertRedirects(response, f"/accounts/login/?next={edit_url(self.goal)}")


class OwnGoalUpdateTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.bob = create_user("bob")
        self.client.force_login(self.ada)
        self.goal = Goal.objects.create(
            owner=self.ada,
            title="Learn Django",
            description="Models first.",
            status=Goal.Status.IN_PROGRESS,
        )

    def test_form_is_prefilled_with_current_values(self):
        response = self.client.get(edit_url(self.goal))

        self.assertTemplateUsed(response, "goals/goal_form.html")
        self.assertContains(response, "<h1>Edit goal</h1>", html=True)
        form = response.context["form"]
        self.assertEqual(form["title"].value(), "Learn Django")
        self.assertEqual(form["description"].value(), "Models first.")
        self.assertEqual(form["status"].value(), "in_progress")

    def test_valid_post_saves_and_redirects_to_detail_with_message(self):
        data = {"title": "Learn Django well", "description": "Views next.", "status": "done"}

        response = self.client.post(edit_url(self.goal), data, follow=True)

        self.assertRedirects(response, f"/goals/{self.goal.pk}/")
        self.assertIn("Goal saved.", messages_section(response.content.decode()))
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.title, "Learn Django well")
        self.assertEqual(self.goal.description, "Views next.")
        self.assertEqual(self.goal.status, Goal.Status.DONE)

    def test_posted_owner_is_ignored(self):
        data = {"title": "Learn Django", "description": "", "status": "planned", "owner": self.bob.pk}

        self.client.post(edit_url(self.goal), data)

        self.goal.refresh_from_db()
        self.assertEqual(self.goal.owner, self.ada)

    def test_invalid_input_rerenders_with_error_and_changes_nothing(self):
        for case, (data, error) in INVALID_GOAL_CASES.items():
            with self.subTest(case=case):
                response = self.client.post(edit_url(self.goal), data)

                self.assertContains(response, error, status_code=200)
                self.goal.refresh_from_db()
                self.assertEqual(self.goal.title, "Learn Django")
                self.assertEqual(self.goal.description, "Models first.")
                self.assertEqual(self.goal.status, Goal.Status.IN_PROGRESS)


class OtherGoalUpdateTests(TestCase):
    def setUp(self):
        self.client.force_login(create_user("ada"))
        self.bobs_goal = Goal.objects.create(owner=create_user("bob"), title="Bob's secret goal")

    def test_get_another_users_goal_is_not_found(self):
        response = self.client.get(edit_url(self.bobs_goal))

        self.assertEqual(response.status_code, 404)

    def test_post_another_users_goal_is_not_found_and_changes_nothing(self):
        data = {"title": "Hijacked", "description": "", "status": "done"}

        response = self.client.post(edit_url(self.bobs_goal), data)

        self.assertEqual(response.status_code, 404)
        self.bobs_goal.refresh_from_db()
        self.assertEqual(self.bobs_goal.title, "Bob's secret goal")
        self.assertEqual(self.bobs_goal.status, Goal.Status.PLANNED)
