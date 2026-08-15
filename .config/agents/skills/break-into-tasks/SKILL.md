---
name: break-into-tasks
description: Break the current plan into vertical-slice tasks and write them to @.agents/tasks.json
---

Read the plan in @.agents/plan.md and convert it into a structured list of tasks.

These tasks will be implemented later by a separate test-first (`/tdd`) workflow, so each task must be independently verifiable. The `steps_to_verify` for a task are the acceptance criteria a failing test will be written from, so make them concrete and specific (exact behavior, inputs, expected outputs or states), never vague.

Output a JSON array where each item has exactly these fields:
- `id`: a short, stable, unique kebab-case slug for the task (e.g. `login-endpoint`). Other tasks reference it in `depends_on`, so it must be unique within the file and must not change meaning once written.
- `category`: a short grouping label for the task
- `description`: what to build, specific enough to act on
- `steps_to_verify`: an array of concrete, testable acceptance criteria
- `depends_on`: an array of task `id`s that must be complete before this task can start. Use `[]` when the task has no prerequisites. List only *true* prerequisites — a task depends on another only if it genuinely needs that task's code to exist first (e.g. an endpoint that calls a model the other task creates). Do not add ordering dependencies for style or preference: independent tasks (with `[]` or already-satisfied deps) run in parallel under `/tdd`, so spurious dependencies only serialize work that could have run concurrently. Never create a dependency cycle.
- `passes`: always `false`

Where it makes sense, break work into vertical slices rather than horizontal layers. For example, instead of writing all database models first and then all API endpoints, write a single model together with its endpoint as one task. Not all work fits this pattern, so use judgment. Vertical slices also tend to be independent, which lets more tasks run in parallel.

Write the result to `@.agents/tasks.json`. If that file already has tasks in it, overwrite it completely so only the new tasks remain. Create the `@.agents/` directory first if it does not exist. Output valid JSON only: a top-level array, no comments, no trailing commas.

<tasks.json_example>
[
  {
    "id": "login-endpoint",
    "category": "auth",
    "description": "Add POST /login that exchanges email+password for a session token",
    "steps_to_verify": [
      "returns 200 and a token when credentials match a known user",
      "returns 401 when the password is wrong",
      "returns 404 when the email is unknown"
    ],
    "depends_on": [],
    "passes": false
  },
  {
    "id": "logout-endpoint",
    "category": "auth",
    "description": "Add POST /logout that invalidates the caller's session token",
    "steps_to_verify": [
      "returns 204 and the token no longer authenticates subsequent requests",
      "returns 401 when no valid session token is presented"
    ],
    "depends_on": ["login-endpoint"],
    "passes": false
  }
]
</tasks.json_example>
