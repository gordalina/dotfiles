---
name: test-design-review
description: Review test code against test design guidelines — testing behavior not implementation, specification-style naming, Arrange-Act-Assert structure, asserting observable outcomes over mock calls, and an appropriate level of abstraction — surfacing violations grouped by guideline and suggesting fixes. Use when the user wants a design-quality review of their tests (or the current diff's tests), or invokes /test-design-review.
---

# Test Design Review

When invoked, review the specified tests (or the diff if none specified) against the guidelines in this document.

Important: use a SEPARATE AGENT which does not share your context.

For each violation found, show the offending code and suggest a fix. Group by guideline.

Frontend tests are TypeScript -- Vitest for units and components, Playwright for
browser and system tests. Backend tests are Python with pytest. Each example
below uses whichever stack fits the scenario it illustrates; the principles apply
to both.

## Core Principle

Tests are executable specifications. A specification answers: "In scenario X, what should happen?"

## Specification Format

Good: "When the user submits an empty form, display a validation error."
Good: "When the API returns 500, show a graceful error message."
Good: "When no records exist, display 'No results found'."

Bad: "It works correctly." (What does 'correctly' mean?)
Bad: "It handles errors." (Which errors? How?)
Bad: "It validates input." (What validation? What happens on failure?)

## Test Behavior, Not Implementation Details

Bad:
```ts
import { describe, expect, it } from 'vitest'

describe('tick', () => {
  it("marks the particle's position blue", () => {
    const world = new World(10, 10)

    world.tick()

    expect(world.colorAt(5, 0)).toBe(0x0000ff)
  })
})
```

Good:
```ts
import { describe, expect, it } from 'vitest'

describe('when a particle touches a grid cell', () => {
  it("turns the cell the particle's color", () => {
    const world = new World(10, 10)
    const particleColor = world.particleColor()
    const { x, y } = world.particlePosition()

    world.tick()

    expect(world.colorAt(x, y)).toBe(particleColor)
  })
})
```

## When Capturing Scenarios, Describe the Essence

The scenario name should describe the behavior, not the mechanism. In TypeScript
it's the `describe`/`it` string; in Python it's the test function name plus its
docstring.

Bad:
```ts
describe('scope=failed', () => {
```
```python
def test_scope_failed():
```

Good:
```ts
describe('rerunning only failed tests', () => {
```
```python
def test_rerunning_only_failed_tests():
    """When the user reruns with scope=failed, only the failed tests run again."""
```

## Avoid Arbitrariness

### Avoid Index-Based Lookups in Tests

Using `[0]` or `[-1]` to retrieve records in tests is fragile because it depends
on ordering, which can change unexpectedly. Instead, assert on an explicit query
and a count delta:

Bad:
```python
await client.post("/repositories", json={"repo_full_name": "jasonswett/ductwork"})
repository = (await db.execute(select(RepositoryDB))).scalars().all()[-1]
assert repository.github_account == github_account_jasonswett
```

Good:
```python
from sqlalchemy import func, select

async def repo_count() -> int:
    result = await db.execute(
        select(func.count())
        .select_from(RepositoryDB)
        .filter_by(github_account=github_account_jasonswett)
    )
    return result.scalar_one()

before = await repo_count()

await client.post("/repositories", json={"repo_full_name": "jasonswett/ductwork"})

assert await repo_count() == before + 1
```

## Make Assertions About What's Essential, Not What's Incidental

Only assert what matters. Don't assert things that are:
- Implied by other assertions (if checking the response body, don't also check `status_code` - if it wasn't successful, the body check would fail)
- Implementation details rather than behavior
- Just noise that makes the test longer without adding meaning

Bad:
```python
assert resp.status_code == 200  # redundant noise
assert "deleted_item" not in resp.text
```

Good:
```python
assert "deleted_item" not in resp.text
```

If the response wasn't successful, the body assertion tells you something went wrong. The `status_code` check adds nothing.

## Don't Mix Levels of Abstraction

Bad:
```ts
import { expect, test } from '@playwright/test'

test.describe('Rerun test suite run', () => {
  // ... existing tests ...

  test.describe('Rerun Failed button', () => {
    test.describe('when the test suite run has failed tests', () => {
      let testSuiteRun: TestSuiteRun

      test.beforeEach(async ({ page, context }) => {
        await context.addInitScript(() =>
          window.localStorage.setItem('feature.rerun', 'true'),
        )
        await page.route('**/api/k8s/**', (route) =>
          route.fulfill({ status: 200, body: '{}' }),
        )
        await page.route('**/api/auth/can-access', (route) =>
          route.fulfill({ status: 200, body: 'true' }),
        )

        testSuiteRun = await createTestSuiteRun({ withFailedRun: true })
        await createTestCaseRun({ task: testSuiteRun.tasks[0], status: 'failed' })
        await login(page, testSuiteRun.repository.user)
      })

      test('displays the Rerun Failed button', async ({ page }) => {
        await page.goto(testSuiteRunPath(testSuiteRun))
        await expect(
          page.getByRole('button', { name: 'Rerun Failed' }),
        ).toBeVisible()
      })
    })
  })
})
```

Good:
```ts
import { expect, test } from '@playwright/test'

test.describe('Rerun Failed button', () => {
  test.describe('when the test suite run has failed tests', () => {
    let testSuiteRun: TestSuiteRun

    test.beforeEach(async ({ page }) => {
      testSuiteRun = await createTestSuiteRun({ withTask: true })
      await createTestCaseRun({ task: testSuiteRun.tasks[0], status: 'failed' })
      await login(page, testSuiteRun.repository.user)
    })

    test('displays the Rerun Failed button', async ({ page }) => {
      await page.goto(testSuiteRunPath(testSuiteRun))
      await expect(
        page.getByRole('button', { name: 'Rerun Failed' }),
      ).toBeVisible()
    })
  })
})
```

## Avoid forward reference

In the below example, `task_id` is referred to before it's defined -- in Python this raises `UnboundLocalError`.

Bad:
```python
from unittest.mock import MagicMock

class TestDockerComposeProjectName:
    def test_returns_task_prefix_for_non_empty_task_id(self):
        executor = MagicMock(task_id=task_id)  # task_id is not defined yet
        worker = Worker(executor)
        task_id = "123"

        assert worker.docker_compose_project_name() == "task-123"
```

Better to do it the other way around.

Better:
```python
class TestDockerComposeProjectName:
    def test_returns_task_prefix_for_non_empty_task_id(self):
        task_id = "123"
        executor = MagicMock(task_id=task_id)
        worker = Worker(executor)

        assert worker.docker_compose_project_name() == "task-123"
```

Even better: just hard-code it.
```python
class TestDockerComposeProjectName:
    def test_returns_task_prefix_for_non_empty_task_id(self):
        worker = Worker(MagicMock(task_id="123"))

        assert worker.docker_compose_project_name() == "task-123"
```

## Don't Assert on the URL

Asserting on the URL (`expect(page).toHaveURL(...)`) is the wrong level of abstraction -- it's too tightly coupled to the routing. Instead, assert on what the user sees on the page.

Bad:
```ts
test('redirects to the repositories page', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL('/repositories')
})
```

Good:
```ts
test('redirects to the repositories page', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Repositories')).toBeVisible()
})
```

## Assert on Observable Outcomes, Not Method Calls

When testing whether something happened (or didn't happen), assert on the observable end result rather than on whether a specific method was called. Mock-based assertions like `mock.assert_called_once_with(...)` test means (was this method called?) rather than ends (did the thing actually happen?).

Bad:
```python
from unittest.mock import MagicMock, patch

def test_queues_the_task():
    worker_pool = MagicMock()
    with patch("src.jobs.WorkerPool", return_value=worker_pool):
        QueueUnqueuedTasksJob().perform()

    worker_pool.queue_task.assert_called_once_with(task)
```

Good:
```python
@pytest.mark.asyncio
async def test_queues_the_task(db_session):
    before = await task_event_count(db_session, name="queued")

    await QueueUnqueuedTasksJob().perform()

    assert await task_event_count(db_session, name="queued") == before + 1
```

The bad version tests that a specific method was called on a specific object -- pure implementation. The good version tests the observable outcome: a "queued" event was created. If the implementation changes (different class, different method name), the good test still works as long as the end result is the same.

Stub only what you must (external services like k8s calls), and let the real code run so you can assert on real outcomes.

## Test Ends, Not Means

When testing performance optimizations like caching, don't assert on the caching mechanism (an implementation detail). Assert on the observable difference: fewer database queries.

Bad:
```python
@pytest.mark.asyncio
async def test_caches_the_result(test_suite_run):
    await test_suite_run.duration()

    assert cache.get(f"test_suite_run/{test_suite_run.uuid}/duration") is not None
```

Good:
```python
@pytest.mark.asyncio
async def test_does_not_query_the_database_on_subsequent_calls(engine, test_suite_run):
    await test_suite_run.duration()

    query_count = await count_queries(engine, test_suite_run.duration)

    assert query_count == 0
```

The bad version is coupled to the caching mechanism (a specific cache store and key). If you switch to memoization, a database column, or a different cache store, the test breaks even though the behavior is the same. The good version tests the essential outcome: no redundant database queries.

Bad:
```python
@pytest.mark.asyncio
async def test_includes_unsubscribe_link_in_email_body():
    await TestSuiteRunResultNotification.send_notifications()

    assert "stop receiving these emails" in (await last_sent_email()).body
```

Good:
```python
import re

@pytest.mark.asyncio
async def test_unsubscribe_link_disables_result_emails(db_session, client):
    """Following the unsubscribe link disables result emails for the repository."""
    test_suite_run = await create_test_suite_run(db_session, cached_status="Passed")
    repository = test_suite_run.repository
    await TestSuiteRunResultNotification.send_notifications()

    body = (await last_sent_email()).body
    unsubscribe_path = re.search(r'href="([^"]*unsubscribe[^"]*)"', body).group(1)

    await client.get(unsubscribe_path)

    await db_session.refresh(repository)
    assert repository.send_test_suite_run_result_emails is False
```

## Maintain an Appropriately High Level of Abstraction

Bad:
```python
from sqlalchemy import event

@pytest.mark.asyncio
async def test_queries_the_database_only_once(engine):
    dispatcher = TestSuiteRunDispatcher(cluster_cpu_headroom_millicores=72000)

    query_count = 0

    def on_execute(*args):
        nonlocal query_count
        query_count += 1

    event.listen(engine.sync_engine, "before_cursor_execute", on_execute)
    await dispatcher.test_suite_runs_with_undispatched_tasks()
    count_after_first_call = query_count
    await dispatcher.test_suite_runs_with_undispatched_tasks()
    event.remove(engine.sync_engine, "before_cursor_execute", on_execute)

    assert query_count == count_after_first_call
```

What's happening in this test? I'm assaulted with a dense block of incidental
details! The following is much clearer. It hides incidental details and shows
me the essence of the test.

Good:
```python
@pytest.mark.asyncio
async def test_queries_the_database_only_once(engine):
    dispatcher = TestSuiteRunDispatcher(cluster_cpu_headroom_millicores=72000)

    await count_queries(engine, dispatcher.test_suite_runs_with_undispatched_tasks)
    second_call_count = await count_queries(
        engine, dispatcher.test_suite_runs_with_undispatched_tasks
    )

    assert second_call_count == 0


async def count_queries(engine, work) -> int:
    count = 0

    def on_execute(*args):
        nonlocal count
        count += 1

    event.listen(engine.sync_engine, "before_cursor_execute", on_execute)
    try:
        await work()
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", on_execute)
    return count
```

Note carefully that the helper `count_queries` appears *after* the test, since
the helper itself is an incidental detail, not part of the essential meaning of
the test.

## Don't Use Hacks to Test Private Methods

Never reach past an access modifier to call a private method -- in TypeScript via
an `as any` cast or bracket access (`obj['privateMethod']()`), in Python by
calling an underscore-prefixed method (`obj._private()`) or its name-mangled form
(`obj._Class__private()`). If you feel yourself wanting to test a method directly
but you can't because it's private, just make it public. It's usually a quite
acceptable price to pay.

## Don't Tightly Couple Tests to Implementation Details

Bad:

```ts
import { expect, test } from '@playwright/test'

test.describe('when a test suite run finishes', () => {
  test('shows the finished status in the sidebar', async ({ page }) => {
    await page.goto(testSuiteRunPath(repository, testSuiteRun))

    await expect(page.getByTestId('test-suite-run-list')).toContainText('Running')

    // The following line is the bad part
    await updateTask(task, {
      jsonOutput: JSON.stringify({ summary: { failure_count: 0 } }),
    })

    await postTaskFinishedEvent(task)

    await expect(page.getByTestId('test-suite-run-list')).toContainText('Passed', {
      timeout: 3_000,
    })
  })
})
```

Good:

```ts
import { expect, test } from '@playwright/test'

test.describe('when a test suite run finishes', () => {
  test('shows the finished status in the sidebar', async ({ page }) => {
    await page.goto(testSuiteRunPath(repository, testSuiteRun))

    await expect(page.getByTestId('test-suite-run-list')).toContainText('Running')

    await updateTask(task, { exitCode: 0 })

    await postTaskFinishedEvent(task)

    await expect(page.getByTestId('test-suite-run-list')).toContainText('Passed', {
      timeout: 3_000,
    })
  })
})
```

## Use an Arrange, Act, Assert Format

Bad:
```ts
import { expect, test } from '@playwright/test'

test.describe('Sidebar test suite run status', () => {
  let task: Task
  let testSuiteRun: TestSuiteRun
  let repository: Repository

  test.beforeEach(async ({ page }) => {
    task = await createTask({ dispatched: true })
    testSuiteRun = task.testSuiteRun
    repository = testSuiteRun.repository

    await testSuiteRun.cacheStatus()
    await login(page, repository.user)
  })

  test.describe('when a test suite run finishes', () => {
    test('shows the finished status in the sidebar', async ({ page }) => {
      await page.goto(testSuiteRunPath(repository, testSuiteRun))

      await expect(page.getByTestId('test-suite-run-list')).toContainText('Running')

      await updateTask(task, { exitCode: 0 })

      await expect(page.getByTestId('test-suite-run-list')).toContainText('Passed')
    })
  })
})
```

Good:
```ts
import { expect, test } from '@playwright/test'

test.describe('Sidebar test suite run status', () => {
  // Beginning of Arrange
  let task: Task
  let testSuiteRun: TestSuiteRun
  let repository: Repository

  test.beforeEach(async ({ page }) => {
    task = await createTask({ dispatched: true })
    testSuiteRun = task.testSuiteRun
    repository = testSuiteRun.repository

    await testSuiteRun.cacheStatus()
    await login(page, repository.user)
  })
  // End of Arrange

  test.describe('when a test suite run finishes', () => {
    test.beforeEach(async ({ page }) => {
      // Beginning of Act (make the test suite run finish)
      await page.goto(testSuiteRunPath(repository, testSuiteRun))

      await expect(page.getByTestId('test-suite-run-list')).toContainText('Running')

      await updateTask(task, { exitCode: 0 })
      // End of Act
    })

    test('shows the finished status in the sidebar', async ({ page }) => {
      // Beginning of Assert
      await expect(page.getByTestId('test-suite-run-list')).toContainText('Passed')
      // End of Assert
    })
  })
})
```

## No Speculative Coding

```ts
await expect(page.getByText('Passed')).toBeVisible({ timeout: 3_000 })
```

Is the `timeout` really needed, or was it just cargo culted? Playwright already
auto-waits. Scrutinize such choices.

## Miscellaneous

Never forcibly set private state to set up a test -- in TypeScript by casting with
`as any`, `Reflect.set`, or `Object.assign`; in Python by assigning to an
underscore-prefixed attribute or using `object.__setattr__`. In cases where it
seems like reaching into private state is the only option, that's probably a sign
of poor design. In that case you should pause, try to find the poor design, and
suggest a specific refactor.
