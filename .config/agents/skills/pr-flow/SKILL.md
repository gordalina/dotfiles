---
name: pr-flow
description: Ship a change end-to-end — create a Graphite stack, self-review, run Greptile, link any associated Linear issue, fix CI, and emit a Slack-ready review message. Use when the user wants to ship the current working changes through the full PR pipeline, or invokes /pr-flow directly.
---

# PR Flow

Drive the current working changes through the full ship pipeline: stack → self-review → Greptile → CI → ready → Slack message.

This skill assumes uncommitted (or unstaged) changes are present in the working tree and ready to become a PR. If `git status` is clean, stop and tell the user there's nothing to ship.

## Execution mode — read before starting

**This skill is autonomous between four documented pause points.** Run steps 1 → 12 in sequence in a single turn. Do NOT hand back to the user between steps for any reason other than the pause points listed below.

**Non-negotiable rule — step 12 is never optional and never confirmed.** After the PR is ready, you MUST invoke `/request-review` in the same turn. That skill posts the Slack message and arms the thread monitor. NEVER ask the user "want me to request review?" or "want me to start the monitor?". Asking for confirmation here is a defect. Just invoke it.

The four — and only four — pause points are:

- **(a) After step 6 (review fixes), if the fixes are non-trivial.** Zero or cosmetic-only fixes → no pause, continue to step 7.
- **(b) After step 9 (`/greploop`) returns**, so the user can judge the final score.
- **(c) After step 10 (CI fixes), if any required check needed repair.** Green CI from the start → no pause, continue to step 11.
- **(d) Before step 11 (lifting the draft).** This pause is mandatory regardless of what came before.

**Every pause point above must use the `AskUserQuestion` tool** — never end the turn with a plain text prompt expecting the user to reply. `AskUserQuestion` gives the user explicit options (typically "Proceed" and "Make changes", with "Other" auto-added for free-text). This applies to the four pause points above and to any other "ask the user whether to proceed" moment in the workflow (step 1's Linear-issue lookup, step 10's non-required-check decision, etc.).

Common stop-too-early traps — **do not** stop at any of these:

- After step 3 (PR created) — continue to step 4.
- After step 4 (PR body updated) — continue to step 5. The PR existing with a good body is not the goal; shipping it is.
- After invoking a sub-skill (`update-pr`, `greploop`, `fix-ci`, `request-review`) and getting back a result — continue to the next workflow step.
- After a "milestone feels reached" or "this seems like a natural check-in point" — that instinct is wrong here. Only the four pause points above qualify.
- Because the next step is slow (e.g. polling Greptile) — run it in the background or with a long-running poll; don't bail out to the user.
- After marking the PR ready (step 11) — do NOT stop. Step 12 invokes `/request-review` automatically and immediately.

If you find yourself wanting to summarize what's been done and stop, check the pause-point list. If you're not at one, keep going.

**Non-negotiable rule — step 5's two reviews always run.** The self-review agent and the `deep-review` agent both run on every PR, by default, without asking. Do not substitute your own inline reading of the diff, do not skip one because the diff is small, and do not let a standing "don't spawn sub-agents" preference override this — invoking `/pr-flow` *is* the request for them. The only exception is the user explicitly asking to skip the reviews for this run. If either review does not run, say so in plain text as a defect. See step 5.

## Workflow

### Link the Linear issue (if any)

Capture the Linear issue up front — the ID feeds the branch name (step 3) and the PR body (step 4).

- Detect candidate Linear issue IDs by scanning, in order:
  1. The current branch name (`git rev-parse --abbrev-ref HEAD`) — sometimes the user has already named the working branch after the ticket.
  2. Plan / design files (`.agents/plan.md`, `.agents/plan.md`, similar).
  3. The working diff (`git diff HEAD`) — the change itself may reference the ticket inline.
