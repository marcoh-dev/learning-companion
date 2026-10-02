# Sign up, log in, log out

## Story
As a learner, I want to create an account, log in and log out with Django's built-in auth, so that my goals and sessions belong to me and the app always shows whether I'm signed in.

## Acceptance criteria
- [x] AC1 `GET /accounts/signup/` returns 200 and renders a sign-up form (Django's `UserCreationForm`: username, password, password confirmation) in a template that extends `base.html`.
- [x] AC2 A valid sign-up `POST` creates the user, logs them in, redirects to the home page (`/`) and shows a success message there.
- [x] AC3 An invalid sign-up `POST` (e.g. mismatched passwords, a password rejected by the configured validators, or an existing username) re-renders the form with 200 and its errors, creates no user, and leaves the visitor logged out.
- [x] AC4 `GET /accounts/login/` returns 200 and renders Django's login form in a template that extends `base.html`.
- [x] AC5 Logging in with valid credentials authenticates the user and redirects to the home page (`/`).
- [x] AC6 Login honours a safe `?next=` target (e.g. `next=/goals/` redirects there after login) and ignores an external one (`next=https://evil.example/` redirects to `/`).
- [x] AC7 Logging in with invalid credentials re-renders the login form with 200 and an error, and the visitor stays logged out.
- [x] AC8 `POST /accounts/logout/` logs the user out and redirects to the login page. A `GET` to the logout URL does not log the user out.
- [x] AC9 For an anonymous visitor, the nav shows "Log in" linking to the login page and "Sign up" linking to the sign-up page, and no log-out control.
- [x] AC10 For a logged-in user, the nav shows "Signed in as <username>" and a "Log out" button inside a `POST` form with a CSRF token aimed at the logout URL, and shows no "Log in" or "Sign up" links.

## Out of scope
- Profile model and profile page (#5). After login the user goes to `/` for now, and #5 may repoint `LOGIN_REDIRECT_URL`.
- Password reset/change, email confirmation, email field on sign-up, social login.
- Redirecting already logged-in users away from the sign-up or login pages.
- Restricting other pages to logged-in users (done with the pages that need it).

## Notes
- Interview answers: auto-login after sign-up then go home; login → home, logout → login page; nav swaps Log in/Sign up for "Signed in as …" + Log out; sign-up fields are username + password only (plain `UserCreationForm`).
- `instructions/challenge.md` requires Django's built-in auth and asks to "confirm you can sign up, log out, and log back in". There is no separate handout.
- Currently there are no accounts routes and no `LOGIN_*` settings. `base.html` has hard-coded placeholder hrefs `/accounts/login/` and `/accounts/signup/` from `base-layout`, and `test_base_layout.py` asserts them, so that test will need to follow the real URLs.
- Django 6.1: `LogoutView` only accepts `POST`, hence the button form. Tests that log a user in need `TestCase` (DB). The existing `SimpleTestCase` layout tests stay anonymous.
- Security: the login view's built-in `next` validation (`url_has_allowed_host_and_scheme`) is what AC6 pins.

## Issue
#4
