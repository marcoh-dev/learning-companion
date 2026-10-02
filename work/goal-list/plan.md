# Plan: goal-list

## Research summary
- **Project layout:** apps live in `src/apps/<name>` with `name = "apps.<name>"` and are listed in `INSTALLED_APPS` (`src/config/settings.py`). `DEFAULT_AUTO_FIELD` is not set. The root URLconf `src/config/urls.py` includes app urls flat (no `app_name`/namespace). URL names are kebab-free so far (`home`, `login`, `profile`), and this ticket fixes `goal-list`.
- **Views:** class-based only, with `LoginRequiredMixin` (`apps/accounts/views.py`). `LOGIN_URL = 'login'`, so an anonymous request redirects to `/accounts/login/?next=<path>`.
- **Templates:** they live at project level, `src/templates/<app>/<page>.html`. They `{% extends "base.html" %}` and fill `title` ("X · Learning Companion") and `content`. Styling is Pico CSS.
- **Nav (`templates/base.html:15-19`):** Goals/Sessions/Dashboard are hard-coded placeholder hrefs, with a comment saying their tickets switch them to `{% url %}`.
  - `config/tests/test_base_layout.py:16` defines `PLACEHOLDER_NAV_LINKS`, used only at `:119-124`. Those lines `assertInHTML` each anchor and ignore order.
  - `render_child("")` renders base.html without a request, against ROOT_URLCONF.
  - `apps/accounts/tests/test_nav.py` has no Goals assertions.
  - `apps/accounts/tests/test_login.py:47` has a now-stale comment, "/goals/ doesn't exist yet".
- **Tests:** files are `apps/<app>/tests/test_<feature>.py` in a `tests/` package. They use `django.test.TestCase` with `self.client`, several small classes per behaviour, and arrange/act/assert separated by blank lines.
  - Fields are checked through `Model._meta.get_field(...)`.
  - Cascade is checked by deleting the user and then `assertFalse(Model.objects.exists())`.
  - Login redirects use `assertRedirects(response, "/accounts/login/?next=...")`.
  - Helpers are module-level (e.g. `create_user` and `PASSWORD` in `apps/accounts/tests/test_profile_page.py`).
  - No test uses `full_clean`, `__str__`, admin, or `makemigrations --check` yet.
  - There's no freezegun. `unittest.mock` is used, and `USE_TZ = True`, `TIME_ZONE = 'UTC'`.
- **Run:** use `.venv/bin/python src/manage.py test src -t src`, or a single module with `... test apps.goals.tests.test_goal_model -t src` from `src`. The hooks run the full suite.

## Design decisions
- **New app `apps.goals`:** the goals domain grows with tickets #8–#18, so it gets its own app. Create it with the startapp command from CLAUDE.md.
- **`Status(TextChoices)` on the model:** `PLANNED="planned"`, `IN_PROGRESS="in_progress"`, `DONE="done"`, labels "Planned"/"In progress"/"Done". It mirrors `Cohort` in accounts.
- **Owner field:** `owner = ForeignKey(AUTH_USER_MODEL, on_delete=CASCADE, related_name="goals")`. It's named `owner` per the issue.
- **Timestamps:** `created_at` uses `auto_now_add` and `updated_at` uses `auto_now`. Tests patch `django.utils.timezone.now` with `unittest.mock` for deterministic times, so no new dependency is needed.
- **Ordering:** the view does `order_by("-updated_at")`. There's no `Meta.ordering`, so other querysets (admin, future filters) stay explicit.
- **List view:** `GoalListView(LoginRequiredMixin, ListView)`. `get_queryset` filters on `owner=request.user`, uses template `goals/goal_list.html`, and serves `/goals/` with name `goal-list`. Rows show `get_status_display`, and the empty state uses `{% empty %}`.
- **Nav test:** proves that the Goals link uses `{% url 'goal-list' %}` and not a literal `/goals/`. It renders the nav under `override_settings(ROOT_URLCONF=...)` with a test URLconf that maps `goal-list` to a different path. A plain href assertion would already pass with the hard-coded link.

