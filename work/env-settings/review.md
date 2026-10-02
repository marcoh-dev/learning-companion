# Review: env-settings

## Verdict: FAIL

One high-severity finding (AC4 not met for keys starting with `$`). The findings became plan steps 14–20.

## Acceptance criteria
- AC1 — `RequirementsTests.test_django_environ_is_pinned_and_importable` — PASS
- AC2 — `ReadSettingsTests.test_values_are_read_from_the_env_file_and_the_environment_wins`, `SettingsWiringTests.test_settings_take_their_values_from_read_settings` — PASS
- AC3 — `ReadSettingsTests.test_missing_env_file_loads_defaults_without_warnings_or_log_messages` — PASS
- AC4 — `ReadSettingsTests.test_secret_key_is_taken_from_the_environment` — **FAIL**: passes for plain values, but a key starting with `$` is resolved as a django-environ proxy and treated as unset (finding 1)
- AC5 — `ReadSettingsTests.test_insecure_dev_key_is_used_when_secret_key_is_unset_and_debug_is_on` — PASS
- AC6 — `ReadSettingsTests.test_missing_secret_key_with_debug_off_is_improperly_configured`, `ReadSettingsTests.test_test_command_uses_the_dev_key_when_secret_key_is_unset_and_debug_is_off` — PASS
- AC7 — `ReadSettingsTests.test_debug_is_parsed_as_a_boolean`, `ReadSettingsTests.test_debug_defaults_to_false` — PASS
- AC8 — `ReadSettingsTests.test_allowed_hosts_is_parsed_as_a_comma_separated_list`, `ReadSettingsTests.test_allowed_hosts_defaults_to_localhost` — PASS (whitespace handling is finding 4)
- AC9 — `SettingsWiringTests.test_the_old_hardcoded_secret_key_is_gone_from_src` — PASS, but only scans `*.py` (finding 5)
- AC10 — `EnvExampleTests.test_documents_every_variable_with_an_example_value_and_a_comment`, `EnvExampleTests.test_env_file_is_git_ignored` — PASS
- AC11 — full suite with `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` unset: 24 tests OK. Caveat: an empty git-ignored `.env` exists at the repo root locally, so the "no `.env`" path is proven by the AC3 unit test and by CI, not by the local run.
- AC12 — `CiWorkflowTests.test_sets_a_non_secret_ci_secret_key_for_the_job` — PASS (the CI run itself is confirmed on the PR)
- AC13 — `SetupDocsTests.test_setup_instructions_mention_copying_env_example` — PASS

