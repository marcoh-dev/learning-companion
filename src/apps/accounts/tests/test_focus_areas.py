from html.parser import HTMLParser

from django.test import TestCase

from apps.accounts.tests.test_profile_page import PROFILE_URL, create_user
from apps.tags.models import Tag


STARTER_TAGS = ["devops", "django", "javascript", "python", "sql", "testing"]


def tag(name):
    return Tag.objects.get_or_create(name=name)[0]


class FocusAreaCheckboxes(HTMLParser):
    """Collect the focus_areas checkboxes: {pk: checked} and {pk: visible label text}."""

    def __init__(self):
        super().__init__()
        self.checked_by_id = {}
        self.label_by_id = {}
        self._current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("type") == "checkbox" and attrs.get("name") == "focus_areas":
            self._current = int(attrs["value"])
            self.checked_by_id[self._current] = "checked" in attrs
            self.label_by_id[self._current] = ""

    def handle_data(self, data):
        if self._current is not None:
            self.label_by_id[self._current] += data

    def handle_endtag(self, tag):
        if tag == "label" and self._current is not None:
            self.label_by_id[self._current] = self.label_by_id[self._current].strip()
            self._current = None


def focus_area_checkboxes(response):
    parser = FocusAreaCheckboxes()
    parser.feed(response.content.decode())
    names = dict(Tag.objects.filter(pk__in=parser.checked_by_id).values_list("pk", "name"))
    return {names[pk]: checked for pk, checked in parser.checked_by_id.items()}


class FocusAreaDisplayTests(TestCase):
    def test_display_lists_focus_areas_alphabetically(self):
        user = create_user()
        # Created in reverse order, so the listing must really sort by name.
        user.profile.focus_areas.add(tag("rust"), tag("go"))
        self.client.force_login(user)

        response = self.client.get(PROFILE_URL)

        self.assertInHTML("<dt>Focus areas</dt>", response.content.decode())
        self.assertInHTML("<dd>go, rust</dd>", response.content.decode())


class FocusAreaFormTests(TestCase):
    def test_form_offers_starter_and_own_tags_with_current_ones_checked(self):
        user = create_user()
        user.profile.focus_areas.add(tag("python"), tag("rust"))
        self.client.force_login(user)

        checkboxes = focus_area_checkboxes(self.client.get(PROFILE_URL))

        expected = {name: name == "python" for name in STARTER_TAGS} | {"rust": True}
        self.assertEqual(checkboxes, expected)

    def test_another_users_private_tag_is_not_offered_or_shown(self):
        bob = create_user("bob")
        bob.profile.focus_areas.add(tag("secret-b"))
        self.client.force_login(create_user("ada"))

        response = self.client.get(PROFILE_URL)

        self.assertNotIn("secret-b", focus_area_checkboxes(response))
        self.assertNotContains(response, "secret-b")

    def test_a_starter_tag_shared_with_another_user_gets_one_checkbox(self):
        create_user("bob").profile.focus_areas.add(tag("python"))
        ada = create_user("ada")
        ada.profile.focus_areas.add(tag("python"))
        self.client.force_login(ada)

        html = self.client.get(PROFILE_URL).content.decode()

        self.assertEqual(html.count(f'name="focus_areas" value="{tag("python").pk}"'), 1)

    def test_each_checkbox_is_labelled_with_its_tag_name(self):
        self.client.force_login(create_user())
        parser = FocusAreaCheckboxes()

        parser.feed(self.client.get(PROFILE_URL).content.decode())

        names_by_id = dict(Tag.objects.values_list("pk", "name"))
        self.assertEqual(parser.label_by_id, {pk: names_by_id[pk] for pk in parser.label_by_id})
        self.assertEqual(sorted(parser.label_by_id.values()), STARTER_TAGS)


def names(profile):
    return list(profile.focus_areas.values_list("name", flat=True))


