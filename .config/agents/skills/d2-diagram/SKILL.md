---
name: d2-diagram
description: Use when creating or refining an architecture, data-flow, block, or system diagram — especially with D2 (Terrastruct diagram-as-code) — or when a diagram looks like spaghetti, too wide, cluttered, or not presentation-ready and needs to look clean and professional.
---

# d2-diagram

Produce clean, professional, presentation-ready architecture diagrams with **D2** (Terrastruct) in one pass, using a locked house style — so you don't churn through layout/style iterations.

**Core principle:** the diagram is a *visual* artifact. Structure and encoding carry the meaning (layout, color, icons, line style); prose detail belongs in the surrounding document, not on the canvas.

## When to use

- Building an architecture / data-flow / signal-flow / block diagram.
- A diagram is too wide, has crossing "spaghetti" lines, unlabeled edges, or looks unpolished.
- You need something to embed in a doc or send to a stakeholder.

Not for: freeform sketches, org charts, or when a one-line ASCII sketch suffices.

## Setup

`d2` CLI: `brew install d2` (macOS). Verify with `d2 --version`.

Keep the diagram self-contained and reproducible: commit the `.d2` source, a `render.sh`, and a local `icons/` folder together. Copy the starter files:
- `templates/diagram.d2` — the house-style skeleton (classes, planes, legend, edges).
- `scripts/render.sh` — the exact render command + flags.
- `scripts/fetch-icons.sh` — downloads icons locally (see Icons).

## The 8 rules (this IS the house style)

1. **Layout = ELK, always.** `--layout elk` gives orthogonal right-angle routing. Dagre's curvy splines look unprofessional. Never ship dagre.
2. **Compact, not cramped.** Tune spacing via flags, don't shrink nodes: `--elk-nodeNodeBetweenLayers 28 --elk-edgeNodeBetweenLayers 20 --elk-padding "[top=24,left=24,bottom=24,right=24]" --pad 25`. Start at 28; only loosen if borders touch.
3. **Nodes = white cards + icon.** White fill, `border-radius 8`, soft `shadow`, one **icon** per node (see Icons). Use a `node` class so every card is identical.
4. **Group into tinted, labelled planes.** Wrap related nodes in a container with a semantic background tint + label (e.g. blue = new/proposed, green = unchanged/certified). Color must *mean* something.
5. **Label every edge; collapse same-data fan-outs.** If one stream feeds N nodes in a container, draw **one labelled edge into the container** (`a -> container: "traces · metrics · logs"`), not N bare lines. Every edge says what flows.
6. **Semantic edge classes.** Solid colored = active/live flow; grey dashed = decision-pending / out-of-scope / conditional. Define `main` and `dim` edge classes and reuse.
7. **No tooltips.** D2 `tooltip:` renders a dead `(i)` icon in static SVG/PNG — useless when embedded. Put detail in the document. If one fact is load-bearing, fold it into the node label ("on-prem edge · HTTP-only").
8. **Short labels + a legend.** Labels are 1–3 words / max 2 lines; long prose lives in the doc. Add a `LEGEND` container (`near: bottom-center`, `grid-columns`) decoding the colors and line styles.

## Icons (the non-obvious part)

Icons are the single biggest professional upgrade — but **use local files, not URLs**. D2 bundles remote images at compile time with a non-browser user-agent, so many CDNs (Wikimedia, and some others) return **403** and the render fails.

Workflow: pick slugs → `scripts/fetch-icons.sh` downloads them into `icons/` with a browser UA → reference as `icon: icons/<name>.svg`.

Reliable sources:
- **SimpleIcons** — `https://cdn.simpleicons.org/<slug>` (brand-colored). Covers most vendors/langs: kubernetes, opentelemetry, fluentbit, dynatrace, sentry, grafana, fastapi, react, temporal, python, postgresql, redis, apachekafka, snowflake…
- **CNCF artwork** — `raw.githubusercontent.com/cncf/artwork/master/projects/<p>/icon/color/<p>-icon-color.svg`.
- **Azure** is NOT on SimpleIcons → Wikimedia `Microsoft_Azure.svg` (download locally, browser UA).
- Terrastruct's `icons.terrastruct.com` paths are guessy and often 403 — don't guess them.

Not every vendor has a SimpleIcons slug (e.g. `amazonapigateway` 404s). `fetch-icons.sh` prints `FAIL` on any non-200 — when that happens, use CNCF/Wikimedia/vectorlogo.zone, or pick the closest representative brand (e.g. `kong` for an API gateway). Don't ship a blank icon.

## Render

`./render.sh` (wraps the flags in rule 2, emits `.svg` + `.png`). Because icons are local, it works offline and regenerates byte-identically.

## Verifying your output

You can't judge a diagram from source. Render the PNG and **look at it** (Read the PNG). iCloud vault paths give the Read tool `EPERM` — copy the PNG to a scratchpad dir first, then Read that copy. Check: no crossing lines, every edge labelled, no `(i)` icons, planes tinted, not too wide.

## Common mistakes

| Mistake | Fix |
|---|---|
| Default (dagre) layout → curvy spaghetti | `--layout elk` |
| Diagram too wide, long connectors | lower `--elk-nodeNodeBetweenLayers` (28) |
| Icons blank / render fails with 403 | download icons locally with browser UA (`fetch-icons.sh`) |
| `(i)` icons everywhere | remove all `tooltip:`; fold key facts into labels |
| N bare lines fanning into a group | one labelled edge into the container |
| Left/edge box huge | long note text — shorten to ≤2 lines, move prose to the doc |
| Unlabeled arrows | label every edge with what flows |
| Guessed `near:` on a nested node fails to compile | `near:` with constants works only on root-level shapes |
