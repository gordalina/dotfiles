# Delivering as a Google Doc

The Google Drive integration converts uploaded content to a native Google Doc. Get the format right the first time, because the integration is create/read-only.

## Use HTML, not markdown

Upload **HTML** with `contentMimeType: text/html` and let it convert. **Do not upload `text/markdown`.** Markdown import leaves inline formatting as literal text: bold shows as `**text**`, and links show as raw `[text](url)` and are not clickable. HTML converts `<strong>`, `<a href>`, `<h1>`/`<h2>`, `<table>`, and lists to native Google Doc elements.

Tool: `mcp__claude_ai_Google_Drive__create_file`

- `title`: include the version, e.g. "... (v0.1 Draft)".
- `contentMimeType`: `text/html`
- `textContent`: the HTML (a minimal `<!DOCTYPE html><html><body> ... </body></html>` document).
- Omit `parentId` to place it in My Drive root, private and unshared.

## HTML that converts cleanly

- Header / metadata block: a two-column `<table border="1">`.
- Section headings: `<h1>` for the title, `<h2>` for sections.
- Content table: `<table border="1">` with `<a href="...">` and `<strong>` inside cells.
- Bold: `<strong>`. Lists: `<ol>` / `<ul>`. Inline code: `<code>`.
- Escape ampersands as `&amp;` (e.g. "K&amp;E", "Kirkland &amp; Ellis").
- The `§` character does not survive well; write "Section 2", not "§2".

## Verify before reporting (do not trust the readback)

`read_file_content` is **lossy inside table cells**: it escapes real bold and links so they look broken even when they are not. For ground truth, export the doc and grep it.

```bash
# download_file_content returns base64 inside JSON; if the output is large it is
# saved to a file. Decode and check for real hyperlinks and zero markdown artifacts:
jq -r '.content' <saved-output-file> | base64 --decode > /tmp/doc.html
grep -oE 'href="https://[^"]*"' /tmp/doc.html | sort -u   # confirm real <a href> links
grep -c '](http' /tmp/doc.html                            # must be 0 (no literal md links)
grep -c '\*\*' /tmp/doc.html                              # must be 0 (no literal bold markers)
```

Confirm the expected number of links and zero literal-markdown artifacts before telling the user it is ready.

## Integration limits (plan around them)

- **No delete, rename, or update.** You cannot fix a bad doc in place. To revise, create a new version (bump the version in the title) and have the user trash the old one manually.
- Get the title and version right on creation.

## Sharing

Create the doc private and unshared by default (omit `parentId`). Sharing to the customer is always the user's decision; never share on their behalf.
