---
date: 2026-06-18
tags: [claude-skills, security, owasp, sast, design]
status: active
type: project
project: claude-skills
agent-written: true
---

# deep-security — Skill Design

> Name: **deep-security** (sibling to `deep-review`; distinct from the built-in `/security-review`).
>
> Multi-angle security review skill: deterministic FOSS scanners + parallel AI-agent lenses → one normalized findings set → severity-ranked, OWASP-tagged HTML report. Designed in a `grill-with-docs` session on 2026-06-18.
>
> *Sources: this design session; two FOSS-security research passes (2026-06-18) — see Provenance.*

## Decisions

### D1 — Three modes
- **`quick`** — pre-commit guardrail. Fast, high-level, scoped to staged changes. Terminal output, no HTML. **Blocks the commit only on NEW Critical findings on added/modified lines** (see D5). Never installs tools, never blocks on a missing tool.
- **`diff`** — PR/branch scope. Medium depth. Findings scoped to the changed set.
- **`full`** — codebase / subsystem audit. Deep, slow-is-OK. Produces the flagship **HTML report**. Reports standing debt; complements (does not duplicate) `deep-review`.

Switchable via invocation (target/flag). Default behavior TBD in naming/invocation section.

### D2 — Hybrid decomposition (attack-surface agents, multi-axis tags)
Agents organized by **attack surface / discipline** (tight, non-overlapping hunting grounds), every finding **tagged with OWASP Top 10 category + tool/provenance**. The Finding is the single source of truth; the HTML report pivots on any axis (OWASP matrix, by-tool, by-severity).

Proposed `full` lens roster (parallel sub-agents):
1. Access Control & Auth (A01/A07) — authz gaps, IDOR, session/JWT
2. Injection & Input Handling (A03) — SQLi, XSS, command/path/template injection, deserialization
3. Secrets & Cryptography (A02) — hardcoded secrets, weak crypto, TLS, key lifecycle
4. Dependencies & Supply Chain (A06) — CVEs, malicious packages, lockfile integrity
5. Infra / IaC / Container (A05) — k8s/kustomize, Dockerfiles, Helm, ARM misconfig
6. Data Exposure & Logging (A09/A04) — PII/secrets in logs, sensitive data, error leakage
7. SSRF & External Calls (A10) + code-defect/dataflow lens (taint, resource leaks, concurrency)

`quick`/`diff` run a subset.

### D3 — Hybrid: FOSS scanners + agents
Agents are NOT decoration: free Semgrep CE reaches only **~30–40%** of Coverity/Sonar security detection (~**45–55%** with Opengrep). The missing ~50–60% is **inter-procedural / cross-file taint** — exactly what the AI agents recover. Scanners carry mechanical/pattern load at high precision; agents carry semantic cross-function taint.

**Default FOSS toolset** (all free for private corporate use, mostly SARIF-native, single-binary):

| Tool | Role | Notes |
|---|---|---|
| **Opengrep** (Semgrep fork) | cross-lang SAST (Py/TS/Go) | preferred over Semgrep CE — free intra-file cross-function taint |
| **Trivy** *(PIN version, verify sig)* | SCA + IaC + container + Dockerfile + k8s + ARM | compromised twice in 2026 — never `@latest` |
| **Checkov** | IaC depth incl. Azure Bicep/ARM | |
| **Gitleaks** *(binary, NOT the Action)* | secrets | Action is paid for Org accounts; binary stays MIT |
| **Bandit** + **gosec** | Python / Go native SAST depth | |
| **govulncheck** | Go deps w/ reachability | needs JSON→SARIF shim |
| **OSV-Scanner** | deps incl. malicious-package feeds | |
| **Socket** *(`--socket`)* | npm supply-chain / malware | cloud (egress to Socket API). Egress OK — Tribe code on Tribe tooling. Free tier: 1k scans/mo, 3 members |
| **GuardDog** *(optional, local)* | npm/PyPI malware, no egress | fallback for no-egress contexts |

