# Plan: base-layout

## Research summary
- `src/config/settings.py` still has the stock `TEMPLATES` block: `'DIRS': []`, `APP_DIRS: True`, and context processors request, auth and messages. Messages are fully enabled (app, middleware, context processor). `BASE_DIR = Path(__file__).resolve().parent.parent` (= `src/`), and paths are built with `/`. settings.py keeps the generated single quotes.
- `src/config/urls.py` only has `path('admin/', admin.site.urls)`. `src/apps/` has no apps yet, and `src/templates/` doesn't exist.
- No document says where non-domain views belong. CLAUDE.md reserves `src/apps/` for domain areas and `src/templates/` for project-level templates.
- Tests: all live in `src/config/tests/` (a package), named `test_<topic>.py` with `<Thing>Tests` classes. They use `django.test.SimpleTestCase` (no DB), have long descriptive method names, separate act and assert with a blank line, use `self.subTest` for tables, and keep small module-level helpers instead of shared fixtures.
- To run one module: `.venv/bin/python src/manage.py test config.tests.test_base_layout -t src`. The full suite: `.venv/bin/python src/manage.py test src -t src`.
- The write guard covers `src/templates/` (everything under `src/`).

## Design decisions
- **Home view:** use `TemplateView.as_view(template_name='home.html')` directly in `config/urls.py`, at `''` with `name='home'`. A static page needs no view code and no new domain app.
- **Templates dir:** set `'DIRS': [BASE_DIR / 'templates']`, as required by AC2 and the CLAUDE.md layout.
- **Pico.css:** load the pinned major version from jsDelivr, `https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css`. It's classless, so templates stay plain semantic HTML.
- **Placeholder hrefs:** hard-code `/goals/`, `/sessions/`, `/dashboard/`, `/accounts/login/` and `/accounts/signup/`. Later tickets swap them for `{% url %}`, and `{% url %}` can't be used now because the names don't exist yet.
- **Messages markup:** `{% if messages %}` wraps a `<section class="messages">` with one element per message (its `tags` as the class). Tests identify the container by `class="messages"`.
- **Tests:** a new module `src/config/tests/test_base_layout.py` with `SimpleTestCase`. Page tests use `self.client.get('/')`; an anonymous request without a session cookie doesn't touch the DB. Layout-only tests (blocks, messages) render templates directly with `django.template.loader.render_to_string` or `Template(...)`. The messages tests pass an explicit `messages` context list of `django.contrib.messages.storage.base.Message`, so they need no request or session.

## Steps
- [x] 1. `GET /` returns 200 for an anonymous visitor. test: `src/config/tests/test_base_layout.py`. impl: `src/config/urls.py` (home route), `src/config/settings.py` (`DIRS`), `src/templates/home.html` (minimal). covers: AC1
- [x] 2. The home response uses both `home.html` and `base.html` (`assertTemplateUsed`). impl: `src/templates/base.html` with a `content` block; `home.html` extends it. covers: AC2
- [x] 3. A child template that extends `base.html` and overrides the `title` and `content` blocks gets them rendered inside `<title>` and the page body. impl: `base.html` (`title` block). covers: AC4
- [x] 4. The home page `<title>` contains "Learning Companion". impl: `home.html` (`title` block). covers: AC4
- [x] 5. `base.html` includes exactly one stylesheet link, and its href is the Pico.css CDN URL. impl: `base.html` `<head>`. covers: AC3
- [x] 6. The page has a `<nav>` containing the brand link `<a href="/">Learning Companion</a>`. impl: `base.html`. covers: AC5
- [x] 7. The nav contains links "Goals", "Sessions", "Dashboard", "Log in" and "Sign up" with the placeholder hrefs above (`subTest` table). impl: `base.html`. covers: AC6
- [x] 8. Rendering `base.html` with one message in the `messages` context shows that message's text inside the `messages` container. impl: `base.html` (container rendered unconditionally, with the guard left for step 9). covers: AC7
- [x] 9. Rendering `base.html` with no messages renders no `class="messages"` container. impl: `base.html` (add the `{% if messages %}` guard around the container). Step 8 renders the container unconditionally as its minimal code, so this test is red until the guard is added. covers: AC7
- [x] 10. The home page has `<h1>Learning Companion</h1>` and an intro paragraph mentioning goals, sessions, resources and AI summaries. impl: `home.html`. covers: AC8

## Coverage
| AC | Steps |
|---|---|
| AC1 | 1 |
| AC2 | 2 |
| AC3 | 5 |
| AC4 | 3, 4 |
| AC5 | 6 |
| AC6 | 7 |
| AC7 | 8, 9 |
| AC8 | 10 |

## Review findings (round 1, see review.md)
- [x] 11. A message added with `django.contrib.messages` (`messages.success(request, "Goal saved.")`) on a request appears in the rendered home page. Use `RequestFactory` with `@override_settings(MESSAGE_STORAGE="django.contrib.messages.storage.cookie.CookieStorage")`, set `request._messages`, then render `TemplateView.as_view(template_name="home.html")(request).render()`, so the real context processors run without touching the DB. This test is expected to pass against the current code. Confirm it is meaningful by checking that it goes red when the `messages` context processor is temporarily removed from `TEMPLATES`, then restore it (note this in the commit). test: `src/config/tests/test_base_layout.py`. impl: none expected. covers: AC7
- [x] 12. Tighten the messages assertion: add a helper that extracts the `<section class="messages">…</section>` fragment (like `render_nav`), and assert the message text is inside it. Test-only fix, done as its own deliberate step per tdd.md. test: `src/config/tests/test_base_layout.py`. covers: AC7
- [x] 13. Make the "only Pico.css" check robust: collect every `<link>` whose `rel` contains `stylesheet` using `html.parser` (any quoting or attribute order), assert there is exactly one and that its href is the Pico URL, and assert there is no `@import` in the page. Test-only fix. test: `src/config/tests/test_base_layout.py`. covers: AC3
