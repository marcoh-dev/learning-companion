# Review: user-profile
## Verdict: FAIL

AC4 is only partly proven. It requires the page to *show* the user's name and cohort label. `ProfilePageTests.test_profile_page_shows_username_name_and_cohort_label` looks for "Ada Lovelace" and "2026 Autumn" anywhere after `</nav>`. Since step 8 the edit form always contains both (the input `value` and the selected `<option>`), so deleting the display `<dl>` would leave the suite green. Only the username check depends on the display block. The "not set" fallback is untested too. An uncovered acceptance criterion means FAIL, as in #3 and #4 round 1.

## Acceptance criteria
- AC1 — covered by `test_profile_model.ProfileFieldTests` (field rules, cascade) + `ProfileCreationTests.test_create_user_creates_one_empty_profile` — PASS
- AC2 — covered by `test_profile_model.ProfileCreationTests` (create_user, create_superuser + re-save, sign-up; mutation-checked) — PASS
- AC3 — covered by `test_profile_page.AnonymousProfileTests` (redirect with next; login with next → profile) — PASS (see low finding)
- AC4 — form part covered by `ProfilePageTests.test_profile_page_has_edit_form_prefilled_with_current_values`; display part (name, cohort label, "not set") not proven — FAIL
- AC5 — covered by `test_profile_page.OwnProfileOnlyTests.test_page_never_shows_another_users_profile` — PASS
- AC6 — covered by `SaveProfileTests.test_valid_post_saves_redirects_and_shows_success_message`, `test_blank_name_is_a_valid_save` — PASS
- AC7 — covered by `SaveProfileTests.test_invalid_post_rerenders_with_error_and_saves_nothing` — PASS
- AC8 — covered by `SaveProfileTests.test_post_cannot_touch_another_users_profile` — PASS
- AC9 — covered by `MissingProfileTests.test_missing_profile_is_created_when_the_page_opens` — PASS
- AC10 — covered by `test_nav.LoggedInNavTests.test_logged_in_nav_links_to_the_profile_page` — PASS
- AC11 — covered by `test_nav.AnonymousNavTests` (`?next=/` on `/`; none on auth pages; none without a request) + `test_login.LoginTests.test_valid_login_authenticates_and_redirects_home` — PASS (see low finding)

Suite: 78 tests, OK. `manage.py check`: no issues. `makemigrations --check`: no changes.

## Findings
Code review: 0 high, 1 medium, 8 low. Security review: 0 high, 0 medium, 0 low (IDOR, mass assignment, CSRF, XSS, attribute injection and open redirect via `next` all checked). Items deferred to #29 were not re-raised.

- [medium] src/apps/accounts/tests/test_profile_page.py:42-51 — The AC4 display assertions are satisfied by the edit form, not the display block. — Assert `<dd>Ada Lovelace</dd>` / `<dd>2026 Autumn</dd>`, and test the "not set" fallback (plan step 17).
- [low] src/apps/accounts/tests/test_nav.py:53-56 — The no-request test passes even if the Log in link disappears. — Assert the exact `<a href="/accounts/login/">Log in</a>` (plan step 18).
- [low] src/apps/accounts/tests/test_profile_page.py:26-34 — `fetch_redirect_response=False` is no longer needed now that the page exists. — Drop it so AC3's landing page is fetched and asserted 200 (plan step 19).
- [low] src/apps/accounts/tests/test_nav.py:44-46, src/apps/accounts/views.py:3-4 — PEP 8: two blank lines inside a class; import order. — Tidy up (plan step 20, refactor).
- [low] src/apps/accounts/tests/test_profile_model.py:36-55 — The field tests restate the model attributes. — Accepted; they pin the exact cohort list, and the behaviour is covered by AC6/AC7.
- [low] src/apps/accounts/signals.py:9-12 — The receiver also fires on `loaddata` (`raw=True`), so a fixture holding users and profiles would hit the unique constraint. — Follow-up: `if created and not kwargs.get('raw')`, with a test, when fixtures are introduced.
- [low] src/templates/base.html:35 — `next` uses `request.path`, so the query string is dropped. That conforms to AC11 ("current path"). — Follow-up: switch to `get_full_path` when list pages get query filters.
- [low] src/templates/accounts/profile.html:18 — The blank cohort option is "---------" in the form but "not set" on the display. — Accepted; cosmetic.

## Reviewed
commit 144c967, 2026-10-02
