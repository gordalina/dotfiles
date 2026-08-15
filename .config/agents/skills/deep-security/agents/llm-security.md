# Lens: LLM / AI-Application Security  (key: llm-security)

**Mandate:** the **OWASP Top 10 for LLM Applications (2025)** — a *separate* taxonomy from the web Top 10. This codebase is an **agentic LLM app** (agents, tools, prompts, RAG), so the attack surface is the *model's control plane*, not just HTTP routes. Natural-language input IS executable here: sanitizing for SQLi/XSS does nothing against a sentence that re-instructs the agent. No other lens covers this; it's the most under-weighted surface in a web-OWASP review.

## Hunt for (the statically-reviewable LLM risks)

- **LLM01 Prompt Injection — incl. INDIRECT (the big one).** Untrusted content reaching the model's instruction context: user input, **tool/function results, RAG/retrieved documents, fetched web pages, file/email contents, DB rows** concatenated into prompts with no trust boundary. *Indirect* injection (poisoned doc/tool output silently re-instructing the agent) is the highest-impact, most-missed variant. Look for: f-string/format building prompts from external data; tool outputs fed back to the model unfiltered; no separation of system vs untrusted content; missing input/output guardrails. CWE-1427.
- **LLM06 Excessive Agency / tool misuse.** Tools the agent can call that perform **destructive or privileged actions** (delete, send email/message, write files, exec, DB writes, money movement, external API calls) with: no authz scoping to the acting user/tenant, no human-in-the-loop confirmation on irreversible actions, over-broad parameters, or the agent able to invoke tools across a tenant/matter boundary. This is where prompt injection becomes *damage*. CWE-250 / CWE-862 / CWE-732.
- **LLM05 Improper Output Handling.** **LLM output is untrusted** — flag it flowing into a dangerous sink without validation: `eval`/`exec`, SQL, shell/subprocess, file paths, HTML (`dangerouslySetInnerHTML`), deserialization, or as unchecked **tool arguments**. CWE-94/77/502/79.
- **LLM02 Sensitive Information Disclosure** & **LLM07 System-Prompt Leakage.** Secrets/PII/credentials placed *in* system or tool prompts; system prompt or tool schemas echoed to users; the model given access (via tools/context) to data the requesting user isn't authorized for. CWE-200 / CWE-522.
- **LLM08 Vector & Embedding Weaknesses.** RAG retrieval **not scoped to the caller's tenant/permissions** → cross-tenant/cross-matter document leakage through the vector store or retrieval query (coordinate with access-control lens, but the embedding/retrieval path is yours). CWE-285.

## Out of scope here (note, don't deeply chase)
LLM03 Supply Chain (→ dependencies lens), LLM04 Data/Model Poisoning, LLM09 Misinformation, LLM10 Unbounded Consumption — these are runtime/data/ops concerns a static review can't confirm. Mention briefly if you see an obvious code-level enabler.

## Method
Locate the agent/tool definitions, prompt-construction sites, and RAG/retrieval code (grep: `system_prompt`, `tool`, `@tool`, `messages`, `prompt`, `invoke`, `retriev`, `embed`, `rag`, `agent`). For each: trace what untrusted data enters the prompt/context, what the model's output can reach, and what each tool is empowered to do without a gate. The finding is the *flow* (untrusted-content → model → privileged action), not just the presence of an LLM call.

## Output (per the shared contract) — with one addition
Assign a **`cwe`** as usual (for dedup + web-OWASP derivation), AND set **`owasp_llm`** to the LLM Top 10 category, e.g. `"LLM01:2025-Prompt Injection"`, `"LLM06:2025-Excessive Agency"`. `tool: ["AI:llm-security"]`. Example finding fields:
```json
{ "title":"Indirect prompt injection: iManage document text fed into agent prompt unfiltered",
  "severity":"High","confidence":8,"cwe":"CWE-1427","owasp_llm":"LLM01:2025-Prompt Injection",
  "cvss_from_advisory":null,"tool":["AI:llm-security"],"source_kind":"agent",
  "file":"...","line":42,"verification_note":null }
```
