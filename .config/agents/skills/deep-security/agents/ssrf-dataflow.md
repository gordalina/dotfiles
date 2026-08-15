# Lens: SSRF & Code-Defect Dataflow  (key: ssrf-dataflow)

**Mandate:** two scanner-weak areas — server-side request forgery, and Coverity-class code defects that have security impact. Both need cross-function dataflow reasoning.

## Hunt for SSRF (A10:2021 / folded into A01:2025)
- **SSRF** (CWE-918) — user-controlled URL/host/port reaching an outbound request (`requests`/`httpx`/`fetch`/`urllib`/webhooks/image-fetchers/PDF/SVG renderers/OIDC discovery). Check for: no allowlist, ability to hit internal IPs (169.254.169.254 cloud metadata, RFC1918, localhost), redirect-following to internal, DNS rebinding exposure.
- **Webhook/callback URLs**, **import-from-URL** features, **proxy** endpoints.

## Hunt for security-relevant code defects (Coverity-class)
- **Tainted data to dangerous sinks** across functions (the inter-procedural taint free SAST misses) — reinforce the injection lens where flows are long.
- **Resource leaks** (CWE-772) — unclosed files/sockets/db connections on error paths (DoS surface).
- **Unsafe concurrency** (CWE-362) — race conditions / TOCTOU in auth, file, or financial logic; check-then-act on shared state.
- **NULL/None deref & unchecked returns** (CWE-476, CWE-252) reachable from untrusted input → crash/DoS.
- **Integer/size issues** (CWE-190) where they affect allocation/bounds with security impact.
- **Improper exception handling** (CWE-755, CWE-703) — fail-open logic, swallowed security exceptions, auth that defaults to allow on error (A10:2025 Mishandling of Exceptional Conditions).
- **Unrestricted upload / resource consumption** (CWE-434, CWE-400) — no size/type limits enabling DoS.

## Method
For SSRF: trace every outbound-request construction back to its URL source. For defects: focus on error/exception paths and shared state in security- or money-sensitive code. Prefer flows that an attacker can actually trigger.

Common CWEs: CWE-918, CWE-772, CWE-362, CWE-367, CWE-476, CWE-252, CWE-755, CWE-703, CWE-400, CWE-434, CWE-190.

Follow the shared output contract. `tool: ["AI:ssrf-dataflow"]`.
