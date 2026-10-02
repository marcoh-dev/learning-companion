from django.test import TestCase
from django.urls import reverse

from apps.goals.models import Goal
from apps.goals.tests.test_goal_list import create_user
from config.tests.test_base_layout import messages_section

CREATE_URL = "/goals/new/"

# Invalid form input and Django's error message for it. Edit uses the same rules.
INVALID_GOAL_CASES = {
    "blank title": (
        {"title": "", "description": "", "status": "planned"},
        "This field is required.",
    ),
    "title over 200 chars": (
        {"title": "x" * 201, "description": "", "status": "planned"},
        "Ensure this value has at most 200 characters (it has 201).",
    ),
    "unknown status": (
        {"title": "Learn Django", "description": "", "status": "archived"},
        "Select a valid choice. archived is not one of the available choices.",
    ),
}


class AnonymousGoalCreateTests(TestCase):
    def test_create_url_is_named_goal_create(self):
        self.assertEqual(reverse("goal-create"), CREATE_URL)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(CREATE_URL)

        self.assertRedirects(response, f"/accounts/login/?next={CREATE_URL}")


class GoalCreatePageTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)

    def test_form_has_title_description_and_status_but_no_owner(self):
        response = self.client.get(CREATE_URL)

        self.assertTemplateUsed(response, "goals/goal_form.html")
        self.assertEqual(list(response.context["form"].fields), ["title", "description", "status"])
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="status"')
        self.assertNotContains(response, 'name="owner"')
        self.assertContains(response, "<h1>New goal</h1>", html=True)

    def test_status_is_preselected_to_planned(self):
        response = self.client.get(CREATE_URL)

        self.assertEqual(response.context["form"]["status"].value(), "planned")
        self.assertContains(response, '<option value="planned" selected>Planned</option>', html=True)

    def test_invalid_input_rerenders_with_error_and_creates_nothing(self):
        for case, (data, error) in INVALID_GOAL_CASES.items():
            with self.subTest(case=case):
                response = self.client.post(CREATE_URL, data)

                self.assertContains(response, error, status_code=200)
                self.assertFalse(Goal.objects.exists())


class GoalCreateSuccessTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.bob = create_user("bob")
        self.client.force_login(self.ada)
        self.data = {
            "title": "x" * 200,
            "description": "Models, views and templates.",
            "status": "in_progress",
            "owner": self.bob.pk,
        }

    def test_valid_post_creates_one_goal_owned_by_the_signed_in_user(self):
        self.client.post(CREATE_URL, self.data)

        goal = Goal.objects.get()
        self.assertEqual(goal.owner, self.ada)
        self.assertEqual(goal.title, "x" * 200)
        self.assertEqual(goal.description, "Models, views and templates.")
        self.assertEqual(goal.status, Goal.Status.IN_PROGRESS)

    def test_valid_post_redirects_to_detail_with_success_message(self):
        response = self.client.post(CREATE_URL, self.data, follow=True)

        goal = Goal.objects.get()
        self.assertRedirects(response, f"/goals/{goal.pk}/")
        self.assertIn("Goal created.", messages_section(response.content.decode()))
