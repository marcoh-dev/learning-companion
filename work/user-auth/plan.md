# Plan: user-auth

## Research summary
- **Django 6.1.1 auth** (installed source, `django/contrib/auth/`):
  - `LoginView` renders `registration/login.html` by default. It redirects to a safe `next` (POST, then GET, checked with `url_has_allowed_host_and_scheme` against the request host), otherwise to `LOGIN_REDIRECT_URL`. Bad credentials raise the `invalid_login` non-field error ("Please enter a correct username and password…").
  - `LogoutView` has `http_method_names = ["post", "options"]`, so a GET returns 405. It redirects to a safe `next`, then `next_page`, then `LOGOUT_REDIRECT_URL`.
  - `UserCreationForm` has the fields `username`, `password1` and `password2`, and rejects usernames that differ only in case (`username__iexact`).
  - `login(request, user)` needs no `backend` argument with the single default backend.
  - `django.contrib.auth.urls` also brings the password change/reset routes, which are out of scope.
- **Current code:**
  - `src/config/urls.py` has only `''` (`home`, a `TemplateView`) and `admin/`. It doesn't import `include`.
  - Settings have no `LOGIN_*` values, and `INSTALLED_APPS` has only Django's defaults. `src/apps/` holds an empty package.
  - The `base.html` nav has a brand `<ul>` and a placeholder `<ul>` with hard-coded `/accounts/login/` "Log in" and `/accounts/signup/` "Sign up".
  - `src/config/tests/test_base_layout.py` asserts those hrefs through `PLACEHOLDER_NAV_LINKS` and `render_nav()`. Both of its classes are `SimpleTestCase`: client tests are anonymous, and `render_child` renders with no request, so `user` is undefined (falsy).
- **Conventions:**
  - New domain apps are created with `mkdir src/apps/<name> && .venv/bin/python src/manage.py startapp <name> src/apps/<name>`, then `name = "apps.<name>"` in `apps.py` and `"apps.<name>"` added to `INSTALLED_APPS`.
  - Tests live in a `tests/` package, in `test_<topic>.py` files with `<Thing>Tests` classes. They use descriptive method names, a blank line between act and assert, `subTest` tables and module-level helpers. Tests that touch the DB use `django.test.TestCase`.
  - Run one app's tests with `.venv/bin/python src/manage.py test apps.accounts -t src`.

