# Document structure & writing conventions

The genre this skill targets: **design / approach / decision docs** — the kind a team reads
to understand a proposal and make the calls it asks for. The visual system works for any
technical explainer, but this is the default skeleton.

## Default section skeleton (reorder/drop per doc)

1. **Hero** — eyebrow (context · audience), H1 title, one-paragraph framing, status/owner chips.
2. **TL;DR** — "the shape in five lines": 3–5 bullets, inverted pyramid (most important first).
   End with the **glossary** (collapsible) if the doc has jargon.
3. **Asks-up-front** — *decision docs only*: a `gate` callout with the open decisions as a
   table, each row linking to where the detail lives. Put it BEFORE the body so the reader
   holds the criteria in mind while reading. Skip for pure explainers.
4. **What it is** — the thing being proposed/explained; lead with a one-line `lead`, then
   cards or prose. Tooltip every new term.
5. **Architecture / how it works** — a CSS flow diagram + legend when there's a pipeline or
   signal flow; otherwise prose + cards.
6. **The approach / key mechanic** — the substance. Tables for "A vs B", code blocks for
   commands, callouts for the load-bearing points.
7. **Decision sections** — non-numbered `⚑` marker, option comparison table, a `note`/`good`
   callout with the recommendation + when you'd pick otherwise.
8. **Cost / tradeoffs** — non-numbered `$` marker if money is involved; KPI tiles + a table
   grounded in real numbers (say so), caveats in a `note` callout.
9. **Risks / considerations** — a numbered risk register table (R1, R2, …) with handling.
10. **Phased plan** — NOW / NEXT / LATER rails.
11. **Open questions** — the decisions still outstanding (mirror the asks-up-front).
12. **Footer** — provenance: sources, version, date, `agent-written: true`.

## Writing conventions (match the exemplar's voice)

- **Inverted pyramid everywhere.** Lead with the answer/recommendation; detail follows.
- **Plain language first, jargon tooltipped.** A reader should never have to leave the doc to
  understand a term. First use of any acronym/tool/concept → `.tt` tooltip.
- **Recommendations are explicit.** Decision sections say what to do AND when you'd choose
  differently. Use a `good` callout for "bottom line".
- **Ground the numbers.** If a figure is measured, say from what; if modeled, say so. Never
  present an estimate as fact.
- **Tables for comparisons, callouts for emphasis, diagrams for flows.** Don't narrate a
  pipeline in prose if a flow diagram shows it.
- **Provenance is mandatory.** Every doc ends with sources; synthesized claims trace back.
- **Tone:** concise, scannable, confident but honest about uncertainty. Short sentences.

## Self-contained, always
One HTML file. No CDN links, no external fonts/images/JS. Charts are CSS or inline SVG.
This keeps the doc openable offline, emailable, and hostable behind SSO without breakage.
