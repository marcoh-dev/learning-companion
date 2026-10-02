# Base layout and home page

## Story
As a visitor, I want every page to share one styled layout with navigation, and a home page at `/` that welcomes me, so that the app feels consistent and later pages only have to supply their own content.

## Acceptance criteria
- [x] AC1 A GET to `/` returns HTTP 200 for an anonymous visitor (no login required).
- [x] AC2 The home page is rendered with the template `home.html`, which extends the project-level `base.html` (both under `src/templates/`; Django finds them via the project templates directory).
- [x] AC3 `base.html` loads Pico.css from a CDN via a `<link rel="stylesheet">` in `<head>`; no other CSS framework is loaded.
- [x] AC4 `base.html` defines a `title` block and a `content` block; the home page sets a page title containing "Learning Companion".
- [x] AC5 `base.html` has a `<nav>` with a brand link "Learning Companion" pointing to `/`.
- [x] AC6 The nav also contains placeholder links labelled "Goals", "Sessions", "Dashboard", "Log in" and "Sign up". The target pages do not exist yet, so hard-coded placeholder hrefs are fine; the tickets that build those pages replace them.
- [x] AC7 `base.html` renders Django messages: a message added to the request (via `django.contrib.messages`) appears in the rendered page, and no messages container is rendered when there are none.
- [x] AC8 The home page shows an `<h1>` with the app name "Learning Companion" and a short intro paragraph describing what the app does (track learning goals and sessions, attach resources, get AI summaries).

## Out of scope
- Real authentication, goals, sessions or dashboard pages (later tickets #4–#18). The placeholder nav links may 404 for now.
- Showing different nav items for logged-in and anonymous users (done with the auth ticket #4).
- Custom CSS beyond Pico defaults, local static files, a `STATICFILES_DIRS` setup, and a dark-mode toggle.

## Notes
- Interview answers: CSS framework Pico.css via CDN; nav = brand + placeholder links; home = title + short intro; ticket id `base-layout`.
- Current state: `TEMPLATES['DIRS']` is empty, and `src/templates/` and `src/apps/*` don't exist yet. The messages app, middleware and context processor are already enabled.
- `instructions/challenge.md` leaves the choice of frontend tech open and does not mention a home page. All later pages are expected to extend this layout.

## Issue
#3
