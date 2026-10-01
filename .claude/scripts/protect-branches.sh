#!/usr/bin/env bash
# One-time GitHub branch protection for the gitflow in .claude/rules/git.md.
# Run after main and develop have been pushed:
#   bash .claude/scripts/protect-branches.sh
#
# main:    PR required (0 approvals, so factory-manager can merge), required
#          checks `source-branch` (PRs only from develop) and `test`
#          (.github/workflows/ci.yml), applies to admins, no force-push,
#          no deletion.
# develop: required check `test`, no force-push, no deletion (also keeps it
#          safe from branch auto-deletion). Admins are exempt, so direct pushes
#          stay possible for the main-sync merge commit; the local hooks block
#          direct commits.
# Run it only after the `test` check has reported at least once, otherwise
# GitHub waits forever on a required check that never reports.
set -euo pipefail

repo="$(jq -r .repo .claude/board.json)"

gh api -X PUT "repos/$repo/branches/main/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["source-branch", "test"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
echo "main protected"

gh api -X PUT "repos/$repo/branches/develop/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["test"] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
echo "develop protected"
