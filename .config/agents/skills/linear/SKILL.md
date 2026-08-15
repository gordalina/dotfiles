---
name: linear
description: Create or update tickets in Linear via the Linear MCP. Use when the user asks to "make a Linear ticket", "file an issue", "open a ticket", "add this to the backlog", or otherwise capture work in Linear. Encodes the workspace's teams, projects, statuses, and labels so you don't have to look them up, and enforces actionable verb-phrased titles.
---

# Linear ticket creation

Create well-formed Linear issues with minimal lookups. The reference data below is for the
**tribeprojects** workspace (`https://linear.app/tribeprojects`). Use it directly instead of
calling `list_teams` / `list_projects` / `list_issue_statuses` / `list_issue_labels` first.

The tool is the Linear MCP `save_issue`. Creating: pass `title` + `team` (both required); omit
`id`. Updating: pass `id` (e.g. `DEAL-123`). `description` is Markdown — use literal newlines, not
`\n`. Set `assignee` (not `assigneeId`); `"me"` works.

## Title rules — actionable verb phrasing (REQUIRED)

A title is a command to do work, not a topic label. **Start with an imperative verb** describing
the action to take, be specific about the object, and keep it scannable.

- Lead with a verb: Add, Fix, Remove, Migrate, Refactor, Wire up, Gate, Enforce, Seed, Pin,
  Investigate, Document, Rename, Deprecate, Surface, Handle, Validate, Backfill.
- Bug reports still get an action title — describe the fix, not the symptom.
- No trailing period. Aim for ≤ 70 chars. Drop filler ("we should", "task to", "ticket for").

| Bad (topic / noun phrase)            | Good (actionable verb phrase)                              |
| ------------------------------------ | ---------------------------------------------------------- |
| HighQ login bug                      | Fix HighQ login rejecting allow-listed emails              |
| MFA stuff                            | Enforce app-layer MFA on id_tokens for the K&E tenant      |
| Walls UAT fixtures                   | Seed Walls/CMV UAT fixtures into stub providers            |
| Client portal matters list          | Hide HighQ "My Site" workspaces from the matters list      |
| EmailEngine mailbox                  | Pin EmailEngine mailbox to the dealos_dev shared mailbox   |
| Slow project list                    | Investigate slow project-list query on the backlog view    |

If the user gives a vague title, rewrite it to verb-first before creating, and briefly note the
rewrite.

## Default behavior

- **Team:** default to **Kirkland & Ellis** (`DEAL`) unless the user names another or context points
  elsewhere. If ambiguous across teams, ask.
- **Status:** new tickets default to **Backlog** (or **Todo** if the user implies it's ready/planned).
- **Project:** pick from the DEAL projects below when the ticket clearly belongs to one; otherwise
  leave unset rather than guessing.
- **Labels:** apply the obvious type label (`Bug` / `Feature` / `Improvement`) plus any domain label
  that clearly fits. Don't over-tag.
- **Security review (REQUIRED):** any new ticket that directly relates to remediating a security
  review — Claude Code review (Rushan), Coverity, or Microsoft Defender findings, plus their
  associated security-review Q&A/tracking — MUST get the `Security Review Remediation` label (team
  label, `#EB5757`). This drives the shared K&E "Security Review Remediation" view. Does NOT apply
  to the separate `PRR Security Audit` (D1–D7) code-audit bucket unless the ticket is genuinely a
  finding from one of those three review sources.
- **Assignee/priority:** only set when the user specifies. After creating, report the identifier and
  URL.

## Reference data (tribeprojects)

Current user: **bo.tembunkiart@tribe.ai** — id `5947ec68-c93f-4e78-a55c-eefcdc16950a`.

### Teams

| Name                     | Key   | ID                                     |
| ------------------------ | ----- | -------------------------------------- |
| Kirkland & Ellis         | DEAL  | `8ee586cd-c5e6-4576-b664-120d0f590f6b` |
| Agent X                  | —     | `5863befd-9bbb-41e6-ae68-46a7c10bba1e` |
| FIS                      | —     | `416b467e-3262-4c6d-9fe3-1bae6d1b3698` |
| Koch                     | —     | `e4c5735b-15d0-4c9f-b46c-a3a7ff6de503` |
| MS-ASN-ContentFreshness  | —     | `e228163b-a8f5-4355-bc07-603fe10b852c` |

### DEAL statuses (`state` field — name works)

`Backlog` · `Todo` · `In Progress` · `Done` · `Canceled` · `Duplicate`

### DEAL projects (`project` field — name works)

| Project                          | Focus                                                       |
| -------------------------------- | ----------------------------------------------------------- |
| DealOS Core                      | Core deal-execution platform (MVP cockpit)                  |
| Client Portal                    | Client-facing deal portal (HighQ, matters list)            |
| Knowledge Graph                  | K&E institutional knowledge infrastructure                  |
| DealOS Platform Backlog (Main)   | General working backlog / roadmap                           |
| Enablement                       | Launch blockers, tester enablement, rollout tasks           |

### DEAL labels (`labels` field — names work)

- **Type:** `Bug`, `Feature`, `Improvement`
- **Discipline:** `Engineering`, `Backend`, `Design Needed`, `Design Audit`, `Developer Experience`,
  `Diligence`, `Infra`
- **Workflow:** `Needs Grooming`, `Draft`, `Risk`
- **Integrations:** `iManage`
- **Security / PRR:** `Security Review Remediation` (REQUIRED on Claude/Coverity/Defender remediation tickets — see Default behavior), `Production Readiness Review`, `PRR Security Audit`, `D1 Auth & Session`,
  `D2 Ethical Walls`, `D3 Audit Logging`, `D4 File Upload Security`, `D5 Rate Limiting`,
  `D6 Authorization`, `D7 PII & Data Exposure`

## When this data is stale

IDs and lists drift. If `save_issue` rejects a team/project/label/status, fall back to the matching
`list_*` tool to refresh, then proceed. For teams other than DEAL, statuses and projects are not
encoded here — look them up with `list_issue_statuses` / `list_projects` scoped to that team.
