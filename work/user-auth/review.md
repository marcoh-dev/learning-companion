# Review: user-auth
## Verdict: PASS

Round 2. Round 1 (commit b176cbb) FAILED because AC3 was only partly proven: the invalid sign-up test checked `form.errors` on the context, not the rendered errors. Plan steps 14–16 resolved it and two related test lows (step 14: specific error text per case, verified red when the template renders fields without errors). Both reviewers confirmed the fixes. Production code is unchanged since round 1.

## Acceptance criteria
- AC1 — covered by `test_signup.SignUpPageTests.test_signup_page_renders_user_creation_form_in_base_layout` — PASS
- AC2 — covered by `test_signup.ValidSignUpTests` (`…creates_user_and_redirects_home`, `…logs_the_new_user_in`, `…shows_success_message_on_home_page`) — PASS
- AC3 — covered by `test_signup.InvalidSignUpTests.test_invalid_signup_rerenders_form_with_errors_and_creates_no_user` (rendered error text per case, no user created, still anonymous) — PASS
- AC4 — covered by `test_login.LoginPageTests.test_login_page_renders_login_form_in_base_layout` — PASS
- AC5 — covered by `test_login.LoginTests.test_valid_login_authenticates_and_redirects_home` — PASS
- AC6 — covered by `test_login.LoginTests.test_login_follows_safe_next_and_ignores_external_next` — PASS
- AC7 — covered by `test_login.LoginTests.test_invalid_credentials_rerender_form_with_error_and_stay_anonymous` — PASS
- AC8 — covered by `test_logout.LogoutTests` (POST logs out + redirects to login; GET → 405, still logged in) — PASS
- AC9 — covered by `test_nav.AnonymousNavTests.test_anonymous_nav_links_to_login_and_signup_without_logout` — PASS
- AC10 — covered by `test_nav.LoggedInNavTests.test_logged_in_nav_shows_username_and_logout_form_instead_of_login_links` — PASS

Suite: 59 tests, OK. `manage.py check`: no issues. `makemigrations --check`: no changes.

## Findings
Code review: 0 high, 0 medium, 3 low. Security review: 0 high, 0 new medium, 1 new low. 1 medium and 3 lows carried over from round 1, already deferred. None block the merge.

- [medium, carried over] src/apps/accounts/urls.py:7,9 (security) — No rate limiting or lockout on login or sign-up. — Deferred to a security-hardening ticket (django-axes or proxy rate limits). Should be done before any real deployment.
- [low] src/apps/accounts/tests/test_nav.py:58-59 — The logged-in "no Log in / Sign up" checks match `">Log in<"` exactly, so whitespace around the link text would slip through. — Follow-up: assert that `reverse("login")` / `reverse("signup")` are absent from the nav.
- [low] src/apps/accounts/tests/test_signup.py:42-45 — The AC2 message test doesn't assert that the landing page is home. The redirect is pinned separately. — Follow-up: `assertTemplateUsed(response, "home.html")`.
- [low] src/apps/accounts/tests/test_login.py:34-48 — The two `next` subtests share a logged-in client. That's fine while `redirect_authenticated_user` is False. — Follow-up: log out per subtest. Do it before enabling `redirect_authenticated_user`.
- [low, new] src/apps/accounts/views.py:8 (security) — A user who is already signed in can open sign-up and is silently switched to the new account. Not exploitable cross-user (CSRF-protected). Listed as out of scope in the ticket. — Follow-up: redirect authenticated users away from sign-up/login (`redirect_authenticated_user=True`), together with the `next`-test follow-up above.
- [low, carried over] src/apps/accounts/views.py:9 (security) — Sign-up reveals whether a username exists. — Accepted; mitigated by the deferred rate limiting.
- [low, carried over] src/config/settings.py (security) — No secure-cookie, SSL redirect or HSTS settings. — Deferred to the hardening ticket (`check --deploy`).
- [low, carried over] src/templates/base.html:7 (security) — The CDN stylesheet has no SRI and uses a floating `@2`. — Deferred to the hardening ticket.
- [low, carried over] Test helpers imported or duplicated from `config.tests.test_base_layout`, and empty startapp `admin.py`/`models.py`. — Accepted.

## Reviewed
commit 0e41170, 2026-10-02
