# Plan: env-settings

## Research summary
- Settings: `src/config/settings.py` hardcodes `SECRET_KEY`, `DEBUG = True`, `ALLOWED_HOSTS = []` and does not import `os`. `manage.py`, `wsgi.py`, `asgi.py` only `setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')`; nothing else reads settings.
- Dependencies: `requirements.txt` pins asgiref, Django 6.1.1, PyYAML, sqlparse. Latest `django-environ` is 0.14.0 (Python 3.14.7 in `.venv`). `.gitignore` already ignores `.env`.
- Tests: two modules in `src/config/tests/` (`test_ci_workflow.py`, `test_branch_protection.py`), package has an empty `__init__.py`. Style: `django.test.SimpleTestCase`, module-level helpers, repo paths via `Path(settings.BASE_DIR).parent / ...`, arrange → blank line → asserts, sentence-style test names. Nothing uses `subprocess`, `importlib.reload` or `override_settings` yet.
- Running: full suite `.venv/bin/python src/manage.py test src -t src`; single module `.venv/bin/python src/manage.py test config.tests.test_env_settings -t src`.
- Hooks: `TEST_CMD` is the full-suite command above, run from the repo root with no extra env vars, after every `src/` write in `implementing` and before every commit. So the suite must pass with no `.env` and no variables set (AC11 is checked on every commit). `LINT_CMD` (`check`) is not used by any hook.
- CI: `.github/workflows/ci.yml`, single job `test`, runs `check` then the suite, no `env:` block today. `test_ci_workflow.py` loads it with PyYAML.
- Docs: `CLAUDE.md` line 10 is the setup command in the "Commands" block. `README.md` "## Install" describes the template install and has no project setup step.

## Design decisions
- **Pure helper + thin wiring.** The logic lives in `src/config/env.py` as `read_settings(environ: Mapping[str, str], env_file: Path, argv: Sequence[str]) -> dict` returning `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`. `settings.py` only calls it with `os.environ`, `BASE_DIR.parent / ".env"` and `sys.argv`, and unpacks the result. Rationale: every branch (env vs. file, missing file, DEBUG on/off, `test` command) is unit-testable with plain dicts and temp files. There's no subprocesses and no dependence on a developer's real `.env`.
- **No mutation of `os.environ`.** `read_settings` merges the `.env` values under a copy of `environ` (real environment wins) instead of calling `Env.read_env` on the process environment. Rationale: tests stay isolated, and precedence (AC2) is explicit. #14 can reuse the same helper/`Env` for `OPENAI_*`.
- **`test` command detection** = `argv[1] == "test"` (as with `manage.py test`). Rationale: it's the only way the suite starts here (hooks, CI). Nothing broader, so `runserver`/`check` with DEBUG False still fail fast without a key.
- **Dev key** is a module constant in `config/env.py` that starts with `django-insecure-` and says it's for development only. It's newly made up and never the old public key.
- **Wiring test** patches `config.env.read_settings` and `importlib.reload`s `config.settings`, then reloads it again unpatched in cleanup. Rationale: it proves the call arguments and the unpacking without depending on the real environment. `django.conf.settings` is already configured and is unaffected.
- New tests go in `src/config/tests/test_env_settings.py` (helper + wiring + `.env.example` + docs + requirements). The CI assertion goes in the existing `test_ci_workflow.py`.

