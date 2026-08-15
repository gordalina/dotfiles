# Orchestration contract

## Why hybrid + verification
Free scanners ≈30–55% of Coverity/Sonar security recall; the gap is cross-function/cross-file taint. AI lens agents recover it. False positives are the #1 SAST trust-killer, so **every** candidate finding (scanner OR agent) passes an adversarial-verification stage before it reaches the report.

## Lens roster (full = all 10; diff = ⊕-marked subset)

| key | lens | OWASP focus | diff? |
|---|---|---|---|
| `access-control` | Access Control & Auth | A01/A07 | ⊕ |
| `auth-integration` | OAuth / OIDC Auth Integration | A01/A07 (redirect_uri, state/CSRF, PKCE, id_token/nonce, token & session handling) | ⊕ |
| `injection` | Injection & Input Handling | A03/A05:2025 | ⊕ |
| `secrets-crypto` | Secrets & Cryptography | A02/A04:2025 | ⊕ |
| `dependencies` | Dependencies & Supply Chain | A06/A03:2025 | |
| `infra-iac` | Infra / IaC / Container | A05/A02:2025 | |
| `data-exposure` | Data Exposure & Logging | A09/A04 | ⊕ |
| `ssrf-dataflow` | SSRF & code-defect dataflow | A10/A01:2025 | |
| `llm-security` | LLM / AI-app security | **OWASP LLM Top 10:2025** (prompt injection, excessive agency, output handling) | ⊕ |
| `database-security` | Data-layer security | A01 (tenant/row isolation, soft-delete leaks), A03/A05 (deep SQLi), A02/A04 (data-at-rest); Alembic migration safety, RLS/grants, ORM mass-assignment | ⊕ |

`database-security` owns the persistence layer (crud/db/models/migrations) — tenant isolation, soft-delete read leaks, migration safety, least-privilege/RLS, ORM mass-assignment. Essential for multi-tenant DB apps; auto-include when the repo has a DB layer (grep `crud`/`models`/`alembic`/`session.execute`/`sa.text`). `llm-security` is essential for agentic/LLM codebases (prompt injection, tool misuse) — the web Top 10 doesn't cover it. Auto-include it when the repo has LLM/agent code (grep `prompt`/`tool`/`llm`/`agent`/`messages`/`retriev`); `--skip llm-security` to drop it on a non-AI repo. `--skip <key>` drops any lens. A lens whose backing scanner is unavailable still runs (semantic-only, flagged in the report).

## Workflow I/O contract (`workflows/deep-security.workflow.js`)

**args in:**
```jsonc
{
  "mode": "full|diff",
  "scope": { "paths": ["..."], "diffRange": "main...HEAD", "changedFile": "OUT/changed.json" },
  "owaspEdition": "2025|2021",
  "scannerFindings": [ /* Finding[] from sarif_to_findings.py */ ],
  "lenses": [ { "key": "injection", "prompt": "<agents/injection.md contents>" }, ... ],
  "verifierPrompt": "<agents/verifier.md>",
  "synthesisPrompt": "<agents/synthesis.md>"
}
```

**pipeline:**
1. **Lens fan-out** (parallel) — each lens agent gets `prompt + scope + the scannerFindings already in its area` (so it focuses on what scanners can't reach). Model: full→Opus, diff→Sonnet. Returns `Finding[]` (schema-validated; `cwe` required).
2. **Merge + dedup** (JS, in-workflow) — union scannerFindings + all lens findings; dedup by `(file, line±3, cwe/class)`; agreement-boost confidence; set `source_kind`.
3. **Adversarial verify** (severity-tiered, per finding):
   - Critical/High → **3 Opus skeptics**, each prompted to *refute*; drop if ≥2 refute. `verified=true`, note the vote.
   - Medium → **1 Sonnet skeptic**; drop if refuted.
   - Low/Info → **skip** (ship with `verified=false`, raw confidence).
4. **Synthesis** — one agent over survivors → `summary` (counts by severity, go/no-go verdict, top themes, new-vs-standing if diff).

**returns:** `{ findings: Finding[], summary: {...} }`

The main agent (SKILL.md) does all deterministic shell (scanners, normalization, rendering) — the Workflow does only the agent work. Workflow scripts have no filesystem, so prompts/scanner-findings are passed via `args`.

## Model routing (D11)
- Lens agents: **Opus** (full) / Sonnet (diff). Verification: Critical/High→Opus, Medium→Sonnet, Low/Info→skip. Synthesis: Opus (full)/Sonnet (diff). Quick inline: **Haiku**.
- Recommend operator `/fast` for Opus-heavy full runs.

## quick-gating
After merge (no Workflow in quick): a finding **blocks the commit** iff `severity=="Critical" && is_new==true`. Print blockers with file:line + remediation, **exit non-zero**. New High/Medium → warn, exit 0. Pre-existing (is_new=false) → report, never block.
