# Plan: ci-test-workflow

## Research summary
- **Tests:** none exist yet. `manage.py test src -t src` reports "Found 0 test(s)". The default `DiscoverRunner` is used (no `TEST_RUNNER`). It discovers `test*.py` inside packages under `src/`. `src/config/` is a package and `src/apps/` holds no apps yet. Run a single file with `.venv/bin/python src/manage.py test config.tests.test_ci_workflow -t src` (from the repo root, as for the full suite).
- **Hooks:**
  - Only `src/` is write-protected outside `implementing`.
  - The post-write hook runs the suite and records `last_test` only for writes under `src/`.
  - Writes to `.github/` and `.claude/scripts/` are never blocked and never trigger a test run. For steps whose production change is outside `src/`, run the suite manually after the impl write to confirm green.
  - The commit guard re-runs the full suite live in `implementing` and `reviewing`.
  - Commits are blocked on `develop` and `main`. The guard pattern-matches the whole command string, so `-n` anywhere in it (e.g. `grep -n`) is read as `--no-verify`. Keep commit commands on their own.
- **Dependencies:** `requirements.txt` has only `asgiref`, `Django` and `sqlparse`. PyYAML is not installed.
- **Conventions:**
  - `.github/workflows/pr-source.yml`:
    - It opens with a two-line `#` header that says what the workflow does and which job name is a required check.
    - `name:` equals the file stem.
    - It uses `runs-on: ubuntu-latest` and steps with plain-English names.
  - `.claude/scripts/*.sh`:
    - Each has a shebang, a `#` header block (purpose, usage, effect per branch) and `set -euo pipefail`.
    - The repo comes from `jq -r .repo .claude/board.json`.
    - GitHub calls use `gh api -X PUT "repos/$repo/branches/<b>/protection" --input - <<'JSON' … JSON` followed by `echo "<b> protected"`.
- **Current protection:**
  - main: `required_status_checks {strict:false, contexts:["source-branch"]}`, `enforce_admins: true`, 0 required approvals, no force-push or deletion.
  - develop: `required_status_checks: null`, `enforce_admins: false`, no force-push or deletion.
- **Docs that name the required check:**
  - `.claude/rules/git.md:5`
  - `CLAUDE.md:39`
  - `.claude/scripts/protect-branches.sh` header (lines 6-11)
  - `.claude/skills/factory-manager/SKILL.md:63` (promotion PR wait)

## Design decisions
- **Workflow file `.github/workflows/ci.yml`, `name: ci`, job id `test`, no matrix.** A matrix would suffix the check context (`test (3.14)`) and break the required-check name.
- **Assert config files from Django tests by parsing them.** The tests check the structure of the workflow YAML and the protection JSON, not just their text. This makes "verifiable by a test" real for a config-only ticket.
- **Add PyYAML to `requirements.txt` (`pip install pyyaml`, then `pip freeze`).** It is needed to parse the workflow in tests, and CI installs it from the same file. PyYAML is YAML 1.1, so the `on:` key loads as `True`. The test helper reads `data.get("on", data.get(True))` and documents that quirk.
- **Branch-protection tests extract each `<<'JSON' … JSON` heredoc from `protect-branches.sh`.** The tests pair each heredoc with the branch named in the preceding `gh api … branches/<b>/protection` line, then `json.loads` it. They don't depend on block order.
- **Tests live in `src/config/tests/`** (new package: `__init__.py`, `test_ci_workflow.py`, `test_branch_protection.py`). They cover repository/project config, not a domain app, and resolve files via `settings.BASE_DIR.parent`.
- **`check` runs before `test`, as separate steps, without `continue-on-error`.** The default `bash -e` shell then fails the job on any non-zero exit.
- **`setup-python` gets `cache-dependency-path: requirements.txt` explicitly.** That makes the cache key unambiguous.
- **`develop` gets `required_status_checks {strict:false, contexts:["test"]}` and keeps `enforce_admins: false`.** The admin's direct push of the main-sync merge commit is then still allowed (AC7). `strict:false` avoids forcing feature branches to be rebased onto develop.

## Steps
- [x] 1. A CI workflow exists, parses as YAML and defines exactly one job with id `test` and no `strategy.matrix`. Test: `src/config/tests/test_ci_workflow.py` (plus `src/config/tests/__init__.py`). Impl: `.github/workflows/ci.yml` (header comment, `name: ci`, minimal `test` job), plus PyYAML in `requirements.txt`. Covers: AC1.
- [x] 2. The workflow triggers on `push` to all branches (no `branches` filter) and on `pull_request` with `branches: [develop, main]`. Test: `src/config/tests/test_ci_workflow.py`. Impl: `.github/workflows/ci.yml`. Covers: AC2.
- [x] 3. The `test` job runs on `ubuntu-latest`, has an `actions/checkout` step, and has an `actions/setup-python` step with `python-version: "3.14"`, `cache: pip` and `cache-dependency-path: requirements.txt`. Test: `src/config/tests/test_ci_workflow.py`. Impl: `.github/workflows/ci.yml`. Covers: AC3.
- [x] 4. A step after setup-python runs `pip install -r requirements.txt`. Test: `src/config/tests/test_ci_workflow.py`. Impl: `.github/workflows/ci.yml`. Covers: AC4.
- [x] 5. After the install step there is one step running `python src/manage.py check` and then one running `python src/manage.py test src -t src`. Neither the job nor any step sets `continue-on-error`. Test: `src/config/tests/test_ci_workflow.py`. Impl: `.github/workflows/ci.yml`. Covers: AC5.
- [x] 6. The `main` protection JSON in `protect-branches.sh` requires contexts `source-branch` and `test`, and keeps `enforce_admins: true`, no force-push and no deletion. Test: `src/config/tests/test_branch_protection.py`. Impl: `.claude/scripts/protect-branches.sh`. Covers: AC6.
- [x] 7. The `develop` protection JSON requires context `test` and keeps `enforce_admins: false`, `allow_force_pushes: false`, `allow_deletions: false` and `required_pull_request_reviews: null`. Test: `src/config/tests/test_branch_protection.py`. Impl: `.claude/scripts/protect-branches.sh`. Covers: AC6, AC7.
- [ ] 8. Docs only, no new test (not a behaviour change). Update these to name `test` as a required check on `main` and `develop`, with `ci.yml` as its source, as one `docs(ci-test-workflow): …` commit:
  - the `protect-branches.sh` header comment
  - `.claude/rules/git.md:5`
  - `CLAUDE.md:39`

## Outside the TDD loop (AC8)
- `final-review` pushes the branch and opens the PR. The `ci` workflow then runs, and the PR must show a green `test` check. `factory-manager` landing already waits on `gh pr checks <pr>`.
- After the feature PR is merged and `test` has reported green at least once, re-run `bash .claude/scripts/protect-branches.sh`. This changes GitHub settings, so it needs explicit user confirmation at that point. It is not part of an implementation step.
- Afterwards verify with `gh api repos/<repo>/branches/{main,develop}/protection --jq .required_status_checks.contexts`.

## Coverage
| AC | Steps |
|----|-------|
| AC1 | 1 |
| AC2 | 2 |
| AC3 | 3 |
| AC4 | 4 |
| AC5 | 5 |
| AC6 | 6, 7 |
| AC7 | 7 |
| AC8 | post-review / landing (see above) |
