# Ticket backlog

Queue for `factory-manager`. One ticket per line, top to bottom = priority order.
Each line ends with its GitHub issue `(#N)`; the issue body holds the full description,
and its card on the project board (https://github.com/users/marcoh-dev/projects/4)
mirrors the status marker here: `[ ]` Todo · `[~]` In Progress / In Review · `[x]` Done.
`factory-manager` owns the status marker, the ticket id, and the `[[parked: ...]]`
annotation on each line. To add a ticket: create the issue, add it to the board as Todo,
then add a plain `- [ ] <title> (#N)` line here.

- [x] ci-test-workflow: CI: run the Django test suite on every push and PR (#1) — work/ci-test-workflow/review.md
- [x] env-settings: Settings from environment (.env) (#2) — work/env-settings/review.md
- [x] base-layout: Base layout and home page (#3) — work/base-layout/review.md
- [x] user-auth: Sign up, log in, log out (#4) — work/user-auth/review.md
- [x] user-profile: Profile model and own-profile page (#5) — work/user-profile/review.md
- [x] profile-focus-areas: Profile focus areas (tags) (#6) — work/profile-focus-areas/review.md
- [x] goal-list: Goal model and goal list (#7) — work/goal-list/review.md
- [~] goal-crud: Create, edit and delete goals (#8)
- [ ] Filter goals by status (#9)
- [ ] Learning session model and CRUD (#10)
- [ ] Tags on learning sessions (#11)
- [ ] Resource model and attach form on goal detail (#12)
- [ ] Show resources grouped by type (#13)
- [ ] OpenAI client service (#14)
- [ ] Generate progress summary for a goal (#15)
- [ ] Suggest next learning steps for a goal (#16)
- [ ] Dashboard: goals per status (#17)
- [ ] Dashboard: hours per tag and per week (#18)
- [ ] Security hardening: auth rate limiting, production cookie/HTTPS settings, CSP and CDN integrity (#29)
- [ ] Dockerfile for the app (#19)
- [ ] CI hardening: least-privilege token and tamper-resistant required checks (#22)
