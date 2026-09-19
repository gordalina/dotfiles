#!/usr/bin/env bash
# Render a mermaid diagram to SVG or PNG with the agent-browser CLI.
# Usage: render.sh <input.mmd|-> <output.svg|output.png> [--bg <color>]
set -eu

# One session per process. A shared name collides when two runs overlap.
SESSION=mermaid-render-$$
CDN=https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs

die() { printf '%s\n' "$*" >&2; exit 1; }

[ $# -ge 2 ] || die "usage: render.sh <input.mmd|-> <output.svg|output.png> [--bg <color>]"

IN=$1
OUT=$2
shift 2
BG=""
while [ $# -gt 0 ]; do
  case $1 in
    --bg) [ $# -ge 2 ] || die "--bg needs a color"; BG=$2; shift 2 ;;
    *) die "unknown option: $1" ;;
  esac
done

case $OUT in
  *.svg) FMT=svg ;;
  *.png) FMT=png ;;
  *.pdf) die "PDF is not supported. agent-browser cannot produce a page-fitted PDF. Playwright ignores the CSS @page size unless preferCSSPageSize is set, and agent-browser does not expose that option. Use .svg instead, which is already vector." ;;
  *) die "unknown output format: $OUT. Use .svg or .png." ;;
esac

if [ "$IN" = "-" ]; then
  SRC=$(cat)
else
  [ -f "$IN" ] || die "no such file: $IN"
  SRC=$(cat "$IN")
fi
[ -n "$SRC" ] || die "the mermaid source is empty"

# Make the output path absolute, because agent-browser resolves paths itself.
case $OUT in
  /*) ;;
  *) OUT=$PWD/$OUT ;;
esac
mkdir -p "$(dirname "$OUT")"

# ponytail: text match, not a parse. Switch to a YAML/init parse if odd themes show up.
if [ -z "$BG" ]; then
  if printf '%s' "$SRC" | grep -Eqi "theme[\"']?[[:space:]]*:[[:space:]]*[\"']?dark"; then
    BG="#1f2020"
  else
    BG="#ffffff"
  fi
fi

TMP=$(mktemp -d)
cleanup() { agent-browser --session "$SESSION" close >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

# The PNG is drawn at 2x. The page scales the SVG, so the device scale factor
# of the browser does not matter and the size is the same on every run.
if [ "$FMT" = png ]; then PXSCALE=2; else PXSCALE=1; fi

# Base64 keeps quotes, backslashes and non-ASCII text safe inside the page.
B64=$(printf '%s' "$SRC" | base64 | tr -d '\n')

cat > "$TMP/page.html" <<HTML
<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body { margin: 0; padding: 0; background: $BG; }
  #out { display: inline-block; line-height: 0; background: $BG; }
</style>
</head><body>
<div id="out"></div>
<script type="module">
import mermaid from '$CDN';
const bytes = Uint8Array.from(atob('$B64'), c => c.charCodeAt(0));
const src = new TextDecoder('utf-8').decode(bytes);
mermaid.initialize({ startOnLoad: false });
try {
  const out = document.getElementById('out');
  const res = await mermaid.render('g', src);
  out.innerHTML = res.svg;
  const svg = out.querySelector('svg');
  const vb = svg.viewBox.baseVal;
  if (vb && vb.width) {
    svg.setAttribute('width', vb.width * $PXSCALE);
    svg.setAttribute('height', vb.height * $PXSCALE);
  }
  svg.style.maxWidth = 'none';
} catch (e) {
  window.__err = String((e && e.message) || e);
}
window.__done = 1;
</script>
</body></html>
HTML

ab() { agent-browser --session "$SESSION" "$@"; }

ab open "file://$TMP/page.html" >/dev/null 2>&1
ab wait "#out svg" >/dev/null 2>&1 || true

ERR=$(ab eval "window.__err || null" 2>/dev/null || printf 'null')
if [ "$ERR" != "null" ]; then
  # eval prints a JSON string. Strip the outer quotes and unescape the newlines.
  MSG=$(printf '%s' "$ERR" | sed -e 's/^"//' -e 's/"$//' -e 's/\\n/\
/g' -e 's/\\"/"/g')
  printf 'mermaid error: %s\n' "$MSG" >&2
  exit 1
fi

DONE=$(ab eval "window.__done || null" 2>/dev/null || printf 'null')
[ "$DONE" != "null" ] || die "the render timed out. Check the network, because mermaid loads from the CDN."

if [ "$FMT" = svg ]; then
  ab get html "#out" > "$TMP/out.svg" 2>/dev/null || die "could not read the SVG markup"
  grep -q '<svg' "$TMP/out.svg" || die "the page produced no SVG"
  mv "$TMP/out.svg" "$OUT"
else
  # The screenshot clips to the viewport, so grow the viewport to the diagram.
  DIM=$(ab eval "(function(){var r=document.getElementById('out').getBoundingClientRect();return Math.ceil(r.width)+'x'+Math.ceil(r.height);})()" 2>/dev/null | tr -d '"')
  case $DIM in
    [0-9]*x[0-9]*)
      W=$(( ${DIM%x*} + 16 ))
      H=$(( ${DIM#*x} + 16 ))
      if [ "$W" -lt 240 ]; then W=240; fi
      if [ "$H" -lt 240 ]; then H=240; fi
      if [ "$W" -gt 12000 ]; then W=12000; fi
      if [ "$H" -gt 12000 ]; then H=12000; fi
      ab set viewport "$W" "$H" 1 >/dev/null 2>&1
      ;;
  esac
  ab screenshot "#out" "$OUT" >/dev/null 2>&1 || die "could not take the screenshot"
  [ -s "$OUT" ] || die "the screenshot is empty"
fi

printf 'wrote %s\n' "$OUT"
