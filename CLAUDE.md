# Learning Companion

Django app for tracking learning goals and sessions, attaching resources, and getting AI-generated summaries. Project brief: `instructions/challenge.md`. Development runs through the AI factory pipeline described in `README.md` and `.claude/rules/`.

## Commands

Run everything from the repository root:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # setup
.venv/bin/python src/manage.py runserver        # dev server on :8000
.venv/bin/python src/manage.py test src -t src  # test suite (the hooks run exactly this)
.venv/bin/python src/manage.py check            # system checks (lint command in hooks)
.venv/bin/python src/manage.py makemigrations && .venv/bin/python src/manage.py migrate
```

Always pass `src -t src` to `test`. Without it, Django discovers from the repo root, finds 0 tests and exits 0, so a broken suite would look green.

After installing a new dependency, update `requirements.txt` with `.venv/bin/pip freeze > requirements.txt`.

## Layout

All source code lives in `src/`, which is the Django project root (`BASE_DIR`):

- `src/manage.py`
- `src/config/`: project package (settings, root URLconf, WSGI/ASGI).
- `src/apps/`: one Django app per domain area. Create a new app with
  `mkdir src/apps/<name> && .venv/bin/python src/manage.py startapp <name> src/apps/<name>`, then set `name = "apps.<name>"` in its `apps.py` and add `"apps.<name>"` to `INSTALLED_APPS`.
- `src/templates/`, `src/static/`: project-level templates and static files (create when needed).

Database: SQLite (Django default), file at `src/db.sqlite3` (git-ignored). Tests use an in-memory SQLite database.

The write guard (`.claude/hooks/config.sh`, `SOURCE_DIRS="src"`) protects everything under `src/`.

## Tickets, board and gitflow

- Backlog: `work/backlog.md`, one line per GitHub issue on https://github.com/marcoh-dev/learning-companion. Its status is mirrored on the project board https://github.com/users/marcoh-dev/projects/4 (Todo → In Progress → In Review → Done) via `bash .claude/scripts/board-status.sh <issue> "<status>"`, using the ids in `.claude/board.json`.
- Drive the pipeline with `factory-manager` (one step per call, e.g. `/loop factory-manager`). It refines, plans, implements and reviews through the phase skills, then lands the ticket itself.
- Gitflow (details in `.claude/rules/git.md`): `feature/<id>` and `fix/<id>` branch off `develop` → PR squash-merged into `develop` → `main` synced into `develop` with a merge commit → promotion PR `develop` → `main` merged with a merge commit. `main` only accepts PRs from `develop` (the `source-branch` check in `.github/workflows/pr-source.yml` plus branch protection from `.claude/scripts/protect-branches.sh`).