**Dropped (not free for private code):** Coverity (Scan = OSS-only), CodeQL (prohibits private repos w/o paid GHAS), SonarQube (Community is server-based + advanced SAST paywalled).

### D4 — Tool availability: setup script + graceful runtime
- One-time `--setup` / install script provisions the kit (version-pinned, signature-checked).
- Runtime always **degrades gracefully**: missing scanner → the corresponding agent lens covers it semantically + report flags "X not run — install with `…`; covered by agent-only (lower CVE precision)."
- `quick` runs only already-installed fast scanners + one lightweight agent; never installs, never blocks on missing tools.

### D5 — Diff-aware gating
- `quick` blocks the commit **only on NEW Critical findings on added/modified lines** (intersect findings with staged hunks vs baseline).
- Pre-existing standing Criticals in untouched code do **not** block (no punishment for inherited debt) — they're reported in `full`.

### D6 — Unified Finding schema
One canonical `Finding` record; **SARIF is the ingestion format** (one normalizer for all SARIF tools), JSON shims for the few that don't emit SARIF (govulncheck, pip-audit). Agents emit the Finding shape directly as JSON.

```
Finding {
  id                 # stable hash (file, line, rule/class) for dedup
  title, description, remediation
  severity           # NORMALIZED 5-level: Critical | High | Medium | Low | Info (D7)
  confidence         # 0–10 (agents self-score; scanners fixed-mapped)
  cwe                # LOAD-BEARING durable key (see D8). Agents/scanners must assign a CWE.
  owasp_2021         # DERIVED from cwe via mapping table (default render)
  owasp_2025         # DERIVED from cwe via mapping table (opt-in: --owasp 2025, RC)
  cvss_from_advisory # PASSTHROUGH only, for CVE findings, attributed to NVD/advisory. NEVER fabricated.
  tool               # provenance: "trivy" | "opengrep" | "gitleaks" | "AI:injection-agent"
  source_kind        # "scanner" | "agent"
  file, line
  is_new             # on added/modified lines vs baseline (drives D5 gating)
  dedup_group        # same issue from multiple sources collapses here
}
```