class SaveFocusAreaTests(TestCase):
    def setUp(self):
        self.user = create_user(name="Ada")
        self.user.profile.focus_areas.add(tag("python"), tag("rust"))
        self.client.force_login(self.user)

    def post(self, *tag_names, **extra):
        data = {"name": "Ada", "cohort": "", "focus_areas": [tag(n).pk for n in tag_names]} | extra
        return self.client.post(PROFILE_URL, data)

    def test_ticked_tags_become_exactly_the_focus_areas(self):
        response = self.post("rust", "sql")

        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(names(self.user.profile), ["rust", "sql"])

    def test_new_tag_is_normalised_and_added_with_the_ticked_ones(self):
        self.post("python", new_tag="  Go ")

        self.assertEqual(names(self.user.profile), ["go", "python"])

    def test_new_tag_reuses_an_existing_tag_of_that_name(self):
        tag_count = Tag.objects.count()

        self.post("rust", new_tag="Python")

        self.assertEqual(names(self.user.profile), ["python", "rust"])
        self.assertEqual(Tag.objects.count(), tag_count)

    def test_blank_new_tag_is_ignored(self):
        tag_count = Tag.objects.count()

        self.post("python", new_tag="   ")

        self.assertEqual(names(self.user.profile), ["python"])
        self.assertEqual(Tag.objects.count(), tag_count)

    def test_invalid_new_tag_shows_error_and_saves_nothing(self):
        cases = {
            "longer than 30 chars": ("x" * 31, "Ensure this value has at most 30 characters (it has 31)."),
            "more than one tag": ("rust, go", "Enter one tag at a time."),
            # "İ" lower-cases to two code points, so 30 of them become 60.
            "longer than 30 chars once lower-cased": (
                "İ" * 30,
                "Ensure this value has at most 30 characters (it has 60).",
            ),
        }
        tag_count = Tag.objects.count()

        for case, (value, error) in cases.items():
            with self.subTest(case=case):
                response = self.post("sql", name="Changed", new_tag=value)

                self.assertContains(response, error, status_code=200)
                self.user.profile.refresh_from_db()
                self.assertEqual(self.user.profile.name, "Ada")
                self.assertEqual(names(self.user.profile), ["python", "rust"])
                self.assertEqual(Tag.objects.count(), tag_count)


class FocusAreaLimitTests(TestCase):
    def setUp(self):
        self.user = create_user(name="Ada")
        self.own = ["elm", "go", "rust", "zig"]
        self.user.profile.focus_areas.add(*[tag(n) for n in self.own])
        self.client.force_login(self.user)
        self.ten = STARTER_TAGS + self.own

    def post(self, new_tag=""):
        data = {"name": "Ada", "cohort": "", "new_tag": new_tag, "focus_areas": [tag(n).pk for n in self.ten]}
        return self.client.post(PROFILE_URL, data)

    def test_more_than_10_focus_areas_are_rejected(self):
        response = self.post(new_tag="nim")

        self.assertContains(response, "Choose at most 10 focus areas.", status_code=200)
        self.assertEqual(names(self.user.profile), self.own)
        self.assertFalse(Tag.objects.filter(name="nim").exists())

    def test_exactly_10_focus_areas_are_saved(self):
        response = self.post()

        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(names(self.user.profile), sorted(self.ten))

    def test_new_tag_equal_to_a_ticked_one_is_not_counted_twice(self):
        response = self.post(new_tag="Python")

        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(names(self.user.profile), sorted(self.ten))


class ForeignTagTests(TestCase):
    def test_posting_a_tag_that_is_not_offered_is_rejected(self):
        bob = create_user("bob")
        secret = tag("secret-b")
        bob.profile.focus_areas.add(secret)
        ada = create_user("ada", name="Ada")
        self.client.force_login(ada)

        response = self.client.post(PROFILE_URL, {"name": "Changed", "cohort": "", "focus_areas": [secret.pk]})

        self.assertContains(
            response,
            f"Select a valid choice. {secret.pk} is not one of the available choices.",
            status_code=200,
        )
        ada.profile.refresh_from_db()
        self.assertEqual((ada.profile.name, names(ada.profile)), ("Ada", []))

    def test_saving_never_changes_another_users_focus_areas(self):
        bob = create_user("bob")
        bob.profile.focus_areas.add(tag("python"), tag("secret-b"))
        ada = create_user("ada")
        ada.profile.focus_areas.add(tag("python"))
        self.client.force_login(ada)

        self.client.post(PROFILE_URL, {"name": "", "cohort": "", "focus_areas": [tag("sql").pk]})

        self.assertEqual(names(ada.profile), ["sql"])
        self.assertEqual(names(bob.profile), ["python", "secret-b"])
