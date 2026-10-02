# Review: profile-focus-areas
## Verdict: FAIL

High-severity defect: every focus-area checkbox is labelled "Tag object (N)" instead of the tag name, because `Tag` has no `__str__`. That was confirmed by rendering the page. Users can't tell which tag they're ticking, so AC4's "offers one checkbox per tag" fails in practice. The AC4/AC5 tests only parse checkbox values, which is why they stayed green. A high finding means FAIL.

## Acceptance criteria
- AC1 — covered by `test_tag_model.FocusAreaRelationTests`, `TagRuleTests` — PASS (see low finding: the length is checked before lower-casing)
- AC2 — covered by `test_tag_model.StarterTagTests.test_migrations_seed_the_starter_tags` — PASS
- AC3 — covered by `test_focus_areas.FocusAreaDisplayTests.test_display_lists_focus_areas_alphabetically` + `test_profile_page.ProfilePageTests.test_empty_profile_shows_not_set_for_name_and_cohort` (count=3) — PASS
- AC4 — `FocusAreaFormTests` cover which tags are offered/checked and that others' tags are hidden, but the labels are wrong ("Tag object (N)") and the one-checkbox-per-tag guarantee (`.distinct()` when a starter tag is shared) is untested — FAIL
- AC5 — covered by `SaveFocusAreaTests.test_ticked_tags_become_exactly_the_focus_areas` — PASS
- AC6 — covered by `SaveFocusAreaTests` (normalised, reuse, blank) — PASS
- AC7 — covered by `SaveFocusAreaTests.test_invalid_new_tag_shows_error_and_saves_nothing` — PASS (see low finding)
- AC8 — covered by `FocusAreaLimitTests` (11 rejected, 10 saved) — PASS (see low finding: a new tag equal to a ticked one is untested)
- AC9 — covered by `ForeignTagTests.test_posting_a_tag_that_is_not_offered_is_rejected` — PASS
- AC10 — covered by `ForeignTagTests.test_saving_never_changes_another_users_focus_areas` — PASS

Suite: 96 tests, OK. `manage.py check`: no issues. `makemigrations --check`: no changes.

## Findings
Code review: 0 high, 1 medium, 5 low. Security review: 0 high, 1 medium, 2 low, plus the label bug (rated high here). Items deferred to #29 were not re-raised.

- [high] src/apps/tags/models.py — No `Tag.__str__`, so the checkbox labels render "Tag object (N)". — Add `__str__` returning the name, and a test that asserts each checkbox's label text (plan step 13).
- [medium] src/apps/accounts/tests/test_focus_areas.py:50 / forms.py:22-24 — `.distinct()` is required (a starter tag shared by two profiles would otherwise get two checkboxes) but untested; the dict-based parser would hide a duplicate. — Pinning test counting the checkbox inputs (plan step 14).
- [medium] src/apps/accounts/forms.py:46 (security) — The shared vocabulary can grow without limit. Each save can create a new `Tag` by unticking old tags and adding new ones, signup is open, and orphaned tags are never deleted. Not covered by any AC. — Deferred: needs a design decision (per-user creation cap with `created_by`, or deleting orphaned non-starter tags). Recommend a follow-up ticket before #11/#18 build on the table.
- [low] src/apps/accounts/forms.py:12,27 — `max_length=30` is checked before `.lower()`. Characters like "İ" lower-case to two code points, so 30 of them store 60 chars (breaks AC1; a 500 on stricter DBs). — Check the length after lower-casing (plan step 15).
- [low] src/apps/accounts/tests/test_focus_areas.py:142-153 — 10 ticked plus a new tag equal to one of them (still 10 distinct) is untested. A `len(ticked) + bool(new_tag)` regression would pass. — Add the case (plan step 16).
- [low] src/apps/tags/views.py, admin.py — Unused startapp boilerplate (`views.py` has an unused import). — Remove (plan step 17, refactor).
- [low] src/apps/accounts/forms.py:22 — `Q(profiles=self.instance)` raises `ValueError` for an unsaved instance (`ProfileForm()`). There is no such caller today. — Follow-up: guard when the form is reused elsewhere.
- [low] forms/profile.html (security) — Sequential global tag ids let a user test, one guessed name at a time, whether a tag name already exists (a reused low id vs a fresh id). — Accepted for now; revisit together with the vocabulary-growth follow-up (e.g. slug `to_field_name`).
- [low] src/apps/tags/tests/test_tag_model.py:26 — The max_length test restates the field definition. — Accepted; AC7 covers the behaviour at form level.

## Reviewed
commit bd7b708, 2026-10-02
