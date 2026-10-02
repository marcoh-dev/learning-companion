# Review: base-layout
## Verdict: PASS

Round 2. Round 1 (commit d8b72ab) FAILED because AC7 was only partly proven: the messages tests injected a hand-built list instead of going through `django.contrib.messages`. Plan steps 11–13 resolved that finding and two related lows. Both reviewers confirmed the fixes, and the code reviewer independently confirmed that the end-to-end messages test goes red when the `messages` context processor is removed.

## Acceptance criteria
- AC1 — covered by `HomePageTests.test_home_page_returns_200_for_anonymous_visitor` — PASS
- AC2 — covered by `HomePageTests.test_home_page_renders_home_template_extending_base` + `BaseLayoutTests.test_child_template_fills_title_and_content_blocks` — PASS
- AC3 — covered by `BaseLayoutTests.test_only_stylesheet_is_pico_css_from_cdn` (parses every stylesheet `<link>`, rejects `@import`) — PASS
- AC4 — covered by `BaseLayoutTests.test_child_template_fills_title_and_content_blocks` + `HomePageTests.test_home_page_title_contains_app_name` — PASS
- AC5 — covered by `BaseLayoutTests.test_nav_has_brand_link_to_home` — PASS
- AC6 — covered by `BaseLayoutTests.test_nav_has_placeholder_links_for_upcoming_pages` — PASS
- AC7 — covered by `HomePageTests.test_message_added_via_messages_framework_appears_on_home_page` (end-to-end), `BaseLayoutTests.test_messages_are_rendered_in_messages_container`, `BaseLayoutTests.test_no_messages_container_without_messages` — PASS
- AC8 — covered by `HomePageTests.test_home_page_shows_heading_and_intro` — PASS

Suite: 46 tests, OK. `manage.py check`: no issues.

## Findings
Code review: 0 high, 0 medium, 4 low. Security review: 0 high, 0 medium, 3 low. None block the merge.

- [low] src/config/tests/test_base_layout.py:133-136 — The "no messages container" case is only tested with an explicit `{"messages": []}` context, not through the real (lazy storage) request path. — Follow-up: assert `class="messages"` is absent from a plain `GET /`.
- [low] src/config/tests/test_base_layout.py:110-114 — The stylesheet check doesn't assert that the Pico `<link>` sits inside `<head>`. — Follow-up: scope the collector to `<head>`.
- [low] src/config/tests/test_base_layout.py:88-97 (security) — No test pins that message text is HTML-escaped. A later `|safe` would go unnoticed. — Follow-up: assert `messages.success(request, "<script>x</script>")` renders as `&lt;script&gt;`. Best done with the first ticket that puts user input into messages (goal CRUD, #8).
- [low] src/config/tests/test_base_layout.py:128-131 — The context-level messages test overlaps the new end-to-end test. — Accepted; kept as a fast template-level check.
- [low] src/config/tests/test_base_layout.py:55-58 — `messages_section` matches the exact opening tag, so it's brittle if attributes change. — Accepted; matches the plan's markup decision.
- [low] src/templates/base.html:7 (security) — The CDN stylesheet has no SRI and uses a floating `@2` range. CSS only. — Deferred to a hardening ticket (pin exact version + SRI, or vendor into `src/static/`).
- [low] src/config/settings.py (security) — No CSP, HSTS or secure-cookie settings yet. — Deferred to the same hardening ticket (built-in CSP, `check --deploy`).

## Reviewed
commit f37a5b4, 2026-10-02
