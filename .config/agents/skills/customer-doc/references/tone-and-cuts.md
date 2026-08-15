# Tone, register, and the cut list

## Register: formal, not startup-deck

Match the register the customer expects. For a conservative enterprise or law firm (for example, Kirkland & Ellis), the document must read as a professional engineering request, not a product pitch.

- **No em dashes (—).** They are a quick tell that a document was AI-generated. Use colons, commas, parentheses, or split the sentence.
- **No arrows (→ ↔ ⟶ ⟵).** Same tell. Spell out flows ("from the Collector to the ActiveGate").
- **Title-case section headings** ("Requested Modules", "Order of Operations", "Open Questions").
- **Expand acronyms on first use** — PRR (Production Readiness Review), OTLP, PTU, ACR, and so on. The audience often includes non-technical risk and legal reviewers.
- **Drop internal nomenclature and codenames.** Replace with functional descriptors ("the backend and task-worker services", not internal service names). Watch for codenames that collide with known products. Drop internal team labels from bylines (use "Tribe AI", not an internal team name).
- **Plain, but professional.** Prefer "notified" over "paged", "selected" over "cherry-picked", "least effort" over "lowest lift".

## Banned phrases (the linter flags these)

Startup and casual tells, plus common AI-ese, to remove:

- "the ask" as a heading (use "Summary" or "Request").
- "read this first" or "up front" as framing.
- "big-bang", "long pole", "lowest lift", "tracked to green", "cherry-pick".
- "let's", "we're excited", "seamless", "leverage", "delve", "boasts", "game-chang".

The list in `scripts/lint_tells.sh` is the enforced set; tune it as new tells surface.

## Cut list: remove unless it directly serves the ask

- Internal nomenclature and codenames.
- Cost, consumption, or budget speculation, unless the customer asked for it. It opens a tangent and invites questions you do not want to field yet.
- Provenance footers, source meetings, and "agent-written" flags.
- Scope-fencing ("explicitly not requested"), unless it de-risks the specific review in front of you.
- Anything that creates room for a question or tangent the ask does not need. When in doubt, cut.

## Urgency without a date

Anchor urgency to the customer's own process gate (for example, observability being required for a production-readiness review), never a fabricated deadline. State readiness to start and ask for the customer's provisioning lead time rather than imposing one. If there is no real date, do not invent one.

## Auditability

- A version and change-history table on every revision.
- v0.x while in internal review; promote to v1.0 on first external share.
