#!/usr/bin/env bash
# Connect with the agent key whose comment matches user.email.
# Without this, GitHub picks the account of whichever key the agent offers first.
set -euo pipefail

email=$(git config user.email 2>/dev/null || true)

# Ask the agent this host actually uses, not the ambient one. A host with its own
# IdentityAgent (1Password, per-repo config.local) must keep its own keys.
agent=$(ssh -G "$@" 2>/dev/null | sed -n 's/^identityagent //p' | head -1)
case "$agent" in
    SSH_AUTH_SOCK | "") agent=${SSH_AUTH_SOCK-} ;;
    none) agent= ;;
esac

key=$(SSH_AUTH_SOCK=$agent ssh-add -L 2>/dev/null | awk -v e="$email" '$NF == e { print; exit }' || true)

[ -n "$key" ] || exec ssh "$@"

pub=$(mktemp)
trap 'rm -f "$pub"' EXIT
printf '%s\n' "$key" > "$pub"

ssh -o IdentitiesOnly=yes -i "$pub" "$@"
