---
name: deep-security
description: Multi-angle security review. Runs free FOSS scanners (Opengrep, Trivy, Gitleaks, Checkov, Bandit, gosec, govulncheck, OSV-Scanner, optional Socket) plus parallel AI lens agents across the OWASP Top 10, adversarially verifies every finding to cut false positives, and emits a canonical findings.json (LLM-first) and a self-contained, severity-ranked HTML report with editor deep-links. Three modes — quick (pre-commit gate on new Criticals), diff (PR/branch), full (codebase audit, the flagship). Use when the user wants a security audit, vulnerability scan, OWASP review, supply-chain/dependency check, secret scan, IaC/k8s misconfig review, a pre-commit security guardrail, or invokes /deep-security.
---

# deep-security

Hybrid security review: **deterministic FOSS scanners + parallel AI lens agents → one normalized, adversarially-verified findings set → `findings.json` (LLM-first) + a designed `report.html`**. Sibling to `deep-review`, specialized and deeper for security.

> Free scanners alone reach only ~30–55% of commercial SAST (Coverity/Sonar) on security; the AI lens agents recover the cross-function/cross-file taint the free engines structurally miss. Scanners = high-precision mechanical load. Agents = semantic depth. Verification = noise control.

## Invocation

```
/deep-security [target] [flags]
```
- **target:** *(none)* → `diff` (working staged+unstaged) · `<path>` → `full` audit of that path · `<PR num/URL>` → `diff` on that PR
- **flags:** `--quick` (pre-commit gate) · `--full` (force whole-repo) · `--owasp 2021` (default 2025) · `--socket` (cloud npm supply-chain) · `--no-egress` (GuardDog, local) · `--skip <lens>` (repeatable) · `--editor zed` (default vscode) · `--setup` (install toolkit) · `--install-hook` (pre-commit wiring)

`SKILL_DIR` below = this skill's directory.

## Modes

| | scope | agents | verification | output | gating |
|---|---|---|---|---|---|
| **quick** | staged hunks | 1 inline (Haiku) | none | terminal | block commit on **new** Critical |
| **diff** | branch/PR diff | lens subset (Sonnet) | single pass | findings.json + report.html | none |
| **full** | path / whole repo (Opus) | 10 lenses | severity-tiered adversarial | findings.json + report.html | none |

## Execution

**Step 0 — Parse** target/flags → `MODE`, `SCOPE` (paths or diff range), `OWASP_EDITION` (default 2025), `EGRESS` (socket|local|off), `EDITOR` (vscode|zed), `SKIPPED`.

**Step 1 — Handle setup flags (and return):**
- `--setup` → run `bash SKILL_DIR/scripts/setup.sh`; report installed/failed; stop.
- `--install-hook` → run `bash SKILL_DIR/scripts/install_hook.sh`; it detects the repo's framework, shows the diff, confirms; stop.

**Step 2 — Compute scope & changed lines:**
- `quick` → `git diff --cached --name-only` + unified hunks → write changed-lines map to `OUT/changed.json`.
- `diff` → diff vs merge-base (or PR diff) → `OUT/changed.json`.
- `full` → target path (or repo root); no changed-lines map (`is_new` omitted, see DESIGN D13).
- `OUT = ./.deep-security/run-<ISO8601>/` (create it; ensure `./.deep-security/` is gitignored — add it if missing).

**Step 2.5 — Tool preflight & confirm (diff/full — do this BEFORE scanning):**
Run `bash SKILL_DIR/scripts/preflight.sh "<EGRESS>"` and **relay the present/missing table to the user**. If any scanners are MISSING, **stop and ask** whether to install them (offer `--setup`, ~a few minutes) or proceed degraded (those lenses run agent-only, lower precision). Do NOT silently proceed with missing scanners — surfacing this up front lets the user get full coverage on the first pass. Only continue once they choose. (Skip this gate for `quick` — it's non-interactive, runs whatever's present, never installs.)

**Step 3 — Run scanners (deterministic):**
`bash SKILL_DIR/scripts/run_scanners.sh "<SCOPE>" "<OUT/sarif>" "<MODE>" "<EGRESS>"` → SARIF per tool + a `skipped.json` of unavailable tools (with install commands). `quick` runs only the fast staged-diff subset (Gitleaks on staged content, Opengrep on changed files); it must NOT re-run heavy scanners the repo's pre-push/CI already does.

**Step 4 — Normalize scanner output:**
`python3 SKILL_DIR/scripts/sarif_to_findings.py --sarif-dir OUT/sarif --changed OUT/changed.json --owasp-map SKILL_DIR/scripts/cwe_owasp_map.json --out OUT/scanner_findings.json`

**Step 4.5 — Scanner triage (verify scanner findings by rule-class — diff/full):**
Scanner findings ship UNVERIFIED and are noisy/mis-severitied; verify them cheaply by rule-class (not per-finding). `python3 SKILL_DIR/scripts/group_scanner_rules.py --findings OUT/scanner_findings.json --out OUT/rule_groups.json` collapses ~1000 findings → ~100–150 rule-classes. Then run the triage Workflow:
  `Workflow({ scriptPath: "SKILL_DIR/workflows/scanner-triage.workflow.js", args: { rulesPath: "<abs OUT/rule_groups.json>", total: <N>, batchSize: 12, model: "sonnet", triageSpecPath: "<abs SKILL_DIR/agents/scanner-triage.md>" } })`
