# Deep Review Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `/deep-review` personal skill — 5 parallel specialized review agents plus a synthesis agent — that produces a severity-sorted, confidence-scored report with conflict detection and a go/no-go recommendation.

**Architecture:** Shared context package assembled in Phase 1, 5 agents dispatched in parallel in Phase 2, synthesis agent consolidates in Phase 3. All files live in `~/.claude/skills/deep-review/`.

**Tech Stack:** Claude Code skill system, `gh` CLI for PR operations, Linear MCP for requirements, `kubeconform`/`helm` for infra validation (advisory).

---

## File Map

| File | Responsibility |
|---|---|
| `~/.claude/skills/deep-review/SKILL.md` | Main entry point — invocation syntax, 3-phase flow, error handling |
| `~/.claude/skills/deep-review/context-assembly.md` | Phase 1 — build shared context package from diff/PR/Linear/infra |
| `~/.claude/skills/deep-review/agents/style.md` | Code style reviewer prompt |
| `~/.claude/skills/deep-review/agents/security.md` | Security reviewer prompt |
| `~/.claude/skills/deep-review/agents/architecture.md` | Architecture reviewer prompt |
| `~/.claude/skills/deep-review/agents/requirements.md` | Requirements adherence reviewer prompt |
| `~/.claude/skills/deep-review/agents/infrastructure.md` | Infrastructure compatibility reviewer prompt |
| `~/.claude/skills/deep-review/agents/synthesis.md` | Synthesis agent — consolidate, detect conflicts, recommend |

---

## Task 1: Create SKILL.md

**Files:**
- Create: `~/.claude/skills/deep-review/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: deep-review
description: Use when completing a feature, preparing to merge, or wanting multi-lens feedback before a PR goes to human review — dispatches 5 specialized agents in parallel then synthesizes by severity with conflict detection
---

# Deep Review

Dispatch 5 specialized reviewers in parallel (code style, security, architecture, requirements, infrastructure), then synthesize their findings into a severity-sorted report with conflict detection and a go/no-go recommendation.

## Invocation

```
/deep-review [target] [flags]
```

**Target:**
- *(none)* — working diff (staged + unstaged)
- `42` or `https://github.com/org/repo/pull/42` — GitHub PR

**Flags:**
- `--issue ENG-123` — link a Linear issue explicitly; repeatable
- `--comment` — post findings as inline PR diff comments (requires PR target)
- `--skip style|security|architecture|requirements|infra` — omit a reviewer

## Execution

**Step 1 — Parse invocation**

Extract from the invocation arguments:
- `TARGET_TYPE`: `working-diff` (no target given) or `pr` (number or URL provided)
- `PR_NUMBER`: integer if PR target; derive from URL if needed
- `EXPLICIT_ISSUES`: list from `--issue` flags (may be empty)
- `COMMENT_MODE`: true if `--comment` present
- `SKIPPED_AGENTS`: list from `--skip` flags (may be empty)

**Step 2 — Assemble context package**

Read and follow `context-assembly.md` to produce the shared context package.

**Step 3 — Dispatch review agents in parallel**

Using the Agent tool, dispatch all non-skipped agents **simultaneously in a single message**. Each agent receives the full context package as its prompt input. Agent files:
- `agents/style.md` (skip if `style` in SKIPPED_AGENTS)
- `agents/security.md` (skip if `security` in SKIPPED_AGENTS)
- `agents/architecture.md` (skip if `architecture` in SKIPPED_AGENTS)
- `agents/requirements.md` (skip if `requirements` in SKIPPED_AGENTS)
- `agents/infrastructure.md` (skip if `infra` in SKIPPED_AGENTS)

**Step 4 — Synthesize**

Once all agents complete, dispatch `agents/synthesis.md` with:
- All agent findings arrays combined
- The original context package
- `COMMENT_MODE` and `PR_NUMBER`

## Error Handling

