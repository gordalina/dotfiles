#!/usr/bin/env bash
f=~/.config/git/allowed_signers
{
  awk '$1 ~ /^(ssh-|ecdsa-|sk-)/ { print $NF, "namespaces=\"git\"", $1, $2; next } { print }' "$f"
  ssh-add -L | awk '{ print $NF, "namespaces=\"git\"", $1, $2 }'
} | sort -u > "$f.tmp" && mv "$f.tmp" "$f"