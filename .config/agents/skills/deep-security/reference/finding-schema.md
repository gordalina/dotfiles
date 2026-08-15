# Finding schema, severity, dedup, CWE→OWASP

The `Finding` is the single source of truth. Scanners (via SARIF) and agents both normalize into it. `findings.json` is an array of these; `report.html` embeds the identical array.

## Canonical Finding

```jsonc
{
  "id": "sha1(file:line:cwe:rule)",   // stable dedup id
  "title": "SQL query built via f-string from request param",
  "description": "…what & why, with the data flow…",
  "remediation": "Use parameterized queries / the ORM bound-param API.",
  "severity": "Critical|High|Medium|Low|Info",   // NORMALIZED 5-level, editorial (NOT CVSS)
  "confidence": 8,                                 // 0–10
  "cwe": "CWE-89",                                 // LOAD-BEARING durable key (required)
  "owasp_2021": "A03:2021-Injection",              // DERIVED from cwe
  "owasp_2025": "A05:2025-Injection",              // DERIVED from cwe
  "owasp_llm": "LLM01:2025-Prompt Injection",      // set DIRECTLY by the llm-security lens (OWASP LLM Top 10); null otherwise
  "cvss_from_advisory": null,                       // passthrough ONLY for CVE findings; never fabricated
  "tool": ["opengrep", "AI:injection"],            // provenance; >1 ⇒ agreement
  "source_kind": "scanner|agent|both",
  "file": "backend/foundry/src/db/crud/user.py",
  "line": 227,
  "is_new": true,                                   // quick/diff only; omit in full
  "verified": true,                                 // passed adversarial verification (agent) or rule-class triage=confirmed (scanner)
  "verification_note": "3/3 skeptics failed to refute; reproduces via /api/users?id=",
  "triage": "confirmed|dismissed|adjust|context_dependent|untriaged",  // scanner findings only (see triage below)
  "triage_note": "why the rule-class got this verdict",
  "dismissed": false,                               // triage=dismissed → noise; hidden by default, kept in JSON
  "needs_review": false,                            // triage=context_dependent → real in some instances, FP in others
  "dedup_group": "sha1(...)"
}
```

## Scanner triage (by rule-class)

Scanner findings ship unverified. Per-finding adversarial verification doesn't scale to ~1000 findings, so they're verified **by rule-class**: group by `(tool, rule)` (~100–150 classes), a triage agent judges each class (reading sample code), and the verdict applies to all instances:
- **`confirmed`** → `verified=true`, counts toward the verdict.
- **`adjust`** → severity corrected (e.g. trivy Dockerfile-syntax Critical → Low), `verified=true`.
- **`dismissed`** → `dismissed=true`; excluded from counts/verdict and hidden in the report by default (kept in `findings.json`, toggle to show).
- **`context_dependent`** → `needs_review=true`; neither confirmed nor dropped.

This is what lets confirmed scanner Criticals/Highs legitimately drive the verdict while noise drops out. See `scripts/group_scanner_rules.py`, `workflows/scanner-triage.workflow.js`, `scripts/apply_triage.py`.

Rules:
- **`cwe` is required.** Agents and the scanner normalizer must assign one (best-effort from rule/CWE taxa). OWASP categories are *derived* from it — never assigned independently.
- **Never fabricate CVSS.** `cvss_from_advisory` is set only when a scanner passes through an authoritative NVD/advisory score for a known CVE.
- **`severity` is our editorial 5-level scale**, normalized from each tool's native scale (table below). It is not a CVSS score.

## Severity normalization (tool native → 5-level)

| Source | Critical | High | Medium | Low | Info |
|---|---|---|---|---|---|
| **CVSS (passthrough)** | ≥9.0 | 7.0–8.9 | 4.0–6.9 | 0.1–3.9 | 0.0 |
| **Trivy** | CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN |
| **Opengrep/Semgrep** | ERROR+security-high | ERROR | WARNING | INFO | — |
| **Gitleaks** | (any secret) High* | — | — | — | — |
| **Bandit** | HIGH sev+HIGH conf | HIGH | MEDIUM | LOW | — |
| **gosec** | HIGH | HIGH | MEDIUM | LOW | — |
| **Checkov/KICS** | by rule severity | HIGH | MEDIUM | LOW | INFO |
| **Agents** | use the 5-level scale directly | | | | |

\* A live/verified secret escalates to Critical; a historical/test-looking one may drop to Medium (agent/verifier judgment).

## Dedup with agreement-boost

When two sources flag the same issue, collapse to one Finding:
- **Key:** `(normalized file, line within ±3 tolerance, cwe OR same OWASP class)`.
- On match: union `tool[]`, set `source_kind="both"`, **raise confidence** (e.g. +2, cap 10) and prepend "confirmed by scanner + agent" to `verification_note`. Scanner+agent concurrence is the strongest trust signal.
- Agent-only findings (scanner couldn't follow the taint) stand alone at their own confidence — that's the recovered cross-function class.

## CWE → OWASP derivation

`scripts/cwe_owasp_map.json` maps `CWE-<n>` → `{ "2021": "A0x:2021-…", "2025": "A0x:2025-…" }`. Both editions are derived from the same CWE so the edition is a pure render choice (default 2025, toggle 2021). Unmapped CWEs fall back to a best-effort category by keyword and are tagged `(unmapped)` so the map can be extended. Key 2021→2025 shifts encoded in the map: SSRF (CWE-918) folds into A01; supply-chain CWEs route to the new A03:2025; improper error/exception handling (CWE-755/703) routes to the new A10:2025.

## is_new

`true` iff the finding's line is in `changed.json` (added/modified). Drives `quick` gating and the report's new-vs-standing split. Omitted in `full`.
