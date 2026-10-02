# Plan: profile-focus-areas

## Research summary
- **Current code:** `apps.accounts` is the only app.
  - `Profile` has `user` (one-to-one to the user model, `related_name='profile'`), `name` (max 100, blank) and `cohort` (Cohort choices, blank). The only migration is `0001_initial`.
  - `ProfileForm(ModelForm)` has `fields = ['name', 'cohort']`.
  - `ProfileView(LoginRequiredMixin, UpdateView)` gets the profile with `get_or_create(user=request.user)`, redirects to `profile` and shows "Your profile has been saved."
  - `profile.html` has a `<dl>` (Username, Name, Cohort, each `default:"not set"`) and a form rendered with `{{ form.as_div }}`.
- **Existing tests** (`apps/accounts/tests/`):
  - `test_profile_page.py` has the helper `create_user(username, **profile_fields)` and `PASSWORD`. Every POST sends only `name`/`cohort`, so a new `required=False` field keeps them green.
  - `ProfilePageTests.test_empty_profile_shows_not_set_for_name_and_cohort` asserts `<dd>not set</dd>` with `count=2`. A third "not set" for focus areas breaks it, so it must be updated deliberately.
  - Other modules: `test_profile_model.py`, `test_nav.py`, `test_login.py`, `test_signup.py`, `test_logout.py`.
- **Django 6.1.1 facts:**
  - `ModelMultipleChoiceField` rejects an id outside its queryset with "Select a valid choice. %(value)s is not one of the available choices." (code `invalid_choice`). The queryset can be reassigned in the form's `__init__`.
  - `ModelForm.save(commit=True)` calls `_save_m2m()`. Overriding `_save_m2m` (call `super()`, then add the extra tag) covers both commit paths.
  - `forms.CharField` strips whitespace by default. Too long gives "Ensure this value has at most 30 characters (it has 31)."
  - Data migrations (`RunPython` with `apps.get_model`) run when the test DB is created, so the seeded rows exist in `TestCase` tests.
  - `assertInHTML(..., count=n)` requires exactly n matches.