## Steps
- [x] 1. **Goal model core fields.** `title` is required with max_length 200, `description` is blank-allowed, `owner` is a FK to the user with CASCADE, and `str()` is the title. Also adds a guard test that `makemigrations --check --dry-run` reports no changes (it passes before and after, so it doesn't count as the red test).
  - test: `src/apps/goals/tests/test_goal_model.py`
  - impl: new app `src/apps/goals/` (`apps.py`, `models.py`, `migrations/0001_initial.py` via makemigrations), `INSTALLED_APPS`
  - covers: AC1 (title/description/owner, migration), AC4, AC5
- [x] 2. **Status field.** It defaults to `planned`, its choices equal `[("planned","Planned"),("in_progress","In progress"),("done","Done")]`, and `full_clean()` raises `ValidationError` for `status="archived"`.
  - test: `test_goal_model.py`
  - impl: `models.py`, `migrations/0002_*`
  - covers: AC1 (status), AC2
- [x] 3. **Timestamps.** With `timezone.now` patched to T1 on create and T2 on a later save, `created_at == T1` and `updated_at == T2`.
  - test: `test_goal_model.py`
  - impl: `models.py`, `migrations/0003_*`
  - covers: AC1 (timestamps), AC3
- [x] 4. **Login required.** An anonymous GET `/goals/` redirects to `/accounts/login/?next=/goals/`, and `reverse("goal-list") == "/goals/"`.
  - test: `src/apps/goals/tests/test_goal_list.py`
  - impl: `apps/goals/views.py`, `apps/goals/urls.py`, include in `config/urls.py`, `templates/goals/goal_list.html` (title "Goals · Learning Companion")
  - covers: AC6
- [x] 5. **Only your own goals.** Signed in as ada, the page shows ada's goal title and not bob's.
  - test: `test_goal_list.py`
  - impl: `views.py` (`get_queryset`), template loop
  - covers: AC7
- [x] 6. **Rows show the status label.** A goal with `in_progress` renders a row containing its title and "In progress".
  - test: `test_goal_list.py`
  - impl: template
  - covers: AC8 (content)
- [ ] 7. **Newest updated first.** Three goals with `updated_at` set via `QuerySet.update()` appear in `-updated_at` order, asserted on `response.context["goal_list"]` and on title order in the HTML.
  - test: `test_goal_list.py`
  - impl: `views.py` (`order_by`)
  - covers: AC8 (ordering)
- [ ] 8. **Empty state.** A user with no goals sees "No goals yet" and no goal rows. The test is also red for a user whose only goals belong to someone else.
  - test: `test_goal_list.py`
  - impl: template `{% empty %}`
  - covers: AC9
- [ ] 9. **Nav Goals link uses `{% url 'goal-list' %}`.**
  - The test renders the nav under `override_settings(ROOT_URLCONF=<test urlconf>)`, which maps `goal-list` to `/elsewhere/goals/` and keeps the other named routes, and asserts that the Goals anchor follows it.
  - Remove Goals from `PLACEHOLDER_NAV_LINKS`, keeping Sessions and Dashboard, and add an explicit Goals assertion against `reverse("goal-list")`.
  - Update the placeholder comment in base.html and the stale comment in `test_login.py:47`.
  - test: `src/config/tests/test_base_layout.py`
  - impl: `templates/base.html`
  - covers: AC10
- [ ] 10. **Admin registration.** `admin.site.is_registered(Goal)` holds, its ModelAdmin has `list_display == ("title", "status", "owner", "updated_at")` and `list_filter == ("status",)`, and a superuser GET on the goal changelist returns 200.
  - test: `src/apps/goals/tests/test_goal_admin.py`
  - impl: `apps/goals/admin.py`
  - covers: AC11

**Coverage:** AC1 → 1, 2, 3 · AC2 → 2 · AC3 → 3 · AC4 → 1 · AC5 → 1 · AC6 → 4 · AC7 → 5 · AC8 → 6, 7 · AC9 → 8 · AC10 → 9 · AC11 → 10
