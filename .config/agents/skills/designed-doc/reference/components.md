# Component cookbook

Every component the template's CSS supports. Copy a snippet, fill it in. All are
self-contained (no JS, no external assets) so the single HTML file stays portable.

---

## Tooltip (jargon) — the signature element
Wrap any term the reader might not know on its **first** use. Keep the tip to one plain sentence.
```html
<span class="tt" tabindex="0" data-tip="One plain-English sentence. No jargon inside the jargon.">term</span>
```
`tabindex="0"` makes it keyboard/focus-accessible. Don't tooltip the same term twice.

## Glossary (collapsible)
Sits at the end of the TL;DR. Two-column grid of `dt`/`dd`. `open` = expanded by default.
```html
<details class="gloss" open>
  <summary>Glossary — expand for the core vocabulary in plain English</summary>
  <div class="gloss-grid">
    <div><dt>Term</dt><dd>Definition.</dd> <dt>Term</dt><dd>Definition.</dd></div>
    <div><dt>Term</dt><dd>Definition.</dd> <dt>Term</dt><dd>Definition.</dd></div>
  </div>
</details>
```

## Numbered section + anchor
Every body section is a `<section id="sN">` with a numbered `<h2>` chip. The `id` makes it
linkable; `scroll-margin-top` (in CSS) keeps the jump from landing flush against the top.
```html
<section id="s1">
<h2><span class="n">1</span> Section title</h2>
<p class="lead">One-line framing.</p>
...
</section>
```
**Non-numbered markers** for special sections — use a symbol instead of a number, and a
matching `id` (`#decision`, `#cost`):
```html
<h2><span class="n">⚑</span> Decision · …</h2>
<h2><span class="n">$</span> Cost · …</h2>
```

## In-doc § links
Reference another section as a clickable link (used heavily in the asks table + inline):
```html
see <a href="#cost">§$</a> · <a href="#s7">§7</a>
```

## Callouts (note / good / gate)
`note` = neutral/info (blue), `good` = recommendation/positive (green), `gate` = decision/caution (red).
```html
<div class="callout note"><h4>Heading</h4><p>Body.</p></div>
<div class="callout good"><h4>Bottom line</h4><p>Body.</p></div>
<div class="callout gate"><h4>What we need from you</h4><p>Body.</p></div>
```

## Asks-up-front (decision table)
A `gate` callout near the top of a decision doc. Each row links to where the detail lives.
```html
<div class="callout gate">
  <h4>What we need from you — the open decisions, up front</h4>
  <p style="margin-top:0">Short framing; each has a recommendation.</p>
  <table>
    <thead><tr><th>#</th><th>Decision</th><th>Our recommendation</th><th>Detail</th></tr></thead>
    <tbody>
      <tr><td>1</td><td><b>Decision</b></td><td><span class="pill p-done">Recommend</span> X</td><td><a href="#s3">§3</a></td></tr>
    </tbody>
  </table>
</div>
```

## Option comparison table
For "which approach?" decisions — columns are the tradeoff axes; pills mark good/bad cells.
```html
<table>
  <thead><tr><th>Option</th><th>Axis A</th><th>Axis B</th></tr></thead>
  <tbody>
    <tr><td><b>1 · Name</b><br><span class="muted" style="font-size:11.5px">subtitle</span></td>
      <td><span class="pill p-gap">downside</span></td><td><span class="pill p-done">upside</span></td></tr>
  </tbody>
</table>
```

## Pills (status)
`p-done` green · `p-prog` blue · `p-gap` red · `p-dark` amber.
```html
<span class="pill p-done">DONE</span> <span class="pill p-prog">IN PROGRESS</span>
<span class="pill p-gap">GAP</span> <span class="pill p-dark">LATER</span>
```

## Card grid
2- or 3-up cards (`grid2`/`grid3`). Optional per-card accent via inline `border-color`.
```html
<div class="grid3">
  <div class="card" style="border-color:rgba(245,158,11,.4)"><h4>Title</h4><p>Body.</p></div>
  <div class="card"><h4>Title</h4><p>Body.</p></div>
  <div class="card"><h4>Title</h4><p>Body.</p></div>
</div>
```

## KPI / stat tiles
Headline numbers. Color the value with `good`/`warn`/`bad`/`info`.
```html
<div class="kpis">
  <div class="kpi info"><div class="v">~$280</div><div class="k">/month</div></div>
  <div class="kpi good"><div class="v">9/9</div><div class="k">lenses passing</div></div>
  <div class="kpi warn"><div class="v">3</div><div class="k">open decisions</div></div>
</div>
```

