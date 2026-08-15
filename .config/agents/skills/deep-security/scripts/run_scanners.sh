#!/usr/bin/env bash
# Run whatever FOSS scanners are installed; emit SARIF + ran.json + skipped.json.
# Missing tools are recorded (the matching AI lens covers that surface).
# Usage: run_scanners.sh <scope_path> <out_sarif_dir> <mode> <egress>
set -uo pipefail
SCOPE="${1:-.}"; OUT="${2:-./.deep-security/sarif}"; MODE="${3:-full}"; EGRESS="${4:-off}"
mkdir -p "$OUT"
# Exclude vendored / third-party / nested-worktree / generated dirs — scanning these
# inflates findings 10x with duplicates and noise. Extend as needed per repo.
SKIPDIRS=".claude,node_modules,vendor,.git,data,.deep-security,dist,build,.venv"
TRIVY_SKIP=(--skip-dirs "$SKIPDIRS" --skip-dirs "**/node_modules" --skip-dirs "manifests/vendor" --skip-version-check)
# Apply the same excludes to every scanner (not just trivy) — vendored/nested-worktree
# dirs inflate findings 10x with duplicates. opengrep/bandit/checkov each have their own flag.
OG_EXCLUDE=(--exclude .claude --exclude node_modules --exclude vendor --exclude data --exclude .deep-security --exclude dist --exclude build --exclude .venv)
BANDIT_EXCLUDE='*/.claude/*,*/node_modules/*,*/vendor/*,*/.deep-security/*,*/.venv/*'
CHECKOV_SKIP=(--skip-path '.claude' --skip-path 'node_modules' --skip-path 'vendor' --skip-path 'manifests/vendor' --skip-path '.deep-security')
RAN="[]"; SKIP="[]"
have(){ command -v "$1" >/dev/null 2>&1; }
ver(){ "$@" 2>/dev/null | head -1 | tr -d '\n' | sed 's/"/'"'"'/g'; }
add_ran(){ RAN=$(printf '%s' "$RAN" | sed 's/]$//'); [ "$RAN" != "[" ] && RAN="$RAN,"; RAN="$RAN{\"name\":\"$1\",\"version\":\"$2\"}]"; }
add_skip(){ SKIP=$(printf '%s' "$SKIP" | sed 's/]$//'); [ "$SKIP" != "[" ] && SKIP="$SKIP,"; SKIP="$SKIP{\"name\":\"$1\",\"install\":\"$2\"}]"; }
present(){ find "$SCOPE" -name "$1" -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null | head -1 | grep -q .; }

echo "deep-security: scanning $SCOPE (mode=$MODE)"

# --- QUICK: fast staged-diff subset only (don't duplicate pre-push/CI) ---
if [ "$MODE" = "quick" ]; then
  if have gitleaks; then gitleaks protect --staged --report-format sarif --report-path "$OUT/gitleaks.sarif" --no-banner >/dev/null 2>&1; add_ran gitleaks "$(ver gitleaks version)"; else add_skip gitleaks "brew install gitleaks"; fi
  if have opengrep; then
    STAGED=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | tr '\n' ' ')
    [ -n "$STAGED" ] && opengrep scan --config auto --sarif --output "$OUT/opengrep.sarif" $STAGED >/dev/null 2>&1
    add_ran opengrep "$(ver opengrep --version)"
  else add_skip opengrep "brew install opengrep/tap/opengrep"; fi
  printf '%s' "$RAN" > "$OUT/ran.json"; printf '%s' "$SKIP" > "$OUT/skipped.json"
  echo "quick scan done"; exit 0
fi

# --- DIFF / FULL: full available kit ---
# SAST
if have opengrep; then opengrep scan --config auto "${OG_EXCLUDE[@]}" --sarif --output "$OUT/opengrep.sarif" "$SCOPE" >/dev/null 2>&1; add_ran opengrep "$(ver opengrep --version)"; else add_skip opengrep "curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash"; fi
if present '*.py'; then
  # -ll -ii = medium+ severity AND confidence (bandit Low-everything is ~99% noise: asserts, try/except/pass).
  # Needs bandit-sarif-formatter injected (no native sarif). If sarif fails, fall back to skip.
  if have bandit; then bandit -r "$SCOPE" --exclude "$BANDIT_EXCLUDE" -ll -ii -f sarif -o "$OUT/bandit.sarif" -q >/dev/null 2>&1 && [ -s "$OUT/bandit.sarif" ] && add_ran bandit "$(ver bandit --version)" || add_skip bandit "pipx inject bandit bandit-sarif-formatter"; else add_skip bandit "pipx install bandit && pipx inject bandit bandit-sarif-formatter"; fi
