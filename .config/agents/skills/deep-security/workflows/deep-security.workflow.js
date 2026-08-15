export const meta = {
  name: 'deep-security',
  description: 'Security lens fan-out + merge/dedup + adversarial verification + synthesis',
  phases: [
    { title: 'Lenses', detail: 'parallel OWASP attack-surface agents' },
    { title: 'Verify', detail: 'severity-tiered adversarial refutation' },
    { title: 'Synthesis', detail: 'executive summary + verdict' },
  ],
}

// ---- args (tolerate args arriving as a JSON string) ----
const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
const MODE = A.mode || 'full'
const EDITION = A.owaspEdition || '2025'
const SCOPE = A.scope || {}
const SCANNER = Array.isArray(A.scannerFindings) ? A.scannerFindings : []
const LENSES = Array.isArray(A.lenses) ? A.lenses : []
const LENS_MODEL = MODE === 'full' ? 'opus' : 'sonnet'
const SYNTH_MODEL = MODE === 'full' ? 'opus' : 'sonnet'

const FINDING = {
  type: 'object',
  properties: {
    title: { type: 'string' }, description: { type: 'string' }, remediation: { type: 'string' },
    severity: { type: 'string', enum: ['Critical', 'High', 'Medium', 'Low', 'Info'] },
    confidence: { type: 'number' }, cwe: { type: 'string' },
    cvss_from_advisory: { type: ['number', 'null'] },
    tool: { type: 'array', items: { type: 'string' } },
    source_kind: { type: 'string' },
    file: { type: 'string' }, line: { type: 'number' },
    verification_note: { type: ['string', 'null'] },
  },
  required: ['title', 'severity', 'cwe', 'file', 'line'],
}
const FINDINGS_SCHEMA = { type: 'object', properties: { findings: { type: 'array', items: FINDING } }, required: ['findings'] }
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' }, reason: { type: 'string' },
    severity_adjustment: { type: ['string', 'null'] }, confidence_in_verdict: { type: 'number' },
  },
  required: ['refuted', 'reason'],
}
const SUMMARY_SCHEMA = {
  type: 'object',
  properties: {
    counts: { type: 'object' }, new_vs_standing: { type: 'object' },
    verdict: { type: 'string', enum: ['block', 'caution', 'pass'] },
    verdict_rationale: { type: 'string' },
    top_themes: { type: 'array', items: { type: 'string' } },
    owasp_hotspots: { type: 'array', items: { type: 'string' } },
    headline: { type: 'string' },
  },
  required: ['counts', 'verdict', 'headline'],
}

const slimScanner = JSON.stringify(SCANNER.map(f => ({ file: f.file, line: f.line, title: f.title, cwe: f.cwe })).slice(0, 200))

// ---- Phase 1: lens fan-out (barrier: dedup needs all lenses + scanner findings together) ----
phase('Lenses')
const lensResults = await parallel(LENSES.map(L => () =>
  agent(
    `${L.prompt}\n\n## Scope\n${JSON.stringify(SCOPE)}\n\n## Already surfaced by scanners (don't re-report; add context only)\n${slimScanner}\n\nReturn structured output {findings:[...]} matching the schema. Assign a CWE to every finding.`,
    { label: `lens:${L.key}`, phase: 'Lenses', schema: FINDINGS_SCHEMA, model: LENS_MODEL, effort: MODE === 'full' ? 'high' : 'medium' }
  ).then(r => (r && r.findings ? r.findings.map(x => ({ ...x, source_kind: 'agent', tool: x.tool && x.tool.length ? x.tool : [`AI:${L.key}`] })) : []))
))
const agentFindings = lensResults.filter(Boolean).flat()

// ---- merge + dedup with agreement-boost (plain JS) ----
function key(f) {
  const cls = f.cwe || f.owasp_2025 || f.owasp_2021 || 'x'
  return `${(f.file || '').replace(/^\.\//, '')}|${cls}|${Math.round((f.line || 0) / 4)}`
}
const merged = new Map()
for (const f of [...SCANNER, ...agentFindings]) {
  const k = key(f)
  if (!merged.has(k)) { merged.set(k, { ...f }); continue }
  const e = merged.get(k)
  e.tool = Array.from(new Set([...(e.tool || []), ...(f.tool || [])]))
  e.source_kind = e.source_kind && f.source_kind && e.source_kind !== f.source_kind ? 'both' : (e.source_kind || f.source_kind)
  if (e.source_kind === 'both') {
    e.confidence = Math.min(10, (e.confidence || 7) + 2)
    e.verification_note = `confirmed by scanner + agent. ${e.verification_note || ''}`.trim()
  }
  // keep the more severe
  const ord = ['Info', 'Low', 'Medium', 'High', 'Critical']
  if (ord.indexOf(f.severity) > ord.indexOf(e.severity)) e.severity = f.severity
  if (!e.cwe && f.cwe) e.cwe = f.cwe
}
const candidates = [...merged.values()]
log(`${candidates.length} candidate findings (${SCANNER.length} scanner + ${agentFindings.length} agent, deduped)`)

// ---- Phase 2: severity-tiered adversarial verification ----
phase('Verify')
function refutePrompt(f) {
  return `${A.verifierPrompt || 'You are an adversarial skeptic — try to REFUTE this security finding.'}\n\n## Candidate finding\n${JSON.stringify(f, null, 2)}\n\n## Scope\n${JSON.stringify(SCOPE)}\n\nReturn the structured verdict.`
}
async function verify(f) {
  const sev = f.severity
  if (sev === 'Low' || sev === 'Info') return { ...f, verified: false } // skip (ship raw)
  const n = (sev === 'Critical' || sev === 'High') ? 3 : 1
  const model = (sev === 'Critical' || sev === 'High') ? 'opus' : 'sonnet'
  const votes = (await parallel(Array.from({ length: n }, (_, i) => () =>
    agent(refutePrompt(f), { label: `verify:${f.file}:${f.line}#${i + 1}`, phase: 'Verify', schema: VERDICT_SCHEMA, model })
  ))).filter(Boolean)
  const refutes = votes.filter(v => v.refuted).length
  if (refutes >= Math.ceil(n / 2)) return null // dropped
  const adj = votes.map(v => v.severity_adjustment).filter(Boolean)
  return {
    ...f,
    severity: adj[0] || f.severity,
    verified: true,
    verification_note: `${f.verification_note || ''} [${n - refutes}/${n} skeptics could not refute]`.trim(),
  }
}
const verified = (await parallel(candidates.map(f => () => verify(f).catch(() => f)))).filter(Boolean)
log(`${verified.length} findings survived verification (${candidates.length - verified.length} refuted)`)

// ---- Phase 3: synthesis ----
phase('Synthesis')
const summary = await agent(
  `${A.synthesisPrompt || 'Summarize these verified security findings into an executive summary.'}\n\n## Verified findings\n${JSON.stringify(verified, null, 2)}\n\nOWASP edition: ${EDITION}. Return the structured summary.`,
  { label: 'synthesis', phase: 'Synthesis', schema: SUMMARY_SCHEMA, model: SYNTH_MODEL, effort: 'high' }
)

return { findings: verified, summary }