## Design decisions
- **App:** create a new `apps.accounts` app (the auth/user domain; #5's profile can join it). Its routes are mounted with `path('accounts/', include('apps.accounts.urls'))`.
- **Routes:** add only `login/` (`LoginView`, name `login`), `logout/` (`LogoutView`, name `logout`) and `signup/` (`SignUpView`, name `signup`) in `apps/accounts/urls.py`. Don't include `django.contrib.auth.urls`, because that would expose password-reset routes with no templates or email setup.
- **Sign-up view:** `SignUpView(CreateView)` with `form_class = UserCreationForm` and `template_name = 'registration/signup.html'`. Its `form_valid` saves the user, calls `login()`, adds `messages.success(...)` and redirects to `home`. It stays a thin view over Django's form.
- **Settings:** `LOGIN_URL = 'login'`, `LOGIN_REDIRECT_URL = 'home'`, `LOGOUT_REDIRECT_URL = 'login'` (URL names, resolved by Django).
- **Templates:** `src/templates/registration/login.html` and `signup.html`, both extending `base.html` and rendering the form with `{% csrf_token %}`. They live in the project templates dir, next to `base.html`.
- **Nav:** `{% if user.is_authenticated %}` shows "Signed in as {{ user.get_username }}" and a `<form method="post" action="{% url 'logout' %}">` with `{% csrf_token %}` and a "Log out" button. Otherwise it shows "Log in"/"Sign up" links through `{% url %}`. Goals, Sessions and Dashboard stay placeholders.
- **Tests:** a new package `src/apps/accounts/tests/` with `test_signup.py`, `test_login.py`, `test_logout.py` and `test_nav.py`, all on `TestCase`. A module-level helper creates a user with a strong test password. Remove the `tests.py` that startapp generates.
- **Pinning tests:** several criteria (AC3, AC6, AC7, part of AC8, AC9) are already met by Django's built-in views once the route exists, so their test passes right away. For those steps the plan names a temporary mutation that must turn the test red. Run it and revert it before committing, and note the check in the commit message.

## Steps
- [x] 1. `GET /accounts/signup/` returns 200, renders `registration/signup.html` (extending `base.html`), and the form has `username`, `password1` and `password2` inputs. test: `src/apps/accounts/tests/test_signup.py`. impl: create `apps.accounts` (startapp, `apps.py` name, `INSTALLED_APPS`), `apps/accounts/urls.py` + `include` in `config/urls.py`, `apps/accounts/views.py` (`SignUpView`, plain `CreateView` for now), `src/templates/registration/signup.html`. covers: AC1
- [x] 2. A valid sign-up POST creates the user and redirects to `/`. impl: `SignUpView.success_url` / `form_valid`. covers: AC2
- [x] 3. After a valid sign-up the new user is authenticated (the client session holds their id, and a follow-up request has `user.is_authenticated`). impl: `login()` in `form_valid`. covers: AC2
- [x] 4. Following the sign-up redirect shows a success message on the home page (inside the messages section). impl: `messages.success` in `form_valid`. covers: AC2
- [x] 5. An invalid sign-up re-renders the form with 200 and errors, creates no user, and leaves the visitor anonymous. Use a `subTest` table: mismatched passwords, a validator-rejected password (e.g. `"12345678"`), and an existing username differing only in case. Pinning test; mutation: make `form_invalid` redirect to `home`. covers: AC3
- [x] 6. `GET /accounts/login/` returns 200 and renders `registration/login.html` (extending `base.html`) with `username` and `password` inputs. impl: `login` route (`LoginView`), `src/templates/registration/login.html`. covers: AC4
- [x] 7. A valid login authenticates the user and redirects to `/`. impl: `LOGIN_REDIRECT_URL = 'home'` (and `LOGIN_URL = 'login'`) in settings. covers: AC5
- [x] 8. Login with `next=/goals/` redirects to `/goals/`, and with `next=https://evil.example/` redirects to `/`. Pinning test; mutation: set `success_url_allowed_hosts={'evil.example'}` on the login view, and the external case must go red. covers: AC6
- [x] 9. Invalid credentials re-render the login form with 200, show the `invalid_login` error, and leave the visitor anonymous. Pinning test; mutation: a template that omits `form.non_field_errors` must make it red. covers: AC7
- [x] 10. `POST /accounts/logout/` logs the user out and redirects to the login page. impl: `logout` route (`LogoutView`), `LOGOUT_REDIRECT_URL = 'login'`. covers: AC8
- [x] 11. `GET /accounts/logout/` does not log the user out (405, still authenticated). Pinning test; mutation: `http_method_names = ['get', 'post', 'options']` on the logout view must make it red. covers: AC8
- [x] 12. For an anonymous visitor the nav has "Log in" → `reverse('login')` and "Sign up" → `reverse('signup')`, and no log-out form. Remove "Log in"/"Sign up" from `PLACEHOLDER_NAV_LINKS` in `src/config/tests/test_base_layout.py`; this is a deliberate test change, called out in the commit. The new test passes against the current hard-coded hrefs, so switch `base.html` to `{% url 'login' %}` / `{% url 'signup' %}` as the refactor. Mutation: point "Sign up" at the wrong URL. test: `src/apps/accounts/tests/test_nav.py`. covers: AC9
- [x] 13. For a logged-in user the nav shows "Signed in as <username>" and a `POST` form aimed at `reverse('logout')` with a CSRF token input and a "Log out" button, and shows no "Log in"/"Sign up" links. impl: `{% if user.is_authenticated %}` branch in `base.html`. test: `src/apps/accounts/tests/test_nav.py`. covers: AC10

## Coverage
| AC | Steps |
|---|---|
| AC1 | 1 |
| AC2 | 2, 3, 4 |
| AC3 | 5 |
| AC4 | 6 |
| AC5 | 7 |
| AC6 | 8 |
| AC7 | 9 |
| AC8 | 10, 11 |
| AC9 | 12 |
| AC10 | 13 |

## Review findings (round 1, see review.md)
- [x] 14. Each invalid sign-up case renders its specific error message in the response HTML. Add the expected text to the cases table: the password-mismatch message, a validator message for `"12345678"` (e.g. "This password is entirely numeric."), and "A user with that username already exists." Then `assertContains` it. Pinning test; mutation: render `signup.html` fields without errors (`{{ form.username }} {{ form.password1 }} {{ form.password2 }}`) must turn every case red. test: `src/apps/accounts/tests/test_signup.py`. covers: AC3
- [x] 15. Make the logged-in nav form check independent of attribute order: parse the `<form>` in the nav with `html.parser` and assert `method` is `post` (case-insensitive) and `action` equals `reverse("logout")`. Test-only fix. Mutation: swapping the attribute order in `base.html` must stay green, and a wrong `action` must turn it red. test: `src/apps/accounts/tests/test_nav.py`. covers: AC10
- [x] 16. The anonymous nav also contains no "Log out" text. Test-only fix. Mutation: adding a "Log out" button with no action to the anonymous branch must turn it red. test: `src/apps/accounts/tests/test_nav.py`. covers: AC9
