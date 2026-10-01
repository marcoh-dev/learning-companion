---
name: refine-ticket
description: Turn a rough ticket or feature idea into a refined ticket with acceptance criteria. First phase of the development workflow; starts a new ticket, creates the feature branch. Use when the user brings a new task, story, or bug report.
---

# Refine a ticket

Input: the user's rough ticket — pasted text, a file path, or a one-line idea (`$ARGUMENTS` if provided). If the input references a GitHub issue (`(#N)`, as backlog lines do), read it with `gh issue view <N> --json title,body,labels` — its body is the ticket's source description.

## Preconditions

Read `.claude/state/workflow.json` (if it exists). If a ticket is already in progress (phase is not `idle` or `done`), stop and ask the user whether to abandon it or finish it first. Do not silently start a second ticket.

## Steps

1. Derive a short kebab-case ticket id from the task (e.g. `comments-endpoint`). Confirm it with the user if the task is ambiguous.
2. Investigate context cheaply: use one `Explore` sub-agent to find the parts of the codebase the ticket touches. Do not read whole modules into the main context — you only need enough to ask informed questions.
3. Interview the user. Ask about anything that changes scope or design, typically: expected behaviour and edge cases, validation and error responses, auth requirements, out-of-scope items. Ask in one batch, not one question per turn.
4. Write `work/<id>/ticket.md`:

   ```markdown
   # <Title>                     <!-- one line -->
   ## Story
   As a ..., I want ..., so that ...
   ## Acceptance criteria
   - [ ] AC1 ... (concrete, testable, one behaviour each)
   ## Out of scope
   ## Notes
   Open questions that were answered, relevant constraints.
   ## Issue
   #<N>                          <!-- omit the section if there is no issue -->
   ```

   Every acceptance criterion must be verifiable by a test. If you cannot phrase it as a test, refine it further.
5. Create the branch from an up-to-date `develop` and record the state. The branch type is `fix` when the issue is labelled `bug` (or the input is clearly a bug report), otherwise `feature` (see `.claude/rules/git.md`):

   ```bash
   git switch develop && git pull --ff-only origin develop
   git switch -c <feature|fix>/<id>
   bash .claude/hooks/set-state.sh phase refined ticket <id> branch <feature|fix>/<id> issue <N>
   git add work/<id>/ticket.md && git commit -m "docs(<id>): refined ticket"
   ```

   Leave out `issue <N>` if there is no issue. If `git switch develop` fails because the working tree is dirty, stop and report it rather than stashing or discarding anything.

6. Show the user the acceptance criteria and ask for approval. On approval, tell them the next step is `plan-ticket`. Do not start planning in the same breath unless the user asks you to continue.

## Hard limits

- Do not touch any source code in this phase.
- Do not propose an implementation; that is the plan phase's job.
