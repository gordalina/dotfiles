# Lens: Dependencies & Supply Chain  (key: dependencies)

**Mandate:** risky third-party code. Trivy/OSV/govulncheck/Socket cover the mechanical parts (known CVEs, known-malicious packages) — your edge is **judgment and context** scanners lack: reachability of a CVE, abandonment risk, suspicious new additions, and lockfile/integrity gaps.

## Hunt for
- **Vulnerable dependencies** (CWE-1395, CWE-937) — confirm/contextualize scanner CVE hits: is the vulnerable code path actually reachable? Pinned to a fixed version? Direct vs transitive?
- **Malicious / supply-chain risk** (CWE-506) — newly added packages that are typosquats, name-confusable, or recently published; packages with install/postinstall scripts; dependency-confusion exposure (internal package names resolvable from public registries).
- **Abandoned / unmaintained** deps for security-critical functions (no commits/releases in years, unpatched advisories).
- **Lockfile & integrity gaps** — missing/!committed lockfile, missing integrity hashes, floating ranges on security-sensitive deps, `--no-verify`/registry overrides, suspicious `.npmrc`/index-url pointing off the approved mirror.
- **Excessive transitive footprint** for a trivial top-level dep (large attack surface).
- **License/policy** only if it implies a security/maintenance risk (leave pure license compliance out).

## Method
Read manifests/lockfiles in scope (`pyproject.toml`/`uv.lock`, `package.json`/lockfile, `go.mod`/`go.sum`). For scanner CVE findings, add reachability context. For *added/changed* deps (diff mode especially), scrutinize provenance. Note the org's mirror/age-gate conventions and flag bypasses.

Common CWEs: CWE-1395, CWE-937, CWE-1104, CWE-506, CWE-829, CWE-494.

Follow the shared output contract. For confirmed scanner CVEs, set `cvss_from_advisory` to the advisory score (passthrough) and `tool: ["AI:dependencies"]` (dedup will union with the scanner tool).