fi
if present '*.go'; then
  if have gosec; then gosec -fmt sarif -out "$OUT/gosec.sarif" "$SCOPE/..." >/dev/null 2>&1; add_ran gosec "$(ver gosec -version)"; else add_skip gosec "go install github.com/securego/gosec/v2/cmd/gosec@latest (pin!)"; fi
  if have govulncheck; then govulncheck -C "$SCOPE" -format sarif ./... > "$OUT/govulncheck.sarif" 2>/dev/null; add_ran govulncheck "$(ver govulncheck -version)"; else add_skip govulncheck "go install golang.org/x/vuln/cmd/govulncheck@latest (pin!)"; fi
fi
# Secrets
# --no-git: scan the working tree as files, NOT the full git history. History scanning
# walks every commit (minutes on a large repo) and belongs in a separate opt-in job, not
# the per-PR/full code scan. `gitleaks dir` is the v8.19+ alias; `detect --no-git` is the
# portable form that works across installed versions.
if have gitleaks; then gitleaks detect --no-git --source "$SCOPE" --report-format sarif --report-path "$OUT/gitleaks.sarif" --no-banner >/dev/null 2>&1; add_ran gitleaks "$(ver gitleaks version)"; else add_skip gitleaks "brew install gitleaks"; fi
# SCA + IaC + container (Trivy = one binary for many)
# Trivy: drop the slow whole-repo `secret` scanner (gitleaks covers secrets) — it's what
# made an earlier run appear to hang. vuln + misconfig only, with dir excludes.
if have trivy; then
  trivy fs --scanners vuln,misconfig "${TRIVY_SKIP[@]}" --format sarif --output "$OUT/trivy.sarif" "$SCOPE" >/dev/null 2>&1
  add_ran trivy "$(ver trivy --version)"
else add_skip trivy "brew install trivy  # PIN the version"; fi
if have osv-scanner; then osv-scanner scan --format sarif --output "$OUT/osv.sarif" "$SCOPE" >/dev/null 2>&1; add_ran osv-scanner "$(ver osv-scanner --version)"; else add_skip osv-scanner "brew install osv-scanner"; fi
# IaC depth (Azure Bicep/ARM)
if present '*.tf' || present '*.bicep' || present 'Dockerfile' || present '*.yaml'; then
  if have checkov; then checkov -d "$SCOPE" "${CHECKOV_SKIP[@]}" -o sarif --output-file-path "$OUT/checkov" >/dev/null 2>&1; [ -f "$OUT/checkov/results_sarif.sarif" ] && mv "$OUT/checkov/results_sarif.sarif" "$OUT/checkov.sarif"; add_ran checkov "$(ver checkov --version)"; else add_skip checkov "pipx install checkov"; fi
fi
# npm supply-chain (malicious, not just CVE)
if present 'package.json'; then
  if [ "$EGRESS" = "socket" ] && have socket; then socket scan create "$SCOPE" --sarif > "$OUT/socket.sarif" 2>/dev/null; add_ran socket "$(ver socket --version)";
  elif [ "$EGRESS" = "local" ] && have guarddog; then guarddog npm scan "$SCOPE" --output-format sarif > "$OUT/guarddog.sarif" 2>/dev/null; add_ran guarddog "$(ver guarddog --version)";
  elif [ "$EGRESS" = "socket" ]; then add_skip socket "npm i -g @socketsecurity/cli (+ SOCKET_CLI_API_TOKEN)";
  elif [ "$EGRESS" = "local" ]; then add_skip guarddog "pipx install guarddog"; fi
fi

printf '%s' "$RAN" > "$OUT/ran.json"
printf '%s' "$SKIP" > "$OUT/skipped.json"
echo "scan done. ran: $RAN"
echo "skipped: $SKIP"