- **Severity normalization:** deterministic per-tool table → 5 levels. Agents told to use the same scale.
- **Dedup with agreement-boost:** scanner + agent flag the same line → collapse to one Finding showing both provenances, confidence boosted ("confirmed by scanner + agent"). Agent-only finding (scanner couldn't follow taint) stands alone at its own confidence. Dedup key = (file, nearest-line within tolerance window, OWASP/CWE class).
- **No fabricated CVSS.** Our severity is editorial and labeled as ours; CVSS only ever passed through from authoritative advisories. CWE/OWASP are classification taxonomies we assign — legitimate.

### D7 — Severity scale: 5 levels
Critical / High / Medium / Low / Info. Finer than `deep-review`'s 3 levels because a standing security report needs the triage resolution and it aligns with native scanner/CVSS scales.

### D8 — OWASP version: CWE-as-durable-key, default to latest (2025)
- 2025 is **RC1**; 2021 is the last ratified-final edition. User wants **latest**.
- Tag each finding on **CWE** (durable). **Derive** OWASP category from CWE via a mapping table.
- **Default render 2025** (latest, what user asked for); **2021 available as a toggle / `--owasp 2021`** for auditors cross-referencing the last final edition. CWE-as-key means edition is a pure render choice — zero re-tagging if RC categories shift at ratification.
- 2025 structural changes that matter here: SSRF folded into A01; new **A03 Software Supply Chain Failures** (Socket/Trivy lens); new **A10 Mishandling of Exceptional Conditions**.

### D9 — Dual-artifact report (LLM-first + developer-facing)
Two consumers: the developer (must act) and an LLM (must act programmatically). So emit **two artifacts**, same data:
- **`findings.json`** — canonical machine artifact (the D6 Finding records). LLM-first: an agent reads this to remediate; never parses HTML.
- **`report.html`** — self-contained (inline CSS/JS, no CDN/network), well-designed human view. **Embeds identical data** as `<script type="application/json" id="findings">` island, so an LLM can extract full structured data from the HTML alone with one selector — no DOM scraping. Visual layer renders from the island.

HTML features:
- **Editor deep-links** on every `file:line` — default `vscode://file/<abs>:<line>`; `--editor zed` → `zed://file/…`. Visible text stays `path:line` (copy-pasteable).
- Sections: header (repo/scope/SHA/timestamp) → exec summary (5-level severity rollup tiles + go/no-go + new-vs-existing split) → **"Work performed"** (scanners run + versions, skipped + why + install cmd, agent lenses, files/LOC, wall-clock — the audit-trust section) → **OWASP coverage matrix** (default 2025, toggle 2021) → findings table (sort/filter/search by severity/OWASP/tool/file/new) → per-finding cards (snippet w/ highlighted line, remediation steps, provenance badges + agreement boost, confidence, CWE/OWASP, CVSS-from-advisory) → methodology/provenance footer (tool versions, OWASP edition, AI-advisory disclaimer).
- **Copy buttons**: copy `file:line`; copy a ready-to-paste "fix-prompt" for an agent to remediate that finding.
- Pure vanilla JS client-side filter/sort/search/pivot. Light/dark. Clean type (Inter/system-ui + mono for code), severity color system.

Per mode: **`quick` = terminal only**; **`diff` + `full` = both artifacts** (findings.json + report.html).

Output location: `./.deep-security/` (gitignore one dir; keeps run history); print absolute path on completion.

### D10 — Mode-scaled orchestration + adversarial verification
False positives are the #1 SAST trust-killer. Every candidate finding (scanner OR agent) passes through an **adversarial-verification stage** — independent skeptic agents prompted to *refute*; drop on majority-refute. Pairs with agreement-boost dedup (scanner+agent concurrence ↑ confidence; refute ↓).
- **`full`** → **Workflow**: scanners + 7 lens agents → adversarial verify each finding (≈3 skeptics, drop on majority-refute) → synthesis → dual artifacts. Thorough, low-noise, slow-OK.
- **`diff`** → lighter Workflow (or Agent fan-out): lens subset, single verification pass → dual artifacts.
- **`quick`** → **no Workflow/fan-out**: fast scanners on staged hunks + one inline lightweight agent → terminal, gate on new Criticals. Speed first.
A skill may invoke Workflow — invoking the skill is the opt-in.

### D11 — Model routing (Opus for depth, Haiku for fast)
- **Lens agents (complex taint/dataflow analysis): pinned Opus** — guaranteed depth on the cross-function vulns scanners miss.
- **Verification skeptics: severity-tiered** — Critical/High → Opus; Medium → Sonnet; **Low/Info → skip verification** (ship with raw confidence + "unverified" tag).
- **Synthesis:** Opus on `full` (reasons over the whole finding set), Sonnet acceptable on `diff`.
- **Fast checks / `quick` inline agent: Haiku.**
- **Fast mode:** recommend running the session with Claude Code fast mode (`/fast`, Opus-only faster output; team OK with it) for Opus-heavy `full` runs. NB: fast mode is a session-level toggle, NOT a per-subagent/Workflow param — skill documents it as an operator recommendation, can't pin it per-agent.

### D12 — Setup & hook integration (framework-aware, explicit)
- **`--setup`** provisions the scanner toolkit only (version-pinned, signature-checked). Repeatable/discoverable.
- **`--install-hook`** is a SEPARATE explicit opt-in. Framework-aware: appends a `deep-security --quick` entry to `.pre-commit-config.yaml` where present (K&E case — the native idiom), Husky if `.husky/`, else a raw `.git/hooks/pre-commit` shim. Always shows the diff + confirms; never silent, never auto-on.
- `quick` deliberately **avoids re-running scanners the repo's pre-push/CI already runs** (K&E runs Trivy in pre-push). Focuses on fast staged-diff checks: Gitleaks on staged content, Opengrep on changed files, new-Critical gating. Heavy SCA/IaC stays in pre-push/CI. No double-scanning; commits stay snappy.

### D13 — `is_new` scope: quick/diff only
- `is_new` is a per-finding label (did the change introduce it vs pre-existing standing debt), NOT a scope limiter. Scope is set by mode.
- **quick/diff:** git diff is the baseline — `is_new=true` iff finding sits on an added/modified line. No stored state. Drives D5 gating + the report's new-vs-standing split.
- **full:** everything is standing — **`is_new` omitted/N-A**. Becomes meaningful only with optional baseline-vs-last-run comparison → **deferred to v1.1**.

### D14 — Invocation grammar
```
/deep-security [target] [flags]
target:  (none)→diff (working staged+unstaged) | <path>→full audit | <PR num/URL>→diff on PR
flags:   --quick        pre-commit mode (fast, gates on new Criticals)
         --full         force full audit (whole repo)
         --owasp 2021   render 2021 categories (default 2025)
         --socket       enable Socket npm supply-chain (cloud egress)
         --no-egress    local-only (GuardDog instead of Socket)
         --skip <lens>  omit a lens agent (repeatable)
         --editor zed   editor deep-link scheme (default vscode)
         --setup        provision scanner toolkit
         --install-hook framework-aware pre-commit wiring (explicit, shows diff)
```
Default (no target) = **diff** (safe/cheap/frequent); path promotes to **full**; `--quick` = pre-commit. `full` is the flagship but reached deliberately, not by default.

## Status
**Built + smoke-tested (2026-06-18).** All 14 decisions implemented: SKILL.md, 7 lens agents + verifier + synthesis + quick, scripts (setup/run_scanners/sarif_to_findings/render_report/install_hook/cwe_owasp_map), Workflow orchestration, reference docs, README. Deterministic pipeline verified end-to-end (SARIF→findings.json→report.html: severity mapping, CWE extraction, OWASP 2025-derived, CVSS passthrough, is_new). Agent/Workflow paths exercised at runtime. Live via the `~/.claude/skills` symlink.

## Lessons from first live run (2026-06-18, against `main`)
Real audit surfaced and fixed several gaps — all now in the skill:
1. **Workflow `args` arrives as a JSON STRING**, not an object. Confirmed via diag (`typeof args = string`). Fixed: workflow parses `args` defensively. First run silently produced 0 findings because `A.lenses` was undefined → no lens agents spawned. *(Watch for this in any Workflow-invoking skill.)*
2. **Scanner scope must exclude vendored/nested dirs.** First trivy run scanned `.claude/worktrees/*` + `node_modules` + `vendor` → 4866+1318 inflated/duplicated findings. Fixed: `run_scanners.sh` now defaults `--skip-dirs .claude,node_modules,vendor,.git,data,…` First-party rescan → 245 misconfig + 45 vuln (sane).
3. **Drop trivy's `secret` scanner** — gitleaks covers secrets; trivy secret over a whole repo is the slow part that made the first run appear to hang/emit nothing. Fixed.
4. **Scanners often emit no explicit CWE** → everything mapped "Unmapped". Fixed: `fallback_cwe()` (gitleaks→CWE-798, trivy-CVE→CWE-1395, trivy-misconfig→CWE-16). OWASP now derives.
5. **Adversarial verification doesn't scale to raw scanner volume** (~170 High/Crit × 3 Opus skeptics ≈ 500 calls). Refinement: **scanner findings (deterministic, tool-confirmed) bypass per-finding verification; only AGENT findings are verified**, then `merge_findings.py` combines (agreement-boost). Orchestrator passes `scannerFindings:[]` to the Workflow for large repos. *(v1.1: batch-verify scanner Criticals cheaply — trivy over-rated a Dockerfile COPY-syntax rule as Critical, so scanner severity alone shouldn't drive the block verdict.)*

