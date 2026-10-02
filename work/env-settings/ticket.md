# Settings from environment (.env)

## Story
As a developer deploying the Learning Companion, I want `SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` read from the environment or a `.env` file, so that no secret is hardcoded in the public repo and each environment (dev, CI, production) can be configured without code changes.

## Acceptance criteria
- [x] AC1 `django-environ` is a pinned dependency in `requirements.txt`.
- [x] AC2 Settings read variables from a `.env` file at the repository root when it exists; real environment variables take precedence over values in `.env`.
- [x] AC3 A missing `.env` file is not an error: settings load and the app falls back to defaults.
- [x] AC4 `SECRET_KEY` is taken from the environment when set.
- [x] AC5 When `SECRET_KEY` is unset and `DEBUG` is True, a clearly marked insecure development key is used.
- [x] AC6 When `SECRET_KEY` is unset and `DEBUG` is False, loading settings raises `ImproperlyConfigured` with a message naming `SECRET_KEY`, except when running the `test` management command, which uses the development key.
- [x] AC7 `DEBUG` is parsed from the environment as a boolean (`True`/`False`, `1`/`0`, etc.) and defaults to `False` when unset.
- [x] AC8 `ALLOWED_HOSTS` is parsed from the environment as a comma-separated list and defaults to `["localhost", "127.0.0.1"]` when unset.
- [x] AC9 The previously hardcoded secret key no longer appears anywhere in `src/`.
- [x] AC10 A committed `.env.example` at the repository root documents `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `OPENAI_API_KEY` and `OPENAI_MODEL`, with example values (`change-me`, `True`, `localhost,127.0.0.1`, empty, empty) and a short comment per variable; `.env` stays git-ignored.
- [x] AC11 `.venv/bin/python src/manage.py test src -t src` passes with no `.env` file and none of the variables set.
- [x] AC12 CI (`.github/workflows/ci.yml`) supplies a non-secret `SECRET_KEY` (job-level `env`) so `manage.py check` passes there without a `.env`; the `test` job stays green. _(CI run itself is confirmed on the PR)_
- [x] AC13 `README.md`/`CLAUDE.md` setup instructions mention copying `.env.example` to `.env`.

## Out of scope
- Reading `OPENAI_API_KEY` / `OPENAI_MODEL` in settings or code (#14; only documented in `.env.example` here).
- Database URL, email, static-files or other settings from the environment.
- Production hardening flags (`SECURE_*`, `CSRF_TRUSTED_ORIGINS`, `check --deploy`).
- Docker wiring of the `.env` file (#19).

## Notes
- User decisions (2026-10-02): SECRET_KEY dev fallback only when DEBUG is True; DEBUG defaults to False; ALLOWED_HOSTS defaults to `localhost,127.0.0.1`; `.env` and `.env.example` live at the repository root (next to `requirements.txt`, where commands are run from).
- Because DEBUG defaults to False, a bare `manage.py check` with no `.env` raises (AC6). That guard against a production deploy running without a key is intended. CI therefore sets a dummy key (AC12), and the `test` command gets the dev key (AC6, AC11) so the hooks and a fresh clone can run the suite.
- The old key `django-insecure-4$t-...` is public in git history and must be treated as compromised; it is just removed, never reused.

## Issue
#2
