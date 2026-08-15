#!/usr/bin/env bash
# Flags AI/startup "tells" in a customer-facing draft before delivery.
# Usage: bash lint_tells.sh <draft-file>
# Exit 0 = clean, 1 = hits found (or usage error).
set -uo pipefail

file="${1:-}"
if [[ -z "$file" || ! -f "$file" ]]; then
  echo "usage: lint_tells.sh <draft-file>" >&2
  exit 1
fi

hits=0

report() {
  # $1 = label, $2 = extended-regex pattern (case-insensitive)
  local label="$1" pattern="$2" out
  out=$(grep -nEi -e "$pattern" "$file" 2>/dev/null) || true
  if [[ -n "$out" ]]; then
    echo "## $label"
    echo "$out"
    echo
    hits=$((hits + $(printf '%s\n' "$out" | grep -c .)))
  fi
}

echo "Linting: $file"
echo

report "Em dashes (—)" "—"
report "Arrows (→ ↔ ⟶ ⟵)" "→|↔|⟶|⟵"
report "Startup / AI-ese phrases" "the ask|read this first|big-bang|long pole|lowest lift|tracked to green|cherry-pick|seamless|leverage|delve|boasts|game-chang|we're excited|let's "

echo "-----"
if [[ "$hits" -gt 0 ]]; then
  echo "FAIL: $hits potential tell(s) found. Review and fix before delivery."
  exit 1
else
  echo "PASS: no tells found."
  exit 0
fi
