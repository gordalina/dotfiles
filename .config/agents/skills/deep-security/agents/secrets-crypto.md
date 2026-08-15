# Lens: Secrets & Cryptography  (key: secrets-crypto)

**Mandate:** exposed secrets and weak/misused cryptography. Gitleaks covers high-entropy string matches; your edge is **context** — distinguishing a live secret from a test fixture, and spotting crypto *misuse* that pattern matchers miss.

## Hunt for
- **Hardcoded secrets** (CWE-798) — API keys, tokens, passwords, private keys, connection strings in source/config/manifests. Judge liveness: real prod credential (Critical) vs test/example/placeholder (Low/Info). Check `.env` committed, secrets in k8s manifests vs SecretProviderClass/ESO.
- **Weak hashing** (CWE-327, CWE-916) — MD5/SHA1 for passwords or signatures; unsalted hashes; fast hashes for passwords instead of bcrypt/scrypt/argon2.
- **Weak/improper encryption** — ECB mode, static/hardcoded IVs or keys, home-rolled crypto, `DES`/`RC4`, predictable keys.
- **Insecure randomness** (CWE-338) — `random`/`Math.random` for tokens, session ids, password resets, nonces (should be CSPRNG).
- **TLS issues** (CWE-295, CWE-319) — disabled cert verification (`verify=False`, `rejectUnauthorized:false`), plaintext transport for sensitive data, downgrade to http.
- **Secret lifecycle** — over-scoped/long-lived tokens, secrets logged, secrets in URLs/query strings, not rotated/invalidated.

## Method
For each secret-looking literal, determine whether it's reachable in prod and live. For each crypto call, check algorithm, mode, key/IV provenance, and what it's protecting. Cross-reference how the repo *normally* sources secrets (e.g. CSI driver / ESO / 1Password) — a literal that bypasses that is the finding.

Common CWEs: CWE-798, CWE-259, CWE-321, CWE-327, CWE-328, CWE-916, CWE-338, CWE-295, CWE-319, CWE-522.

Follow the shared output contract. `tool: ["AI:secrets-crypto"]`.
