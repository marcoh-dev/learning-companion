# Review: goal-status-filter
## Verdict: PASS

The suite is green (166 tests, OK) and `manage.py check` is clean. The code-reviewer agent found 0 high, 0 medium and 6 low findings. The security-reviewer agent found nothing. All 5 plan steps were built in order, one commit each.

## Acceptance criteria
All tests are in `apps/goals/tests/test_goal_filter.py`.

- **AC1 — PASS.** Valid status filters own goals, newest first.
  - `StatusFilterTests.test_valid_status_lists_only_own_goals_with_that_status_newest_first`.
- **AC2 — PASS.** No status lists all goals.
  - `InvalidStatusFilterTests.test_no_status_lists_all_own_goals`.
- **AC3 — PASS.** An unknown or empty status shows the unfiltered list with status 200.
  - `InvalidStatusFilterTests.test_unknown_or_empty_status_lists_all_own_goals` (`archived`, `""`, `DONE`, `planned;drop`).
- **AC4 — PASS.** GET form, select options and Filter button.
  - `FilterFormTests.test_page_has_a_get_form_with_status_select_and_filter_button`.
- **AC5 — PASS.** Preselected option.
  - `FilterFormTests.test_active_status_is_preselected`.
- **AC6 — PASS.** Counts of own goals, independent of the filter.
  - `FilterCountTests`: `test_option_labels_count_own_goals_per_status`, `test_statuses_without_goals_count_zero`.
- **AC7 — PASS.** Status-specific empty message, form still shown.
  - `EmptyFilterTests.test_filter_without_matches_names_the_status`.
- **AC8 — PASS.** "No goals yet" and the "New goal" link for users without goals.
  - `EmptyFilterTests.test_user_without_goals_sees_no_goals_yet_with_or_without_filter`.
  - The existing `test_goal_list.EmptyGoalListTests` and `NewGoalLinkTests` still pass.
- **AC9 — PASS.** No other users' goals.
  - `StatusFilterTests.test_filter_never_shows_another_users_goals`, plus the exact-list assertion in the AC1 test.

## Findings
None of these blocks the PASS. They are recorded for follow-up and not fixed in this review.

- **[low] AC9 test passes even if the filter returns nothing.** `src/apps/goals/tests/test_goal_filter.py:96`. It only asserts the absence of Bob's goal. The AC1 test's exact `[python, git]` assertion covers the gap. Recommendation: also assert that Ada's done goals appear.
- **[low] Label check wouldn't notice missing options on its own.** `src/apps/goals/tests/test_goal_filter.py:141`. It uses `zip()` with `startswith`; the option-values assertion above it covers the length. Recommendation: compare the label prefixes directly.
- **[low] Hard-coded create URL.** `src/apps/goals/tests/test_goal_filter.py:220`. `/goals/new/` is written out. Recommendation: use `reverse("goal-create")`.
- **[low] Status parsed twice per request.** `src/apps/goals/views.py:28,34`. `active_status()` runs in both `get_queryset` and `get_context_data`. It's cheap and consistent. Recommendation (optional): compute it once.
- **[low] Small deviation from the plan.** `src/apps/goals/views.py:37`. It uses `values_list(...)` where the plan says `values(...)`, with identical results. No action needed.
- **[low] Untested accessibility label.** `src/templates/goals/goal_list.html:9`. A visible "Status" `<label>` was added for accessibility; it isn't in the plan and isn't tested. Accepted.

The reviewer also checked edge cases and found nothing wrong:
- **Repeated `?status=` parameters:** the last value wins, and the list and preselected option agree.
- **Query count:** a filtered request runs 4 queries, with no N+1.
- **Owner scoping:** `super().get_queryset()` in `get_context_data` resolves to the owner-scoped `OwnGoalMixin`.

## Reviewed
commit ea33b10, 2026-10-02
