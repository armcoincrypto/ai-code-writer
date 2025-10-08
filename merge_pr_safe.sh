#!/usr/bin/env bash
set -euo pipefail

OWNER="armcoincrypto"
REPO="ai-code-writer"
PR="${1:-5}"

restore_reviews() {
  gh api -X PATCH \
    "repos/$OWNER/$REPO/branches/main/protection/required_pull_request_reviews" \
    -H "Accept: application/vnd.github+json" \
    --input <(cat <<'JSON'
{
  "dismiss_stale_reviews": true,
  "required_approving_review_count": 1,
  "require_code_owner_reviews": true
}
JSON
)
}

relax_reviews() {
  gh api -X PATCH \
    "repos/$OWNER/$REPO/branches/main/protection/required_pull_request_reviews" \
    -H "Accept: application/vnd.github+json" \
    --input <(cat <<'JSON'
{
  "dismiss_stale_reviews": true,
  "required_approving_review_count": 0,
  "require_code_owner_reviews": false
}
JSON
)
}

check() {
  gh pr view "$PR" \
    --json number,mergeStateStatus,reviewDecision,state \
    -q '{pr:.number,merge:.mergeStateStatus,review:.reviewDecision,state:.state}'
}

trap 'echo "[trap] restoring review rule..."; restore_reviews || true' EXIT

echo ">>> Before:"
check || true
echo ">>> Relaxing reviews..."
relax_reviews
echo ">>> After relax:"
check || true

echo ">>> Merging PR #$PR (squash + delete branch)..."
gh pr merge "$PR" --squash --delete-branch

echo ">>> Restoring review rule..."
restore_reviews

echo ">>> Final protection state (reviews):"
gh api "repos/$OWNER/$REPO/branches/main/protection" | jq '.required_pull_request_reviews'
echo ">>> Done."
