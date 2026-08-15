export const meta = {
  name: 'scanner-triage',
  description: 'Batch-triage scanner rule-classes: real vs noise vs mis-severity',
  phases: [{ title: 'Triage', detail: 'parallel batch verifiers over rule-class slices' }],
}

const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
const RULES_PATH = A.rulesPath           // abs path to rule_groups.json (agents read their slice)
const TOTAL = A.total || 0               // number of rule-classes
const BATCH = A.batchSize || 12
const MODEL = A.model || 'sonnet'
const SPEC = A.triageSpecPath            // abs path to agents/scanner-triage.md

const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          verdict: { type: 'string', enum: ['confirmed', 'dismissed', 'adjust', 'context_dependent'] },
          adjusted_severity: { type: ['string', 'null'] },
          reason: { type: 'string' },
        },
        required: ['id', 'verdict'],
      },
    },
  },
  required: ['verdicts'],
}

phase('Triage')
const ranges = []
for (let i = 0; i < TOTAL; i += BATCH) ranges.push([i, Math.min(i + BATCH, TOTAL)])
log(`${TOTAL} rule-classes → ${ranges.length} triage batches of ${BATCH}`)

const results = await parallel(ranges.map(([s, e], i) => () =>
  agent(
    `First Read the triage spec at '${SPEC}' and follow it exactly. Then read the rule-classes file at '${RULES_PATH}' (a JSON array) and triage ONLY entries at indices ${s}..${e - 1} (0-based, inclusive). For each, open its sample file(s) to judge. Return {verdicts:[...]} with exactly one entry per rule-class id in that index range.`,
    { label: `triage:${s}-${e - 1}`, phase: 'Triage', schema: VERDICTS, model: MODEL, effort: 'medium' }
  ).then(r => (r && r.verdicts ? r.verdicts : []))
))

const verdicts = results.filter(Boolean).flat()
const counts = verdicts.reduce((m, v) => ((m[v.verdict] = (m[v.verdict] || 0) + 1), m), {})
log(`verdicts: ${JSON.stringify(counts)}`)
return { verdicts }
