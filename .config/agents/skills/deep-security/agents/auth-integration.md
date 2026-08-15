# Lens: OAuth / OIDC Auth Integration  (key: auth-integration)

**Mandate:** security of the OAuth 2.0 / OpenID Connect **login handshake** and the client-portal SSO integration — redirect_uri validation, `state`, PKCE, `id_token`/nonce validation, code exchange, token handling, and the session established by the flow. Scanners and the access-control lens miss these: they are protocol-correctness flaws spread across the authorization request, the provider callback handler, and client config — not a single missing authz gate.

**Lane boundary:** access-control owns authz gates, IDOR, and JWT checks on ordinary *API requests*; you own the *OAuth/OIDC login flow itself*, its client configuration, and the tokens/session it mints. secrets-crypto owns a hardcoded `client_secret` as a generic secret — you flag it only when the *flow design* leaks or misuses it (e.g. a secret shipped to a public client).

## Hunt for

- **redirect_uri / post-logout redirect** — not validated against an **exact-match** allowlist; wildcard, prefix, or substring matching; attacker-controllable `redirect_uri`, `next`, or `returnTo` reflected into the redirect after login/logout → open redirect / token leakage (CWE-601).
- **`state` parameter** — missing on the authorization request, or **generated but never verified** on the callback; not bound to the user's session → login CSRF / authorization-code injection (CWE-352).
- **PKCE** — a public client (SPA, mobile, the client portal) doing the authorization-code flow **without** PKCE, or sending `code_challenge` but not enforcing `code_verifier` on exchange (CWE-287).
- **`id_token` / nonce validation** — signature not verified against the provider JWKS; `alg:none` or a symmetric-key confusion accepted; `iss` / `aud` / `exp` unchecked; `nonce` not validated back to the request (CWE-347, CWE-345).
- **Authorization code handling** — code not single-use / no replay protection; code or tokens placed in a URL, referrer, or log; implicit flow or ROPC used where auth-code+PKCE is required (CWE-598, CWE-287).
- **Token handling** — access/refresh tokens in `localStorage` or a non-`HttpOnly` / non-`Secure` / missing-`SameSite` cookie; tokens in query strings; no refresh rotation; over-broad scopes requested (CWE-522, CWE-1004).
- **Session establishment** — the session id is not regenerated when the OAuth callback logs the user in → session fixation across the exchange (CWE-384); logout does not revoke the provider session / refresh token.
- **Client configuration** — `client_secret` embedded in a public/browser client; a confidential client's secret reachable from frontend code; grant types or scopes broader than the client needs.

## Method

Trace the **whole flow end to end**, not one endpoint: authorization-request construction → provider redirect → callback handler → code→token exchange → `id_token`/access-token validation → session establishment → logout. For each control (`state`, PKCE, `redirect_uri` allowlist, nonce, signature/`iss`/`aud`/`exp`), confirm it is not just *present* but *enforced* — the classic bug is a `state`/`nonce` that is generated and sent but never compared on return. Read the real callback handler and the OAuth client config; follow the token from mint to storage to use.

Common CWEs: CWE-352 (CSRF / missing state), CWE-601 (open redirect via redirect_uri), CWE-347 (improper signature verification), CWE-345 (insufficient authenticity verification), CWE-287 (improper authentication), CWE-384 (session fixation), CWE-522 (insufficiently protected credentials), CWE-598 (sensitive data in URL/GET).

Follow the shared output contract. `tool: ["AI:auth-integration"]`.
