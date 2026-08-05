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
If both return nothing, stop and tell the user: "No changes detected in working tree or staging area. Nothing to review." Do not continue.

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

**From recent commits (PR target only):**
Skip this sub-step if `TARGET_TYPE = working-diff`. For working-diff mode, the git log reflects the full repo history, not the current change — scanning it produces unrelated issue IDs.

If `TARGET_TYPE = pr`:
```bash
git log --oneline origin/{BASE_BRANCH}..HEAD
```
Apply the same regex to each commit message line.

Combine all found IDs with `EXPLICIT_ISSUES`. Deduplicate. Store as `ALL_ISSUE_IDS`.

**If ALL_ISSUE_IDS is non-empty**, fetch each issue using the Linear MCP:
```
For each ID in ALL_ISSUE_IDS:
  Invoke the Linear MCP tool `mcp__linear-server__get_issue` with parameter `issueId` set to the ID string.
  If the tool returns an error (issue not found), skip that ID and continue to the next.
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
find . -path "*/.github/workflows/*" -name "*.yml" \
  ! -path "*/.venv/*" ! -path "*/node_modules/*" 2>/dev/null | head -10
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

Note: Lines beginning with `{for each...}` below are loop directives — expand them into repeated content, do not copy them literally into the output.

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
