# Profile model and own-profile page

## Story
As a learner, I want a profile with my name and cohort that only I can see and edit, so that the app knows who I am and which cohort I belong to.

## Acceptance criteria
- [ ] AC1 A `Profile` model is linked one-to-one to the user (`user.profile`), with `name` (optional text, max 100 chars) and `cohort` (one of a fixed set of choices, or not set). Deleting the user deletes their profile.
- [ ] AC2 Creating a user by any route (`create_user`, `create_superuser`, sign-up) creates exactly one profile for them, with an empty `name` and no cohort. Saving an existing user again does not create a second profile.
- [ ] AC3 An anonymous `GET /accounts/profile/` redirects to the login page with `next=/accounts/profile/`, and logging in from there lands on the profile page.
- [ ] AC4 For a logged-in user, `GET /accounts/profile/` returns 200 and renders `accounts/profile.html` (extending `base.html`). It shows their username, name and cohort label, and an edit form (`name`, `cohort`) prefilled with their current values.
- [ ] AC5 The profile page only ever shows the logged-in user's own profile. With two users, user A's page never contains user B's name or cohort, and adding a query parameter such as `?user=<B's id>` changes nothing.
- [ ] AC6 A valid `POST` to `/accounts/profile/` saves the logged-in user's name and cohort, redirects back to `/accounts/profile/`, and shows a success message there. A blank `name` is a valid save.
- [ ] AC7 An invalid `POST` (a `name` over 100 chars, or a `cohort` outside the choices) re-renders the page with 200 and the rendered field error, and saves nothing.
- [ ] AC8 A `POST` can't touch anyone else's profile. Extra fields such as `user=<B's id>` are ignored, and B's profile stays unchanged.
- [ ] AC9 If a logged-in user has no profile (e.g. it was deleted), opening the profile page creates an empty one and returns 200.
- [ ] AC10 The logged-in nav has a "Profile" link to `/accounts/profile/`.
- [ ] AC11 The anonymous nav's "Log in" link carries `?next=<current path>` (e.g. on `/` it points to `/accounts/login/?next=/`), so logging in returns to the page the user came from. On the login and sign-up pages themselves the link has no `next`. Opening the login page without `next` still lands on `/` after login.

## Out of scope
- Focus-area tags on the profile (#6).
- Viewing other users' profiles, and a public profile page.
- Registering `Profile` in the Django admin.
- Changing the sign-up redirect (still `/`) and the logout redirect (still the login page).
- Avatar, bio, or other profile fields.

## Notes
- Interview answers:
  - One page at `/accounts/profile/` that shows the profile and holds the edit form; saving redirects back with a message.
  - A profile is created for every new user, not only via sign-up.
  - `cohort` comes from fixed choices. For now that's a placeholder list in code: "2026 Spring", "2026 Autumn", "2027 Spring", plus "not set".
  - `name` is optional (may stay blank), max 100 chars. An earlier answer made it required, and that was later changed to optional. A blank name is a valid save.
  - The nav gets a "Profile" link.
  - After login the user goes back to where they came from, via `?next=`. The `LOGIN_REDIRECT_URL` fallback stays `/`.
- `instructions/challenge.md`: "a `Profile` model … linked to the user with `name`, `cohort`, and a list of `focus_area` tags" and "the profile page only shows your own data". The tags are #6.
- `src/apps/accounts/models.py` is still empty and there are no migrations yet. `LOGIN_REDIRECT_URL = 'home'` and `LOGIN_URL = 'login'` are set (#4).
- `src/apps/accounts/tests/test_nav.py` (from #4) asserts the anonymous "Log in" href as exactly `reverse("login")`, so AC11 changes it to include `?next=`.

## Issue
#5
