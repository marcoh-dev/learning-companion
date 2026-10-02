from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Profile
from config.tests.test_base_layout import messages_section


PROFILE_URL = "/accounts/profile/"
PASSWORD = "correct-horse-battery-9"


def create_user(username="ada", **profile_fields):
    user = get_user_model().objects.create_user(username=username, password=PASSWORD)
    for field, value in profile_fields.items():
        setattr(user.profile, field, value)
    user.profile.save()
    return user


class AnonymousProfileTests(TestCase):
    def test_anonymous_visitor_is_redirected_to_login_with_next(self):
        response = self.client.get(PROFILE_URL)

        self.assertRedirects(response, "/accounts/login/?next=/accounts/profile/")

    def test_login_from_the_redirect_lands_on_the_profile_page(self):
        create_user()

        response = self.client.post(
            "/accounts/login/?next=/accounts/profile/", {"username": "ada", "password": PASSWORD}
        )

        self.assertRedirects(response, PROFILE_URL)


class ProfilePageTests(TestCase):
    def setUp(self):
        self.user = create_user(name="Ada Lovelace", cohort="2026-autumn")
        self.client.force_login(self.user)

    def test_profile_page_shows_username_name_and_cohort_label(self):
        response = self.client.get(PROFILE_URL)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertTemplateUsed(response, "base.html")
        html = response.content.decode()
        # Asserted on the <dd> display elements: the edit form also contains these values.
        for value in ("ada", "Ada Lovelace", "2026 Autumn"):
            with self.subTest(value=value):
                self.assertInHTML(f"<dd>{value}</dd>", html)

    def test_empty_profile_shows_not_set_for_name_and_cohort(self):
        self.user.profile.name, self.user.profile.cohort = "", ""
        self.user.profile.save()

        response = self.client.get(PROFILE_URL)

        self.assertInHTML("<dd>not set</dd>", response.content.decode(), count=2)

    def test_profile_page_has_edit_form_prefilled_with_current_values(self):
        response = self.client.get(PROFILE_URL)

        self.assertRegex(response.content.decode(), r'<input[^>]*name="name"[^>]*value="Ada Lovelace"')
        self.assertInHTML('<option value="2026-autumn" selected>2026 Autumn</option>', response.content.decode())


class OwnProfileOnlyTests(TestCase):
    def setUp(self):
        self.ada = create_user("ada", name="Ada Lovelace", cohort="2026-autumn")
        self.bob = create_user("bob", name="Bob Distinctive", cohort="2027-spring")
        self.client.force_login(self.ada)

    def test_page_never_shows_another_users_profile(self):
        for url in (PROFILE_URL, f"{PROFILE_URL}?user={self.bob.pk}"):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertContains(response, "Ada Lovelace")
                self.assertNotContains(response, "Bob Distinctive")
                self.assertNotContains(response, "2027 Spring</dd>")
                self.assertNotContains(response, '<option value="2027-spring" selected>')


class SaveProfileTests(TestCase):
    def setUp(self):
        self.user = create_user(name="Ada", cohort="2026-spring")
        self.client.force_login(self.user)

    def test_valid_post_saves_redirects_and_shows_success_message(self):
        response = self.client.post(PROFILE_URL, {"name": "Ada Lovelace", "cohort": "2026-autumn"}, follow=True)

        self.assertRedirects(response, PROFILE_URL)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual((profile.name, profile.cohort), ("Ada Lovelace", "2026-autumn"))
        self.assertIn("Your profile has been saved.", messages_section(response.content.decode()))

    def test_blank_name_is_a_valid_save(self):
        response = self.client.post(PROFILE_URL, {"name": "", "cohort": ""})

        self.assertRedirects(response, PROFILE_URL)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual((profile.name, profile.cohort), ("", ""))

    def test_invalid_post_rerenders_with_error_and_saves_nothing(self):
        cases = {
            "name too long": (
                {"name": "x" * 101, "cohort": "2026-autumn"},
                "Ensure this value has at most 100 characters (it has 101).",
            ),
            "cohort outside the choices": (
                {"name": "Ada Lovelace", "cohort": "nope"},
                "Select a valid choice. nope is not one of the available choices.",
            ),
        }

        for case, (data, error) in cases.items():
            with self.subTest(case=case):
                response = self.client.post(PROFILE_URL, data)

                self.assertContains(response, error, status_code=200)
                profile = Profile.objects.get(user=self.user)
                self.assertEqual((profile.name, profile.cohort), ("Ada", "2026-spring"))

    def test_post_cannot_touch_another_users_profile(self):
        bob = create_user("bob", name="Bob", cohort="2027-spring")

        self.client.post(PROFILE_URL, {"name": "Hijacked", "cohort": "2026-autumn", "user": bob.pk})

        own, other = Profile.objects.get(user=self.user), Profile.objects.get(user=bob)
        self.assertEqual((own.name, own.cohort), ("Hijacked", "2026-autumn"))
        self.assertEqual((other.name, other.cohort), ("Bob", "2027-spring"))


class MissingProfileTests(TestCase):
    def test_missing_profile_is_created_when_the_page_opens(self):
        user = create_user()
        Profile.objects.filter(user=user).delete()
        self.client.force_login(user)

        response = self.client.get(PROFILE_URL)

        self.assertEqual(response.status_code, 200)
        profile = Profile.objects.get(user=user)
        self.assertEqual((profile.name, profile.cohort), ("", ""))