## D15 — LLM / AI-application security lens (8th lens)
Added `agents/llm-security.md` covering the **OWASP LLM Top 10:2025** — the target is an agentic LLM app (Foundry), and the web Top 10 structurally misses its defining risks: **LLM01 prompt injection (esp. indirect via tool/RAG/document content)** and **LLM06 excessive agency / tool misuse**, plus LLM05 (LLM output → dangerous sink), LLM02/07 (sensitive info / system-prompt leakage), LLM08 (RAG retrieval not tenant-scoped). Findings carry both a CWE (for dedup + web-OWASP derivation; CWE-1427 = prompt injection) and a direct `owasp_llm` tag. Wired through schema, render (badge + detail), summary (`by_owasp_llm_2025`), orchestration roster (auto-include when repo has LLM/agent code), and SKILL (full = 8 lenses). Identified as the #1 gap vs the 2026 tooling landscape for this target.

## D16 — Database-security lens (9th lens)
Added `agents/database-security.md` — owns the **persistence layer** (crud/db/models/Alembic migrations) for a multi-tenant Postgres app where **matter isolation IS the security model**. Covers: tenant/row-isolation leaks + **soft-delete read leaks** (data-layer IDOR, CWE-639/863/566), deep SQLi incl. dynamic identifiers/JSONB (CWE-89), **ORM mass-assignment** (CWE-915), **Alembic migration safety** (dropping constraints/RLS, broadening GRANTs, raw `op.execute`), least-privilege/RLS/`SECURITY DEFINER` (CWE-732/250/266), data-at-rest (CWE-312/311/256), DB TLS/query-log hygiene. Owns the data-layer findings the access-control/injection lenses previously caught as spillover (iManage IDOR, `crud.user.patch` mass-assignment). Wired through orchestration roster, SKILL (full = 9 lenses, auto-include when DB layer present), README, CWE map. Deterministic complement **squawk** (Postgres migration linter) documented but not yet wired (needs JSON→SARIF shim).

