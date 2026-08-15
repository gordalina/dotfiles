#!/usr/bin/env bash
# Framework-aware pre-commit wiring for `deep-security --quick`. Explicit opt-in.
# Detects the repo's hook framework, shows the change, asks before writing.
# Never silent, never auto-on.
set -uo pipefail
ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "not a git repo"; exit 1; }
cd "$ROOT"
CMD='deep-security --quick   # or: claude -p "/deep-security --quick"'

confirm(){ printf '%s [y/N] ' "$1"; read -r a; [ "$a" = y ] || [ "$a" = Y ]; }

if [ -f .pre-commit-config.yaml ]; then
  echo "Detected: pre-commit framework (.pre-commit-config.yaml)"
  cat <<'EOF'

Proposed addition to .pre-commit-config.yaml:

  - repo: local
    hooks:
      - id: deep-security-quick
        name: deep-security (quick)
        entry: bash -c 'deep-security --quick'   # adapt to your invocation
        language: system
        pass_filenames: false
        stages: [pre-commit]
EOF
  if confirm "Append this hook?"; then
    cat >> .pre-commit-config.yaml <<'EOF'

  - repo: local
    hooks:
      - id: deep-security-quick
        name: deep-security (quick)
        entry: bash -c 'deep-security --quick'
        language: system
        pass_filenames: false
        stages: [pre-commit]
EOF
    echo "Added. Run: pre-commit install"
  else echo "Skipped."; fi

elif [ -d .husky ]; then
  echo "Detected: Husky (.husky/)"
  echo "Proposed: append to .husky/pre-commit -> $CMD"
  if confirm "Append to .husky/pre-commit?"; then
    printf '\n%s\n' "$CMD" >> .husky/pre-commit; chmod +x .husky/pre-commit; echo "Added."
  else echo "Skipped."; fi

else
  HOOK="$(git rev-parse --git-path hooks)/pre-commit"
  echo "No framework detected — proposing a raw git hook at $HOOK"
  echo "Content:"; printf '  #!/usr/bin/env bash\n  %s\n' "$CMD"
  if confirm "Create/append the raw hook?"; then
    [ -f "$HOOK" ] || printf '#!/usr/bin/env bash\n' > "$HOOK"
    printf '%s\n' "$CMD" >> "$HOOK"; chmod +x "$HOOK"; echo "Added."
  else echo "Skipped."; fi
fi
