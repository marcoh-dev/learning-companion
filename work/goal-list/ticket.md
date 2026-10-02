# Goal model and goal list

## Story
As a signed-in learner, I want my learning goals stored with a title, description and status, and listed on one page, so that I can see at a glance what I'm working towards.

## Acceptance criteria
- [ ] AC1 A `Goal` has `title` (required, max 200 chars), `description` (optional), `status`, `created_at`, `updated_at` and an `owner` (user). The schema change comes from a `makemigrations`-generated migration, and `makemigrations --check` reports no pending changes.
- [ ] AC2 `status` is one of `planned` / `in_progress` / `done` (labels "Planned", "In progress", "Done") and defaults to `planned`. Any other value fails `full_clean()`.
- [ ] AC3 `created_at` is set on create and does not change on later saves. `updated_at` changes on every save.
- [ ] AC4 Deleting a user deletes their goals.
- [ ] AC5 `str(goal)` returns its title.
- [ ] AC6 An anonymous GET to `/goals/` (URL name `goal-list`) redirects to the login page with `?next=/goals/`.
- [ ] AC7 A signed-in user's goal list shows only their own goals. Another user's goal titles don't appear on it.
- [ ] AC8 Each row shows the goal's title and its status label, and goals are ordered by `updated_at`, newest first.
- [ ] AC9 A user with no goals sees an empty-state message ("No goals yet") and no list rows.
- [ ] AC10 The nav's "Goals" link points to `{% url 'goal-list' %}` (`/goals/`) and is no longer a placeholder. The Sessions and Dashboard links stay placeholders, and the layout/nav tests are updated to match.
- [ ] AC11 `Goal` is registered in the Django admin with `title`, `status`, `owner` and `updated_at` in `list_display` and `status` in `list_filter`.

## Out of scope
- Create / edit / delete goals (#8). The list has no "New goal" link yet.
- Filtering by status (#9).
- Goal detail page, sessions, resources (#10, #12+).
- Pagination.

## Notes
- Interview answers: the list shows title + status, ordered newest updated first. Status defaults to planned. In scope: the nav link, the empty state and admin registration. Ticket id is `goal-list`.
- Follow existing conventions: CBVs with `LoginRequiredMixin`, templates under `src/templates/<app>/`, title pattern "Goals · Learning Companion", and tests in `apps/<app>/tests/test_<feature>.py`.
- `PLACEHOLDER_NAV_LINKS` in `config/tests/test_base_layout.py` and the nav tests in `apps/accounts/tests/test_nav.py` currently assume `/goals/` is a placeholder.
- Status values are `planned` / `in_progress` / `done`. The brief writes "in-progress", but a valid identifier is used for the stored value.

## Issue
#7
