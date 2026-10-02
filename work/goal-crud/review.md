# Review: goal-crud
## Verdict: PASS

The suite is green (156 tests, OK), `manage.py check` is clean and `makemigrations --check --dry-run` reports "No changes detected". The code-reviewer and security-reviewer agents found 0 high and 0 medium findings. All 7 plan steps were built in order, one commit each.

## Acceptance criteria
Tests are in `apps/goals/tests/`. The anonymous-redirect preamble is covered by `Anonymous*Tests.test_anonymous_user_is_redirected_to_login` in the detail, create, update and delete test files.

- **AC1 — PASS.** Create form fields and default.
  - `test_goal_create.GoalCreatePageTests`: `test_form_has_title_description_and_status_but_no_owner`, `test_status_is_preselected_to_planned`.
- **AC2 — PASS.** Valid create.
  - `test_goal_create.GoalCreateSuccessTests`: `test_valid_post_creates_one_goal_owned_by_the_signed_in_user`, `test_valid_post_redirects_to_detail_with_success_message`.
- **AC3 — PASS.** Create validation.
  - `test_goal_create.GoalCreatePageTests.test_invalid_input_rerenders_with_error_and_creates_nothing` (blank, 201 characters, unknown status).
  - The 200-character title is accepted in `GoalCreateSuccessTests`.
- **AC4 — PASS.** Detail content and links.
  - `test_goal_detail.OwnGoalDetailTests`: `test_detail_shows_title_status_and_description`, `test_detail_shows_created_and_updated_timestamps`, `test_detail_links_to_edit_page`, `test_detail_links_to_delete_page`.
- **AC5 — PASS.** Detail 404.
  - `test_goal_detail.OtherGoalDetailTests`: `test_another_users_goal_is_not_found`, `test_unknown_goal_is_not_found`.
- **AC6 — PASS.** Edit prefill.
  - `test_goal_update.OwnGoalUpdateTests.test_form_is_prefilled_with_current_values`.
- **AC7 — PASS.** Valid edit, owner unchanged.
  - `test_goal_update.OwnGoalUpdateTests`: `test_valid_post_saves_and_redirects_to_detail_with_message`, `test_posted_owner_is_ignored`.
- **AC8 — PASS.** Edit validation.
  - `test_goal_update.OwnGoalUpdateTests.test_invalid_input_rerenders_with_error_and_changes_nothing`.
- **AC9 — PASS.** Edit 404.
  - `test_goal_update.OtherGoalUpdateTests`: `test_get_another_users_goal_is_not_found`, `test_post_another_users_goal_is_not_found_and_changes_nothing`.
- **AC10 — PASS.** Delete confirmation.
  - `test_goal_delete.OwnGoalDeleteTests`: `test_get_shows_confirmation_and_deletes_nothing`, `test_confirmation_is_a_csrf_protected_post_form`.
- **AC11 — PASS.** Delete.
  - `test_goal_delete.OwnGoalDeleteTests.test_post_deletes_and_redirects_to_list_with_message`.
- **AC12 — PASS.** Delete 404.
  - `test_goal_delete.OtherGoalDeleteTests`: `test_get_another_users_goal_is_not_found`, `test_post_another_users_goal_is_not_found_and_keeps_it`.
- **AC13 — PASS.** "New goal" link.
  - `test_goal_list.NewGoalLinkTests`: `test_list_links_to_create_page`, `test_empty_state_links_to_create_page`.
- **AC14 — PASS.** Title links.
  - `test_goal_list.GoalTitleLinkTests.test_each_title_links_to_its_detail_page`.

## Findings
None of these blocks the PASS. They are recorded for follow-up and not fixed in this review.

- **[low] List view refactor not in the plan.** `src/apps/goals/views.py:16-20`. `GoalListView` now uses `OwnGoalMixin` and `super().get_queryset()`. This refactor was done on green in step 1 and is covered by the existing list tests. It's noted here for scope transparency.
- **[low] Validation tests don't check which field the error is on.** `src/apps/goals/tests/test_goal_create.py:58-64` and `test_goal_update.py:70-79` check that the error text appears, not that it is attached to the right field. Recommendation: add the field name to `INVALID_GOAL_CASES` and use `assertFormError(response.context["form"], field, error)`.
- **[low] Edit prefill test doesn't check the page.** `src/apps/goals/tests/test_goal_update.py:39-47` checks the bound form values, not the rendered inputs. Recommendation: also assert on the rendered `value="Learn Django"` and the selected `in_progress` option.
- **[low] Timestamp test doesn't check the visible date.** `src/apps/goals/tests/test_goal_detail.py` (timestamps test) checks the machine-readable `datetime` attributes only. Recommendation (optional): assert part of the visible date.
- **[low] "New goal" link position isn't tested.** `src/apps/goals/tests/test_goal_list.py` (`NewGoalLinkTests`) doesn't assert that the link sits above the list. The template does place it first (`goal_list.html:7`). Recommendation (optional): assert the link comes before `<ul class="goal-list">`.
- **[low] Description has no length limit.** `src/apps/goals/models.py:16`. This is a minor resource-abuse risk. Recommendation: cap it in `GoalForm` (e.g. 5000 characters) in a later ticket.
- **[low, outside this diff] Pico CSS loaded without pinning or SRI.** `src/templates/base.html:7`. Already covered by #29.

## Reviewed
commit 62796a0, 2026-10-02
