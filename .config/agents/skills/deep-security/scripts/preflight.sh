#!/usr/bin/env bash
# Report scanner availability BEFORE a run so the user can choose to install the
# missing kit (full coverage) vs proceed degraded (agent-only for those lenses).
# Prints a human table + a machine line (PRESENT=… MISSING=…) for the agent to relay.
# Usage: preflight.sh [egress]   (egress: socket|local|off — controls npm row)
export PATH="$HOME/.local/share/mise/shims:$PATH"
EGRESS="${1:-off}"
have(){ command -v "$1" >/dev/null 2>&1; }

# tool | covers | install
ROWS=(
"opengrep|cross-language SAST taint (Py/TS/Go) — the core agent-complement|curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash"
"trivy|deps(SCA) + IaC/k8s/Dockerfile misconfig + container|brew install trivy  # pin"
"gitleaks|secret scanning|brew install gitleaks"
"bandit|Python SAST depth|pipx install bandit"
"gosec|Go SAST depth|go install github.com/securego/gosec/v2/cmd/gosec@<pin>"
"govulncheck|Go deps w/ reachability|go install golang.org/x/vuln/cmd/govulncheck@<pin>"
"osv-scanner|deps + malicious-package feeds|brew install osv-scanner"
"checkov|IaC depth incl. Azure Bicep/ARM|pipx install checkov"
)
[ "$EGRESS" = socket ] && ROWS+=("socket|npm supply-chain / malware (cloud)|npm i -g @socketsecurity/cli")
[ "$EGRESS" = local ] && ROWS+=("guarddog|npm/PyPI malware (local, no egress)|pipx install guarddog")

PRESENT=(); MISSING=(); MISSING_INSTALL=()
printf '\n  %-13s %-8s %s\n' "SCANNER" "STATUS" "COVERS"
printf '  %-13s %-8s %s\n' "-------" "------" "------"
for r in "${ROWS[@]}"; do
  IFS='|' read -r tool covers install <<<"$r"
  if have "$tool"; then printf '  %-13s \033[32m%-8s\033[0m %s\n' "$tool" "present" "$covers"; PRESENT+=("$tool")
  else printf '  %-13s \033[33m%-8s\033[0m %s\n' "$tool" "MISSING" "$covers"; MISSING+=("$tool"); MISSING_INSTALL+=("$install"); fi
done

echo
if [ ${#MISSING[@]} -gt 0 ]; then
  echo "  Missing → those lenses run AGENT-ONLY (lower precision on CVEs/known-malware/IaC)."
  echo "  Install all missing with:  /deep-security --setup   (or per-tool below)"
  for i in "${!MISSING[@]}"; do printf '    - %-13s %s\n' "${MISSING[$i]}" "${MISSING_INSTALL[$i]}"; done
fi
echo
echo "PRESENT=$(IFS=,; echo "${PRESENT[*]}")"
echo "MISSING=$(IFS=,; echo "${MISSING[*]}")"