Suite: 24 tests OK. `check` (with CI's `SECRET_KEY`): no issues.

## Findings
1. [high] `src/config/env.py:25` — `env.str("SECRET_KEY")` applies django-environ proxy resolution. `$abc123` is looked up as variable `abc123` and becomes `""`, so it's silently replaced by the dev key (DEBUG on) or raises (DEBUG off). About 1 in 50 `get_random_secret_key()` keys start with `$`. Reproduced. — Read the raw value without interpolation. → step 14
2. [medium] `.env.example:4` (security) — `SECRET_KEY=change-me` passes the "key is set" guard. `cp .env.example .env` plus `DEBUG=False` starts production with a public placeholder key. — When DEBUG is off (outside `test`), treat `change-me` and any `django-insecure-` key as unset. AC10's example value stays. → step 15
3. [medium] `src/config/tests/test_env_settings.py:93` (code) — `assertNotIn("ALLOWED_HOSTS", os.environ)` fails on machines that export `ALLOWED_HOSTS`, checks only one key, and a regression would leak into later tests. — Snapshot `os.environ` before and after inside `mock.patch.dict(os.environ)`, using a test-only key. → step 16
4. [low] `src/config/env.py:37` (code) — `ALLOWED_HOSTS=a.com, b.com` yields `" b.com"`, which never matches. Reproduced. — Strip entries and drop empty ones. → step 17
5. [low] `src/config/tests/test_env_settings.py:123` (code) — the AC9 test scans only `*.py`, while AC9 says "anywhere in `src/`". — Scan all text files under `src/` (skip `db.sqlite3` and binaries). → step 18
6. [low] `src/config/env.py:27` (security) — the `test` exception looks only at `argv[1]`, so `gunicorn test ...`-style argv would also match. — Also require `argv[0]` to be `manage.py`. → step 19
7. [low] `.gitignore:5` (security) — only `.env` is ignored, so `.env.local` / `.env.production` would be committable. — Add `.env.*` and `!.env.example`. → step 20
8. [low] `src/config/env.py:28-33` (security) — DEBUG=True with no key silently uses the public dev key. — **Not planned:** the user explicitly chose "dev fallback when DEBUG is True" during refinement. Re-raise it if wanted.
9. [low] `src/config/env.py:37` (security) — `ALLOWED_HOSTS=*` is accepted. — **Not planned:** a deliberate operator choice. Production hardening (`check --deploy`) is out of scope per the ticket.

## Reviewed
commit f896c1b, 2026-10-02


---

# Review round 2: env-settings

## Verdict: FAIL

The fixes for round-1 findings 1–7 are confirmed by both reviewers. AC6 is still not fully met: a whitespace-only `SECRET_KEY` (effectively unset) and a padded placeholder such as `change-me ` are accepted with DEBUG off (reproduced). The findings became plan steps 21–22.

## Acceptance criteria
- AC1–AC5, AC7–AC13 — same tests as round 1, plus `test_secret_key_starting_with_dollar_is_taken_verbatim` (AC4), `test_allowed_hosts_entries_are_stripped_and_empty_entries_dropped` / `test_explicitly_empty_allowed_hosts_stays_empty` (AC8), the widened `test_the_old_hardcoded_secret_key_is_gone_from_src` (AC9) and `test_env_variants_are_git_ignored_but_the_example_is_tracked` (AC10) — PASS
- AC6 — `test_missing_secret_key_with_debug_off_is_improperly_configured`, `test_placeholder_secret_key_with_debug_off_is_improperly_configured`, `test_test_command_*`, `test_test_exception_only_applies_to_manage_py` — **FAIL**: a blank or whitespace-padded key gets past the guard (finding R2-1)

Suite: 31 tests OK (with and without the shell variables set). `check` (with CI's `SECRET_KEY`): no issues.

## Findings
1. [medium] `src/config/env.py:30-31, 53-58` (code + security) — `_is_placeholder` compares the unstripped, case-sensitive value. django-environ's `read_env` keeps trailing spaces and inline `# comments`. `"   "`, `"change-me "`, `" django-insecure-x"` and `"Change-Me"` are accepted as real keys with DEBUG off. — Strip the key, compare case-insensitively, and use the stripped key. → step 21
2. [low] `CLAUDE.md:20` (code) — the settings sentence is out of date after steps 15/19 (placeholders count as missing; the exception is `manage.py test` only). `.env.example` doesn't say that inline comments are unsupported (security). — Reword both. → step 22
3. [low] `src/config/env.py:28, 47` (code) — `DEBUG`/`ALLOWED_HOSTS` still use `env.bool`/`env.list`, so `ALLOWED_HOSTS=$OTHER` resolves `$OTHER`, and a list-valued proxy crashes with `AttributeError`. — **Not planned:** it needs a deliberate `$NAME` value, and it fails loudly at startup (fails closed). Can become its own ticket.
4. [low] (security) — a stronger rule (reject keys shorter than 50 chars, like `security.W009`). — **Not planned:** `check --deploy` hardening is out of scope per the ticket.

## Reviewed
commit 1f976e2, 2026-10-02

---

# Review round 3: env-settings

## Verdict: PASS

Round-2 findings 1 and 2 are confirmed fixed by both reviewers (code review: no findings). No high or medium findings, every acceptance criterion is covered, and the suite is green.

## Acceptance criteria
- AC1–AC13 — same tests as round 2. AC6 now additionally `test_blank_or_padded_placeholder_secret_key_with_debug_off_is_improperly_configured` and `test_real_secret_key_is_returned_without_surrounding_whitespace`. AC10/AC13 now additionally `test_env_example_says_inline_comments_are_not_supported` and `test_claude_md_describes_the_placeholder_rule_and_the_manage_py_test_exception` — PASS

Suite: 35 tests OK (with `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` unset). `check` (with CI's `SECRET_KEY`): no issues.

## Findings (low, not blocking; candidates for a follow-up ticket)
1. [low] `src/config/env.py:26` (security) — django-environ's `read_env` logs malformed `.env` lines verbatim (`Invalid line: ...`) at WARNING. Settings load before Django logging is configured, so a malformed `SECRET_KEY`/`OPENAI_API_KEY` line could print its value to stderr. Reported by the security reviewer from django-environ's source; not reproduced in this session. — Silence or filter the `environ.environ` logger around `read_env`, plus a test.
2. [low] `src/config/env.py:31` (security) — `.env` quoting edge case: `SECRET_KEY='change-me' ` (space after the closing quote) keeps the quotes, so the placeholder check misses it. The same goes for the documented-unsupported `change-me # comment`. — Strip one pair of surrounding quotes before the placeholder check.
3. [low, informational] `.github/workflows/ci.yml:15` (security) — the public CI value `ci-only-not-a-secret` passes the guard when DEBUG is off. Overlaps round-2 finding 4 (minimum key length, out of scope). — Add it to the refused values, or accept the risk together with R2-4.

Still not planned, unchanged: round 1 findings 8–9, round 2 findings 3–4.

## Reviewed
commit 26ed03e, 2026-10-02
