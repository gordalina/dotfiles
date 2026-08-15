# deep-security

Multi-angle security review skill. **FOSS scanners + parallel AI lens agents → one normalized, adversarially-verified findings set → `findings.json` (LLM-first) + a designed `report.html`.** Sibling to `deep-review`, specialized and deeper for security; complements (doesn't duplicate) the built-in `/security-review`.

## Why
Free SAST (Opengrep/Semgrep) reaches only ~30–55% of commercial Coverity/Sonar on security — the gap is cross-function/cross-file taint. The AI lens agents recover that; the scanners carry the high-precision mechanical load (CVEs, secrets, IaC, known-malicious packages). Every candidate finding is adversarially verified (skeptics try to refute it) to kill the false positives that make SAST untrustworthy.

## Use
```
/deep-security                 # diff mode: working staged+unstaged changes
/deep-security backend/foundry # full audit of a path
/deep-security 1560            # diff mode on PR #1560
/deep-security --quick         # fast pre-commit gate (blocks on NEW Criticals)
/deep-security --full          # force whole-repo audit
/deep-security --setup         # install the FOSS scanner kit
/deep-security --install-hook  # wire the quick gate into pre-commit (explicit)
```
Flags: `--owasp 2021` (default 2025) · `--socket` (cloud npm supply-chain) · `--no-egress` (local GuardDog) · `--skip <lens>` · `--editor zed`.

## Modes
| mode | scope | output | gate |
|---|---|---|---|
| quick | staged hunks | terminal | blocks commit on **new** Critical |
| diff | branch/PR diff | findings.json + report.html | none |
| full | path / whole repo | findings.json + report.html | none |

## Running headless / in CI
The Claude Code orchestration (`workflows/*.workflow.js`) only runs inside the Claude Code Workflow runtime. For CI or any non-interactive use, **`run_ci.py`** is a stdlib-only port that drives the whole pipeline (scanners → scanner-triage → lens fan-out → adversarial verify → synthesis → render) via headless `claude -p`:
```
python run_ci.py --mode pr   --diff-range origin/main...HEAD   # diff-scoped, Sonnet
python run_ci.py --mode full --scope backend                   # whole-path audit, Opus
python run_ci.py --mode full --dry-run                         # wire-test, no claude calls
```
It writes `findings.json`, `report.html`, `summary.json`, a GFM `comment.md`, and `telemetry.json` (per-run cost) to `--out`. **Security:** run it with **only** `ANTHROPIC_API_KEY` in the environment — the lens agents read untrusted code and run with a `Bash/Write/Edit/web` tool denylist, so a prompt-injection in scanned code can't run a shell or exfiltrate the key. `ci_install_scanners.sh` provisions the kit on Linux from pinned release binaries. See the K&E repo's `.github/actions/deep-security/` for the composite-action + workflow wiring (per-PR gate + weekly delta-first Slack audit + findings store; `delta.py` + `build_slack_payload.py` + `publish_findings.sh` support the weekly).

## Output
Written to `./.deep-security/run-<timestamp>/`:
- **`findings.json`** — canonical, LLM-first. Point an agent at it to remediate.
- **`report.html`** — self-contained (no CDN), severity tiles, OWASP coverage matrix (2025 default, 2021 toggle), "Work performed" audit trail, filterable findings, editor deep-links on every `file:line`, copy-fix-prompt buttons, light/dark. Embeds the same data as a JSON island so an LLM can read the HTML directly.

## Layout
- `SKILL.md` — orchestrator (the agent reads this)
- `run_ci.py` — headless/CI orchestrator (the `.workflow.js` port; see *Running headless / in CI*)
- `agents/` — 10 lens prompts (7 web OWASP + **`auth-integration`** for the OAuth/OIDC login flow (redirect_uri, state/CSRF, PKCE, id_token/nonce, token & session handling) + **`llm-security`** for the OWASP **LLM** Top 10 + **`database-security`** for the persistence layer: tenant isolation, soft-delete leaks, migration safety) + verifier + scanner-triage + synthesis + quick
- `scripts/` — `setup.sh` / `ci_install_scanners.sh` (kit install: dev / CI), `run_scanners.sh`, `sarif_to_findings.py`, `group_scanner_rules.py` + `apply_triage.py` (scanner triage), `merge_findings.py`, `summarize_findings.py`, `render_report.py`, `delta.py` + `build_slack_payload.py` + `publish_findings.sh` (weekly CI), `install_hook.sh`, `cwe_owasp_map.json`
- `workflows/deep-security.workflow.js` — fan-out → merge/dedup → verify → synthesize (Claude Code runtime; `run_ci.py` is the portable equivalent)
- `reference/` — toolset, finding schema, orchestration contract
- `DESIGN.md` — full decision record (D1–D14)

## Toolset (all free for private corporate use)
Opengrep · Trivy (pin!) · Gitleaks (binary) · Checkov · Bandit · gosec · govulncheck · OSV-Scanner · Socket/GuardDog (npm). Coverity/CodeQL/SonarQube are **not** free for private code — the lens agents recover what they'd catch. See `reference/toolset.md`.

## Notes
- Never fabricates CVSS (passthrough from advisories only). Severity is an editorial 5-level scale. OWASP categories are derived from CWE.
- Missing scanners never block — the matching lens covers that surface semantically and the report flags it.
- For Opus-heavy `full` runs, enable Claude Code fast mode (`/fast`).