- `--comment` without PR target → print "Warning: --comment requires a PR target. Skipping inline comment posting." and continue
- No Linear issue found and no `--issue` → pass `REQUIREMENTS_MODE=internal-consistency` to requirements agent
- Infrastructure tools not installed → agent notes per-tool with install instructions; review continues
```

- [ ] **Step 2: Verify the file was written correctly**

Read `~/.claude/skills/deep-review/SKILL.md` and confirm:
- YAML frontmatter is valid (name, description fields present)
- Description starts with "Use when..."
- All three phases are described
- Error handling section is present

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/SKILL.md && git commit -m "feat: add deep-review skill entry point (SKILL.md)"
```

If `~/.claude` is not a git repo, skip the commit step and note it.

---

## Task 2: Create context-assembly.md

**Files:**
- Create: `~/.claude/skills/deep-review/context-assembly.md`

- [ ] **Step 1: Write context-assembly.md**

```markdown
# Context Assembly — Phase 1

Build the shared context package before dispatching review agents. Execute each step in order and produce the context package at the end.

## Step 1: Parse Invocation

You should already have from SKILL.md Phase 1 parsing:
- `TARGET_TYPE`: `working-diff` or `pr`
- `PR_NUMBER`: integer (if PR target)
- `EXPLICIT_ISSUES`: list of Linear issue IDs (may be empty)
- `COMMENT_MODE`: true/false

## Step 2: Get the Diff

**If TARGET_TYPE = working-diff:**
```bash
git diff HEAD
```
If that returns nothing, try:
```bash
git diff --cached
```
If both return nothing, warn: "No changes detected in working tree or staging area. Proceeding with empty diff." and continue.

**If TARGET_TYPE = pr:**
```bash
gh pr diff {PR_NUMBER}
```

## Step 3: Get PR Metadata (PR target only)

Skip this step if TARGET_TYPE = working-diff.

```bash
gh pr view {PR_NUMBER} --json title,body,author,headRefName,baseRefName
```

Store: `PR_TITLE`, `PR_BODY`, `PR_AUTHOR`, `HEAD_BRANCH`, `BASE_BRANCH`.

## Step 4: Infer Linear Issues

Run these in order and collect all matching IDs:

**From branch name:**
```bash
git rev-parse --abbrev-ref HEAD
```
Apply regex `[A-Z]+-[0-9]+` to extract any issue IDs (e.g., `ENG-123`, `PLAT-456`).

**From PR title** (if TARGET_TYPE = pr): apply the same regex to `PR_TITLE`.

**From recent commits:**
```bash
git log --oneline -20
```
Apply the same regex to each commit message line.

Combine all found IDs with `EXPLICIT_ISSUES`. Deduplicate. Store as `ALL_ISSUE_IDS`.

**If ALL_ISSUE_IDS is non-empty**, fetch each issue using the Linear MCP:
```
For each ID in ALL_ISSUE_IDS:
  mcp__linear-server__get_issue(issueId: "{ID}")
