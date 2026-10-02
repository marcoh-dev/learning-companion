# Filter goals by status

## Story
As a signed-in learner, I want to filter my goal list by status and see how many goals I have in each status, so that I can focus on what's planned, in progress or done.

## Acceptance criteria
"Own goals" means goals owned by the signed-in user. The list stays login-required, owner-scoped and ordered newest updated first, as shipped in goal-list.

- [ ] AC1 GET `/goals/?status=<value>` for each of `planned`, `in_progress` and `done` lists only the own goals with that status, still ordered by `updated_at`, newest first.
- [ ] AC2 GET `/goals/` without `status` lists all own goals, as before.
- [ ] AC3 An unknown or empty `status` (e.g. `?status=archived`, `?status=`) returns 200 with the unfiltered list, exactly as without the parameter.
- [ ] AC4 The page has a GET form whose action is the goal list: a `<select name="status">` with the options All (value `""`), Planned, In progress and Done, plus a "Filter" submit button.
- [ ] AC5 The select preselects the active filter: the matching status when `status` is valid, otherwise All.
- [ ] AC6 Each option label shows the count of own goals for that option, e.g. "All (5)", "Planned (2)", "In progress (1)", "Done (2)". Other users' goals are never counted, and the counts don't change with the active filter.
- [ ] AC7 When a valid filter matches no own goals but the user has goals in other statuses, the page shows "No <label lower-cased> goals." (e.g. "No done goals.", "No in progress goals.") instead of "No goals yet". The filter form is still shown.
- [ ] AC8 A user with no goals at all still sees "No goals yet" (with any or no filter), and the "New goal" link keeps working as before.
- [ ] AC9 Filtering never shows another user's goals: with `?status=done`, Bob's done goal doesn't appear on Ada's list.

## Out of scope
- Filter links or auto-submit with JavaScript (the select uses a plain submit button).
- Filtering by anything other than status. Search, sorting options and pagination.
- Dashboard charts (#17).
- Notices about invalid filter values (they are silently ignored).

## Notes
- Interview answers:
  - **UI:** a select with a "Filter" button (GET form), not links.
  - **Invalid values:** ignored, showing all goals with All selected.
  - **Empty filter:** a specific message, keeping "No goals yet" for users with no goals at all.
  - **Counts:** each option shows a count.
- Ticket id `goal-status-filter`.
- The status values and labels come from `Goal.Status` (`planned`/"Planned", `in_progress`/"In progress", `done`/"Done").
- The goal-list ordering and row format stay unchanged (`goal_rows()` in `test_goal_list.py`).

## Issue
#9
