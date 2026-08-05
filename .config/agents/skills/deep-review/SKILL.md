---
name: deep-review
description: Use when completing a feature, preparing to merge, wanting multi-lens feedback on changes, or whenever the user invokes /deep-review
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
