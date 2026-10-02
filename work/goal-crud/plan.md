# Plan: goal-crud

## Research summary
- **Existing goals app** (`src/apps/goals/`, from goal-list):
  - `Goal` has `owner` (FK, `related_name="goals"`), `title` (max 200), `description` (blank), `status` (`Goal.Status` TextChoices, default planned), `created_at` and `updated_at`.
  - `GoalListView(LoginRequiredMixin, ListView)` filters on `request.user.goals.order_by("-updated_at")`.
  - `urls.py` has `goal-list` at `''` and is included at `goals/`.
  - The template `templates/goals/goal_list.html` renders `<ul class="goal-list">` rows `<li><strong>title</strong> <mark>status</mark></li>` and, when empty, `<p>No goals yet.</p>`.
- **Views convention** (`apps/accounts/views.py`):
  - CBVs with `LoginRequiredMixin`. Success messages come from `messages.success(self.request, ...)` inside `form_valid`, not from `SuccessMessageMixin`.
  - Imports are grouped as django.contrib, then django.urls/views, then local modules.
- **Forms convention** (`apps/accounts/forms.py`): `ModelForm` with `Meta.fields` as a list and `widgets` as a dict.
- **Templates:** `{% extends "base.html" %}`, title "X · Learning Companion", forms as `<form method="post">{% csrf_token %}{{ form.as_div }}<button type="submit">…</button></form>`. Errors come from `as_div`'s errorlist, and messages render in `base.html`'s `<section class="messages">`.
- **Tests:**
  - `django.test.TestCase` with `force_login` in `setUp`.
  - Validation is checked with a dict of cases plus `subTest`, `assertContains(response, "<django error text>", status_code=200)`, then a DB check that nothing changed.
  - Messages are checked by posting with `follow=True`, then `assertRedirects`, then `assertIn(text, messages_section(response.content.decode()))`. The helper is `config.tests.test_base_layout.messages_section`.
  - Anonymous access gets `assertRedirects(response, "/accounts/login/?next=<url>")`.
  - There are no 404 tests yet; use `assertEqual(response.status_code, 404)`.
  - `apps/goals/tests/test_goal_list.py` has `create_user`, `PASSWORD`, `GOALS_URL` and `goal_rows()`; the new test files import them.
- **Quotes:** Python in `apps/goals` is mostly double-quoted (`urls.py` is single-quoted startapp style). Tests and templates use double quotes.

## Design decisions
- **One `GoalForm(ModelForm)`** in `apps/goals/forms.py` with `fields = ["title", "description", "status"]`, used by create and edit. `owner` is never a form field, so a posted `owner` value is ignored by construction.
- **`OwnGoalMixin(LoginRequiredMixin)`** with `get_queryset()` returning `self.request.user.goals.all()`. Detail, edit and delete all use it, so another user's goal is not in the queryset and `get_object` raises 404. There's one place to get ownership right.
- **`Goal.get_absolute_url()`** returns `reverse("goal-detail", args=[self.pk])`. Create and edit then redirect there without needing `success_url`.
- **Create:** `GoalCreateView.form_valid` sets `form.instance.owner = self.request.user`, then adds "Goal created.".
- **Edit:** `GoalUpdateView.form_valid` adds "Goal saved.".
- **Delete:** `GoalDeleteView(OwnGoalMixin, DeleteView)` with `success_url = reverse_lazy("goal-list")`. `form_valid` adds "Goal deleted." (Django ≥4 DeleteView deletes in `form_valid`). Its default GET renders the confirmation page.
- **URLs:** `goals/new/` (`goal-create`), `goals/<int:pk>/` (`goal-detail`), `goals/<int:pk>/edit/` (`goal-update`) and `goals/<int:pk>/delete/` (`goal-delete`). `new/` is a literal path, so it can't clash with `<int:pk>`.
- **Templates:**
  - `goals/goal_detail.html` and `goals/goal_confirm_delete.html`.
  - `goals/goal_form.html` is shared by create and edit, with the heading "New goal" or "Edit goal" depending on whether `object` exists.
- **Quotes:** new goals Python code uses double quotes, matching `models.py`/`views.py`. `urls.py` is switched to double quotes while it's edited in step 1.
- **Tests:** a new file per page:
  - `test_goal_detail.py`
  - `test_goal_create.py`
  - `test_goal_update.py`
  - `test_goal_delete.py`
  - list-link tests go in `test_goal_list.py`.

