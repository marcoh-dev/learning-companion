from io import StringIO

from django.contrib.auth import get_user_model
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
