---
name: mermaid-render
description: Use when you already have mermaid source and need it as an image file. Triggers - a .mmd file, a fenced mermaid code block that must become a PNG or SVG, or a request like "render this mermaid", "export this mermaid to png", "turn this mermaid into an svg". This skill renders mermaid. It does not write mermaid. For a new architecture, data-flow, or system diagram, use the d2-diagram skill instead.
---

# mermaid-render

Render existing mermaid source to a PNG or an SVG file. The renderer is the
`agent-browser` CLI plus mermaid from the CDN. There is no other dependency.

## Usage

```sh
~/.claude/skills/mermaid-render/render.sh diagram.mmd out.svg
~/.claude/skills/mermaid-render/render.sh diagram.mmd out.png
~/.claude/skills/mermaid-render/render.sh diagram.mmd out.png --bg "#f6f8fa"
```

Read the source from stdin with `-`:

```sh
pbpaste | ~/.claude/skills/mermaid-render/render.sh - out.png
```

The output format comes from the file extension. The PNG is drawn at 2x.

## Theme

There is no theme flag. Set the theme in the diagram source. Use YAML frontmatter:

```
---
config:
  theme: dark
---
flowchart LR
  A --> B
```

The init directive also works: `%%{init: {'theme':'dark'}}%%`.

A dark theme gets a `#1f2020` background. Every other theme gets white. Use
`--bg <color>` to override the background with any CSS color.

## Verify the output

ALWAYS render a PNG and Read it. Do this even when the deliverable is an SVG.
You cannot judge a diagram from the source.

If the deliverable is an SVG, render a check PNG to a temp path first. Read that
PNG, then ship the SVG. Check for these faults:

- Labels that overlap each other or an edge.
- Text that is cut off at the edge of the image.
- A background that hides the text, for example dark text on a dark theme.

## Limits

- The render needs the network. Mermaid loads from the CDN.
- PDF is not supported. Use SVG, which is already vector.
- The PNG is opaque. The SVG is transparent.
- There is no markdown rewrite mode. The script takes one diagram and writes one file.