```
Store each issue's title, description, and state.

**If ALL_ISSUE_IDS is empty:** Set `REQUIREMENTS_MODE = internal-consistency`. Otherwise set `REQUIREMENTS_MODE = linked-issues`.

## Step 5: Locate Infrastructure Files

```bash
# Kubernetes manifests (files containing "kind:")
find . -type f \( -name "*.yaml" -o -name "*.yml" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" \
  | xargs grep -l "^kind:" 2>/dev/null | head -20

# Helm values
find . -path "*/helm/*" -name "values*.yaml" 2>/dev/null | head -10
find . -path "*/charts/*" -name "Chart.yaml" 2>/dev/null | head -10

# CI/CD
find . -path "*/.github/workflows/*" -name "*.yml" 2>/dev/null | head -10
find . -name "Dockerfile*" ! -path "*/.git/*" 2>/dev/null | head -10
```

Store the list as `INFRA_FILES`. For any infra file that appears in the diff (i.e., its path matches a changed file), read its full content and include it in the context package.

## Step 6: Build Changed File Index

**If TARGET_TYPE = working-diff:**
```bash
git diff HEAD --name-only
git diff --cached --name-only
```

**If TARGET_TYPE = pr:**
```bash
gh pr diff {PR_NUMBER} --name-only
```

Deduplicate. For each file, extract from the diff which line ranges were added or modified (the `+` lines in each hunk).

## Step 7: Assemble Context Package

Produce this text block. This is what every review agent will receive as input:

```
## Context Package

**Target:** {working diff | PR #{PR_NUMBER} — "{PR_TITLE}"}
**Requirements Mode:** {linked-issues | internal-consistency}
**Comment Mode:** {enabled | disabled}

### Diff
{full diff output from Step 2}

### PR Metadata
{omit this section entirely if TARGET_TYPE = working-diff}
- **Title:** {PR_TITLE}
- **Description:** {PR_BODY}
- **Branch:** {HEAD_BRANCH} → {BASE_BRANCH}
- **Author:** {PR_AUTHOR}

### Linear Issues
{omit this section if REQUIREMENTS_MODE = internal-consistency}
{for each issue in ALL_ISSUE_IDS:}
**{ISSUE_ID}: {ISSUE_TITLE}**
{ISSUE_DESCRIPTION}

### Infrastructure Files
{list of INFRA_FILES paths}
{for each infra file that appears in the diff: include full file content under a subheading}

### Changed Files Index
{for each changed file: "filename — lines {X}-{Y} modified"}
```
```

- [ ] **Step 2: Verify**

Read `~/.claude/skills/deep-review/context-assembly.md` and confirm:
- All 7 steps are present
- Bash commands are exact (no placeholders)
- The output format section (Step 7) matches the spec's context package format
- `REQUIREMENTS_MODE` logic is correctly captured (inferred issues → linked-issues; no issues → internal-consistency)

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/context-assembly.md && git commit -m "feat: add context-assembly.md for deep-review Phase 1"
```

---

## Task 3: Create agents/style.md

**Files:**
- Create: `~/.claude/skills/deep-review/agents/style.md`

- [ ] **Step 1: Write agents/style.md**

```markdown
# Code Style Reviewer

You are the Code Style reviewer in a multi-agent deep review. Your mandate: review the diff for consistency, formatting, and naming conventions relative to the surrounding codebase.

## Input
You will receive a Context Package. Use the diff and changed files index. Do not fetch or read files outside those referenced in the diff.

## Review Criteria
- **Naming:** Are identifiers (variables, functions, types, constants) consistent with the naming style used in unchanged surrounding code?
- **Formatting:** Indentation, line length, bracket placement — consistent with the existing file?
- **Documentation:** Are exported functions, types, and methods documented per the project's existing convention?
- **Error handling style:** Consistent with how the rest of the codebase returns/wraps errors?
- **Import organization:** Groups and ordering match the project's existing pattern?

## Confidence Self-Assessment

For **each potential finding**, before including it:

1. Score your confidence 0–10 using this calibration:
   - 9–10: Clear, unambiguous violation visible in the diff
   - 7–8: Strong evidence in the diff; minor assumptions about surrounding code
   - 5–6: Possible issue, but limited context makes it uncertain
   - 0–4: Speculative — you cannot point to specific evidence

2. **If confidence < 5:** Look at more context — read adjacent unchanged lines in the diff, or check other changed files for the same pattern. If you still cannot raise confidence to ≥ 5, **drop this finding. Do not include it.**

3. **If confidence 5–6:** Include the finding but add an `uncertainty_note` explaining what additional context would confirm or dismiss it.

4. **If confidence ≥ 7:** Include as a standard finding with `uncertainty_note: null`.

## Output

Return a JSON array and nothing else. No prose, no explanation outside the JSON.

```json
[
  {
    "severity": "Critical|Important|Minor",
    "file": "path/to/file.go",
    "line": 47,
    "description": "Exported function Foo missing doc comment; all other exported functions in this file are documented",
    "agent": "Style",
    "confidence": 8,
    "uncertainty_note": null
  },
  {
    "severity": "Minor",
    "file": "path/to/file.go",
    "line": 23,
    "description": "Error wrapped with fmt.Errorf but surrounding code uses errors.Wrap from pkg/errors",
    "agent": "Style",
    "confidence": 6,
    "uncertainty_note": "Only 2 other error sites visible in diff — may be intentional if this file is being migrated"
  }
]
```

If you have no findings that meet the confidence threshold, return: `[]`
```

- [ ] **Step 2: Verify**

Read `~/.claude/skills/deep-review/agents/style.md` and confirm:
- Confidence self-assessment loop is present with all 4 cases (< 5 drop, 5-6 note, ≥ 7 standard)
- Output format exactly matches the spec (severity, file, line, description, agent, confidence, uncertainty_note)
- "Return JSON and nothing else" instruction is present

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/agents/style.md && git commit -m "feat: add style reviewer agent for deep-review"
```

---

## Task 4: Create agents/security.md

**Files:**
- Create: `~/.claude/skills/deep-review/agents/security.md`

- [ ] **Step 1: Write agents/security.md**

```markdown
# Security Reviewer

You are the Security reviewer in a multi-agent deep review. Your mandate: identify security vulnerabilities, credential exposure risks, and dependency concerns introduced by the diff.

## Input
You will receive a Context Package. Focus on the diff and changed files index. Reference infrastructure files if they appear in the diff.

## Review Criteria
- **Hardcoded secrets:** API keys, tokens, passwords, private keys in code or config
- **Input validation:** Missing or insufficient validation at system boundaries (user input, external API responses, file uploads)
- **Injection vectors:** SQL injection, XSS, command injection, path traversal, template injection
- **Auth/authz gaps:** Missing authentication checks, privilege escalation paths, insecure direct object references
- **Sensitive data in logs:** PII, tokens, credentials appearing in log statements or error messages
- **Dependency risk:** New packages added — flag packages with known CVEs, abandoned maintenance, or excessively large transitive dependency trees
- **Encryption/TLS:** Data transmitted or stored without appropriate encryption
- **Secrets handling:** Token/credential lifecycle — are they properly scoped, short-lived, invalidated on logout?
- **RBAC/permissions:** Overly permissive roles or permissions granted by the change

## Confidence Self-Assessment

For **each potential finding**, before including it:

1. Score confidence 0–10:
   - 9–10: Clear vulnerability — can point to the exact line with no ambiguity
   - 7–8: Strong evidence; minor assumptions about how the code is called
   - 5–6: Possible issue but requires runtime or broader context to confirm
   - 0–4: Speculative

2. **If confidence < 5:** Examine more context — check how the function is called, look at related changed files. If cannot raise to ≥ 5, **drop the finding.**

3. **If confidence 5–6:** Include with `uncertainty_note` explaining what would confirm or dismiss it.

4. **If confidence ≥ 7:** Include as standard.

## Output

Return a JSON array and nothing else.

```json
[
  {
    "severity": "Critical|Important|Minor",
    "file": "src/auth/middleware.go",
    "line": 47,
    "description": "JWT signing secret read directly from os.Getenv with no fallback — will panic if SECRET_KEY is unset",
    "agent": "Security",
    "confidence": 9,
    "uncertainty_note": null
  }
]
```

If no findings meet the confidence threshold, return: `[]`
```

- [ ] **Step 2: Verify**

Read `~/.claude/skills/deep-review/agents/security.md` and confirm:
- Review criteria covers the OWASP top 10 categories relevant to a code diff
- Confidence self-assessment loop matches the spec exactly (same thresholds as style.md)
- Output format matches style.md output format (same fields, same types)

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/agents/security.md && git commit -m "feat: add security reviewer agent for deep-review"
```

---

## Task 5: Create agents/architecture.md

**Files:**
- Create: `~/.claude/skills/deep-review/agents/architecture.md`

- [ ] **Step 1: Write agents/architecture.md**

```markdown
# Architecture Reviewer

You are the Architecture reviewer in a multi-agent deep review. Your mandate: evaluate whether the change fits the system's structural design, whether interfaces are well-defined, and whether upstream or downstream consumers are affected.

## Input
You will receive a Context Package. Consider the full context of what changed, not just individual lines. The PR description and branch context are especially relevant here.

## Review Criteria
- **Breaking changes:** Does the change modify a public interface, exported type, or API contract? Are callers or consumers identified and accounted for in the diff?
- **Structural fit:** Does the change belong in these files/packages? Does it respect existing separation of concerns?
- **Dependency direction:** Does this introduce a dependency that creates cycles or violates the project's layering?
- **Interface design:** Are new interfaces well-defined with single responsibility and clear contracts?
- **Abstraction level:** Are new abstractions at the right level — not premature, not overdue?
- **Dead code:** Does this leave unreachable code paths, unused exports, or orphaned types?
- **Data flow:** Are new data flows clearly defined? Is mutability contained?

## Confidence Self-Assessment

For **each potential finding**, before including it:

1. Score confidence 0–10:
   - 9–10: Clear structural violation visible in the diff with no ambiguity
   - 7–8: Strong evidence; some assumptions about the broader codebase
   - 5–6: Possible issue but requires full codebase context to confirm
   - 0–4: Speculative

2. **If confidence < 5:** Look at more context in the diff — related files, PR description, commit messages. If cannot raise to ≥ 5, **drop the finding.**

3. **If confidence 5–6:** Include with `uncertainty_note`.

4. **If confidence ≥ 7:** Include as standard.

## Output

Return a JSON array and nothing else.

```json
[
  {
    "severity": "Critical|Important|Minor",
    "file": "pkg/api/routes.go",
    "line": 12,
    "description": "Route handler signature changed from (w http.ResponseWriter, r *http.Request) to (ctx context.Context) — breaking change for all 3 files that register handlers via this interface",
    "agent": "Architecture",
    "confidence": 8,
    "uncertainty_note": null
  }
]
```

If no findings meet the confidence threshold, return: `[]`
```

- [ ] **Step 2: Verify**

Confirm output format matches style.md and security.md exactly (same field names and types).

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/agents/architecture.md && git commit -m "feat: add architecture reviewer agent for deep-review"
```

---

## Task 6: Create agents/requirements.md

**Files:**
- Create: `~/.claude/skills/deep-review/agents/requirements.md`

- [ ] **Step 1: Write agents/requirements.md**

```markdown
# Requirements Reviewer

You are the Requirements reviewer in a multi-agent deep review. Your mandate: verify whether the change satisfies its stated requirements, or — when no requirements are linked — assess internal completeness.

## Input
You will receive a Context Package. Check the **Requirements Mode** field:

- `linked-issues`: Linear issues are included in the context package. Review against them.
- `internal-consistency`: No Linear issues were found. Review for completeness and correctness without external requirements.

## Review Criteria

### In `linked-issues` mode
- Does the implementation satisfy each acceptance criterion in the linked issues?
- Are there requirements or acceptance criteria in the issues that have no corresponding code in the diff?
- Does the implementation contradict or misinterpret a stated requirement?
- Are there tests for the acceptance criteria? If tests are absent for a stated requirement, flag it as Important.
- If a requirement is ambiguous, note this in your uncertainty_note rather than assuming intent.

### In `internal-consistency` mode
- Does the implementation appear complete (no obvious stub or missing branches)?
- Are edge cases (empty inputs, nulls, concurrent access, large inputs) handled?
- Is error handling consistent with the surrounding codebase?
- Note at the top of your findings: "No Linear issue linked — running in internal consistency mode."

## Confidence Self-Assessment

For **each potential finding**, before including it:

1. Score confidence 0–10:
   - 9–10: Clear, unambiguous gap between the requirement and the implementation
   - 7–8: Strong evidence of a gap; minor interpretive assumptions
   - 5–6: Possible gap but requirement wording is ambiguous or implementation may address it elsewhere
   - 0–4: Speculative

2. **If confidence < 5:** Re-read the requirement and the diff. Look for related changed files. If cannot raise to ≥ 5, **drop the finding.**

3. **If confidence 5–6:** Include with `uncertainty_note` explaining the ambiguity.

4. **If confidence ≥ 7:** Include as standard.

## Output

Return a JSON array and nothing else. `line` may be null for findings not tied to a specific line.

```json
[
  {
    "severity": "Critical|Important|Minor",
    "file": "src/ratelimit/middleware.go",
    "line": null,
    "description": "ENG-103 requires per-user rate limiting. The diff adds global rate limiting only — no per-user tracking present.",
    "agent": "Requirements",
    "confidence": 8,
    "uncertainty_note": null,
    "mode": "linked-issues"
  },
  {
    "severity": "Minor",
    "file": null,
    "line": null,
    "description": "No Linear issue linked — running in internal consistency mode. Implementation appears complete for the happy path but error handling for the case where the upstream service returns 503 is not present.",
    "agent": "Requirements",
    "confidence": 7,
    "uncertainty_note": null,
    "mode": "internal-consistency"
  }
]
```

If no findings meet the confidence threshold, return: `[]`
```

- [ ] **Step 2: Verify**

Confirm:
- Both `linked-issues` and `internal-consistency` modes are fully described
- Output format adds `mode` field (as per spec) while keeping all other fields from prior agents
- `line` and `file` may be null — this is explicitly shown in the example

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/agents/requirements.md && git commit -m "feat: add requirements reviewer agent for deep-review"
```

---

## Task 7: Create agents/infrastructure.md

**Files:**
- Create: `~/.claude/skills/deep-review/agents/infrastructure.md`

- [ ] **Step 1: Write agents/infrastructure.md**

```markdown
# Infrastructure Reviewer

You are the Infrastructure Compatibility reviewer in a multi-agent deep review. Your mandate: verify that the change is compatible with the Kubernetes/AKS/Azure stack and deployment pipeline.

## Input
You will receive a Context Package including the diff, any infrastructure files found in the repo, and the changed files index.

## Review Criteria

### Static Analysis of Changed Code
- Hardcoded ports, hostnames, or environment-specific values that should be externalized as config
- Filesystem writes or process-level shared state that would break in a multi-replica k8s deployment
- Missing or incorrect environment variable usage for configuration
- Health check or readiness probe compatibility (does the service still expose the expected /health endpoint after this change?)
- Missing graceful shutdown handling for new goroutines/workers/connections

### Infrastructure File Review
When infra files are present in the context package:
- **k8s manifests:** Missing resource limits/requests on new containers, missing liveness/readiness probes, overly permissive RBAC, missing namespace labels
- **Helm values.yaml:** New services not reflected, missing secrets references, replica counts inconsistent with resource constraints
- **CI/CD pipeline:** New dependencies not installed in pipeline image, missing deployment steps for new services, environment variable gaps

### Tool Validation
**kubeconform** — run on any k8s manifest files that appear in the diff:
```bash
which kubeconform 2>/dev/null && kubeconform -strict {manifest_file}
```
If kubeconform is not installed: add a finding noting "kubeconform not installed — run `brew install kubeconform` for manifest schema validation" at Minor severity with confidence 10 (tool availability is a fact, not an inference).

**helm lint** — run if Helm chart files changed:
```bash
which helm 2>/dev/null && helm lint {chart_directory}
```
If helm is not installed and chart files changed: add a Minor finding noting this.

## Confidence Self-Assessment

For **each finding**, before including it:

1. Score confidence 0–10:
   - 9–10: Confirmed by tool output, or explicit config absence with no ambiguity
   - 7–8: Strong evidence from manifest/config review
   - 5–6: Possible issue but depends on runtime environment assumptions
   - 0–4: Speculative

2. **If confidence < 5:** Examine the infrastructure files more carefully. If cannot raise to ≥ 5, **drop the finding.**

3. **If confidence 5–6:** Include with `uncertainty_note`.

4. **If confidence ≥ 7:** Include as standard.

Note: tool availability findings (kubeconform/helm not installed) always have confidence 10 and are always included — they are facts, not inferences.

## Output

Return a JSON array and nothing else.

```json
[
  {
    "severity": "Important",
    "file": "deploy/k8s/deployment.yaml",
    "line": 23,
    "description": "New container 'worker' has no resource limits — will compete unconstrained with other pods on the node",
    "agent": "Infrastructure",
    "confidence": 9,
    "uncertainty_note": null,
    "tool_output": null
  },
  {
    "severity": "Minor",
    "file": "deploy/k8s/deployment.yaml",
    "line": 1,
    "description": "kubeconform reports schema violation: unknown field 'spec.template.spec.containers[0].resources.requests.gpu'",
    "agent": "Infrastructure",
    "confidence": 10,
    "uncertainty_note": null,
    "tool_output": "kubeconform: ERR - deploy/k8s/deployment.yaml - could not find schema for Deployment"
  }
]
```

Set `tool_output` to the relevant tool output string if a tool was run for this finding, null otherwise.
If no findings, return: `[]`
```

- [ ] **Step 2: Verify**

Confirm:
- Both static analysis and tool validation sections are present
- Tool-not-installed case is explicitly handled and always included (confidence 10)
- Output format adds `tool_output` field while keeping all other fields
- Bash commands are exact, not pseudocode

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/agents/infrastructure.md && git commit -m "feat: add infrastructure reviewer agent for deep-review"
```

---

## Task 8: Create agents/synthesis.md

**Files:**
- Create: `~/.claude/skills/deep-review/agents/synthesis.md`

- [ ] **Step 1: Write agents/synthesis.md**

```markdown
# Synthesis Agent

You are the Synthesis agent in a multi-agent deep review. You receive reports from up to 5 specialized reviewers and produce the final consolidated output.

## Input

You receive:
- Up to 5 findings arrays (JSON arrays, one per reviewer that ran)
- The original context package
- `COMMENT_MODE`: true/false
- `PR_NUMBER`: integer (if applicable)

## Step 1: Detect Conflicts

A conflict exists when two agents reference the **same file** with **overlapping or adjacent line ranges** (within ±5 lines of each other) and their findings are contradictory or in tension (one flags something the other approves, or they recommend opposing actions).

For each conflict found, record:
- Agent A name, finding description, confidence score
- Agent B name, finding description, confidence score
- Which agent has higher confidence

## Step 2: Sort and Group

Merge all findings from all agents into one list. Apply these rules:

1. Group by severity: **Critical** first, then **Important**, then **Minor**
2. Within each severity group, sort by confidence descending (highest confidence first)
3. Findings involved in a conflict are included in their severity group as normal AND in the Conflicts section

**Severity definitions:**
- **Critical:** Security vulnerabilities with confidence ≥ 7, breaking API changes, or requirements failures for confirmed acceptance criteria
- **Important:** Non-breaking issues that should be addressed before merge; high-confidence requirements gaps; infra issues that would cause degraded behavior
- **Minor:** Style, doc gaps, low-severity improvements, tool-not-installed notes

## Step 3: Determine Recommendation

Evaluate in order:
1. If any Critical finding has confidence ≥ 8 → **Block**
2. If any Critical finding has confidence 5–7, OR 3+ Important findings → **Fix then ship**
3. If 1–2 Important findings → **Fix then ship**
4. If only Minor findings, or no findings → **Ship**

## Step 4: Format Final Report

Output this exact format:

```
## Deep Review

**Target:** {from context package — e.g., "working diff" or "PR #42 — 'Add user authentication middleware'"}
**Linear:** {issue IDs with how they were found, e.g., "ENG-99 (inferred from branch), ENG-103 (inferred from PR title)" — or "None — internal consistency mode"}
**Reviewers:** {comma-separated list of agents that ran, e.g., "Code Style · Security · Architecture · Requirements · Infrastructure"}

---

### Critical
{for each Critical finding, one bullet:}
- [{Agent} · {confidence}/10] `{file}:{line}` — {description}
{if uncertainty_note is non-null:}
  ↳ *Uncertain: {uncertainty_note}*

### Important
{same format as Critical}

### Minor
{same format}

{Omit any severity section entirely if it has no findings}

---

### Conflicts Between Reviewers
{for each conflict:}
- **{AgentA} ({confidenceA}/10) vs {AgentB} ({confidenceB}/10)** on `{file}:{line_or_range}`: {AgentA description}. {AgentB description}. {Higher-confidence agent}'s assessment takes precedence — {one sentence resolution recommendation}.

{Omit this section entirely if no conflicts}

---

### Recommendation
**{Ship|Fix then ship|Block}.** {2–3 sentences explaining the key factors driving this recommendation.}
```

If there are no findings from any agent:
```
## Deep Review

**Target:** {target}
**Reviewers:** {agents that ran}

### Recommendation
**Ship.** All {N} reviewers found no issues above the confidence threshold.
```

## Step 5: Post Inline Comments (if COMMENT_MODE = true)

Only execute this step if `COMMENT_MODE = true` AND `PR_NUMBER` is set.

For each finding that has a non-null `file` AND non-null `line`, post an inline PR diff comment:

```bash
gh pr review {PR_NUMBER} --comment --body "**[{Agent} · {confidence}/10] {severity}**

{description}
{if uncertainty_note is non-null: "⚠️ Uncertain: {uncertainty_note}"}"
```

Execute each `gh` call and wait for it to complete before the next. If a `gh` call fails, note "Failed to post inline comment for {file}:{line}" in the final report but continue.

After all inline comments are posted (or attempted), post the full formatted report as a top-level PR comment:

```bash
gh pr comment {PR_NUMBER} --body "{full formatted report from Step 4}"
```

## Step 6: Output

Print the final formatted report to the terminal regardless of whether `--comment` was used.
```

- [ ] **Step 2: Verify**

Confirm:
- Conflict detection logic is explicit (same file, ±5 lines, contradictory)
- Recommendation logic covers all cases (Block, Fix then ship, Ship)
- Output format matches the spec exactly, including conditional section omission
- Comment posting is gated on both `COMMENT_MODE = true` AND `PR_NUMBER` set
- Terminal output always happens (Step 6)

- [ ] **Step 3: Commit**

```bash
cd ~/.claude && git add skills/deep-review/agents/synthesis.md && git commit -m "feat: add synthesis agent for deep-review"
```

---

## Task 9: Smoke Test

Verify the skill loads and can be invoked in a project with a git diff.

- [ ] **Step 1: Find a local git repo and make a trivial change**

```bash
# Find any local git repo (pick one you're actively working in)
ls ~/dev   # or wherever your repos live

# Navigate to it and make a trivial change to produce a diff
cd {your-repo}
echo "# test" >> README.md
```

- [ ] **Step 2: Invoke the skill**

```
/deep-review
```

Confirm:
- The skill loads (SKILL.md is read)
- context-assembly.md is read and executed
- A diff is found
- All 5 agent files are read
- Agents are dispatched in parallel
- Synthesis agent runs after all 5 complete
- A formatted report is printed

- [ ] **Step 3: Revert the test change**

```bash
git checkout README.md
```

- [ ] **Step 4: Test PR flow (if a PR is available)**

```
/deep-review {any open PR number}
```

Confirm PR diff is fetched, PR metadata is included in context package, Linear inference runs.

- [ ] **Step 5: Note any issues found during smoke test**

Document any gaps or failures as follow-up tasks. The writing-skills skill requires a formal RED-GREEN-REFACTOR pressure test cycle after this initial implementation — schedule that as a follow-up.
```
