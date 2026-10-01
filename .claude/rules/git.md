# Git conventions (gitflow)

## Branches

- `main`: protected, release branch. Only receives **promotion PRs from `develop`**, merged with a merge commit. Never commit or push to it directly (enforced by a hook and by GitHub branch protection; a required `source-branch` check rejects PRs into `main` from any other branch).
- `develop`: protected integration branch. Only changes through squash-merged feature/fix PRs and the main-sync merge commit (see Landing). Never `git commit` on it (hook-enforced).
- `feature/<ticket-id>` / `fix/<ticket-id>`: all development. Created from an up-to-date `develop` by the `refine-ticket` skill (`fix/` when the ticket's issue is labelled `bug`, otherwise `feature/`). The branch name is recorded as `branch` in the state file.

## Commits

- Conventional Commits. The type follows the branch: `feat(<ticket-id>): ...` on `feature/`, `fix(<ticket-id>): ...` on `fix/` for plan steps; `docs(<ticket-id>): ...` for workflow artifacts and backlog updates; `refactor(<ticket-id>): ...` for pure refactoring commits; `chore(release): ...` for the sync and promotion merges.
- Commit after every green TDD cycle. Small commits are the audit trail of the workflow; do not batch several steps into one commit. They are squashed into one commit when the feature PR lands on `develop`.
- Commits require a green test suite and `--no-verify` is forbidden (both enforced by a hook).

## Pull requests and landing

- Pushing is only possible once the final review has passed (phase `done`, enforced by a hook). `final-review` pushes the ticket branch and opens the PR into **`develop`** with `gh pr create --base develop`, with the ticket summary, `Refs #<issue>`, and a reference to `work/<id>/review.md` in the body.
- Landing is done by `factory-manager` in phase `done`, in this order and nowhere else:
  1. Squash-merge the feature/fix PR into `develop` (`gh pr merge --squash --delete-branch`), subject `<type>(<id>): <title> (#<pr>)`.
  2. Sync: merge `origin/main` into `develop` with `git merge --no-ff origin/main -m "chore(release): sync main into develop"` and push `develop`. On conflicts: `git merge --abort` and stop for a human; never resolve conflicts by editing source outside the `implementing` phase.
  3. Promote: PR `develop` → `main` titled `chore(release): promote <id> to main`, merged with `gh pr merge --merge` (never squash, never `--delete-branch`).
- Never rewrite history on a protected branch, never force-push to one.
