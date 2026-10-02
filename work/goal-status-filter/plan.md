# Plan: goal-status-filter

## Research summary
- **List view:** `GoalListView(OwnGoalMixin, ListView)` in `src/apps/goals/views.py`. `OwnGoalMixin` (LoginRequiredMixin) limits `get_queryset()` to `request.user.goals.all()`, and the list view adds `.order_by("-updated_at")`. The context name is `goal_list`.
- **Template** (`src/templates/goals/goal_list.html`):
  - `<h1>Your goals</h1>`, then `<p><a href="{% url 'goal-create' %}">New goal</a></p>`.
  - Then either `<ul class="goal-list">` rows `<li><strong><a href=detail>title</a></strong> <mark>status label</mark></li>`, or `<p>No goals yet.</p>`.
- **Statuses:** `Goal.Status` TextChoices: `planned`/"Planned", `in_progress`/"In progress", `done`/"Done". `Goal.Status.values` and `.choices` are available.
- **Tests:**
  - `src/apps/goals/tests/test_goal_list.py` has helpers `create_user(username)`, `PASSWORD`, `GOALS_URL = "/goals/"` and `goal_rows(response)`, which returns the row texts or `[]` when the `<ul class="goal-list">` markup is missing.
  - Existing classes cover anonymous access, own-only rows, ordering, the empty state and the links. The style is `TestCase`, `force_login` in `setUp`, `updated_at` set with `QuerySet.update()` for ordering, and regex/HTMLParser helpers for extracting markup.
- **Forms convention:** GET forms aren't used yet. Templates use double-quoted attributes and 2-space indentation.

## Design decisions
- **Filter parsing in the view:** `GoalListView.active_status()` returns `request.GET["status"]` only if it's in `Goal.Status.values`, otherwise `""`. Invalid or empty values are ignored with no error branch (AC3).
- **Queryset:** `get_queryset()` filters `status=active` when it's set, and keeps the owner scope and `-updated_at` ordering from the mixin and the existing code.
- **Context:** `get_context_data()` adds:
  - `status_options`: a list of `(value, label, count, selected)` for All plus each `Goal.Status`. Counts come from one aggregate over the owner-scoped, unfiltered queryset (`values("status").annotate(Count("pk"))`), so they ignore the active filter and other users (AC6).
  - `has_goals`: True when the user has any goals at all (the All count is greater than 0), used to tell AC7 from AC8 apart.
  - `active_status_label`: the label of the active status, used in "No done goals.".
- **Form markup:** `<form method="get" action="{% url 'goal-list' %}" class="goal-filter">` with `<select name="status">`, options `value=""` and the status values, the label text `"<label> (<count>)"`, `selected` on the active option, and `<button type="submit">Filter</button>`.
- **Empty states:** rows if any. Otherwise "No <label|lower> goals." when a filter is active and the user has goals. Otherwise "No goals yet.".
- **Tests:** a new file `src/apps/goals/tests/test_goal_filter.py` reuses `create_user`, `GOALS_URL` and `goal_rows` from `test_goal_list.py`. A local helper `status_options(response)` parses the `<select name="status">` options into `(value, label, selected)` tuples.

## Steps
- [ ] 1. **Filter by a valid status.**
  - Ada has goals in each status, and Bob has a done goal.
  - For each of `planned`, `in_progress` and `done`, `?status=<value>` lists exactly Ada's goals with that status (via `response.context["goal_list"]`), ordered newest updated first. Bob's done goal never appears with `?status=done`.
  - test: `test_goal_filter.py`
  - impl: `views.py` (`GoalListView.get_queryset`)
  - covers: AC1, AC9
- [ ] 2. **Unknown or empty status shows the full list.**
  - `?status=archived` and `?status=` both return 200 with all of Ada's goals, matching the response without the parameter.
  - Without a parameter, all goals are listed (AC2, already true; asserted in the same test).
  - test: `test_goal_filter.py`
  - impl: `views.py` (`active_status()` validation)
  - covers: AC2, AC3
- [ ] 3. **Filter form with a preselected option.**
  - The page has a GET form whose action is `/goals/`, containing `<select name="status">` with option values `["", "planned", "in_progress", "done"]` and labels starting with All/Planned/In progress/Done, plus a "Filter" submit button.
  - The selected option is the active status for each valid value, and `""` for no parameter, `?status=archived` and `?status=`.
  - test: `test_goal_filter.py`
  - impl: `views.py` (`get_context_data`: `status_options` without counts), `goal_list.html`
  - covers: AC4, AC5
- [ ] 4. **Counts in option labels.**
  - Ada has 2 planned, 1 in progress and 2 done goals; Bob has 3 done goals.
  - The labels are exactly `["All (5)", "Planned (2)", "In progress (1)", "Done (2)"]`, and they're identical with `?status=done`.
  - test: `test_goal_filter.py`
  - impl: `views.py` (aggregate counts), `goal_list.html`
  - covers: AC6
- [ ] 5. **Empty-filter message.**
  - Ada has only planned goals. `?status=done` shows "No done goals." and `?status=in_progress` shows "No in progress goals."; neither shows "No goals yet", and both still render the filter form.
  - A user with no goals sees "No goals yet" with no filter and with `?status=done`, plus the "New goal" link. The existing `EmptyGoalListTests` and `NewGoalLinkTests` must stay green.
  - test: `test_goal_filter.py`
  - impl: `views.py` (`has_goals`, `active_status_label`), `goal_list.html`
  - covers: AC7, AC8

**Coverage:** AC1 → 1 · AC2 → 2 · AC3 → 2 · AC4 → 3 · AC5 → 3 · AC6 → 4 · AC7 → 5 · AC8 → 5 · AC9 → 1