## Roadmap — runtime gaps beyond a static reviewer (gap research 2026-06-23)
`deep-security` is static (reads + reasons; never runs/attacks/observes). Real maturity gaps that need a runtime harness *alongside* it (prioritized for an agentic LLM app on Azure/AKS):
1. **LLM red-teaming (test-time):** PyRIT + promptfoo + Agentic Radar — dynamic prompt-injection/tool-misuse testing (complements the static D15 lens). FOSS.
2. **Validation-by-exploitation:** **Strix** (Apache-2.0) — sandboxed AI pentester that builds working PoCs; turns "looks risky" into proven/disproven. Low CI bolt-on (no running app needed), LLM-cost-bound.
3. **DAST + API fuzzing:** OWASP ZAP (API-scan from our OpenAPI) + Schemathesis — one staging/CI investment closes both.
4. **Live Azure/AKS CSPM:** Prowler + kube-bench/Kubescape — IaC scanning misses drift/deployed config.
5. Live secret verification: TruffleHog (verifies creds by live auth — gitleaks can't tell dead from live).
6. Longitudinal vuln-mgmt: Syft → Dependency-Track → DefectDojo (the time axis we lack).
- **Honest caveat:** no FOSS function-level **reachability SCA** exists for Python/JS in 2026 (Go-only); approximate via AI-assisted triage, don't promise a free tool.

## Deferred to v1.1
- `full` baseline-vs-last-run comparison (`--baseline`) for "new since last audit" trend tracking.
- Batch/cheap verification pass for scanner Criticals (don't trust raw scanner severity for the verdict).
- Wire the above scope-excludes + scanner-bypass-verification flow into `SKILL.md` step 5/6 as the default for `full`.
- Quick-mode baseline mechanics (how `is_new` is computed cheaply).
- Per-mode agent count, model routing, cost envelope.
- Pre-commit hook integration (auto-wire on `--setup`?).

## Provenance
- Design session: `grill-with-docs`, 2026-06-18.
- FOSS scanner landscape research (licensing verified against primary sources), 2026-06-18.
- Socket vs GuardDog + Semgrep/Coverity/Sonar parity research, 2026-06-18.
- Sibling skill reference: `deep-review` (parallel-agent + JSON-findings + synthesis pattern).