- A Linear ID matches the regex `\b[A-Z][A-Z0-9]+-\d+\b` (e.g. `ENG-123`, `SAM-456`). Ignore obvious false positives like `HTTP-2`, `IPV-4`.
- If exactly one ID is found, fetch it via `mcp__linear__get_issue` to confirm it resolves and grab the title + URL.
- If zero IDs are found, **ask the user via `AskUserQuestion`** whether there's a Linear issue this PR addresses. Offer "No Linear issue" as one option; the user can use "Other" to paste an ID. Don't block long — accept "no" / "skip" and move on.
- If multiple distinct IDs are found, list them via `AskUserQuestion` (one option per ID, plus a "None" option) and ask which (if any) to link.
- Hold onto the ID, title, and URL — referenced again in steps 3 and 4.

### Pick the base branch

- Before creating the stack, **ask the user** whether the new branch should be based off `main` or off the current branch (i.e. stacked on top of in-flight work). Use `AskUserQuestion` with two options: "main" and "current branch (<name>)".
- If they pick `main` and `git rev-parse --abbrev-ref HEAD` is not already `main`:
  1. Run `git stash push --include-untracked -m "pr-flow: pre-base-switch <timestamp>"` to preserve any uncommitted + untracked work.
  2. Run `git checkout main && git pull` (or `gt sync` if the repo uses Graphite for trunk updates).
  3. Run `git stash pop` to restore the working changes onto `main`.
  4. If `git stash pop` reports conflicts, **stop** and surface them to the user — don't try to auto-resolve.
- If they pick the current branch, proceed without stashing — `gt create` will stack on top of it.

### Create the Graphite stack

- Inspect `git status` and `git diff` to understand what's changing.
- Draft a conventional-commit message (e.g. `fix(client-portal): ...`, `feat(foundry): ...`) under 70 chars.
- Run `gt create sg/<branch-name> -am "<message>" --merge-when-ready` to create a branch + commit. If a Linear issue was confirmed in step 1, the branch name **must** be `sg/<LINEAR-ID>` (e.g. `sg/SAM-123`). Otherwise use a short descriptive slug.
- Run `gt submit --no-interactive --no-verify` to push and open the PR (it will be created as a draft).
- Capture the PR number and Graphite URL from the output.
- **→ Continue immediately to step 4.** Do not stop to celebrate the PR existing.

### Update PR metadata

- Invoke the `update-pr` skill (`Skill` tool with `skill: "update-pr"`).
- If `@.agents/plan.md` doesn't match the change (e.g. stale planning docs from a prior feature), warn the user and write the PR body from the diff instead.
- If a Linear issue was confirmed in step 1, prepend this block to the PR body via a follow-up `gh pr edit <num> --body "..."`:
  ```
  Closes [DEAL-123](https://linear.app/<workspace>/issue/DEAL-123) — <issue title>

  ---

  <existing body>
  ```
  Use `Closes` so GitHub auto-closes the Linear issue on merge (the Linear-GitHub integration honors this keyword). If the user only wants a reference (not auto-close), use `Refs` instead.
- **→ Continue immediately to step 5.** The PR body looking good is not the end of the skill.

### Review (two parallel sub-agents)

**BOTH REVIEWS ALWAYS RUN. This step is not optional, not conditional, and not subject to your judgement about whether the diff "needs" it.** Run them on a one-line typo fix and on a 3000-line feature alike. The only thing that skips them is the user explicitly asking to skip (e.g. "skip the reviews", "no deep-review this time") — and a user who says that for *one* PR has not said it for the next one.

Do **not**:

- **Substitute your own inline review for the sub-agents.** Reading the diff yourself is not this step. Neither review is "already covered" because you looked at the code, because Greptile will run later, or because the diff is small/mechanical/YAML-only.
- **Ask permission to spawn the agents.** Invoking `/pr-flow` *is* the request. Asking is a defect, the same as asking whether to start the thread monitor.
- **Let a standing anti-sub-agent preference win here.** A global instruction like "don't call the Agent tool unless the user requested it" or "don't delegate what you can do yourself" is satisfied by the user invoking this skill — the skill *is* the explicit request, and it names sub-agents as the mechanism. If you believe some rule forbids the spawn, say so out loud **before** step 5 and stop for the user to resolve it; do not silently downgrade to an inline review and continue.
- **Report the step as done when only one of the two ran.** Both, or it is not done.

