---
name: tdd
description: Drive tasks in @.agents/tasks.json to completion with test-driven development. Invoked with no argument it completes EVERY incomplete task, each in its own sub-agent; invoked with a task id or spec it implements that single task via the specify-encode-fulfill loop.
---

# Test-Driven Development

This skill runs in one of two modes, decided by whether an argument was passed.

$ARGUMENTS

- **If an argument appears above → Worker mode.** Treat it as the specification (or a task id to look up in `@.agents/tasks.json`) and implement that single task. Jump to "Worker mode" below and do **not** loop to other tasks.
- **If no argument appears → Orchestrator mode.** Drive *every* incomplete task to completion, each in its own sub-agent. Follow "Orchestrator mode" next.

## Orchestrator mode — complete ALL tasks, one sub-agent per task, parallel where possible

Your job here is **dispatch, not implementation**. Do NOT do any TDD work, read the source diff, or run tests yourself — delegating each task to a fresh sub-agent is what keeps this context small and is the whole point of this mode.

**Strictly one task per sub-agent.** Never hand two or more tasks to a single sub-agent. Parallelism comes from running many single-task sub-agents at once, not from batching tasks into one.

A task is **ready** when its `passes` is not `true` *and* every id in its `depends_on` refers to a task whose `passes` is `true`. Treat a missing or empty `depends_on` as no prerequisites. Drive the queue in waves:

1. Read `@.agents/tasks.json` and compute the set of **ready** tasks.
2. If there are no incomplete tasks left, every task is done — report the final summary (below) and stop.
3. If there are incomplete tasks but none are ready, the remaining tasks are blocked (a failed/unmet dependency, or a dependency cycle). **Stop and surface this to the user** rather than spinning — name the blocked tasks and what they are waiting on.
4. Spawn one sub-agent (`general-purpose`) per ready task, **all in parallel in a single message** (one tool call per task). Each sub-agent prompt must tell it to:
   - Use the Skill tool to invoke skill `tdd`, passing that one task's id as the argument (this runs the skill in Worker mode for exactly that task).
   - Report back concisely: the task id, what it implemented, the test results that verify it, whether the task now meets its acceptance criteria (`passes: true`), and any blocker.
5. When the whole wave returns, re-read `@.agents/tasks.json` to see which tasks are now `passes: true`.
   - For any task a sub-agent reported as blocked or that is still not passing, **stop and surface the blocker to the user** — do not respawn the same task in a spin loop.
6. Repeat from step 1. Newly-unblocked tasks (whose deps just went green) become ready in the next wave.

Between waves read only `tasks.json`; do not read the working-tree diff.

**Parallel-write caution:** sub-agents in the same wave edit the working tree concurrently. Tasks that were correctly declared independent via `depends_on` should touch disjoint code, so this is safe. If you can already see that two ready tasks will clearly collide on the same files despite lacking a declared dependency, run those two sequentially (dispatch one, wait, then the other) and note the missing `depends_on` as a papercut.

When the queue is empty, report: which tasks were completed, the final test state as reported by the workers, and any papercuts or blockers recorded along the way.

## Worker mode — implement one task

### Selecting the work

The argument identifies the work: a task id to look up in `@.agents/tasks.json`, or a free-form specification to implement directly. Implement **only** that task, not the whole plan. The task description should make the expected interface clear.

Read for context: `@.agents/plan.md` (overall plan), `@.agents/design-discussion.md` (design rationale and trade-offs), `@.agents/tasks.json` (queue and acceptance criteria), `@.agents/progress.txt` (history), `@.agents/papercuts.md` (known rough edges).

### The specify-encode-fulfill loop

1. **Specify**: Derive the specifications for the selected task
2. **Encode**: Encode each specification as an automated test
3. **Fulfill**: Write the code that satisfies the specifications

At a finer grain:

1. Write the list of specifications in scope for this session
2. Encode one specification as a single test
3. Change the code *just barely enough* to make the current test failure go away. Avoid speculative coding: any code written beyond what the current failing test demands is code no test exercises
4. Optionally refactor, but never before the behavior change is green. Never mix a behavior change and a refactor in the same step
5. Return to step 2 until the list is empty

This follows Kent Beck's [Canon TDD](https://tidyfirst.substack.com/p/canon-tdd).

### Translating specifications into tests

Each scenario maps to one test case. Specifications take the form: "under scenario A, X happens; under scenario B, Y happens." Mirror that structure with nested grouping where the test framework supports it:

```
describe the target behavior:
  given scenario A:
    expect specific outcome X
  given scenario B:
    expect specific outcome Y
```

Name each test after the specific behavior it pins down, never after a generic claim of correctness.

**Good:** "returns a 10% discount when the order total is above 100"
**Bad:** "returns the correct discount" or "handles the discount case"

"Correct" is meaningless. Every test asserts the code is correct. What a test exists to specify is *what the correct behavior actually is*. The name should make the expected behavior legible without reading the body.

### Clean the kitchen before you make dinner

Before writing each test, picture the test and where it will live. Does this new behavior slot tidily into the conceptual framework of the area you are touching? If not, consider whether reconceptualizing the existing behavior would make the result more coherent.

If a refactoring is called for, do it now, before starting the new behavior. Keep it as its own step, separate from any behavior change, then continue with the loop. Do not build new behavior on top of a structure that does not fit it.

### Fulfilling the specification

Write only enough code to make the current failing test pass. Never write defensive code that no failing test demands; defensive coding is almost always speculative coding, which is code added without justification or feedback.

These automated reviews replace the human approval steps and are the quality gate for this loop:

1. After writing the test, invoke a subagent with `/test-design-review` to scrutinize the test
2. After writing the application code, invoke a subagent with `/software-design-review` to scrutinize the implementation

Address their findings before moving on. If those commands are unavailable in this project — or you are already running as a sub-agent and cannot spawn a nested one — review the test and code yourself against the same standards.

**Do not commit.** Leave each green behavior change in the working tree, keeping refactors as separate logical steps from behavior changes. The user reviews and commits the work themselves.

### Don't be sloppy

If a pre-existing failure surfaces mid-session, do not work around it. This reasoning is wrong:

> That failure is pre-existing (unrelated to our change, it's in the email sender). Our new and existing tests pass. Are we done?

We do not make dinner in a dirty kitchen. The right move is to stop, stash the in-progress change, fix the pre-existing failure, then resume.

### When the loop is empty

After the task is done and its tests pass:

- Append a concise summary of what you did to `@.agents/progress.txt`
- Mark the task complete in `@.agents/tasks.json` only if it actually meets the acceptance criteria by updating `passes: true`
- Record any small papercuts you noticed in `@.agents/papercuts.md`

Do **not** commit and do **not** push. Leave all changes in the working tree for the user to review and commit.

## Output style

Be extremely concise. Sacrifice grammar for concision.
