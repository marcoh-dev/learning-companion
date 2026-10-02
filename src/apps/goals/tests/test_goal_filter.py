from datetime import datetime, timezone as dt_timezone
from html.parser import HTMLParser

from django.test import TestCase

from apps.goals.models import Goal
from apps.goals.tests.test_goal_list import GOALS_URL, create_user, goal_rows


def create_goal(owner, title, status, day):
    """Create a goal with a fixed updated_at (2026-10-<day>) so ordering is deterministic."""
    goal = Goal.objects.create(owner=owner, title=title, status=status)
    Goal.objects.filter(pk=goal.pk).update(
        updated_at=datetime(2026, 10, day, 12, 0, tzinfo=dt_timezone.utc)
    )
    return goal


class FilterFormParser(HTMLParser):
    """Collect the form that holds <select name="status">: its attributes, options and buttons."""

    def __init__(self):
        super().__init__()
        self.forms = []
        self._form = None
        self._in_status_select = False
        self._text_target = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self._form = {"attrs": attrs, "options": [], "buttons": [], "has_status": False}
        elif self._form is None:
            return
        elif tag == "select" and attrs.get("name") == "status":
            self._form["has_status"] = True
            self._in_status_select = True
        elif tag == "option" and self._in_status_select:
            option = {"value": attrs.get("value"), "label": "", "selected": "selected" in attrs}
            self._form["options"].append(option)
            self._text_target = option
        elif tag == "button":
            button = {"type": attrs.get("type"), "label": ""}
            self._form["buttons"].append(button)
            self._text_target = button

    def handle_endtag(self, tag):
        if tag == "select":
            self._in_status_select = False
        elif tag in ("option", "button"):
            self._text_target = None
        elif tag == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None

    def handle_data(self, data):
        if self._text_target is not None:
            self._text_target["label"] = " ".join((self._text_target["label"] + data).split())


def filter_form(response):
    """The status filter form on the page, or None if there is none."""
    parser = FilterFormParser()
    parser.feed(response.content.decode())
    return next((form for form in parser.forms if form["has_status"]), None)


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


class InvalidStatusFilterTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)
        self.newer = create_goal(self.ada, "Learn Django", Goal.Status.IN_PROGRESS, 2)
        self.older = create_goal(self.ada, "Learn SQL", Goal.Status.PLANNED, 1)

    def test_no_status_lists_all_own_goals(self):
        response = self.client.get(GOALS_URL)

        self.assertQuerySetEqual(response.context["goal_list"], [self.newer, self.older])

    def test_unknown_or_empty_status_lists_all_own_goals(self):
        unfiltered = self.client.get(GOALS_URL)

        for value in ("archived", "", "DONE", "planned;drop"):
            with self.subTest(status=value):
                response = self.client.get(GOALS_URL, {"status": value})

                self.assertEqual(response.status_code, 200)
                self.assertQuerySetEqual(response.context["goal_list"], [self.newer, self.older])
                self.assertEqual(goal_rows(response), goal_rows(unfiltered))


class FilterFormTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)
        create_goal(self.ada, "Learn Django", Goal.Status.IN_PROGRESS, 1)

    def test_page_has_a_get_form_with_status_select_and_filter_button(self):
        response = self.client.get(GOALS_URL)

        form = filter_form(response)
        self.assertIsNotNone(form)
        self.assertEqual(form["attrs"].get("method"), "get")
        self.assertEqual(form["attrs"].get("action"), GOALS_URL)
        self.assertEqual(
            [option["value"] for option in form["options"]], ["", "planned", "in_progress", "done"]
        )
        labels = [option["label"] for option in form["options"]]
        for label, expected_start in zip(labels, ["All", "Planned", "In progress", "Done"]):
            self.assertTrue(label.startswith(expected_start), f"{label!r} should start with {expected_start!r}")
        self.assertIn({"type": "submit", "label": "Filter"}, form["buttons"])

    def test_active_status_is_preselected(self):
        cases = {
            "planned": "planned",
            "in_progress": "in_progress",
            "done": "done",
            "archived": "",
            "": "",
            None: "",
        }

        for status, expected in cases.items():
            with self.subTest(status=status):
                params = {} if status is None else {"status": status}
                response = self.client.get(GOALS_URL, params)

                form = filter_form(response)
                self.assertIsNotNone(form)
                selected = [option["value"] for option in form["options"] if option["selected"]]
                self.assertEqual(selected, [expected])


class FilterCountTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        bob = create_user("bob")
        self.client.force_login(self.ada)
        for day, status in enumerate(["planned", "planned", "in_progress", "done", "done"], start=1):
            create_goal(self.ada, f"Ada goal {day}", status, day)
        for day in (6, 7, 8):
            create_goal(bob, f"Bob goal {day}", "done", day)

    def test_option_labels_count_own_goals_per_status(self):
        expected = ["All (5)", "Planned (2)", "In progress (1)", "Done (2)"]

        for status in (None, "done", "archived"):
            with self.subTest(status=status):
                params = {} if status is None else {"status": status}
                response = self.client.get(GOALS_URL, params)

                labels = [option["label"] for option in filter_form(response)["options"]]
                self.assertEqual(labels, expected)

    def test_statuses_without_goals_count_zero(self):
        self.ada.goals.exclude(status="planned").delete()

        response = self.client.get(GOALS_URL)

        labels = [option["label"] for option in filter_form(response)["options"]]
        self.assertEqual(labels, ["All (2)", "Planned (2)", "In progress (0)", "Done (0)"])


class EmptyFilterTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada")
        self.client.force_login(self.ada)

    def test_filter_without_matches_names_the_status(self):
        create_goal(self.ada, "Learn SQL", Goal.Status.PLANNED, 1)
        cases = {"done": "No done goals.", "in_progress": "No in progress goals."}

        for status, message in cases.items():
            with self.subTest(status=status):
                response = self.client.get(GOALS_URL, {"status": status})

                self.assertContains(response, message)
                self.assertNotContains(response, "No goals yet")
                self.assertEqual(goal_rows(response), [])
                self.assertIsNotNone(filter_form(response))

    def test_user_without_goals_sees_no_goals_yet_with_or_without_filter(self):
        for params in ({}, {"status": "done"}):
            with self.subTest(params=params):
                response = self.client.get(GOALS_URL, params)

                self.assertContains(response, "No goals yet")
                self.assertNotContains(response, "No done goals")
                self.assertContains(response, '<a href="/goals/new/">New goal</a>', html=True)
