# Review: base-layout
## Verdict: FAIL

AC7 is only partly proven. It requires "a message added to the request (via `django.contrib.messages`) appears in the rendered page". Both messages tests inject a hand-built `messages` list straight into the template context and never exercise the messages framework or the `messages` context processor. Removing the context processor, or renaming the template variable, would leave the suite green while real messages never render. An uncovered acceptance criterion means FAIL.

## Acceptance criteria
- AC1 — covered by `HomePageTests.test_home_page_returns_200_for_anonymous_visitor` — PASS
- AC2 — covered by `HomePageTests.test_home_page_renders_home_template_extending_base` + `BaseLayoutTests.test_child_template_fills_title_and_content_blocks` — PASS
- AC3 — covered by `BaseLayoutTests.test_only_stylesheet_is_pico_css_from_cdn` — PASS (see low finding on robustness)
- AC4 — covered by `BaseLayoutTests.test_child_template_fills_title_and_content_blocks` + `HomePageTests.test_home_page_title_contains_app_name` — PASS
- AC5 — covered by `BaseLayoutTests.test_nav_has_brand_link_to_home` — PASS
- AC6 — covered by `BaseLayoutTests.test_nav_has_placeholder_links_for_upcoming_pages` — PASS
- AC7 — partly covered by `BaseLayoutTests.test_messages_are_rendered_in_messages_container` + `test_no_messages_container_without_messages`; the "added to the request via django.contrib.messages" path is untested — FAIL
- AC8 — covered by `HomePageTests.test_home_page_shows_heading_and_intro` — PASS

Suite: 45 tests, OK. `manage.py check`: no issues.

## Findings
- [medium] src/config/tests/test_base_layout.py:89-97 — The AC7 tests bypass `django.contrib.messages` (context processor and storage). — Add an end-to-end test that adds a message with `messages.success(request, ...)` and renders the home page through the real context processors (plan step 11).
- [low] src/config/tests/test_base_layout.py:92 — `assertRegex(r'(?s)class="messages".*Goal saved\.')` would pass even if the text were rendered after `</section>`. — Assert on the extracted `<section class="messages">` fragment (plan step 12).
- [low] src/config/tests/test_base_layout.py:70-75 — The "only Pico" check only counts links containing exactly `rel="stylesheet"`, so it misses quoting variants and `@import`. — Parse `<link>` tags with `html.parser` and also assert there is no `@import` (plan step 13).
- [low] src/config/tests/test_base_layout.py:38-42 — `assertTemplateUsed` alone would also pass for `{% include %}`. AC2 is adequately covered together with the block-inheritance test. — Accepted, no change.
- [low] src/config/tests/test_base_layout.py:49-56 — The intro check joins all `<p>` text on the page. That's fine while there is a single paragraph. — Accepted, no change.
- [low] src/templates/base.html:7 (security) — The CDN stylesheet has no SRI `integrity`/`crossorigin` attributes and uses a floating `@2` range. CSS only, so no script execution. — Out of scope for this ticket. Recommend a hardening ticket (pin an exact version + SRI, or vendor into `src/static/`).
- [low] src/config/settings.py (security) — No Content-Security-Policy or production cookie/HSTS settings yet. — Out of scope. Same hardening ticket (Django's built-in CSP, `check --deploy`).

Security review: 0 high, 0 medium, 2 low. Code review: 0 high, 1 medium, 4 low.

## Reviewed
commit d8b72ab, 2026-10-02