## Design decisions
- **New app `apps.tags`.** It holds the `Tag` model, which is its own domain and is reused by sessions (#11) and the dashboard (#18). Create it with the CLAUDE.md startapp recipe, `name = 'apps.tags'`, and add it to `INSTALLED_APPS`.
- **`Tag` model:**
  - `name = CharField(max_length=30, unique=True)` and `starter = BooleanField(default=False)`, with `Meta.ordering = ['name']`.
  - The `starter` flag marks the curated set, so the form can offer "starter tags + own tags" without a hard-coded list in app code.
  - The seed migration has its own copy of the six names, because migrations must not import app code.
- **`Profile.focus_areas`:** `ManyToManyField('tags.Tag', blank=True, related_name='profiles')`, in accounts migration `0002`. Many-to-many relations never delete the tags themselves.
- **`ProfileForm`:**
  - `fields = ['name', 'cohort', 'focus_areas']`, with `focus_areas` as a `CheckboxSelectMultiple`.
  - `__init__` sets its queryset to `Tag.objects.filter(Q(starter=True) | Q(profiles=self.instance)).distinct()`.
  - Extra field `new_tag = forms.CharField(max_length=30, required=False)`. `clean_new_tag` lower-cases the value and rejects commas with "Enter one tag at a time."
  - `clean()` rejects more than 10 distinct focus areas (ticked plus new) with "Choose at most 10 focus areas."
  - `_save_m2m()` calls `super()` and then adds `Tag.objects.get_or_create(name=new_tag)[0]` when `new_tag` is set.
- **Display:** the `<dd>` lists the focus area names alphabetically, joined by ", ", or "not set" (via `{% for … %}{% empty %}`).
- **No view change.** `ProfileView` already uses `ProfileForm` and the requester's own profile.
- **Tests:**
  - New `src/apps/tags/tests/test_tag_model.py` (a `tests/` package; delete the startapp `tests.py`).
  - New `src/apps/accounts/tests/test_focus_areas.py`, reusing `create_user`/`PASSWORD` from `test_profile_page.py`. All tests on `TestCase`.
- **Pinning tests:** as in #3–#5, a step whose test passes straight away names a temporary mutation that must turn it red. Run it, revert it, and note it in the commit message.

## Steps
- [x] 1. A profile can hold focus-area tags: after `profile.focus_areas.add(Tag.objects.create(name="rust"))`, `profile.focus_areas` contains exactly that tag. test: `apps/tags/tests/test_tag_model.py`. impl: `apps.tags` app (startapp, `apps.py` name, `INSTALLED_APPS`), `Tag` model + migration `tags/0001`, `Profile.focus_areas` + migration `accounts/0002`. covers: AC1
- [x] 2. Tag rules: a duplicate name raises `IntegrityError`, `name` has `max_length` 30, and deleting the user (and with it the profile) leaves the tag in place. Pinning; mutation: `unique=False` must go red, and so must `max_length=50`. covers: AC1
- [x] 3. A freshly migrated DB contains exactly the starter tags `devops, django, javascript, python, sql, testing` with `starter=True`. impl: data migration `tags/0002_seed_starter_tags` (`RunPython` + reverse). covers: AC2
- [x] 4. The display block shows `<dd>python, testing</dd>` (alphabetical) for a profile with those focus areas, and `<dd>not set</dd>` when there are none. Deliberate test change: `test_empty_profile_shows_not_set_for_name_and_cohort` now expects `count=3`, called out in the commit. impl: `profile.html` display row. covers: AC3
- [x] 5. The edit form offers checkboxes for all starter tags plus the user's own non-starter tag, and the user's current focus areas are `checked`. test: `apps/accounts/tests/test_focus_areas.py`. impl: `focus_areas` in `ProfileForm.Meta.fields` with `CheckboxSelectMultiple`, and the queryset in `__init__`. covers: AC4
- [ ] 6. A tag only user B has (e.g. "secret-b") is not offered on A's form and appears nowhere on A's page. Pinning; mutation: queryset `Tag.objects.all()` must go red. covers: AC4
- [ ] 7. A POST with a set of ticked tags makes exactly those the focus areas: newly ticked added, unticked removed. Pinning (`ModelForm` saves many-to-many relations); mutation: a `_save_m2m` that skips `super()` must go red. covers: AC5
- [ ] 8. `new_tag="  Rust "` adds tag `rust` alongside the ticked ones. `new_tag="Python"` reuses the existing `python` tag, so the `Tag` count stays the same. A blank `new_tag` changes nothing. impl: the `new_tag` field, lower-casing in `clean_new_tag`, `_save_m2m` override. covers: AC6
- [ ] 9. An invalid `new_tag` (31 chars; `"rust, go"`) returns 200 with the exact error text ("Ensure this value has at most 30 characters (it has 31)." / "Enter one tag at a time."). The profile's focus areas, name and cohort are unchanged, and no new `Tag` exists. impl: the comma check in `clean_new_tag`. The length case is pinned by `max_length=30` on the form field; mutation: `max_length=50` must make that case red. covers: AC7
- [ ] 10. Ticking 10 tags plus a new one (11 in total) returns 200 with "Choose at most 10 focus areas." and saves nothing. Exactly 10 still saves. Fixture: the six starter tags plus four own tags already on the profile. impl: `ProfileForm.clean()`. covers: AC8
- [ ] 11. Posting the id of a tag that isn't offered (another user's private tag) returns 200 with the `invalid_choice` error text, and saves nothing. Pinning; mutation: queryset `Tag.objects.all()` must go red. covers: AC9
- [ ] 12. A's save leaves B's focus areas unchanged, even when both share a starter tag that A unticks. Pinning; mutation: a `_save_m2m` that applies the same set to every profile must go red. covers: AC10

## Coverage
| AC | Steps |
|---|---|
| AC1 | 1, 2 |
| AC2 | 3 |
| AC3 | 4 |
| AC4 | 5, 6 |
| AC5 | 7 |
| AC6 | 8 |
| AC7 | 9 |
| AC8 | 10 |
| AC9 | 11 |
| AC10 | 12 |
