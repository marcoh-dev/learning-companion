# Plan: user-profile

## Research summary
- **Current code:**
  - `apps.accounts` has `SignUpView(CreateView)`, which logs the user in, adds a success message and redirects to `home`.
  - Its routes are `login`, `logout` and `signup`. `models.py` is an empty stub, there are no migrations, and `AccountsConfig` has no `ready()`.
  - The `base.html` nav has a brand `<ul>`, a placeholder `<ul>` (Goals/Sessions/Dashboard) and an auth `<ul>`. Logged-in users see "Signed in as …" and a POST logout form; anonymous visitors see `<a href="{% url 'login' %}">Log in</a>` and Sign up.
- **Tests:**
  - `apps/accounts/tests/` holds `test_signup.py` (`PASSWORD`, `signup_data()`, imports `messages_section` from `config.tests.test_base_layout`), `test_login.py` (`create_user()`, plus `test_valid_login_authenticates_and_redirects_home`, which already pins "login without next → `/`"), `test_logout.py` and `test_nav.py` (`nav_of()`, `FormAttrsCollector`).
  - `AnonymousNavTests` asserts the Log in link as exactly `<a href="/accounts/login/">Log in</a>`, so it changes in this ticket.
  - `config/tests/test_base_layout.py` renders `base.html` without a request (`render_child`). There, `request.path` is `""`, which must not produce a stray `?next=`.
- **Django 6.1.1 facts** (installed source):
  - `LoginRequiredMixin` redirects to `redirect_to_login(request.get_full_path())`, which gives exactly `/accounts/login/?next=/accounts/profile/` (`safe="/"`).
  - The `urlencode` filter keeps `/`, so `?next={{ request.path|urlencode }}` gives `?next=/`. `{% querystring %}` would encode `/` as `%2F`.
  - `UpdateView.get_object(queryset=None)` can return the user's profile with no URL kwargs. A `ModelForm` ignores POST keys outside `Meta.fields`.
  - A `CharField` with `choices` and `blank=True` gets a `"---------"` option. Error texts: "Select a valid choice. %(value)s is not one of the available choices." and "Ensure this value has at most 100 characters (it has N)."
  - `create_user`, `create_superuser` and `UserCreationForm.save()` all call `user.save()` on a new instance, so `post_save` fires with `created=True`. Receivers are connected in `AppConfig.ready()`.

## Design decisions
- **Model** (`apps/accounts/models.py`):
  - `Cohort(models.TextChoices)` with `SPRING_2026 = '2026-spring', '2026 Spring'`, `AUTUMN_2026 = '2026-autumn', '2026 Autumn'`, `SPRING_2027 = '2027-spring', '2027 Spring'`.
  - `Profile` has `user = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='profile')`, `name = CharField(max_length=100, blank=True)` and `cohort = CharField(max_length=20, choices=Cohort, blank=True)`.
  - Migration `0001_initial`.
- **Creation:** a `post_save` receiver in `apps/accounts/signals.py` creates the profile when `created` is true. It's connected in `AccountsConfig.ready()`. This covers every way of creating a user, not only sign-up.
- **Form:** `ProfileForm(ModelForm)` in `apps/accounts/forms.py` with `fields = ['name', 'cohort']` and nothing else, so `user` can't be posted.
- **View:** `ProfileView(LoginRequiredMixin, UpdateView)` at `profile/` (name `profile`, i.e. `/accounts/profile/`).
  - `get_object()` returns `Profile.objects.get_or_create(user=self.request.user)[0]`. It is always the requester's own profile, with no id in the URL or query.
  - `success_url = reverse_lazy('profile')`, and `form_valid` adds `messages.success`.
- **Template:** `src/templates/accounts/profile.html` extends `base.html`. It shows the username, name and `get_cohort_display` (or "not set"), then the form with `{% csrf_token %}` and `{{ form.as_div }}`.
- **Nav:**
  - The authenticated branch gets `<a href="{% url 'profile' %}">Profile</a>`.
  - The anonymous Log in href is `{% url 'login' %}` plus `?next={{ request.path|urlencode }}`, but only when `request.path` is set and isn't the login or sign-up URL (compared via `{% url … as … %}`).
  - `LOGIN_REDIRECT_URL` stays `'home'` as the fallback.
- **Tests:** new `apps/accounts/tests/test_profile_model.py` and `test_profile_page.py`, and additions to `test_nav.py`, all on `TestCase`.
- **Pinning tests:** where a step's test passes straight away, because of Django's built-ins or code an earlier step needed, the step names a temporary mutation that must turn it red. Run it, revert it, and note it in the commit message, as in #3 and #4.

