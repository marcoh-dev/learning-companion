# Review: ci-test-workflow
## Verdict: PASS

There are no high-severity findings, the suite is green (7 tests) and `manage.py check` reports no issues. AC1–AC7 are covered by passing tests. AC8 is by definition verified at landing (see below).

## Acceptance criteria
- AC1: covered by `CiWorkflowTests.test_defines_a_single_test_job_without_matrix`. PASS
- AC2: covered by `CiWorkflowTests.test_triggers_on_every_push_and_on_prs_into_develop_and_main`. PASS
- AC3: covered by `CiWorkflowTests.test_runs_on_ubuntu_with_checkout_and_cached_python_3_14`. PASS
- AC4: covered by `CiWorkflowTests.test_installs_requirements_after_setting_up_python`. PASS
- AC5: covered by `CiWorkflowTests.test_runs_system_checks_then_the_test_suite_after_installing`. PASS
- AC6: covered by `BranchProtectionTests.test_main_requires_source_branch_and_test_checks` and `BranchProtectionTests.test_develop_requires_test_check_but_lets_admins_push_the_main_sync`. PASS
- AC7: covered by `BranchProtectionTests.test_develop_requires_test_check_but_lets_admins_push_the_main_sync`. PASS
- AC8: deferred to landing. The ticket itself defines AC8 as verified during landing. A unit test cannot cover it, because the `test` check only exists once this PR runs on GitHub.
  - Gate: `factory-manager` landing step 3 (`gh pr checks <pr> --watch --fail-fast`) must show a green `test` check before the squash-merge.
  - After the merge, re-running `bash .claude/scripts/protect-branches.sh` changes GitHub settings, so it needs explicit user confirmation.

## Findings
Security reviewer (0 high, 2 medium, 4 low on changed files):
- [medium] `.github/workflows/ci.yml:5-11`: there is no `permissions:` block, so `GITHUB_TOKEN` gets the repo default scope on every pushed branch. Recommendation: follow-up ticket to add top-level `permissions: contents: read`, and set the repo default workflow permissions to read-only.
- [medium] `.claude/scripts/protect-branches.sh:22,34`: the required check is matched by the name `test` only. Any workflow or app reporting `test` satisfies it, including a branch that edits `ci.yml`, and there is no review requirement. This adds protection rather than removing any, but it is not tamper-proof. Recommendation: follow-up ticket to use `checks: [{"context":"test","app_id":15368}]` (GitHub Actions) and add a CODEOWNERS entry with code-owner review for `.github/workflows/` and `.claude/scripts/`.
- [low] `.github/workflows/ci.yml:15`: `actions/checkout@v7` is pinned to a tag, and `persist-credentials` defaults to true. Recommendation: pin to a SHA and set `persist-credentials: false`.
- [low] `.github/workflows/ci.yml:17`: `actions/setup-python@v7` is pinned to a tag. Recommendation: pin to a SHA and add Dependabot for `github-actions`.
- [low] `requirements.txt:1-4`: versions are pinned but there are no hashes. Recommendation: optionally `--require-hashes`, and Dependabot for pip.
- [low] `.github/workflows/ci.yml:20-21`: there is a theoretical pip-cache poisoning risk, mitigated by exact pins. Recommendation: accept, or use hash-checked installs.
- [low, pre-existing, unchanged file] `.github/workflows/pr-source.yml:15-16`: `${{ github.head_ref }}` is interpolated into `run:`. Recommendation: pass it via `env:` in a separate ticket.
- [low, pre-existing, unchanged file] `src/config/settings.py:23,26,28`: `SECRET_KEY` is hardcoded and `DEBUG = True`. Recommendation: covered by backlog ticket #2 (settings from environment).

Code reviewer (0 high, 0 medium, 6 low):
- [low] `.claude/skills/factory-manager/SKILL.md:63`: the promotion step names only `source-branch` as the required check. Behaviour is unaffected, because `--watch --fail-fast` waits on all checks. Recommendation: docs follow-up to mention `test`.
- [low] `src/config/tests/test_branch_protection.py:11-23`: if a heredoc style is not recognised, the test fails with a bare `KeyError`, and a duplicated branch silently keeps the last body. Recommendation: assert the parsed branch set is `["develop", "main"]`.
- [low] `src/config/tests/test_ci_workflow.py:51-58,74-77`: the exact-equality checks on the setup-python `with:` and on the steps after install are brittle against harmless additions. Recommendation: assert only the relevant keys and the relative order.
- [low] `src/config/tests/test_ci_workflow.py:7`, `test_branch_protection.py:8`: the tests read files outside `BASE_DIR`, so they will fail in a `src/`-only Docker image. Recommendation: handle this in #19.
- [low] `.github/workflows/ci.yml:10-13`: there is no `permissions:` and no `timeout-minutes`. This duplicates the security medium above. Recommendation: same follow-up ticket.
- [low] `requirements.txt:3`: PyYAML is test-only but sits in the runtime requirements. Recommendation: split into `requirements-dev.txt` with #19.

None of these findings block the verdict. The two mediums are recommended as a follow-up "CI hardening" ticket.

## Reviewed
commit 60139ff, 2026-10-01
