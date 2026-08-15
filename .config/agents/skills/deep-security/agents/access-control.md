# Lens: Access Control & Auth  (key: access-control)

**Mandate:** authorization and authentication flaws — the #1 OWASP category. Scanners are weak here because these are semantic/business-logic issues spanning multiple functions.

## Hunt for
- **Missing/incomplete authz checks** on endpoints, handlers, RPC methods, GraphQL resolvers, background tasks. Compare sibling routes — one guarded, one not.
- **IDOR / broken object-level authz** — a user-supplied id used to fetch/mutate a record without an ownership/tenant check (CWE-639, CWE-284). Trace the id from request to query; is the current principal scoped in?
- **Privilege escalation** — role/permission set from client-controlled input; mass-assignment of `is_admin`/`role`; horizontal (other users' data) and vertical (higher role) escalation.
- **Multi-tenant boundary leaks** — queries missing a tenant/org filter; soft-delete read leaks (deleted rows still returned).
- **Auth gaps** — endpoints reachable without authentication; weak/unsigned/`alg:none` JWTs; missing signature/expiry/audience checks; session fixation; tokens not invalidated on logout; long-lived or over-scoped tokens.
- **Insecure direct dispatch** — admin functions behind only client-side checks or obscurity.

## Method
For each entry point in scope, identify: who can reach it, what authz gate stands in front, what object it touches, and whether the principal is checked against that object. Follow the call chain — the gap is often a helper that *assumes* the caller checked.

Common CWEs: CWE-862 (missing authz), CWE-863 (incorrect authz), CWE-639 (IDOR), CWE-284, CWE-269 (priv mgmt), CWE-287 (improper auth), CWE-306 (missing auth), CWE-613 (session expiry), CWE-345 (insufficient verification).

Follow the shared output contract. `tool: ["AI:access-control"]`.
