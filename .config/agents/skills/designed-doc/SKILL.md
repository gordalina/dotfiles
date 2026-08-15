---
name: designed-doc
description: >-
  Generate a polished, self-contained HTML document in a dark-themed "house style" —
  jargon tooltips, a collapsible glossary, numbered sections with anchor links, pure-CSS
  flow/architecture diagrams, asks-up-front + decision tables, NOW/NEXT/LATER phase rails,
  inline-SVG/CSS charts, KPI tiles, and a provenance footer. Builds from the current
  conversation OR from a file/notes/text you provide. Use when the user wants a design doc,
  approach or architecture writeup, decision brief, proposal, technical explainer, or a
  "nice HTML doc/report like the last one", or invokes /designed-doc.
---

# designed-doc

Produce one **self-contained** HTML doc (no CDN/JS/external assets) in the established style:
dark theme, tooltipped jargon, numbered sections, CSS diagrams, decision tables, charts,
provenance footer. The look is fixed (a bundled template); you supply the content.

## Quick start
```
/designed-doc                      # synthesize from this conversation
/designed-doc path/to/notes.md     # build from a file
/designed-doc "the X migration plan we discussed"   # build from described context
```

## Workflow
1. **Get the content + the audience.** No arg → synthesize from the conversation. A path/text/topic
   → use that as the source. **Always establish the target audience** — who the doc is written for
   drives its tone and depth — and fill the hero `Audience:` chip (a required field). If the source
   is thin or ambiguous, or the audience isn't clear, ask 1–2 sharp questions before writing.
2. **Outline.** Map the material onto the skeleton in [reference/structure.md](reference/structure.md)
   (TL;DR → asks-up-front → what-it-is → architecture → approach → decisions → cost → risks →
   plan → open questions → footer). Drop sections that don't apply; this is a guide, not a cage.
3. **Draft from the template.** Copy [assets/template.html](assets/template.html) to the output
   path and fill every `REPLACE`. Pull each component (tooltip, glossary, callout, comparison
   table, flow diagram, phase rail, KPI tiles, chart, footer) from
   [reference/components.md](reference/components.md). Tooltip every term on first use.
4. **Keep it self-contained.** No external links for assets; charts are CSS or inline SVG. The
   file must open offline and survive being emailed or hosted behind SSO.
5. **Validate** (see below), then **report the absolute path** and open it.

## Output & conventions
- **Save** to the path the user gives, else the current working directory (these are shareable
  artifacts — not the vault; internal-only *plans* still belong in the vault). Name it
  `kebab-title.html`.
- **Report the ABSOLUTE path** (`/Users/.../foo.html`) so it's clickable, then open it:
  `open <file>.html` (renders in the browser).
- End with a provenance footer + `agent-written: true`.

## Validate before reporting
- Tags balanced: `<section>`/`</section>`, `<div>`/`</div>`, `<table>`/`</table>` counts match.
- Every `href="#x"` has a matching `id="x"` (no dead anchors).
- No `http(s)://` asset/CDN references (links to external *resources* in prose are fine).
- Spot-check it renders (open it).

## Notes
- The voice: inverted-pyramid, plain-language-first, explicit recommendations, grounded numbers.
  See [reference/structure.md](reference/structure.md).
- The design system + every component snippet live in `assets/` and `reference/` — read them;
  don't re-derive the CSS.
- Shareable by default (general content). The save-path/open-in-browser defaults above are the
  local profile; the doc itself carries no environment assumptions.

## House style — "Dark Editorial" (baked 2026-06-29)

The bundled `assets/template.html` now ships this style; fill the REPLACE slots and it inherits:

- **Dark theme, serif body, sans headings.** Serif (system: Charter/Iowan/Georgia) at 17.5px/1.72 for readable long-form; sans for headings/labels/tables.
- **Reading column.** Running prose (`p`, `.lead`, `ul`, `ol`, `blockquote`) is capped at `--measure` (~68ch); tables, `.diagram`, `.grid2/3`, `.kpis`, `.callout`, `.codeblock` break out to full width.
- **Modern section UX.** `h2` leads with a filled **accent number-chip** (`.n`) + underline divider; callouts are left-border admonitions with ℹ/✓/▲ icons; auto-built **sticky section TOC** (left gutter, ≥1500px) + a top **reading-progress bar** (both wired by the inline script — keep `section[id]` + `h2` on every section so they populate).
- **Masthead + brand mark.** A `.masthead` above the hero locks up the Tribe symbol + "Tribe AI · Infrastructure" wordmark (left) with a `.masthead-tag` short context label (right, a `REPLACE` slot). The symbol is inline SVG with `fill="currentColor"` → inherits `--ink` so it reads on dark. Baked into `assets/template.html`; source of truth is `assets/brandmark.svg`. Keep the masthead on every doc; fill the tag; if the logo changes, update both.
- Still self-contained: no CDNs, CSS/JS inline, prints to PDF.

### Reusable prompt snippet (to steer ad-hoc HTML docs outside this skill)

```
<html_doc_style>
SINGLE self-contained .html: CSS/JS inline, NO CDNs/external fonts, prints to PDF.
Aesthetic: "Dark Editorial" — a polished long-form article, NOT a dashboard.
LAYOUT  — centered wrap (~1060px); running prose in a ~68ch reading column; data/diagrams full-width.
TYPE    — dark bg (#101217), warm off-white ink; serif body 17.5px/1.72 (Charter/Iowan/Georgia);
          sans headings (h1 2.5 / h2 1.5 / h3 1.12rem), decisive weight. NEVER Inter/Roboto/Arial as body.
SECTIONS — h2 with a filled accent number-chip + underline divider; generous rhythm.
COLOR   — ONE accent (#7ba6ff) for links/chips/rules; semantic green/amber/red for status only.
COMPONENTS — callouts = left-border admonitions w/ icon+label (note/good/gate); tables header-rule+hover,
          no heavy gridlines; code = dark panel, mono, 6px radius; cards/KPIs subtle elevation.
EXTRAS  — sticky section TOC (wide screens) + top reading-progress bar; at most one page-load fade-in.
Every element earns its place — no filler.
</html_doc_style>
```
