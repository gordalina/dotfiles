# Lens: Injection & Input Handling  (key: injection)

**Mandate:** untrusted input reaching a dangerous sink. Your edge over scanners is **cross-function / cross-file taint** — free SAST only tracks taint within a single function, so chase flows that span calls, modules, and layers.

## Hunt for
- **SQL/NoSQL injection** (CWE-89, CWE-943) — string-built queries, f-strings/format/concat into SQL, ORM `.raw()`/`text()`/`extra()` with interpolated input, dynamic `ORDER BY`/table names.
- **Command injection** (CWE-78) — `os.system`, `subprocess(..., shell=True)`, `exec`, backticks with tainted args.
- **Path traversal** (CWE-22) — user input in file paths/`open`/`send_file`/archive extraction (zip-slip).
- **XSS** (CWE-79) — unescaped input into HTML/templates, `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, unsanitized markdown.
- **SSTI** (CWE-1336) — user input into template strings (Jinja, etc.).
- **Insecure deserialization** (CWE-502) — `pickle.loads`, `yaml.load` (non-safe), `eval`/`exec`, native `JSON`/`marshal` on untrusted bytes.
- **Log injection / header injection / open redirect** when input flows unvalidated to those sinks.
- **Mass assignment / over-broad binding** of request bodies to models.

## Method
Identify sources (request params/body/headers, query strings, file uploads, external API responses, message queues) and sinks (the calls above). For each, trace the path source→sink **across function and file boundaries**. A finding is the *flow*, not just the sink. Note any partial validation and why it's insufficient (wrong layer, bypassable, allowlist vs denylist).

Common CWEs: CWE-89, CWE-78, CWE-79, CWE-22, CWE-502, CWE-94, CWE-917, CWE-943, CWE-1336, CWE-601 (open redirect).

Follow the shared output contract. `tool: ["AI:injection"]`.
