#!/usr/bin/env bash
# Publish a weekly run to the long-lived `security-findings` branch — the versioned
# findings store + the baseline the next week's delta diffs against. gh-pages style:
# an orphan branch with its own history, so the detail (which names live vulns) never
# lands in main's default checkout. Idempotent: creates the branch on first run.
#
# Usage: publish_findings.sh <findings.json> <report.html> <date-tag>
# Env:   GIT_AUTHOR_* / committer set by caller; needs a token with contents:write.
set -euo pipefail
FINDINGS="$1"; REPORT="$2"; TAG="${3:-$(date -u +%F)}"
BRANCH="security-findings"
WT="$(mktemp -d)"
# set -e aborts on any error (e.g. a push auth failure); clean up the worktree regardless.
trap 'git worktree remove --force "$WT" 2>/dev/null || true; rm -rf "$WT" 2>/dev/null || true' EXIT

git fetch --no-tags origin "$BRANCH" 2>/dev/null || true
if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
  git worktree add "$WT" "origin/$BRANCH"
  git -C "$WT" checkout -B "$BRANCH"
else
  echo "first run — creating orphan $BRANCH"
  git worktree add --detach "$WT"
  git -C "$WT" checkout --orphan "$BRANCH"
  git -C "$WT" rm -rf . >/dev/null 2>&1 || true
fi

mkdir -p "$WT/findings" "$WT/reports"
cp "$FINDINGS" "$WT/findings/findings-$TAG.json"
cp "$FINDINGS" "$WT/findings/latest.json"      # stable path the delta step reads
cp "$REPORT"   "$WT/reports/report-$TAG.html"
cp "$REPORT"   "$WT/reports/latest.html"

# A browsable index so the branch has a thin front door (README links here).
{
  echo "# deep-security findings store"
  echo
  echo "Versioned weekly audit output. \`findings/latest.json\` is the current baseline;"
  echo "\`reports/latest.html\` is the latest report. History = the week-over-week delta."
  echo
  echo "_Last run: $TAG_"
} > "$WT/README.md"

git -C "$WT" add -A
if git -C "$WT" diff --cached --quiet; then
  echo "no changes to publish"
else
  git -C "$WT" commit -q -m "security audit $TAG"
  git -C "$WT" push origin "$BRANCH"
  echo "published findings + report to $BRANCH ($TAG)"
fi
