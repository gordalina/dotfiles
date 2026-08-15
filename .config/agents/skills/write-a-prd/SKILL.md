---
name: write-a-prd
description: Create a PRD through user interview, codebase exploration, and module design, then write it to @.agents/plan.md and a design discussion to @.agents/design-discussion.md. Use when user wants to write a PRD, create a product requirements document, or plan a new feature.
model: fable
effort: high
---

This skill is invoked when the user wants to create a PRD. The user will give you comments about the specific PRD they want; you are responsible for all output file placement yourself (see step 5), so the user does not need to specify where files go. You may skip steps if you don't consider them necessary.

1. Ask the user for a long, detailed description of the problem they want to solve and any potential ideas for solutions.
2. Explore the repo to verify their assertions and understand the current state of the codebase.
3. Interview the user until the design is settled — keep pulling on threads while real ambiguity remains, but match the depth to the feature's size; don't interrogate past the point of useful signal. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.
4. Sketch out the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep modules that can be tested in isolation.
- A deep module (as opposed to a shallow module) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.
Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.
5. Once you have a complete understanding of the problem and solution, write the following two files. Create the `@.agents/` directory if it does not already exist.
   - `@.agents/plan.md`: the PRD, written using the template below. If this file already has contents, replace its contents.
   - `@.agents/design-discussion.md`: a record of the decisions made during this discussion, written using the design discussion template below, with one entry per significant decision. If this file already exists, replace its contents.
   These artifacts feed break-into-tasks, which derives concrete test criteria from the User Stories and Testing Decisions. Write those sections concretely enough (observable behavior, inputs, expected outputs) that they can become acceptance criteria without re-interviewing

<prd-template>
## Problem Statement
The problem that the user is facing, from the user's perspective.
## Solution
The solution to the problem, from the user's perspective.
## User Stories
Aim for coverage: every actor and every meaningful path should appear. Length is a byproduct of thoroughness, not a goal — don't pad with restatements. Create a numbered list of user stories. Each user story should be in the format of:
1. As an <actor>, I want a <feature>, so that <benefit>
<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>
This list of user stories should be extremely extensive and cover all aspects of the feature.
## Implementation Decisions
A list of implementation decisions that were made. This can include:
- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions
Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.
## Testing Decisions
A list of testing decisions that were made. Include:
- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)
## Out of Scope
A description of the things that are out of scope for this PRD.
## Further Notes
Any further notes about the feature.
</prd-template>

<design-discussion-template>
A section for each significant decision made during the discussion, in the order the decisions were resolved. For each decision:

### <Short title of the decision>
**Decision:** What was ultimately decided.
**Alternatives considered:** The other options that were on the table.
**Rationale:** Why the chosen option won out over the alternatives, including any tradeoffs accepted.
</design-discussion-template>