#!/usr/bin/env bash
# One-time GitHub branch protection for the gitflow in .claude/rules/git.md.
# Run after main and develop have been pushed:
#   bash .claude/scripts/protect-branches.sh
#
# main:    PR required (0 approvals, so factory-manager can merge), required
#          check `source-branch` (PRs only from develop), applies to admins,
#          no force-push, no deletion.
# develop: no force-push, no deletion (also keeps it safe from branch
#          auto-deletion). Direct pushes stay possible for the main-sync merge
#          commit; the local hooks block direct commits.
set -euo pipefail

repo="$(jq -r .repo .claude/board.json)"

gh api -X PUT "repos/$repo/branches/main/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["source-branch"] },
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
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
echo "develop protected"
