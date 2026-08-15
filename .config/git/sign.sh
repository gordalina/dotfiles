#!/usr/bin/env bash
# Sign with whichever agent key has a comment matching user.email.
# Git calls: sign -Y sign -n git -f <key> <buffer>, or sign -Y verify ...
set -euo pipefail

[ "${2-}" = "sign" ] || exec ssh-keygen "$@"

email=$(git config user.email)
key=$(ssh-add -L | awk -v e="$email" '$NF == e {print; exit}')
[ -n "$key" ] || { echo "sign: no agent key for $email" >&2; exit 1; }

pub=$(mktemp); trap 'rm -f "$pub"' EXIT
printf '%s\n' "$key" > "$pub"

ssh-keygen -Y sign -n git -f "$pub" "${@: -1}"