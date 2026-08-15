#!/usr/bin/env bash
# CI/Linux provisioning for the deep-security scanner kit. setup.sh is brew-first
# (macOS dev); this is the Linux/GitHub-Actions path. Best-effort by design:
# run_scanners.sh records anything missing in skipped.json and the matching AI lens
# covers that surface, so a failed install degrades coverage — it never breaks the run.
#
# SUPPLY CHAIN: every tool is fetched from a PINNED release asset — never a
# `curl … | bash` of a floating branch. This runner holds ANTHROPIC_API_KEY, so a
# compromised installer = key exfil. Bump the pins deliberately (trivy especially —
# compromised twice in 2026).
#
# Usage: ci_install_scanners.sh <pr|full>
#   pr   = fast subset (opengrep + gitleaks + bandit) — enough for diff-scoped review
#   full = whole kit (+ trivy + checkov + osv-scanner) for the weekly audit
set -uo pipefail
MODE="${1:-full}"
BIN="${HOME}/.local/bin"; mkdir -p "$BIN"
case ":$PATH:" in *":$BIN:"*) ;; *) export PATH="$BIN:$PATH" ;; esac
[ -n "${GITHUB_PATH:-}" ] && echo "$BIN" >> "$GITHUB_PATH"  # persist for later steps

have(){ command -v "$1" >/dev/null 2>&1; }

# Pins (release tags / versions) — bump deliberately.
OPENGREP_VERSION="${OPENGREP_VERSION:-1.23.0}"
GITLEAKS_VERSION="${GITLEAKS_VERSION:-8.21.2}"
TRIVY_VERSION="${TRIVY_VERSION:-0.58.0}"
OSV_VERSION="${OSV_VERSION:-2.0.2}"

# Arch-specific release-asset names.
case "$(uname -m)" in
  x86_64|amd64)  OG_ASSET=opengrep_manylinux_x86;     TRIVY_ARCH=Linux-64bit; OSV_ARCH=linux_amd64; GL_ARCH=linux_x64 ;;
  aarch64|arm64) OG_ASSET=opengrep_manylinux_aarch64; TRIVY_ARCH=Linux-ARM64; OSV_ARCH=linux_arm64; GL_ARCH=linux_arm64 ;;
  *)             OG_ASSET=""; TRIVY_ARCH=""; OSV_ARCH=""; GL_ARCH="" ;;
esac

dl(){ curl -fsSL "$1" -o "$2" 2>/dev/null; }  # download to a path, quiet, non-fatal

# --- always: SAST + secrets + python ---
# Opengrep — pinned release binary (NOT the floating main install.sh).
if ! have opengrep && [ -n "$OG_ASSET" ]; then
  dl "https://github.com/opengrep/opengrep/releases/download/v${OPENGREP_VERSION}/${OG_ASSET}" "$BIN/opengrep" \
    && chmod +x "$BIN/opengrep" || true
fi

# Gitleaks — pinned release tarball.
if ! have gitleaks && [ -n "$GL_ARCH" ]; then
  curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_${GL_ARCH}.tar.gz" \
    2>/dev/null | tar -xz -C "$BIN" gitleaks 2>/dev/null || true
fi

# Python SAST — bandit needs the SARIF formatter injected (no native -f sarif).
if ! have bandit; then
  if have uv; then uv tool install bandit --with bandit-sarif-formatter 2>/dev/null || true
  elif have pipx; then pipx install bandit >/dev/null 2>&1 && pipx inject bandit bandit-sarif-formatter >/dev/null 2>&1 || true
  fi
fi

# --- full only: SCA + IaC ---
if [ "$MODE" = "full" ]; then
  # Trivy — pinned release tarball (NOT the floating main contrib/install.sh; the
  # version pin is meaningless if the installer script itself can be swapped).
  if ! have trivy && [ -n "$TRIVY_ARCH" ]; then
    curl -fsSL "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_${TRIVY_ARCH}.tar.gz" \
      2>/dev/null | tar -xz -C "$BIN" trivy 2>/dev/null || true
  fi
  if ! have checkov; then
    if have uv; then uv tool install checkov 2>/dev/null || true
    elif have pipx; then pipx install checkov >/dev/null 2>&1 || true
    fi
  fi
  if ! have osv-scanner && [ -n "$OSV_ARCH" ]; then
    dl "https://github.com/google/osv-scanner/releases/download/v${OSV_VERSION}/osv-scanner_${OSV_ARCH}" "$BIN/osv-scanner" \
      && chmod +x "$BIN/osv-scanner" || true
  fi
fi

echo "deep-security CI scanner install (mode=$MODE) — present:"
for t in opengrep gitleaks bandit trivy checkov osv-scanner; do
  if have "$t"; then echo "  ✓ $t"; else echo "  • $t (skipped — lens covers this surface)"; fi
done
