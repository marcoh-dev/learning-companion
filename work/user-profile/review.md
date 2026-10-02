# Review: user-profile
## Verdict: PASS

Round 2. Round 1 (commit 144c967) FAILED because AC4 was only partly proven: the display assertions were also satisfied by the edit form. Plan steps 17–19 resolved that finding and two related test lows, and step 20 tidied PEP 8. Both reviewers confirmed the fixes. The production code is unchanged apart from the import order.

## Acceptance criteria
- AC1 — covered by `test_profile_model.ProfileFieldTests` + `ProfileCreationTests.test_create_user_creates_one_empty_profile` — PASS
- AC2 — covered by `test_profile_model.ProfileCreationTests` (create_user, create_superuser + re-save, sign-up) — PASS
- AC3 — covered by `test_profile_page.AnonymousProfileTests` (redirect with next; login lands on the profile page with 200) — PASS
- AC4 — covered by `test_profile_page.ProfilePageTests` (templates, `<dd>` display of username/name/cohort label, "not set" fallback, prefilled form) — PASS
- AC5 — covered by `test_profile_page.OwnProfileOnlyTests.test_page_never_shows_another_users_profile` — PASS
- AC6 — covered by `SaveProfileTests.test_valid_post_saves_redirects_and_shows_success_message`, `test_blank_name_is_a_valid_save` — PASS
- AC7 — covered by `SaveProfileTests.test_invalid_post_rerenders_with_error_and_saves_nothing` — PASS
- AC8 — covered by `SaveProfileTests.test_post_cannot_touch_another_users_profile` — PASS
- AC9 — covered by `MissingProfileTests.test_missing_profile_is_created_when_the_page_opens` — PASS
- AC10 — covered by `test_nav.LoggedInNavTests.test_logged_in_nav_links_to_the_profile_page` — PASS
- AC11 — covered by `test_nav.AnonymousNavTests` (3 tests) + `test_login.LoginTests.test_valid_login_authenticates_and_redirects_home` — PASS

Suite: 79 tests, OK. `manage.py check`: no issues. `makemigrations --check`: no changes.

## Findings
Code review: 0 high, 0 medium, 3 low. Security review: 0 high, 0 medium, 0 low (IDOR, mass assignment, CSRF, XSS/attribute injection, open redirect and authn all checked). Items deferred to #29 were not re-raised. None block the merge.

- [low] src/apps/accounts/tests/test_profile_page.py:81 — `assertNotContains("2027 Spring</dd>")` depends on the exact markup. AC5 is still caught by the name and `selected`-option checks. — Follow-up: `assertInHTML("<dd>2027 Spring</dd>", html, count=0)`.
- [low] src/apps/accounts/tests/test_profile_page.py:64 — The prefill regex relies on Django's `name`-before-`value` attribute order. — Follow-up: parse the input attributes (like `FormAttrsCollector`) or also assert `form["name"].value()`.
- [low] src/apps/accounts/tests/test_profile_page.py:9-17, test_profile_model.py:25 — `PASSWORD` / `create_user` / sign-up payload are duplicated across the accounts test modules. — Follow-up: a shared accounts test-helper module (together with the round-1 note about helpers imported from `config.tests.test_base_layout`).
- Carried over from round 1, accepted or follow-up: the field tests restate model attributes (accepted); the signal fires on `loaddata` `raw=True` (follow-up when fixtures arrive); `next` uses `request.path` without the query string (follow-up when list pages filter); "---------" vs "not set" on the blank cohort option (accepted).

## Reviewed
commit eec65ff, 2026-10-02
