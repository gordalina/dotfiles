#!/usr/bin/env bash
# Provision the deep-security FOSS toolkit. Idempotent. Pins live in PINS below.
# Trivy MUST be pinned + checksum-verified (compromised twice in 2026).
set -uo pipefail

# --- PINS (bump deliberately; never float to @latest) ---
TRIVY_PIN="0.58.0"        # verify checksum after install
GOSEC_PIN="v2.21.4"
GOVULN_PIN="v1.1.3"

have(){ command -v "$1" >/dev/null 2>&1; }
ok(){ printf '  ✓ %s\n' "$1"; }
miss(){ printf '  • %s — %s\n' "$1" "$2"; }

echo "deep-security setup — installing FOSS scanner kit"
BREW=0; PIPX=0; GO=0
have brew && BREW=1; have pipx && PIPX=1; have go && GO=1
[ $BREW = 0 ] && echo "  (homebrew not found — brew installs will be skipped)"
[ $PIPX = 0 ] && echo "  (pipx not found — pip installs will be skipped; 'brew install pipx' or 'python3 -m pip install pipx')"

# Opengrep (preferred SAST) — distributed via release binary, NOT homebrew (no official tap)
OPENGREP_INSTALL='curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash'
if have opengrep; then ok "opengrep present"
else
  mkdir -p "$HOME/.local/bin"
  case "$(uname -s)/$(uname -m)" in
    Darwin/arm64) OG_ASSET=opengrep_osx_arm64 ;; Darwin/x86_64) OG_ASSET=opengrep_osx_x86 ;;
    Linux/x86_64) OG_ASSET=opengrep_manylinux_x86 ;; Linux/aarch64) OG_ASSET=opengrep_manylinux_aarch64 ;;
    *) OG_ASSET="" ;;
  esac
  OG_URL=$(curl -fsSL https://api.github.com/repos/opengrep/opengrep/releases/latest 2>/dev/null | grep '"browser_download_url"' | grep "${OG_ASSET}\"" | head -1 | sed -E 's/.*"(https[^"]+)".*/\1/')
  if [ -n "$OG_ASSET" ] && [ -n "$OG_URL" ] && curl -fsSL "$OG_URL" -o "$HOME/.local/bin/opengrep" 2>/dev/null; then
    chmod +x "$HOME/.local/bin/opengrep"; ok "opengrep (~/.local/bin — ensure on PATH)"
  else miss opengrep "$OPENGREP_INSTALL"; fi
fi

# Trivy — PINNED
if have trivy; then ok "trivy present ($(trivy --version 2>/dev/null | head -1))";
elif [ $BREW = 1 ]; then brew install "trivy@${TRIVY_PIN}" 2>/dev/null || brew install trivy; echo "  ! verify trivy version == ${TRIVY_PIN} and checksum"; ok trivy;
else miss trivy "install trivy ${TRIVY_PIN} from a verified release + checksum"; fi

# Gitleaks (binary, NOT the Action)
have gitleaks && ok "gitleaks present" || { [ $BREW = 1 ] && brew install gitleaks && ok gitleaks || miss gitleaks "brew install gitleaks"; }

# OSV-Scanner
have osv-scanner && ok "osv-scanner present" || { [ $BREW = 1 ] && brew install osv-scanner && ok osv-scanner || miss osv-scanner "brew install osv-scanner"; }

# Python SAST + IaC
# Bandit needs the SARIF formatter plugin injected — it has NO native -f sarif
if have bandit; then ok "bandit present"; [ $PIPX = 1 ] && pipx inject bandit bandit-sarif-formatter >/dev/null 2>&1 || true
elif [ $PIPX = 1 ]; then pipx install bandit && pipx inject bandit bandit-sarif-formatter >/dev/null 2>&1 && ok bandit
else miss bandit "pipx install bandit && pipx inject bandit bandit-sarif-formatter"; fi
have checkov && ok "checkov present" || { [ $PIPX = 1 ] && pipx install checkov && ok checkov || miss checkov "pipx install checkov"; }

# Go tools (only meaningful if Go is used)
if [ $GO = 1 ]; then
  have gosec && ok "gosec present" || { go install "github.com/securego/gosec/v2/cmd/gosec@${GOSEC_PIN}" && ok gosec || miss gosec "go install gosec@${GOSEC_PIN}"; }
  have govulncheck && ok "govulncheck present" || { go install "golang.org/x/vuln/cmd/govulncheck@${GOVULN_PIN}" && ok govulncheck || miss govulncheck "go install govulncheck@${GOVULN_PIN}"; }
fi

echo
echo "Optional npm supply-chain (enable per-run with --socket or --no-egress):"
miss "socket (cloud, best npm)" "npm i -g @socketsecurity/cli  + export SOCKET_CLI_API_TOKEN"
miss "guarddog (local, no egress)" "pipx install guarddog"
echo
echo "Done. Re-run /deep-security --setup anytime; it only installs what's missing."
