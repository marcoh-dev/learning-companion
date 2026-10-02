from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.goals.models import Goal


class GoalFieldTests(TestCase):
    def test_title_is_required_text_of_at_most_200_chars(self):
        field = Goal._meta.get_field("title")

        self.assertFalse(field.blank)
        self.assertEqual(field.max_length, 200)

    def test_description_is_optional(self):
        field = Goal._meta.get_field("description")

        self.assertTrue(field.blank)

    def test_str_is_the_title(self):
        owner = get_user_model().objects.create_user(username="ada")

        goal = Goal.objects.create(owner=owner, title="Learn Django")

        self.assertEqual(str(goal), "Learn Django")


class GoalStatusTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="ada")

    def test_status_choices_are_planned_in_progress_and_done(self):
        field = Goal._meta.get_field("status")

        self.assertEqual(
            field.choices,
            [("planned", "Planned"), ("in_progress", "In progress"), ("done", "Done")],
        )

    def test_status_defaults_to_planned(self):
        goal = Goal.objects.create(owner=self.owner, title="Learn Django")

        goal.refresh_from_db()
        self.assertEqual(goal.status, "planned")
        self.assertEqual(goal.get_status_display(), "Planned")

    def test_unknown_status_fails_validation(self):
        goal = Goal(owner=self.owner, title="Learn Django", status="archived")

        with self.assertRaises(ValidationError) as caught:
            goal.full_clean()

        self.assertIn("status", caught.exception.message_dict)


class GoalOwnerTests(TestCase):
    def test_goal_belongs_to_its_owner(self):
        owner = get_user_model().objects.create_user(username="ada")

        goal = Goal.objects.create(owner=owner, title="Learn Django")

        self.assertQuerySetEqual(owner.goals.all(), [goal])

    def test_deleting_the_owner_deletes_their_goals(self):
        owner = get_user_model().objects.create_user(username="ada")
        Goal.objects.create(owner=owner, title="Learn Django")

        owner.delete()

        self.assertFalse(Goal.objects.exists())


class GoalMigrationTests(TestCase):
    def test_models_have_no_pending_migrations(self):
        out = StringIO()

        call_command("makemigrations", "--check", "--dry-run", stdout=out)

        self.assertIn("No changes detected", out.getvalue())
