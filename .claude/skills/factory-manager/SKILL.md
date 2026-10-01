---
name: factory-manager
description: Inspects the ticket backlog and the current workflow phase, then triggers the one pipeline skill (refine-ticket, plan-ticket, tdd-implement, or final-review) that owns the next step, keeps work/backlog.md and the GitHub project board in sync, and lands finished tickets (squash-merge into develop, promote develop to main). Picks the next queued ticket once the previous one is on main. Advances the pipeline by exactly one step per call and reports cleanly, so it is safe to invoke repeatedly, including from a loop. Use when the user wants the AI factory to keep moving without manually tracking phase and ticket state themselves.
---

# Manage the AI factory

Orchestrates the pipeline defined in `.claude/rules/workflow.md` and the gitflow in `.claude/rules/git.md`. This skill never changes `phase` itself, never writes source code, and never invokes more than one phase skill per call — it reads state, decides which phase skill owns the next step, triggers it with the `Skill` tool, and keeps the backlog and the GitHub board in sync. The one thing it does itself is **landing** a ticket whose review has passed.

## Preconditions

1. Read `.claude/state/workflow.json`. It may not exist yet — treat a missing file or a missing `phase` key as phase `idle`, exactly like `lib.sh:current_phase` does. Note `ticket`, `issue` and `branch` the same way (missing = none).
2. Read `work/backlog.md`. If it doesn't exist, create it with just this header, then stop this call and report that the backlog is empty and needs entries:

   ```markdown
   # Ticket backlog

   Queue for `factory-manager`. One ticket per line, top to bottom = priority order.
   Each line ends with its GitHub issue `(#N)`. `factory-manager` owns the status marker,
   the ticket id, and the `[[parked: ...]]` annotation on each line.
   ```

## Backlog and board sync

Backlog lines look like `- [ ] <title> (#N)`, then `- [~] <id>: <title> (#N)` while in progress, then `- [x] <id>: <title> (#N) — work/<id>/review.md` once landed on `main`. The issue's card on the project board mirrors that, set with:

```bash
bash .claude/scripts/board-status.sh <N> "<status>"
```

| phase after this call | backlog marker | board status |
|---|---|---|
| `refined`, `planned`, `implementing` | `[~]` | In Progress |
| `reviewing`, `done` (not yet landed) | `[~]` | In Review |
| landed on `main` | `[x]` | Done |

After every dispatch in step 2, re-read the phase and set the board status from this table (it's idempotent, so just set it). If the board call fails, report it but don't undo the pipeline step — the next call re-syncs.

## Steps

Do exactly one of the following, then stop and report (step 6). Never chain two phase skills in one call — one call is one observable pipeline step.

1. **Idempotence check.** If `ticket` is set, find its line in `work/backlog.md`. If that line carries `[[parked: <skill> @ <phase>]]` and `<phase>` equals the *current* phase, the last call already triggered `<skill>` at this phase and it stopped to ask a human something, and nothing has moved since. Do not re-invoke it — go straight to step 6 and report that it is still waiting. Otherwise (no tag, or the tag's phase no longer matches — meaning progress happened since) continue normally and discard any stale tag when you next touch that line.

2. **Dispatch on phase:**

   | phase | action |
   |---|---|
   | `idle` | Selection (step 4). |
   | `done` | If `ticket` is set and its backlog line is not `[x]`: landing (step 3). Otherwise: selection (step 4). |
   | `refined` | Invoke `plan-ticket`. |
   | `planned` | Invoke `tdd-implement`. |
   | `implementing` | Invoke `tdd-implement` (it resumes from the plan itself). |
   | `reviewing` | Invoke `final-review`. |

3. **`done` — landing.** `final-review` passed and opened a PR from `branch` into `develop`. Land it, following `.claude/rules/git.md`. Every sub-step checks first whether it has already happened (a previous call may have been interrupted) and skips if so:

   1. `git status` must be clean; otherwise stop and report. Find the PR: `gh pr list --head <branch> --base develop --state all --json number,state,title`.
   2. If the PR is still open and you're on `branch`: mark the backlog line `[x] <id>: <title> (#N) — work/<id>/review.md`, commit `docs(<id>): mark ticket done in backlog`, and `git push`. That way the backlog change travels with the squash commit.
   3. Wait for checks: `gh pr checks <pr> --watch --fail-fast`. If a check fails, stop and report — don't merge. ("no checks reported" is fine; continue.)
   4. If the PR is open, squash-merge it: `gh pr merge <pr> --squash --delete-branch --subject "<feat|fix>(<id>): <title> (#<pr>)" --body "Closes #<N>"`. Then `git switch develop && git pull --ff-only origin develop`.
   5. Sync: `git fetch origin && git merge --no-ff origin/main -m "chore(release): sync main into develop"`. If it says "Already up to date", skip the push; otherwise `git push origin develop`. On a conflict: `git merge --abort`, stop, and report that a human needs to resolve it — never edit source to resolve it here.
   6. Promote: unless an open `develop` → `main` PR already exists, `gh pr create --base main --head develop --title "chore(release): promote <id> to main" --body "Promotes #<pr> (<feat|fix>(<id>): <title>). Closes #<N>"`. Wait for its checks (`gh pr checks <promo> --watch --fail-fast`; the required `source-branch` check must pass), then `gh pr merge <promo> --merge --subject "chore(release): promote <id> to main (#<promo>)"`. Never squash and never `--delete-branch` here.
   7. Close-out: `gh issue close <N> --comment "Landed on main via #<promo>."` (skip if already closed), `bash .claude/scripts/board-status.sh <N> "Done"`, then `git switch develop && git pull --ff-only origin develop`.

   The ticket is now on `main`. Stop here; the next call picks the next ticket.

4. **Selection** (`idle`, or `done` after landing). Make sure you're on an up-to-date `develop` (`git switch develop && git pull --ff-only origin develop`; if the tree isn't clean, stop and report it). Read the backlog top to bottom and pick the first `[ ]` line, skipping any whose description names a dependency that's still open (e.g. "after X ships") — log a skip like that rather than guessing an order, and ask the user only if two candidates are genuinely ambiguous in priority. If no eligible `[ ]` line exists, report **"Backlog is empty — nothing to do"** and stop; that's the signal for a wrapping loop to stop too.

   Invoke `refine-ticket` with the picked line's text, including its `(#N)`. Afterwards, re-read `.claude/state/workflow.json` for the derived ticket id:
   - If `phase` is now `refined` (`refine-ticket` created and switched to the ticket branch): rewrite the line from `- [ ] <title> (#N)` to `- [~] <id>: <title> (#N)`, commit it with `docs(<id>): start ticket in backlog`, and set the board to In Progress.
   - If `phase` is still `idle`/unchanged, `refine-ticket` stopped mid-interview (or asked for ticket-id confirmation): leave the line as `- [ ]` but add `[[parked: refine-ticket @ idle]]` so the next call doesn't restart the interview from scratch. Don't commit this (commits are blocked in `idle` and on `develop`). Set the board to In Progress anyway, since a human is now working on it.

5. **Parking other skills.** If `plan-ticket`, `tdd-implement` or `final-review` stops to ask a human (for example, plan approval) and the phase didn't change, add `[[parked: <skill> @ <phase>]]` to the ticket's line.

6. **Report.** One short summary: phase before → phase after, the ticket id and issue, the board status set, and the artifact or PR that changed. If the invoked skill stopped to ask the user something — ticket interview, ticket-id confirmation, plan approval — say exactly that instead of answering on its behalf; a human needs to be present for that turn, and this skill does not fabricate approval to keep a loop moving.

## Hard limits

- Never call `.claude/hooks/set-state.sh`; only the phase skill that owns a transition may change `phase`, `ticket`, `issue` or `branch`.
- Never invoke more than one phase skill per call, and never select a new ticket in the same call that landed the previous one.
- Never fabricate or infer the user's approval of a ticket or plan.
- Never write source code from this skill (the write-protection hook would block it outside `implementing` anyway); it only ever delegates.
- Never merge a PR whose checks fail. Never push to `main`, squash a promotion PR, or delete `develop`.
- Never reorder or delete backlog lines beyond updating a line's own status marker, ticket id, done-reference and `[[parked: ...]]` tag.