## Flow / architecture diagram (pure CSS)
A left→right pipeline: 4 `stage` columns of `node` boxes. Node classes tint by lane:
`src` (neutral) · `scann` (amber) · `ain` (purple) · `outn` (green). Pair with a `legend`.
```html
<div class="legend">
  <span><span class="sw s"></span> Lane A</span>
  <span><span class="sw a"></span> Lane B</span>
  <span><span class="sw o"></span> Lane C</span>
</div>
<div class="diagram"><div class="flow">
  <div class="stage"><div class="stage-h">Stage 1</div>
    <div class="node src"><span class="t">Box</span><span class="d">detail</span><small>note</small></div>
  </div>
  <div class="stage"><div class="stage-h">Stage 2</div>
    <div class="node ain"><span class="t">Box</span><span class="d">detail</span></div>
  </div>
  <!-- up to 4 stages; change .flow grid-template-columns if fewer/more -->
</div>
<div class="join">⟵ one-line caption tying the flow together ⟶</div>
</div>
```
For ≠4 stages, override inline: `<div class="flow" style="grid-template-columns:repeat(3,1fr);min-width:660px">`.

## Embedded figure (image / SVG diagram) — click-to-zoom
For a real image or a tool-exported diagram (D2, Graphviz, Mermaid CLI), wrap it in `.figure`.
It renders on a white matte and is **automatically click-to-expand**: the inline lightbox script
wires every `.figure` so a click opens the artwork full-window (backdrop click / × / Esc to close).
No per-doc wiring needed. Add the `.zoom-hint` badge so users know it's interactive.
```html
<div class="figure"><span class="zoom-hint">⤢ Click to expand</span>
  <!-- inline the SVG here (self-contained), or an <img> with a data: URI -->
  <svg viewBox="0 0 1200 400" xmlns="http://www.w3.org/2000/svg"> ... </svg>
</div>
<p class="figcap">One-line caption; legend colors decoded in the diagram itself.</p>
```
**Inline the SVG, don't link it** (self-contained rule). To embed a D2 render, strip the
`<?xml …?>` declaration and paste the `<svg>…</svg>` into the `.figure`.

**Gotcha — collapsed / tiny SVG:** tool-exported SVGs frequently carry a `viewBox` but no
intrinsic `width`/`height`. With `width:auto` they collapse to the browser default (~300×150).
The template already fixes this: `.figure svg` gets `width:100%` and the lightbox stage gets a
concrete `width:90vw` (scoped to the direct-child `> svg` so a tool's nested `<svg>` is untouched).
Keep those rules if you hand-edit. Raster `<img>` uses natural size capped at `90vw × 84vh`.

## Phase rails (NOW / NEXT / LATER)
Sequenced plan. Badge classes: `now` (green) · `next` (blue) · `later` (grey).
```html
<div class="phase now"><div class="badge">NOW</div><div class="body"><ul><li>…</li></ul></div></div>
<div class="phase next"><div class="badge">NEXT</div><div class="body"><ul><li>…</li></ul></div></div>
<div class="phase later"><div class="badge">LATER</div><div class="body"><ul><li>…</li></ul></div></div>
```

## Charts
**CSS horizontal bars** (simplest; label / track / value grid):
```html
<div class="bars">
  <div class="bar-row"><span>Label</span>
    <div class="bar-track"><div class="bar-fill" style="width:72%;background:var(--ok5)"></div></div>
    <span class="bar-val">72</span></div>
</div>
```
**Inline-SVG horizontal bars** (publication-grade; exportable, exact). Scale widths to your max.
Use the Okabe–Ito vars (`--ok1`..`--ok7`) so it's colorblind-safe.
```html
<svg viewBox="0 0 400 90" width="100%" role="img" aria-label="Breakdown" style="margin:14px 0">
  <g font-family="var(--sans)" font-size="11" fill="#9aa7b8">
    <text x="0" y="20">Critical</text>
    <rect x="70" y="10" width="180" height="14" rx="3" fill="#d55e00"></rect>
    <text x="258" y="20" fill="#e7ecf3">12</text>
    <text x="0" y="46">High</text>
    <rect x="70" y="36" width="120" height="14" rx="3" fill="#e69f00"></rect>
    <text x="198" y="46" fill="#e7ecf3">8</text>
    <text x="0" y="72">Medium</text>
    <rect x="70" y="62" width="60" height="14" rx="3" fill="#56b4e9"></rect>
    <text x="138" y="72" fill="#e7ecf3">4</text>
  </g>
</svg>
```

## Code block
Monospace block with muted comments via `<span class="c">`. Use `<br>` for line breaks.
```html
<div class="codeblock">
<span class="c"># comment</span><br>
command --flag value
</div>
```

## Footer (provenance) — always include
Every claim should be traceable; the footer lists sources + an `agent-written` flag.
```html
<footer>
  <b>Provenance.</b> vN · drafted YYYY-MM-DD from <source>.
  <div class="src-list" style="margin-top:8px"><div>Source: …</div></div>
  <p style="margin-top:10px;opacity:.7">Status note. <code>agent-written: true</code></p>
</footer>
```
