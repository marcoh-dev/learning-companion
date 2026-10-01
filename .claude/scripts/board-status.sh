#!/usr/bin/env bash
# Set the GitHub project board status of a ticket's issue.
# Usage: bash .claude/scripts/board-status.sh <issue-number> "Todo|In Progress|In Review|Done"
# Board ids live in .claude/board.json. Adds the issue to the board if it is
# not on it yet. Prints the new status; exits non-zero on any failure.
set -euo pipefail

CONF=".claude/board.json"
issue="${1:?usage: board-status.sh <issue-number> <status>}"
status="${2:?usage: board-status.sh <issue-number> <status>}"

repo="$(jq -r .repo "$CONF")"
owner="$(jq -r .owner "$CONF")"
number="$(jq -r .project_number "$CONF")"
project_id="$(jq -r .project_id "$CONF")"
field_id="$(jq -r .status_field_id "$CONF")"
option_id="$(jq -r --arg s "$status" '.status_options[$s] // empty' "$CONF")"
[ -n "$option_id" ] || { echo "unknown status '$status' (see $CONF)" >&2; exit 1; }

url="https://github.com/$repo/issues/$issue"
item_id="$(gh project item-add "$number" --owner "$owner" --url "$url" --format json --jq .id)"

gh project item-edit --id "$item_id" --project-id "$project_id" \
  --field-id "$field_id" --single-select-option-id "$option_id" >/dev/null

echo "#$issue -> $status"
