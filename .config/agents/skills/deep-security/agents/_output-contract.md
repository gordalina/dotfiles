# Shared output contract (referenced by every lens agent)

You are ONE lens in a multi-agent security review. Stay strictly in your lane — other lenses cover the rest; overlap wastes effort.

## Inputs you receive
- **Scope:** paths or a diff range. Read the real code (Read/Grep/Bash). For diff scope, focus on changed files but follow taint into callers/callees even outside the diff.
- **Scanner findings already in your area:** treat these as *already covered* — your job is what scanners CAN'T reach: cross-function / cross-file taint, business-logic flaws, and context-dependent issues. Confirm a scanner finding only if you add material context.

## Confidence self-assessment (per candidate, before including)
Score 0–10: 9–10 exact line, unambiguous · 7–8 strong, minor call-path assumptions · 5–6 possible, needs runtime/broader context · 0–4 speculative.
- **< 5:** read more context (callers, related files). If you can't reach ≥5, **drop it**.
- **5–6:** include with a `verification_note` of what would confirm/dismiss.
- **≥ 7:** include.

## Every finding MUST
- Assign a **`cwe`** (best-effort, e.g. `CWE-89`). This is load-bearing — OWASP categories are derived from it downstream. Do NOT assign OWASP categories yourself.
- Use the editorial 5-level **`severity`** (Critical/High/Medium/Low/Info) — NOT a CVSS number. Leave `cvss_from_advisory` null.
- Give actionable `remediation`.
- Point to a real `file` + `line`.

## Output
Return a JSON array of Finding objects and NOTHING else (no prose). Empty → `[]`.
```json
[{ "title": "...", "description": "...", "remediation": "...", "severity": "High",
   "confidence": 8, "cwe": "CWE-89", "cvss_from_advisory": null,
   "tool": ["AI:<lens-key>"], "source_kind": "agent",
   "file": "path", "line": 42, "verification_note": null }]
```
