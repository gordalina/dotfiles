# Lens: Data Exposure & Logging  (key: data-exposure)

**Mandate:** sensitive data leaking through logs, errors, responses, or storage; and inadequate security logging. Almost entirely semantic — scanners barely touch this.

## Hunt for
- **Sensitive data in logs** (CWE-532) — PII, credentials, tokens, full request bodies, SQL with values, secrets logged at any level. Check log statements on auth, payment, and user-data paths.
- **Sensitive data in errors / responses** (CWE-209, CWE-200) — stack traces, internal exception text, raw DB errors, debug info returned to clients; over-broad API serialization exposing fields the caller shouldn't see (internal flags, other users' data, password hashes).
- **Verbose error handling** — `debug=True` in prod, detailed error pages, exception detail echoed in API responses.
- **Sensitive data at rest / in transit** — PII unencrypted, sent over plaintext, stored in caches/temp files/URLs.
- **Missing security logging/alerting** (A09) — auth failures, access-control denials, and high-value actions not logged; no audit trail for sensitive mutations.
- **Caching/headers** — sensitive responses cacheable, missing `Cache-Control: no-store`, secrets in referrer.

## Method
Trace where sensitive values (passwords, tokens, PII, financial/deal data) are produced and everywhere they flow — logs, exceptions, serializers, responses, caches. For serializers/DTOs, compare returned fields against caller authorization. For error paths, check what reaches the client. Note the repo's logging/scrubbing conventions and flag bypasses.

Common CWEs: CWE-532, CWE-209, CWE-200, CWE-201, CWE-312 (cleartext storage), CWE-319, CWE-538, CWE-778 (insufficient logging).

Follow the shared output contract. `tool: ["AI:data-exposure"]`.
