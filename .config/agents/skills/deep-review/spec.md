# Deep Review — Design Spec

**Date:** 2026-05-28
**Status:** Approved, pending implementation

---

## Overview

`/deep-review` is a personal skill that dispatches 5 specialized review agents in parallel, then runs a synthesis agent to produce a consolidated, severity-sorted report with conflict detection and a high-level recommendation. It replaces the single-agent `requesting-code-review` workflow with a multi-lens review optimized for pre-merge quality gates.

---

## Architecture

Three sequential phases:

### Phase 1 — Context Assembly

Before any agents are dispatched, the skill assembles a shared context package:

- **Diff:** Working tree diff (staged + unstaged) when no target is given, or PR diff when a PR number/URL is provided
- **PR metadata:** Title, description, existing comments (when PR target provided)
- **Linear issues:** Inferred from branch name, PR title, and commit messages; supplemented by explicit `--issue` flags; gracefully absent — requirements agent falls back to internal consistency review
- **Infrastructure files:** Helm charts, k8s manifests, CI/CD configs located in the repo
- **Changed file index:** File paths + line numbers, used for `--comment` placement

All 5 review agents receive the same context package.

### Phase 2 — Parallel Review

5 agents dispatched simultaneously, each with a different mandate:

| Agent | Mandate |
|---|---|
| Code Style | Consistency, formatting, naming conventions |
| Security | Vulnerabilities, credential exposure, dependency risk |
| Architecture | Structural fit, interface changes, upstream/downstream impact |
| Requirements | Verify against Linear requirements; internal consistency if no issue found |
| Infrastructure | Compatibility with k8s/AKS/Azure; run kubeconform and similar tools if available |

**Agent self-assessment loop (per finding):**
1. Score confidence 0–10 using calibration: 9–10 very high, 7–8 solid, 5–6 meaningful uncertainty, <5 speculative
2. If < 5: attempt to self-resolve by examining more context, related files, or re-reading the code. If confidence cannot be raised, drop the finding entirely — do not include it
3. If 5–6: include with an uncertainty note explaining what additional context would resolve it
4. If ≥ 7: include as a standard finding

Each agent returns a structured list: `{severity, file, line, description, agent, confidence}`.

### Phase 3 — Synthesis

A synthesis agent receives all 5 reports plus the original context package and produces:

1. Findings grouped by severity (Critical → Important → Minor), with agent name and confidence score inline
2. Explicit callouts where agents disagreed or contradicted each other — confidence scores used to weight the conflict
3. A single-line recommendation: **Ship**, **Fix then ship**, or **Block**

If `--comment` is passed, findings with file + line data are posted as inline PR diff comments via `gh`.

---

## Invocation

```
/deep-review [target] [flags]
```

**Target (optional):**
- No argument → working diff
- `42` → PR number
- `https://github.com/org/repo/pull/42` → PR URL

**Flags:**
- `--issue ENG-123` — explicitly link a Linear issue; repeatable
- `--comment` — post findings as inline PR diff comments (requires PR target)
- `--skip <agent>` — skip a reviewer; valid: `style`, `security`, `architecture`, `requirements`, `infra`

**Examples:**
```
/deep-review                          # working diff, no Linear inference
/deep-review 42                       # PR #42, infer Linear
/deep-review 42 --comment             # PR #42, post inline comments
/deep-review 42 --issue ENG-99        # explicit Linear issue
/deep-review --skip infra             # skip infra agent
```

**Error handling:**
- `--comment` without a PR target → warn and skip comment posting, still run review
- No Linear issue found and no `--issue` passed → requirements agent runs in internal consistency mode, notes it
- Infra tools not installed → findings note it with install instructions, don't fail the review

---

## Output Format

```
## Deep Review

**Target:** PR #42 — "Add user authentication middleware"
**Linear:** ENG-99, ENG-103 (inferred from branch)
**Reviewers:** Code Style · Security · Architecture · Requirements · Infrastructure

---

### Critical
- [Security · 9/10] `src/auth/middleware.go:47` — JWT secret read from env without fallback; will panic in misconfigured environments
- [Architecture · 8/10] `pkg/api/routes.go:12` — Breaking change to route signature affects 3 downstream consumers

### Important
- [Requirements · 6/10] Feature satisfies ENG-99 but ENG-103 (rate limiting) has no coverage
  ↳ *Uncertain: ENG-103 description is vague about scope — may be intentionally deferred*
- [Infrastructure · 7/10] `deploy/k8s/deployment.yaml` — No resource limits set on new container; kubeconform reports schema violation

### Minor
- [Style · 8/10] `src/auth/middleware.go:23` — Exported function missing doc comment
- [Style · 8/10] `src/auth/token.go:8` — Inconsistent error wrapping style vs rest of package

---

### Conflicts Between Reviewers
- **Architecture (8/10) vs Security (9/10)** on `src/auth/middleware.go:31`: Architecture approves the token caching approach as a reasonable pattern; Security flags the same cache as a potential token replay surface. Security's higher confidence takes precedence — recommend reviewing cache TTL and invalidation strategy.

---

### Recommendation
**Fix then ship.** Two Critical issues must be resolved before merge. The JWT panic risk is straightforward to fix. The breaking route change needs a migration path or a major version bump. Important issues should be addressed but are not blockers if tracked.
```

---

## Skill File Structure

```
~/.claude/skills/deep-review/
├── SKILL.md                    # Main skill — invocation, flow, output format
├── agents/
│   ├── style.md                # Code style reviewer prompt template
│   ├── security.md             # Security reviewer prompt template
│   ├── architecture.md         # Architecture reviewer prompt template
│   ├── requirements.md         # Requirements adherence reviewer prompt template
│   ├── infrastructure.md       # Infrastructure compatibility reviewer prompt template
│   └── synthesis.md            # Synthesis agent prompt template
├── context-assembly.md         # Phase 1 context gathering instructions
└── spec.md                     # This document
```

---

## Key Design Decisions

- **Shared context package** ensures all agents evaluate the same evidence, making synthesis and conflict detection meaningful
- **Confidence self-assessment** cuts noise — agents drop speculative findings rather than polluting the report
- **Findings below confidence 5 are dropped entirely** — not surfaced anywhere in the report
- **Synthesis agent weights conflicts** using the confidence scores of the opposing agents
- **`--comment` is opt-in** — inline PR comments only when explicitly requested
- **Infrastructure tools are advisory** — missing tools produce notes, not failures
