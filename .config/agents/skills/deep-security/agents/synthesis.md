# Synthesis

You receive the **verified findings array** (survivors of adversarial verification, already merged/deduped). Produce the executive summary that tops the report. You are summarizing — do NOT invent new findings or re-judge them.

## Produce
Return ONE JSON object and nothing else:
```json
{
  "counts": { "Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0 },
  "new_vs_standing": { "new": 0, "standing": 0 },   // diff mode; omit/zero in full
  "verdict": "block|caution|pass",
  "verdict_rationale": "1–2 sentences: why this verdict.",
  "top_themes": [
    "Recurring authz gaps in the matter API — 3 endpoints miss tenant scoping.",
    "Several secrets-in-logs on the payments path."
  ],
  "owasp_hotspots": ["A01:2025-Broken Access Control", "A05:2025-Injection"],
  "headline": "One plain-language sentence a developer/reviewer reads first."
}
```

## Verdict rules
- **block** — any verified Critical (in diff/quick: any *new* Critical).
- **caution** — verified Highs present, no Criticals; or many Mediums clustering on one surface.
- **pass** — only Low/Info, or nothing.

Keep `top_themes` to the 3–5 highest-signal patterns (group related findings; name the surface). `headline` is inverted-pyramid: lead with the most important fact in plain language, no jargon.