Save its `verdicts` to `OUT/verdicts.json`, then `python3 SKILL_DIR/scripts/apply_triage.py --findings OUT/scanner_findings.json --verdicts OUT/verdicts.json --out OUT/scanner_findings.json`. Each scanner finding becomes `confirmed` (verified=true) / `dismissed` (noise, hidden by default) / `adjust` (severity corrected) / `context_dependent` (needs-review). This is what makes scanner Criticals/Highs trustworthy — confirmed ones can drive the verdict; dismissed noise drops out. ~8–12 cheap Sonnet calls for the whole surface. Can run in parallel with Step 5 (independent).

**Step 5 — Agent analysis + verification:**
- **quick:** dispatch ONE Haiku agent (use `agents/quick.md` as its prompt) over the staged hunks → fast findings. Merge with scanner findings. No Workflow.
- **diff / full:** read the relevant `agents/*.md` lens prompts (full = all 10; diff = the ⊕-subset in orchestration.md). **Always include `llm-security` when the repo has LLM/agent code** (prompt injection + excessive agency) and **`database-security` when the repo has a persistence layer** (tenant isolation, soft-delete leaks, migration safety) — both are otherwise uncovered. For each lens, build its prompt as `agents/_output-contract.md` + the lens body. Also read `agents/verifier.md` and `agents/synthesis.md`. Invoke the Workflow:
  `Workflow({ scriptPath: "SKILL_DIR/workflows/deep-security.workflow.js", args: { mode, scope, owaspEdition, scannerFindings: <contents of OUT/scanner_findings.json>, lenses: [{key,prompt}…], verifierPrompt, synthesisPrompt } })`
  The workflow fans out lens agents (full → Opus; diff → Sonnet), merges+dedups with scanner findings (agreement-boost), adversarially verifies (Critical/High→Opus·3 skeptics; Medium→Sonnet·1; Low/Info→skip), synthesizes, and returns `{ findings, summary }`.
- See [reference/orchestration.md](reference/orchestration.md) for the full contract.

**Step 5.5 — Run telemetry (cost + timer + funnel):**
Record a wall-clock start at Step 2 and per-phase durations (scan, lenses+verify, render). Build `OUT/telemetry.json` = `{phases:[{name,seconds}], usage:[{stage,model,input,output}], funnel:{candidates,verified,refuted}, coverage:{...}}`. Pull `usage` and the funnel from the Workflow result's `usage` + `logs` ("N candidate findings", "M survived verification"); scanners are free (no usage). Then `python3 SKILL_DIR/scripts/run_summary.py --telemetry OUT/telemetry.json --out OUT/run_summary.json` and merge `run_summary.json` into `meta.run_summary` so the report renders the Run-summary panel. Cost is an estimate (Opus $5/$25, Sonnet $3/$15, Haiku $1/$5 per MTok; fast mode = faster output, same price; Opus 1M context has no long-context premium). Print the cost + wall-clock to the user.

**Step 6 — Finalize & render:**
- Write the verified findings to `OUT/findings.json` (canonical schema, see [reference/finding-schema.md](reference/finding-schema.md)). For `full`, merge scanner + verified-agent findings with `scripts/merge_findings.py --owasp-map …` (scanner findings bypass per-finding adversarial verification; agent findings arrive verified).
- **Build the WHOLE-SURFACE summary** (don't use the agent-only synthesis as the top-level summary — it only saw the AI findings and will contradict the merged counts): `python3 SKILL_DIR/scripts/summarize_findings.py --findings OUT/findings.json --ai-summary OUT/synthesis_summary.json --ran OUT/sarif/ran.json --skipped OUT/sarif/skipped.json --out OUT/summary.json`, then set `meta.summary = OUT/summary.json`. This computes counts/verdict/by-tool/by-OWASP/source-split over the merged set; the agent synthesis is demoted to `ai_highlights` (clearly scoped). Verdict honesty: a hard **block requires a VERIFIED Critical**; unverified scanner Criticals/Highs are surfaced but flagged (scanner severity is often inflated — e.g. trivy rating a Dockerfile COPY-syntax rule Critical).
- `diff`/`full`: `python3 SKILL_DIR/scripts/render_report.py --findings OUT/findings.json --owasp-map SKILL_DIR/scripts/cwe_owasp_map.json --owasp-default <2025|2021> --editor <vscode|zed> --skipped OUT/sarif/skipped.json --meta OUT/meta.json --out OUT/report.html`
- Print the absolute paths to `findings.json` and `report.html`.

**Step 7 — Gate (quick only):** if any finding has `severity == Critical` AND `is_new == true`, print them and **exit non-zero** (blocks the commit). Otherwise warn on new High/Medium and exit 0. See [reference/orchestration.md](reference/orchestration.md#quick-gating).

## Operator notes
- For Opus-heavy `full` runs, recommend the operator enable Claude Code **fast mode** (`/fast`) — faster Opus output; the team is OK with it. (Session toggle, not a per-agent param.)
- Missing scanners never block: the matching lens agent covers that surface semantically and the report flags it (lower CVE precision). See [reference/toolset.md](reference/toolset.md).
- **Never fabricate a CVSS score.** CVSS is passthrough-only from authoritative advisories. Severity is our editorial 5-level scale. CWE/OWASP are taxonomies we assign; OWASP categories are **derived from CWE**.

## Reference
- [reference/toolset.md](reference/toolset.md) — scanners, install, SARIF flags, version pins, licensing
- [reference/finding-schema.md](reference/finding-schema.md) — canonical Finding, severity normalization, dedup, CWE→OWASP
- [reference/orchestration.md](reference/orchestration.md) — Workflow contract, model routing, gating
- [DESIGN.md](DESIGN.md) — full decision record (D1–D14)
