# Review: user-auth
## Verdict: FAIL

AC3 is only partly proven. It requires an invalid sign-up to re-render the form "with its errors". `InvalidSignUpTests` asserts only that `response.context["form"].errors` is truthy, so it never checks that the errors reach the HTML. A `signup.html` that rendered the fields without their errors would keep the suite green. The login counterpart (AC7) does assert the rendered error text. An uncovered acceptance criterion means FAIL, as in base-layout round 1.

## Acceptance criteria
- AC1 — covered by `test_signup.SignUpPageTests.test_signup_page_renders_user_creation_form_in_base_layout` — PASS
- AC2 — covered by `test_signup.ValidSignUpTests` (`…creates_user_and_redirects_home`, `…logs_the_new_user_in`, `…shows_success_message_on_home_page`) — PASS
- AC3 — partly covered by `test_signup.InvalidSignUpTests.test_invalid_signup_rerenders_form_with_errors_and_creates_no_user`; the rendered errors are not asserted — FAIL
- AC4 — covered by `test_login.LoginPageTests.test_login_page_renders_login_form_in_base_layout` — PASS
- AC5 — covered by `test_login.LoginTests.test_valid_login_authenticates_and_redirects_home` — PASS
- AC6 — covered by `test_login.LoginTests.test_login_follows_safe_next_and_ignores_external_next` — PASS
- AC7 — covered by `test_login.LoginTests.test_invalid_credentials_rerender_form_with_error_and_stay_anonymous` — PASS
- AC8 — covered by `test_logout.LogoutTests` (POST logs out + redirects; GET → 405, still logged in) — PASS
- AC9 — covered by `test_nav.AnonymousNavTests.test_anonymous_nav_links_to_login_and_signup_without_logout` — PASS (see low finding)
- AC10 — covered by `test_nav.LoggedInNavTests.test_logged_in_nav_shows_username_and_logout_form_instead_of_login_links` — PASS (see low finding)

Suite: 59 tests, OK. `manage.py check`: no issues. `makemigrations --check`: no changes.

## Findings
Code review: 0 high, 1 medium, 4 low. Security review: 0 high, 1 medium, 3 low.

- [medium] src/apps/accounts/tests/test_signup.py:61 — The AC3 test checks `form.errors` on the context, not the rendered HTML. — Assert the expected error text per case with `assertContains`, kept in the cases table (plan step 14).
- [medium] src/apps/accounts/urls.py:7,9 (security) — No rate limiting or lockout on login, and none on sign-up, which leaves brute force, credential stuffing and mass sign-up open. — Not part of any AC. Out of scope for this ticket and deferred to a security-hardening ticket (e.g. django-axes or proxy rate limits).
- [low] src/apps/accounts/tests/test_nav.py:34 — The logout form check depends on `method` coming before `action`. — Parse the form attributes with `HTMLParser` (plan step 15).
- [low] src/apps/accounts/tests/test_nav.py:20 — The AC9 "no log-out control" check only asserts that the logout URL is absent. — Also assert there is no "Log out" text in the anonymous nav (plan step 16).
- [low] src/apps/accounts/tests/test_signup.py:4, test_nav.py:8 — Test modules import or duplicate helpers from `config.tests.test_base_layout`. — Accepted for now. Move them to a shared test-utilities module once a third app needs them.
- [low] src/apps/accounts/admin.py, models.py — Empty startapp boilerplate. — Accepted; #5 (profile) will fill models.py.
- [low] src/apps/accounts/views.py:9 (security) — Sign-up reveals that a username exists ("A user with that username already exists."). Login errors stay generic. — Accepted; inherent to username sign-up, and mitigated by the rate limiting deferred above.
- [low] src/config/settings.py (security) — No `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` / `SECURE_SSL_REDIRECT` / HSTS. — Deferred to the hardening ticket (`check --deploy`).
- [low] src/templates/base.html:7 (security) — The CDN stylesheet has no SRI and uses a floating `@2`, and it now also loads on the login and sign-up pages. — Deferred to the hardening ticket (already logged in base-layout).

## Reviewed
commit b176cbb, 2026-10-02
