# CI: run the Django test suite on every push and PR

## Story
As a developer on the AI factory, I want every push and every PR into `develop`/`main` to run the Django test suite and system checks on GitHub Actions, so that no change lands on a protected branch without a green, independently verified `test` check.

## Acceptance criteria
- [ ] AC1 A workflow file exists under `.github/workflows/` that defines a job whose id/name is exactly `test` (no matrix, so the check context is literally `test`).
- [ ] AC2 The workflow triggers on `push` to all branches and on `pull_request` targeting `develop` and `main`.
- [ ] AC3 The `test` job runs on `ubuntu-latest`, checks out the repo and sets up Python 3.14 with `actions/setup-python` and `cache: pip` (keyed on `requirements.txt`).
- [ ] AC4 The `test` job installs dependencies with `pip install -r requirements.txt`.
- [ ] AC5 The `test` job runs `python src/manage.py check` and `python src/manage.py test src -t src` (the exact `src -t src` form, so discovery cannot silently find 0 tests); either failing fails the job.
- [ ] AC6 `.claude/scripts/protect-branches.sh` requires the `test` status check on `main` (in addition to `source-branch`) and on `develop`.
- [ ] AC7 `develop` protection keeps `enforce_admins: false`, no force-push and no deletion, so the admin's direct push of the main-sync merge commit (`.claude/rules/git.md`, Landing step 2) is still possible.
- [ ] AC8 The feature PR for this ticket shows a green `test` check (verified during landing), after which `protect-branches.sh` is re-run so `test` is required on both branches.

## Out of scope
- Python version matrix (single version, 3.14, matching the local venv).
- Linting/formatting tools beyond `manage.py check`.
- Docker image build (ticket #19) and deployment.
- Coverage reporting.

## Notes
- Answered in refinement: Python 3.14 only; required check is in scope for both `main` and `develop`; push trigger on all branches (feature branches get feedback before a PR exists; duplicate push+PR runs are accepted); pip caching enabled.
- Existing `.github/workflows/pr-source.yml` (`source-branch` check) stays unchanged.
- Hooks run exactly `.venv/bin/python src/manage.py test src -t src`; CI must mirror that command.
- Tests use in-memory SQLite, so CI needs no database service.
- AC6/AC7 change GitHub settings when the script is re-run. Re-running is an outward-facing action and happens only after the `test` check has reported green at least once (otherwise GitHub would wait forever on a required check that never reported).

## Issue
#1