## Steps
- [x] 1. `django-environ` is pinned in `requirements.txt` and importable — test: `src/config/tests/test_env_settings.py` — impl: `.venv/bin/pip install django-environ==0.14.0`, `requirements.txt` (via `pip freeze`) — covers: AC1
- [x] 2. `read_settings` returns `SECRET_KEY` from `environ` when set — test: `test_env_settings.py` — impl: `src/config/env.py` (new) — covers: AC4
- [x] 3. `DEBUG` is parsed as a boolean (`True`/`False`/`1`/`0`/`yes`/`no`) and defaults to `False` — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC7
- [x] 4. `ALLOWED_HOSTS` is parsed as a comma-separated list and defaults to `["localhost", "127.0.0.1"]` — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC8
- [x] 5. With `SECRET_KEY` unset and `DEBUG` True, the insecure dev key is returned (starts with `django-insecure-`) — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC5
- [x] 6. With `SECRET_KEY` unset and `DEBUG` False, `ImproperlyConfigured` is raised and its message names `SECRET_KEY` — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC6
- [x] 7. With `SECRET_KEY` unset, `DEBUG` False and `argv` = `["manage.py", "test", ...]`, the dev key is returned instead of raising — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC6, AC11
- [x] 8. Values are read from `env_file` when it exists, and a variable in `environ` overrides the same variable in the file — test: `test_env_settings.py` (temp `.env` via `tempfile`) — impl: `config/env.py` — covers: AC2
- [x] 9. A non-existent `env_file` loads the defaults without raising and without emitting a warning/log message (`assertNoLogs`, `warnings.catch_warnings`) — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC3. *If this is green right after writing it (step 8 already guards the missing file), keep it as a characterization test, note that in the commit message and don't add production code.*
- [x] 10. `config.settings` takes `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` from `read_settings(os.environ, BASE_DIR.parent / ".env", sys.argv)`, and `settings.py` no longer contains the old hardcoded key (checked via a fragment built at runtime so the test file doesn't contain the literal either) — test: `test_env_settings.py` (patch + `importlib.reload`) — impl: `src/config/settings.py` — covers: AC2, AC9
- [x] 11. `.env.example` at the repo root lists `SECRET_KEY=change-me`, `DEBUG=True`, `ALLOWED_HOSTS=localhost,127.0.0.1`, `OPENAI_API_KEY=`, `OPENAI_MODEL=`, each preceded by a `#` comment line, and `.env` is in `.gitignore` — test: `test_env_settings.py` — impl: `.env.example` (new) — covers: AC10
- [x] 12. The CI `test` job has a job-level `env` with a non-empty `SECRET_KEY` that is not the dev key — test: `src/config/tests/test_ci_workflow.py` — impl: `.github/workflows/ci.yml` — covers: AC12
- [x] 13. `CLAUDE.md` setup commands and `README.md` mention `cp .env.example .env` — test: `test_env_settings.py` — impl: `CLAUDE.md` (Commands block), `README.md` (new project-setup line under Install) — covers: AC13

## Coverage
| AC | Steps |
|---|---|
| AC1 | 1 |
| AC2 | 8, 10 |
| AC3 | 9 |
| AC4 | 2 |
| AC5 | 5 |
| AC6 | 6, 7 |
| AC7 | 3 |
| AC8 | 4 |
| AC9 | 10 |
| AC10 | 11 |
| AC11 | 7, plus the hooks/CI running the full suite with no `.env` on every commit and push |
| AC12 | 12 |
| AC13 | 13 |

## Review findings (round 1, see review.md)
- [x] 14. A `SECRET_KEY` starting with `$` (e.g. `$abc123`) is returned verbatim, with no django-environ proxy resolution — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC4 (finding 1)
- [x] 15. With DEBUG off and not under `manage.py test`, a placeholder key (`change-me`, or anything starting with `django-insecure-`) raises `ImproperlyConfigured` naming `SECRET_KEY`. Under `test` it is replaced by the dev key — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC6 (finding 2)
- [x] 16. The `.env` precedence test proves that `os.environ` is left unchanged (snapshot before and after, inside `mock.patch.dict(os.environ)`, using a test-only key in the temp `.env`) instead of `assertNotIn("ALLOWED_HOSTS", os.environ)`. Test-only fix, as its own step — test: `test_env_settings.py` — impl: none — covers: AC2 (finding 3)
- [x] 17. `ALLOWED_HOSTS` entries are stripped and empty entries dropped (`"a.com, b.com,"` → `["a.com", "b.com"]`). An explicitly empty value stays `[]` (fails closed) — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC8 (finding 4)
- [ ] 18. The old-key test scans every readable text file under `src/` (excluding `db.sqlite3`), not just `*.py`. Test-only change — test: `test_env_settings.py` — impl: none — covers: AC9 (finding 5)
- [ ] 19. The `test` exception only applies when `argv[0]` is `manage.py` (basename), so e.g. `["gunicorn", "test"]` still raises — test: `test_env_settings.py` — impl: `config/env.py` — covers: AC6 (finding 6)
- [ ] 20. `.gitignore` ignores `.env.*` variants but keeps `.env.example` tracked — test: `test_env_settings.py` (`git check-ignore`, or `.gitignore` lines `.env.*` and `!.env.example`) — impl: `.gitignore` — covers: AC10 (finding 7)
