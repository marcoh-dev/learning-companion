from django.contrib.auth import get_user_model
from django.test import TestCase


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

        # The logged-in page itself is covered by ProfilePageTests.
        self.assertRedirects(response, PROFILE_URL, fetch_redirect_response=False)


class ProfilePageTests(TestCase):
    def setUp(self):
        self.user = create_user(name="Ada Lovelace", cohort="2026-autumn")
        self.client.force_login(self.user)

    def test_profile_page_shows_username_name_and_cohort_label(self):
        response = self.client.get(PROFILE_URL)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertTemplateUsed(response, "base.html")
        content = response.content.decode().split("</nav>", 1)[1]
        for text in ("ada", "Ada Lovelace", "2026 Autumn"):
            with self.subTest(text=text):
                self.assertIn(text, content)

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
