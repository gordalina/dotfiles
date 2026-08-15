---
name: customer-doc
description: Distill an internal, exhaustive Tribe artifact (a designed-doc HTML, a working draft, or an analysis) into a concise, customer-facing document, then deliver it as a Google Doc. Use when turning internal Tribe material into an external customer- or client-facing ask (module or enablement requests, proposals, requirement docs) for an engagement. Composes with a customer-specific messaging skill (for example, kirkland_messaging for Kirkland & Ellis) for tone and routing.
---

# customer-doc

Turns an internal Tribe artifact into a distilled, customer-facing document. This is the second half of the two-artifact model: the internal doc stays exhaustive and is the source of truth; this produces the trimmed external ask and is regenerated as the internal doc evolves. Keep the two in sync; do not let them drift.

This skill is the distill step between `designed-doc` (which produces the internal artifact) and the customer-specific messaging skill that governs tone and routing for that customer (for example, `kirkland_messaging` for Kirkland & Ellis).

## When to use

- You have an internal doc (designed-doc HTML, working draft, or analysis) and need the customer-facing version.
- The output goes to a customer's stakeholders (architecture, risk, security, program office, executives).

## Inputs to confirm before drafting

1. **Source artifact** — path or URL to the internal doc.
2. **The single ask** — what the customer must *do* (for example, "enable these five modules").
3. **Audience and routing** — which customer reviewers, in what order (defer to the customer's messaging skill).
4. **Delivery** — default is a Google Doc, drafted in markdown first for review.

## Workflow

### 1. Verify the premise against primary sources (do this first)

Do not distill on an unverified assumption. Before trimming anything, confirm the load-bearing facts against primary sources (Granola, the vault, Obsidian, meeting notes):

- Deployment shape, ownership boundaries, who-said-what, and any constraint the doc asserts.
- If a claim has no primary source, cut it or reframe it. An unsourced assumption in a customer document is a liability.
- Record the source (meeting, note) for each load-bearing fact in your working notes.

This is the highest-value step: it prevents shipping a confidently-wrong document. Real failures caught this way include an on-prem-vs-SaaS deployment assumption and an ownership boundary the customer never actually stated.

### 2. Reduce to the ask

Lead with a one-line request. Keep only what helps the customer act on it. The bar for every element: "does the customer need this to say yes and proceed?" Everything else is a cut candidate. See `references/tone-and-cuts.md` for the cut list.

### 3. Calibrate to the audience

Apply the customer's messaging skill for framing and routing (for Kirkland & Ellis, `kirkland_messaging`). The pattern it supplies: frame dependencies as "Items to Accelerate," state direction rather than inviting veto, keep architecture detail minimal for IT, credit the customer's contributors, and anchor urgency to the customer's own process gate rather than a fabricated date.

### 4. Draft in markdown for review

Write the draft to the scratchpad and review it with the user before creating the Google Doc. Use a standalone structure (drop sections that do not apply):

- **Header / version block** — status, version, prepared by, prepared for (reviewers), scope.
- **Summary** — the ask in two or three sentences.
- **Context** — minimal setup: what exists today, what is requested.
- **Data Boundary** — two to four factual sentences, only if data egress is a customer concern (what leaves, what never leaves, the control point). Not a treatise.
- **Requested items** — one table; per item: purpose, data used, risk/privacy note, and a link to the vendor's official docs. Order by priority.
- **Order of Operations** — priority and sequence, no dates.
- **Items to Accelerate** — the scoped enablement asks, grouped.
- **Open Questions** — each tied to a specific configuration decision.
- **Change History** — a version table for auditability.

Never expose internal provenance, meeting sources, "agent-written" flags, or codenames to the customer.

### 5. Tone and AI-tell pass

Run the linter (in this skill's `scripts/` directory), fix every hit, then apply the register rules in `references/tone-and-cuts.md`:

```bash
bash scripts/lint_tells.sh <draft-file>   # path relative to this skill's directory
```

The rules in brief: no em dashes, no arrows, formal register (not startup-deck), title-case headings, acronyms expanded on first use, and no internal jargon.

### 6. Deliver as a Google Doc

Follow `references/google-doc-delivery.md` exactly. It documents the HTML-not-markdown requirement, the export-and-grep verification (the readback tool lies about table cells), and the integration's create/read-only limits. Create the doc private and unshared; sharing to the customer is always the user's decision.

## Conventions

- **Two artifacts stay in sync.** Regenerate this doc from the internal source when the source changes.
- **Versioning:** v0.x during internal review; promote to v1.0 on first external share. Keep a change-history table.
- **Auditability matters to enterprise customers** — version, date, and change history on every revision.

## Resources

- `references/tone-and-cuts.md` — register rules, banned phrases, and the cut list.
- `references/google-doc-delivery.md` — Google Doc creation procedure, verification, and limits.
- `scripts/lint_tells.sh` — greps a draft for em dashes, arrows, and register tells.