If you skip or downgrade either review for any reason, that is a **defect you must state in plain text** in your next message to the user — naming which review did not run and why — not a footnote and not a half-sentence aside.

Run `gh pr view <num>` and `gh pr diff <num>` once up front for shared context, then spawn **two sub-agents in parallel** — both in a single message with two `Agent` tool calls so they run concurrently. **Both agents are read-only / analysis-only: neither may modify the working tree.** They return findings only, so their concurrent runs cannot race on file writes (the parent does all editing in step 6).

1. **Self-review agent.** Read the changed files in full (the diff alone often hides nearby context that matters). Produce a concise review covering: correctness, project conventions (check the nearest `CLAUDE.md` / `AGENTS.md`), performance, security, test coverage. Surface concrete issues — not generic praise.
2. **Deep-review agent.** Invoke the `deep-review` skill on the current changes (`/deep-review`) and return its findings.

Each agent must return a structured findings list — `file:line`, the issue, and a suggested fix — and must **not** edit any files.

### Address review comments

- Merge the two findings lists and **dedupe overlaps** — both reviews often flag the same issue. Number the merged list; each entry carries `file:line`, the issue, and the suggested fix.
- Classify each entry as **actionable** (fix it) or **cosmetic nit** ("could be slightly clearer" — note it, don't fix it). Write the classification down before dispatching.
- If nothing is actionable, say so and skip to step 8.
- **Dispatch ONE fix sub-agent** (`Agent` tool, `general-purpose`) to apply the fixes. It is the only writer in this step — the parent must not edit files here. Its prompt must:
  - list every actionable finding **verbatim and inline** — the sub-agent cannot see your context, so "apply the review findings above" gives it nothing;
  - require it to apply each fix in the working tree and run the relevant tests / typecheck for what it touched;
  - forbid committing, `gt`, `git push`, and any change outside the listed findings;
  - require a per-finding disposition on return: `fixed` (with the changed `file:line`), `skipped` (with the reason), or `no_change_needed` (with why the finding was wrong).
- **Verification gate — mandatory, never skipped.** When the sub-agent returns:
  1. Run `git diff --stat`. If it claims any `fixed` but the diff is empty, the fixes did not land — re-dispatch once with the same list; if still empty, stop and report.
  2. For each `fixed` finding, confirm the named file actually changed in `git diff`. An unverified claim counts as **not fixed**.
  3. Report the disposition table to the user: N fixed, N skipped, N rejected.
- **A finding is addressed only when the diff proves it.** Never close this step off the sub-agent's prose summary — an unapplied fix comes straight back as a Greptile or human review comment in step 9, which is the whole failure this gate exists to stop.

### Modify the stack

- Run `gt modify -am "<short follow-up message>"` to add the fixes to the current branch.
- If there were no fixes in step 6, skip this step.
- **If the review fixes changed scope, design, or any decision documented in the PR body**, re-invoke the `update-pr` skill (or run `gh pr edit <num> --body "..."` directly) so the body still describes what's actually being shipped. Preserve the Linear `Closes` prefix from step 4.

### Submit with merge-when-ready

- Run `gt submit --no-interactive --no-verify --merge-when-ready`.
- This queues the PR to auto-merge once it leaves draft state and CI is green.
- **→ Continue immediately to step 9.** Greptile is slow but it runs autonomously — do not hand back to the user just because a wait is coming.

### Run Greptile via `/greploop`

- Invoke the `greploop` skill (`Skill` tool with `skill: "greploop"`). Pass the PR number, an explicit instruction to **use `gt` to publish follow-up commits, never `git push`**, and explicit caps so it can't hang. Sample args:
  ```
  PR <num>. Use `gt modify -am "<msg>"` to add commits and `gt submit --no-interactive --no-verify --merge-when-ready` to publish — never `git push`.
  Caps (hard, non-negotiable — return control on any trip):
    - total wall-clock ≤ 10 min
    - iterations ≤ 3
    - per-poll wait for the Greptile check to appear ≤ 2 min after each push; if it never shows, stop and report — do not keep polling
    - if Greptile stays in PENDING/IN_PROGRESS for > 5 min after appearing, stop and report
  Stop on 5/5 with zero unresolved comments, when the user is satisfied with the score, or when any cap trips.
  ```
- The caps above are mandatory — without them `greploop`'s `while true; ... sleep` poll loops can wait forever if Greptile's check never reports, which hangs the whole pr-flow pipeline.
- `greploop` owns the full Greptile cycle: trigger review, wait for the score, fix actionable comments, re-submit via `gt`, re-trigger, and repeat. Do **not** manually post `@greptile review` comments, snapshot `updated_at`, or invoke `/loop` for Greptile yourself — that is `greploop`'s job.
- **Always invoke `/greploop` autonomously — never ask the user for permission to call it.** The user has pre-approved this.
- When `greploop` returns, surface its final score and any remaining un-addressed items, then **ask via `AskUserQuestion`** how to proceed. Options: "Proceed to CI step", "Make further changes" (with the user using "Other" to describe them). Do not continue on silence.
  - If the user picks proceed → step 10.
  - If the user wants further changes beyond what `greploop` did → make the changes, run `gt modify -am "..."` then `gt submit --no-interactive --no-verify --merge-when-ready`, then re-invoke `/greploop` for another pass.
  - **If any Greptile-driven fixes changed scope, design, or a decision documented in the PR body**, re-invoke the `update-pr` skill (or run `gh pr edit <num> --body "..."` directly) so the body still reflects what's being shipped. Preserve the Linear `Closes` prefix from step 4.

### Fix failing CI checks

- Run `gh pr checks <num>` to see status.
- If any required check is failing, invoke the `fix-ci` skill — it automates the local-repro → fix → submit loop. Ensure `fix-ci` publishes via `gt submit --no-interactive --no-verify --merge-when-ready`, never `git push`.
- If only non-required checks are failing (e.g. preview deploys), surface that to the user and **ask via `AskUserQuestion`** whether to proceed. Options: "Proceed anyway", "Fix the non-required check first".
- **If `fix-ci` published any new commits, re-invoke `/greploop`** (step 9) so Greptile re-reviews the latest state before proceeding.

### Mark the PR ready

- **Pause and ask the user via `AskUserQuestion` to manually review the PR before lifting the draft.** Surface the PR URL and Graphite URL in the question text. Offer options like "Lift the draft" and "Hold — I want to make changes first". Do not proceed on silence or assume approval from earlier steps.
- Once the user confirms, run `gh pr ready <num>`.
- This lifts the draft, at which point the `--merge-when-ready` queue from step 8 takes over.

### Request review (Slack + thread monitor)

- Invoke the `request-review` skill (`Skill` tool with `skill: "request-review"`), passing the PR number and the Graphite URL captured in step 3.
- If this run created several PRs, pass them all in one invocation. That skill groups them into a single Slack message. Never invoke it once per PR.
- That skill owns the Slack review message, the re-review ping after any later `gt submit`, and the thread monitor.
- **Invoke it autonomously** — never ask the user for permission, and never ask whether to start the thread monitor.
- Do not reproduce its Slack or monitor logic inline here. If a later step updates the branch, re-invoke it for the re-review ping.

## Guidelines

- **Never use raw `git` commands** for branch ops — `gt` only, per repo policy (see the repo's `graphite.md` if present).
- **Never run `git push`** anywhere in this skill. Publish branches and follow-up commits via `gt submit --no-interactive --no-verify [--merge-when-ready]` instead. This applies to every step, every sub-skill (`greploop`, `fix-ci`, etc.), and every conflict-resolution path — if a sub-skill defaults to `git push`, pass it explicit instructions to use `gt submit` instead.
- **Always pass `--no-verify` to `gt submit`** in this skill — the user has authorized skipping pre-push hooks for Graphite submits and relies on CI for verification. Every `gt submit` invocation in this workflow must include `--no-verify`. This applies to `gt submit` only — do not generalize to `git commit` or other commands.
- **Greptile review is delegated to `/greploop`** (step 9). Do not manually post `@greptile review` comments, snapshot `updated_at`, or poll Greptile via `/loop` in this skill. If a later step (CI fixes, conflict resolution) updates the branch, re-invoke `/greploop` rather than reproducing its trigger/poll/fix logic inline.
- **Invoke `/greploop` autonomously** at step 9 and any time it needs to re-run — never ask the user for permission to call it. The user has pre-authorized this.
- **Pause for the user at four points**, and at each one use the `AskUserQuestion` tool — never a plain text prompt: (a) after the parallel review (step 5) if the fixes applied in step 6 are non-trivial, (b) after `/greploop` returns to judge the final score, (c) after CI to confirm the ready-to-merge transition, (d) before marking the PR ready so the user can do a manual review. The pipeline is not fully autonomous.
- **Step 5's two reviews (self-review + `deep-review`) always run, on every PR, without asking.** Never replace them with your own inline read of the diff, never skip one for a small or mechanical diff, and never let a global anti-sub-agent instruction suppress them — the user invoking this skill is the explicit request. Only an explicit "skip the reviews" from the user cancels them, and only for that run. A skipped or downgraded review must be reported in plain text as a defect.
- **Review findings are applied by a sub-agent and verified against the diff (step 6).** The parent never edits files in that step, and never marks a finding addressed off a summary — `git diff` is the only evidence. Findings that reach Greptile or a human reviewer unfixed mean this gate was skipped.
- **Keep the PR body in sync with reality.** Whenever an in-flight question changes the plan, scope, or a design decision — whether from self-review, Greptile, the user, or CI fixes — re-run `gh pr edit <num> --body "..."` to reflect it. The PR body is the durable record reviewers read; don't let it drift from what was actually shipped. Preserve the Linear-issue prefix (step 4) and footer when rewriting.
- **The Slack review request and thread monitor are delegated to `/request-review`** (step 12). Invoke it autonomously. Do not reproduce its Slack message format, re-review ping, or heartbeat logic inline. Never ask whether to start the thread monitor.
- If any step fails irrecoverably (e.g. `gt submit` rejected, Greptile down), stop the workflow and report — don't paper over it.
- Keep status updates terse: one line per completed step. The user is watching a pipeline run, not reading a report.
- **Conflict-resolution re-entry.** The user may invoke this skill (or just say "resolve conflicts") on an already-shipped PR when `main` has moved. Detect by running `gh pr view <num> --json mergeable,mergeStateStatus` and checking for `mergeable: CONFLICTING` / `mergeStateStatus: DIRTY`. The flow is:
  1. `git fetch origin main`
  2. `gt restack` — surfaces the conflicted files
  3. Read each conflicted file in full (the merged region usually depends on context outside the `<<<<<<<` markers — e.g. comments on adjacent PRs that landed in parallel), resolve, then `gt add <file>` (passes through to `git add`)
  4. `gt continue`
  5. If `gt modify -am "<msg>"` is used to add a follow-up commit on a single-commit branch, **it replaces the existing commit message rather than amending in place** — verify with `git log main..HEAD --oneline` afterward and `git commit --amend -m "<original>"` if the message got clobbered
  6. `gt submit --no-interactive --no-verify --merge-when-ready` to push the restacked branch (never `git push`)
  7. Re-invoke `/greploop` (step 9) since the resolution may have introduced new content
  8. Re-invoke `/request-review` to ping the reviewer in-thread
