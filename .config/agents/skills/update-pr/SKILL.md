---
name: update-pr
description: Update the GitHub PR for the current branch with a title and description derived from the plan and design discussion files in .agents/. Use when the user wants to update or generate PR metadata from planning documents, or calls this skill directly.
---

# Update PR

Generate and apply a PR title and description from the structured planning documents in `.agents/`.

## Workflow

1. **Read planning documents** — Read `.agents/plan.md` and `.agents/design-discussion.md` from the repo root. If either file is missing, warn the user and proceed with what's available.

2. **Find the PR** — Run `gh pr view` for the current branch. If no PR exists, tell the user and stop.

3. **Generate title** — Derive a concise PR title (under 70 characters) from the plan's problem statement and solution. Use conventional commit format (e.g., `feat:`, `fix:`, `refactor:`).

4. **Generate description** — Build the PR body using this structure:

   ```
   ## Summary
   - 3-5 bullet points covering what changed and why, drawn from the plan's Solution section

   ## Endpoints / API changes
   (if applicable — table from the plan's Endpoints section)

   ## Design decisions
   - Key decisions and their rationale, drawn from design-discussion.md
   - Focus on decisions that reviewers need to understand

   ## Test plan
   - What's tested, drawn from the plan's Testing Decisions section

   ## Out of scope
   - Notable exclusions reviewers might ask about, from the plan's Out of Scope section
   ```

   Omit any section that has no relevant content in the source documents.

5. **Update the PR** — Use `gh pr edit` to apply the title and body. Show the user the PR URL when done.

## Guidelines

- Write for PR reviewers, not for planning. Translate planning language into reviewer-facing language.
- Keep bullets concise — one line each where possible.
- Do not include implementation details that are obvious from the diff (file paths, import changes, etc.).
- Preserve any existing footer (e.g., "Generated with Claude Code") or add one if missing.
