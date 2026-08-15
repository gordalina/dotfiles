# Toolset — FOSS scanners

All free for **private commercial** use, mostly SARIF-native, single-binary installable. Verified 2026-06-18 (licensing against primary sources). `setup.sh` provisions these; `run_scanners.sh` runs whatever is installed and records the rest in `skipped.json`.

## Default kit

| Tool | Role | Install | SARIF out | License | Notes |
|---|---|---|---|---|---|
| **Opengrep** | cross-lang SAST (Py/TS/Go), intra-file cross-fn taint | `curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh \| bash` (NO homebrew tap) or release binary → `~/.local/bin` | `scan --sarif --output f.sarif` | LGPL-2.1 | Preferred over Semgrep CE (free taint). Rulesets: `--config auto` / p/owasp-top-ten |
| **Trivy** | SCA + IaC + container + Dockerfile + k8s + ARM + secrets | `brew install trivy` **at a PINNED version** | `--format sarif --output f.sarif` | Apache-2.0 | **Compromised twice in 2026 — never `@latest`.** Pin + verify checksum. `trivy fs` and `trivy config` |
| **Checkov** | IaC depth incl. Azure Bicep/ARM | `pipx install checkov` | `-o sarif` | Apache-2.0 | Best Azure coverage |
| **Gitleaks** | secrets | `brew install gitleaks` | `--report-format sarif --report-path f.sarif` | MIT | **Use the binary, NOT the GitHub Action** (Action is paid for Org accounts) |
| **Bandit** | Python SAST depth | `pipx install bandit` + `pipx inject bandit bandit-sarif-formatter` (NO native sarif) | `-ll -ii -f sarif -o f.sarif` | Apache-2.0 | run with `-ll -ii` (medium+ sev & confidence) — Low-everything is ~99% noise (asserts, try/except/pass) |
| **gosec** | Go SAST depth | `go install github.com/securego/gosec/v2/cmd/gosec@<pin>` | `-fmt sarif -out f.sarif` | Apache-2.0 | only if Go present |
| **govulncheck** | Go deps w/ reachability | `go install golang.org/x/vuln/cmd/govulncheck@<pin>` | **none** → JSON shim | BSD-3 | lowest FP for Go; `-json` → normalizer shim |
| **OSV-Scanner** | deps incl. malicious-package feeds | `brew install osv-scanner` | `--format sarif` | Apache-2.0 | Py/JS/Go lockfiles |

## Database / migration safety (optional, complements the `database-security` lens)

| Tool | Role | Install | SARIF | Notes |
|---|---|---|---|---|
| **squawk** | Postgres **migration linter** — unsafe/locking/destructive DDL, dropped constraints | `cargo install squawk` or release binary | **no** (JSON/GH only) | Deterministic complement to the `database-security` lens for Alembic migrations. **Not yet wired into `run_scanners.sh`** — needs a JSON→Finding shim (the lens covers migration safety semantically until then). |

## npm supply-chain (malicious, not just vulnerable)

CVE scanners (Trivy/OSV) catch *vulnerable* packages; these catch *malicious* ones (typosquats, install-script exfil, behavior changes).

| Tool | Trigger | Install | Egress | Notes |
|---|---|---|---|---|
| **Socket** | `--socket` | `npm i -g @socketsecurity/cli` (or `pipx install socketsecurity`) | **cloud** (sends manifests to Socket API) | Best npm coverage. MIT CLI, SARIF/JSON out. Free tier 1k scans/mo, 3 members. Needs `SOCKET_CLI_API_TOKEN`. Egress to Tribe-controlled tooling is approved |
| **GuardDog** | `--no-egress` (default local fallback) | `pipx install guarddog` | **none** (offline) | DataDog; Semgrep-rules + metadata heuristics. Use when egress not permitted |

## Dropped (NOT free for private code)
- **Coverity** — Coverity Scan is OSS-only; commercial is paid. Illegal on private corp code.
- **CodeQL** — license prohibits private/non-OSS repos without paid GitHub Advanced Security.
- **SonarQube** — Community Build is server-based (not a stdout CLI) and advanced taint SAST is paywalled.

The AI lens agents are how we recover what these would have caught (cross-function taint) — see [orchestration.md](orchestration.md).

## Graceful degradation
`run_scanners.sh` records every unavailable tool in `skipped.json` with its install command. The corresponding **lens agent covers that surface semantically** (lower precision on CVEs/known-malware) and `render_report.py` surfaces it in the "Work performed" section so coverage is never silently incomplete.

## Version pinning
`setup.sh` keeps a `PINS` table at the top of the script. **Trivy especially must be pinned** and checksum-verified. Bump pins deliberately, never float to `@latest`/`@master`.