## Steps
- [x] 1. `create_user` creates exactly one profile for the new user, reachable as `user.profile`, with `name == ""` and `cohort == ""`. test: `test_profile_model.py`. impl: `Profile` + `Cohort` in `models.py`, migration `0001_initial`, `signals.py` receiver, `AccountsConfig.ready()`. covers: AC1, AC2
- [x] 2. `create_superuser` also creates exactly one profile, and saving an existing user again leaves the profile count at 1. Pinning; mutation: a receiver that ignores `created` (creates on every save) must turn it red. covers: AC2
- [x] 3. A sign-up POST creates exactly one profile for the new user. Pinning; mutation: remove the signal connection in `ready()` and it must go red. test: `test_profile_model.py`. covers: AC2
- [x] 4. Field rules: `name` allows blank and has `max_length` 100. `cohort` allows blank and its choices are exactly 2026 Spring / 2026 Autumn / 2027 Spring with the values above. Deleting the user deletes the profile. Pinning; mutation: `on_delete=PROTECT` must go red, and so must dropping one cohort choice. covers: AC1
- [x] 5. An anonymous `GET /accounts/profile/` redirects to `/accounts/login/?next=/accounts/profile/`. test: `test_profile_page.py`. impl: `ProfileView` (`LoginRequiredMixin` + `UpdateView`, `ProfileForm`), `profile` route, minimal `accounts/profile.html`. covers: AC3
- [x] 6. Logging in via `/accounts/login/?next=/accounts/profile/` lands on `/accounts/profile/` with 200. Pinning; mutation: `redirect_field_name='goto'` on the login view must go red. covers: AC3
- [x] 7. A logged-in `GET` returns 200, renders `accounts/profile.html` and `base.html`, and shows the username, the profile's name and the cohort label (e.g. "2026 Autumn"). impl: `get_object()` returning `request.user.profile`, display markup in the template. covers: AC4
- [x] 8. The page holds an edit form whose `name` input is prefilled and whose `cohort` select has the current value selected. impl: the form in the template. covers: AC4
- [x] 9. With users A and B (B has a distinctive name and cohort), A's page shows neither B's name nor B's cohort label, including with `?user=<B.pk>`. Pinning; mutation: a `get_object()` that honours a `user` query parameter must go red. covers: AC5
- [x] 10. A valid POST (`name`, `cohort`) saves both, redirects to `/accounts/profile/`, and the followed page shows a success message in the messages section. A POST with a blank `name` is also saved. impl: `success_url`, `messages.success` in `form_valid`. covers: AC6
- [x] 11. Invalid POSTs (a `name` of 101 chars; `cohort="nope"`) return 200 with the exact rendered error text, and the stored profile is unchanged. `subTest` table. Pinning; mutation: a template that renders the fields without errors must go red. covers: AC7
- [x] 12. A POST from A that includes `user=<B.pk>` saves A's name on A's profile, leaves B's profile unchanged, and doesn't move A's profile to B. Pinning; mutation: `ProfileForm.Meta.fields` including `'user'` must go red. covers: AC8
- [x] 13. A logged-in user whose profile was deleted gets 200 on `GET /accounts/profile/`, and a fresh empty profile exists afterwards. impl: `get_or_create` in `get_object()`. covers: AC9
- [ ] 14. The logged-in nav contains `<a href="/accounts/profile/">Profile</a>`. test: `test_nav.py`. impl: `base.html` authenticated branch. covers: AC10
- [ ] 15. On `/` the anonymous nav's Log in link is `/accounts/login/?next=/`. This deliberately updates `AnonymousNavTests`, whose old exact `reverse("login")` href would otherwise fail; the commit calls it out. impl: the conditional `?next=` in `base.html`. covers: AC11
- [ ] 16. On `/accounts/login/` and `/accounts/signup/` the anonymous Log in link is exactly `/accounts/login/` with no `next`, and rendering `base.html` without a request (`render_child`) produces no `?next=`. impl: the login/signup exclusion and empty-path guard. Expected red after step 15, because the login page would link to itself with `next`. covers: AC11

## Coverage
| AC | Steps |
|---|---|
| AC1 | 1, 4 |
| AC2 | 1, 2, 3 |
| AC3 | 5, 6 |
| AC4 | 7, 8 |
| AC5 | 9 |
| AC6 | 10 |
| AC7 | 11 |
| AC8 | 12 |
| AC9 | 13 |
| AC10 | 14 |
| AC11 | 15, 16 (the "login without next → `/`" part is already pinned by `test_login.LoginTests.test_valid_login_authenticates_and_redirects_home` from #4) |
