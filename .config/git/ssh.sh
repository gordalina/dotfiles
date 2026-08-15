#!/usr/bin/env bash
# Connect with the agent key whose comment matches user.email.
# Without this, GitHub picks the account of whichever key the agent offers first.
set -euo pipefail

email=$(git config user.email 2>/dev/null || true)
key=$(ssh-add -L 2>/dev/null | awk -v e="$email" '$NF == e { print; exit }' || true)

[ -n "$key" ] || exec ssh "$@"

pub=$(mktemp)
trap 'rm -f "$pub"' EXIT
printf '%s\n' "$key" > "$pub"

ssh -o IdentitiesOnly=yes -i "$pub" "$@"
