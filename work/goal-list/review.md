# Review: goal-list
## Verdict: PASS

The suite is green (123 tests, OK), `manage.py check` is clean and `makemigrations --check --dry-run` reports "No changes detected". The code-reviewer and security-reviewer agents found 0 high and 0 medium findings. All 10 plan steps were built in order, one commit each.

## Acceptance criteria
Unless a path is given, tests are in `apps/goals/tests/`.

- **AC1 — PASS.** Fields and migration.
  - `test_goal_model`: `GoalFieldTests.test_title_is_required_text_of_at_most_200_chars`, `test_description_is_optional`; `GoalOwnerTests.test_goal_belongs_to_its_owner`; `GoalStatusTests`; `GoalTimestampTests`; `GoalMigrationTests.test_models_have_no_pending_migrations`.
- **AC2 — PASS.** Status choices, default and validation.
  - `test_goal_model.GoalStatusTests`: `test_status_choices_are_planned_in_progress_and_done`, `test_status_defaults_to_planned`, `test_unknown_status_fails_validation`.
- **AC3 — PASS.** Timestamps.
  - `test_goal_model.GoalTimestampTests`: `test_created_at_and_updated_at_are_set_on_create`, `test_saving_again_moves_updated_at_but_keeps_created_at`.
- **AC4 — PASS.** Cascade on user delete.
  - `test_goal_model.GoalOwnerTests.test_deleting_the_owner_deletes_their_goals`.
- **AC5 — PASS.** `str()`.
  - `test_goal_model.GoalFieldTests.test_str_is_the_title`.
- **AC6 — PASS.** Login required.
  - `test_goal_list.AnonymousGoalListTests`: `test_anonymous_user_is_redirected_to_login`, `test_goal_list_url_is_named_goal_list`.
- **AC7 — PASS.** Own goals only.
  - `test_goal_list.OwnGoalsOnlyTests.test_list_shows_own_goals_but_not_other_users_goals`.
- **AC8 — PASS.** Row content and ordering.
  - `test_goal_list`: `GoalRowTests.test_each_row_shows_title_and_status_label`, `GoalOrderingTests.test_goals_are_listed_newest_updated_first`.
- **AC9 — PASS.** Empty state.
  - `test_goal_list.EmptyGoalListTests`: all three tests.
- **AC10 — PASS.** Nav link.
  - `config/tests/test_base_layout.BaseLayoutTests`: `test_nav_goals_link_points_to_goal_list`, `test_nav_goals_link_follows_the_goal_list_url_name`, `test_nav_has_placeholder_links_for_upcoming_pages`.
- **AC11 — PASS.** Admin.
  - `test_goal_admin.GoalAdminTests`: `test_goal_is_registered_with_list_columns_and_status_filter`, `test_superuser_can_open_the_goal_changelist`.

## Findings
None of these blocks the PASS. They are recorded for follow-up and not fixed in this review.

- **[low] Title rules only checked via field settings.** `src/apps/goals/tests/test_goal_model.py:11-15`. The title test inspects `blank`/`max_length` and does not run `full_clean()` on a blank or 201-character title. It follows the existing `_meta.get_field` convention. Recommendation: add `full_clean()` cases when goal forms arrive in #8.
- **[low] `goal_rows()` hides missing list markup.** `src/apps/goals/tests/test_goal_list.py:17-23`. It returns `[]` when the `<ul class="goal-list">` markup is missing, so the empty-state "no rows" assertions are weaker than they look. The row and ordering tests currently catch a markup rename. Recommendation: also assert `response.context["goal_list"]` is empty in the empty-state tests.
- **[low] Ordering has no tie-breaker.** `src/apps/goals/views.py:9`. Recommendation: use `order_by("-updated_at", "-pk")` for a stable order, especially before pagination exists.
- **[low] Three migrations for a new model.** `src/apps/goals/migrations/0001`–`0003`: one per TDD step, and 0003 carries a one-off `timezone.now` default that a new table doesn't need. It's harmless. Recommendation (optional): squash before the first deploy, as a planned step.
- **[low] Mixed quote styles.** `src/apps/goals/models.py`, `views.py`, `admin.py` use double quotes, while `urls.py` and `apps.py` in the same app use single quotes. Recommendation: settle on one style.
- **[low] No pagination.** `src/apps/goals/views.py`. Every goal renders on one page. Pagination is explicitly out of scope in `ticket.md`. Recommendation: add `paginate_by` in a later ticket.
- **[low] Pico CSS loaded without pinning or SRI.** `src/templates/base.html:7`. It loads from a CDN with a floating `@2` version and no Subresource Integrity hash. This predates the branch and is already covered by #29 (security hardening, CDN integrity).

## Reviewed
commit f1be1ca, 2026-10-02
