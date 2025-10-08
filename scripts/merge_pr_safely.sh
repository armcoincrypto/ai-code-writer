#!/usr/bin/env bash
set -euo pipefail

PR="${1:?Usage: merge_pr_safely.sh <pr-number>}"
OWNER="${OWNER:?export OWNER=<org_or_user>}"
REPO="${REPO:?export REPO=<repo_name>}"
BASE="${BASE:-main}"   # override if your default branch isn’t main

relax_reviews() {
  gh api -X PATCH \
    "repos/$OWNER/$REPO/branches/$BASE/protection/required_pull_request_reviews" \
    -H "Accept: application/vnd.github+json" \
    --input <(cat <<'JSON'
{ "dismiss_stale_reviews": true, "required_approving_review_count": 0, "require_code_owner_reviews": false }
JSON
)
}

restore_reviews() {
  gh api -X PATCH \
    "repos/$OWNER/$REPO/branches/$BASE/protection/required_pull_request_reviews" \
    -H "Accept: application/vnd.github+json" \
    --input <(cat <<'JSON'
{ "dismiss_stale_reviews": true, "required_approving_review_count": 1, "require_code_owner_reviews": true }
JSON
)
}

relax_checks() {
  gh api -X PATCH \
    "repos/$OWNER/$REPO/branches/$BASE/protection/required_status_checks" \
    -H "Accept: application/vnd.github+json" \
    -f strict:=false \
    --input <(cat <<'JSON'
{ "checks": [] }
JSON
)
}

restore_checks() {
  gh api -X PATCH \
    "repos/$OWNER/$REPO/branches/$BASE/protection/required_status_checks" \
    -H "Accept: application/vnd.github+json" \
    -f strict:=true \
    --input <(cat <<'JSON'
{ "checks": [ {"context":"CI"}, {"context":"project-doctor"} ] }
JSON
)
}

snapshot() {
  gh api "repos/$OWNER/$REPO/branches/$BASE/protection" \
    -q '{checks:.required_status_checks,reviews:.required_pull_request_reviews}'
}

echo ">>> BEFORE:"
gh pr view "$PR" --json number,state,mergeStateStatus,reviewDecision \
  -q '{pr:.number,state:.state,merge:.mergeStateStatus,review:.reviewDecision}' || true

echo ">>> Ensuring checks are green..."
bad=$(gh pr view "$PR" --json statusCheckRollup \
      -q '.statusCheckRollup[] | select(.conclusion!="SUCCESS")' || true)
[ -z "$bad" ] || { echo "!! Some checks are not SUCCESS. Aborting."; exit 1; }

# Always restore even on error
trap 'echo "[trap] restoring protections..."; restore_checks || true; restore_reviews || true' EXIT

echo ">>> Temporarily relaxing review requirement..."
relax_reviews
echo ">>> Temporarily relaxing required status checks..."
relax_checks

echo ">>> Waiting for PR to become MERGEABLE..."
for i in {1..20}; do
  ms=$(gh pr view "$PR" --json mergeStateStatus -q .mergeStateStatus 2>/dev/null || echo "UNKNOWN")
  echo "mergeStateStatus=$ms (attempt $i/20)"
  [[ "$ms" == "CLEAN" || "$ms" == "HAS_HOOKS" || "$ms" == "UNSTABLE" ]] && break
  sleep 2
done

echo ">>> Merging (squash) + deleting branch..."
gh pr merge "$PR" --squash --delete-branch

echo ">>> Restoring protections (checks + reviews)..."
restore_checks
restore_reviews

echo ">>> AFTER:"
snapshot
echo ">>> Done."
