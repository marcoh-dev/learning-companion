# Profile focus areas (tags)

## Story
As a learner, I want to tag my profile with the focus areas I'm working on, picking from common topics or adding my own, so that the app knows what I'm learning and later tickets can report my hours per topic.

## Acceptance criteria
- [ ] AC1 A `Tag` model holds a unique `name` (max 30 chars). `Profile.focus_areas` is a many-to-many relation to `Tag` that may be empty. Deleting a profile does not delete any tag.
- [ ] AC2 A data migration seeds the starter tags `python`, `django`, `testing`, `sql`, `javascript` and `devops`. They exist in a freshly migrated database.
- [ ] AC3 The profile page's display block lists the user's focus areas in alphabetical order, or shows "not set" when there are none.
- [ ] AC4 The edit form offers one checkbox per tag that is either a starter tag or already one of this user's focus areas, with the user's current focus areas ticked. A tag that only another user has added is not offered and appears nowhere on the page.
- [ ] AC5 Saving with a set of checkboxes ticked makes exactly those tags the user's focus areas: newly ticked ones are added, unticked ones are removed.
- [ ] AC6 The form has a single "new tag" text field. On save, a non-blank value is trimmed and lower-cased, then added to the user's focus areas together with the ticked tags. An existing tag with that name is reused instead of creating a duplicate. A blank value is ignored.
- [ ] AC7 An invalid new-tag value re-renders the page with 200 and a field error, and saves nothing. Invalid means longer than 30 chars after trimming, or containing a comma (only one tag per save).
- [ ] AC8 Saving more than 10 focus areas in total (ticked plus new) re-renders the page with 200 and a form error, and saves nothing.
- [ ] AC9 Posting the id of a tag that the form doesn't offer (e.g. a tag only another user has added) is rejected as an invalid choice, and nothing is saved.
- [ ] AC10 Saving one user's focus areas never changes another user's focus areas.

## Out of scope
- Tags on learning sessions (#11) and the hours-per-tag dashboard (#18). Both will reuse this `Tag` model.
- Managing the tag vocabulary: renaming, deleting, merging, cleaning up unused tags, or an admin UI for tags.
- Adding several new tags in one save.
- Showing other users' focus areas or a tag browser.

## Notes
- Interview answers:
  - Use our own `Tag` model with a many-to-many relation; no third-party library such as django-taggit.
  - Tags are one shared vocabulary: "python" is the same tag for everyone. Each user only sees the tags on their own data.
  - Editing uses checkboxes plus a new-tag field.
  - The checkboxes show the starter set plus the user's own tags, so tags other users invented stay invisible.
  - One new tag per save.
  - Tag names are max 30 chars, and a profile has at most 10 focus areas.
- `instructions/challenge.md` line 48 asks for "a list of `focus_area` tags" on the Profile. Line 56 asks for `tags` on `LearningSession`. Line 88 asks to total "logged session hours per tag" with ORM aggregation. A plain `Tag` model with a many-to-many relation keeps that aggregation a simple `annotate(Sum(...))`.
- Current state:
  - `Profile` has `user`, `name` and `cohort`.
  - `ProfileForm` fields are `name` and `cohort`.
  - The profile page shows a `<dl>` display block and the edit form. These tests must keep passing: `test_profile_page.py`, `test_profile_model.py` and `test_nav.py`.
- Names are stored trimmed and lower-cased, so "Python " and "python" are the same tag.

## Issue
#6
