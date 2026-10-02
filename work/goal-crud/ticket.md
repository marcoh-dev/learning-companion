# Create, edit and delete goals

## Story
As a signed-in learner, I want to create, view, edit and delete my learning goals, so that my goal list stays accurate as my plans change, without anyone else being able to see or touch my goals.

## Acceptance criteria
The URLs below are absolute paths. "Another user's goal" means a goal whose `owner` is a different user. All goal pages require login. An anonymous GET to any URL below redirects to `/accounts/login/?next=<that URL>`.

**Create**
- [x] AC1 GET `/goals/new/` (`goal-create`) shows a form with `title`, `description` and `status`, with status preselected to "Planned". There is no `owner` field.
- [x] AC2 A valid POST to `/goals/new/` creates one goal owned by the signed-in user. A posted `owner` value is ignored. The response redirects to that goal's detail page, which shows the message "Goal created."
- [x] AC3 A POST with a blank title, a title over 200 characters, or an unknown status creates no goal and re-renders the form with an error on that field. A 200-character title is accepted.

**Detail**
- [x] AC4 GET `/goals/<id>/` (`goal-detail`) for an own goal shows the title, status label, description, created and updated timestamps, and links to its edit and delete pages.
- [x] AC5 GET `/goals/<id>/` for another user's goal, or for an id that doesn't exist, returns 404.

**Edit**
- [x] AC6 GET `/goals/<id>/edit/` (`goal-update`) for an own goal shows the form prefilled with its current values.
- [x] AC7 A valid POST to `/goals/<id>/edit/` saves the changes and redirects to the goal's detail page, which shows "Goal saved." The owner doesn't change, even if a different `owner` value is posted.
- [x] AC8 An invalid edit POST changes nothing and re-renders the form with field errors (same rules as AC3).
- [x] AC9 GET or POST `/goals/<id>/edit/` for another user's goal returns 404, and the goal is unchanged.

**Delete**
- [x] AC10 GET `/goals/<id>/delete/` (`goal-delete`) for an own goal shows a confirmation naming the goal, with a POST form (CSRF-protected). The GET deletes nothing.
- [x] AC11 POST `/goals/<id>/delete/` for an own goal deletes it and redirects to `/goals/`, which shows "Goal deleted."
- [x] AC12 GET or POST `/goals/<id>/delete/` for another user's goal returns 404, and the goal still exists.

**List links**
- [x] AC13 The goal list shows a "New goal" link to `goal-create`, both above the list and in the empty state.
- [x] AC14 Each goal title on the list links to its `goal-detail` page.

## Out of scope
- Filtering by status (#9), learning sessions (#10+), resources (#12+), AI summary/next steps (#15, #16).
- Pagination and bulk actions.
- Changing the list ordering or row layout beyond adding the links (goal-list behaviour stays as shipped).

## Notes
- Interview answers:
  - **Fields:** one form for create and edit (title, description, status), with status defaulting to Planned on create. The owner is never a form field.
  - **Redirects:** after create/edit go to the detail page with a flash message; after delete go to the list with "Goal deleted."
  - **Delete:** a confirmation page, and only POST deletes.
  - **Links:** New goal on the list, titles link to detail, Edit/Delete on detail.
- Ticket id `goal-crud`.
- 404 (not 403) for other users' goals, per the issue. Ownership must not be revealed through a different status code.
- The status code for an invalid POST isn't fixed by the ACs. Django's form re-render is 200.
- The goal-list review (`work/goal-list/review.md`) flagged that title validation was only tested through field settings. AC3/AC8 now cover it through the form.
- Follow existing conventions: CBVs with `LoginRequiredMixin`, success messages as in `ProfileView`, templates in `src/templates/goals/`, tests in `src/apps/goals/tests/`.

## Issue
#8