## Steps
- [x] 1. **Detail page, own goals only.**
  - Signed in as ada, GET `/goals/<id>/` shows the title, status label, description and created/updated timestamps.
  - Bob's goal returns 404, and an unknown id returns 404.
  - Anonymous access redirects to login with `next`.
  - `reverse("goal-detail", args=[pk]) == f"/goals/{pk}/"`.
  - test: `apps/goals/tests/test_goal_detail.py`
  - impl: `views.py` (`OwnGoalMixin`, `GoalDetailView`), `urls.py`, `templates/goals/goal_detail.html`
  - covers: AC4 (content), AC5
- [x] 2. **Create page, GET and invalid POST.**
  - GET `/goals/new/` shows a form with title, description and status inputs, status preselected to "planned", and no owner input. Anonymous access redirects.
  - POSTs with a blank title, a 201-character title or `status="archived"` re-render with Django's error text and create no goal.
  - test: `apps/goals/tests/test_goal_create.py`
  - impl: `forms.py` (`GoalForm`), `views.py` (`GoalCreateView`), `urls.py`, `templates/goals/goal_form.html`
  - covers: AC1, AC3 (invalid cases)
- [x] 3. **Create, valid POST.**
  - A POST with a 200-character title, a description and status `in_progress` creates exactly one goal owned by ada. That's true even when `owner=bob.pk` is posted.
  - The response redirects to the new goal's detail page, which shows "Goal created." in the messages section.
  - test: `test_goal_create.py`
  - impl: `views.py` (`form_valid`), `models.py` (`get_absolute_url`)
  - covers: AC2, AC3 (200 characters accepted)
- [x] 4. **Edit page.**
  - GET `/goals/<id>/edit/` shows the form prefilled with the goal's current title, description and status.
  - A valid POST saves, redirects to detail, and shows "Goal saved.". The owner is unchanged even with `owner=bob.pk` posted.
  - Invalid POSTs (the AC3 cases) re-render with errors, and the DB row is unchanged.
  - GET and POST for Bob's goal return 404, and Bob's goal is unchanged.
  - Anonymous access redirects.
  - The detail page links to the edit URL.
  - test: `apps/goals/tests/test_goal_update.py`, plus one test in `test_goal_detail.py` for the Edit link
  - impl: `views.py` (`GoalUpdateView`), `urls.py`, `goal_form.html` (heading), `goal_detail.html` (Edit link)
  - covers: AC6, AC7, AC8, AC9, AC4 (Edit link)
- [x] 5. **Delete page.**
  - GET `/goals/<id>/delete/` shows a confirmation naming the goal, with a `method="post"` form containing the CSRF token, and the goal still exists.
  - A POST deletes it, redirects to `/goals/`, and shows "Goal deleted.".
  - GET and POST for Bob's goal return 404, and his goal still exists.
  - Anonymous access redirects.
  - The detail page links to the delete URL.
  - test: `apps/goals/tests/test_goal_delete.py`, plus one test in `test_goal_detail.py` for the Delete link
  - impl: `views.py` (`GoalDeleteView`), `urls.py`, `templates/goals/goal_confirm_delete.html`, `goal_detail.html` (Delete link)
  - covers: AC10, AC11, AC12, AC4 (Delete link)
- [ ] 6. **"New goal" link on the list.** The list page links to `reverse("goal-create")`, both when the user has goals and in the empty state.
  - test: `test_goal_list.py`
  - impl: `goal_list.html`
  - covers: AC13
- [ ] 7. **List titles link to detail.** Each row's title is an `<a href="/goals/<id>/">` with the title text. The existing `goal_rows()` text assertions keep passing, because only the tags change.
  - test: `test_goal_list.py`
  - impl: `goal_list.html`
  - covers: AC14

Every goal page's anonymous-redirect requirement (the preamble of the ACs) is covered in steps 1, 2, 4 and 5.

**Coverage:** AC1 → 2 · AC2 → 3 · AC3 → 2, 3 · AC4 → 1, 4, 5 · AC5 → 1 · AC6 → 4 · AC7 → 4 · AC8 → 4 · AC9 → 4 · AC10 → 5 · AC11 → 5 · AC12 → 5 · AC13 → 6 · AC14 → 7
