#!/usr/bin/env python3
"""Merge scanner findings (deterministic) with verified agent findings.

Dedup with agreement-boost (mirrors the workflow's JS dedup). Scanner findings
are tool-confirmed and bypass per-finding adversarial verification; agent
findings arrive already verified. Recomputes severity counts + verdict.
"""
import argparse, json, collections

ORD = ["Info", "Low", "Medium", "High", "Critical"]


def derive_confidence(f):
    """Confidence as a TRUST signal that actually varies, not a near-constant 7.
    Driven by verification/triage outcome + source agreement."""
    if f.get("source_kind") == "both":
        return 10                      # scanner + agent independently agree
    t = f.get("triage")
    if t == "confirmed":
        return 9                       # scanner finding triage-confirmed real
    if t == "adjust":
        return 8                       # real, severity corrected by triage
    if f.get("needs_review") or t == "context_dependent":
        return 4                       # rule real in some instances, FP in others
    if t == "dismissed":
        return 2
    if f.get("source_kind") == "agent":
        # agent self-score, but verification is the stronger signal
        return min(10, (f.get("confidence") or 6) + (2 if f.get("verified") else 0))
    return 6                            # untriaged scanner (diff/quick without triage)


def key(f):
    # Distinct scanner rules must NOT collapse just because a fallback CWE makes
    # them share a class. Prefer rule_id (scanner) and exact line; fall back to
    # cwe/owasp for agent findings (which carry no rule_id).
    cls = f.get("rule_id") or f.get("cwe") or f.get("owasp_2025") or f.get("owasp_2021") or "x"
    return f"{(f.get('file') or '').lstrip('./')}|{cls}|{f.get('line') or 0}"


def merge(scanner, agent):
    m = {}
    for f in scanner + agent:
        k = key(f)
        if k not in m:
            m[k] = dict(f)
            continue
        e = m[k]
        e["tool"] = sorted(set((e.get("tool") or []) + (f.get("tool") or [])))
        if e.get("source_kind") and f.get("source_kind") and e["source_kind"] != f["source_kind"]:
            e["source_kind"] = "both"
            e["confidence"] = min(10, (e.get("confidence") or 7) + 2)
            e["verification_note"] = ("confirmed by scanner + agent. " + (e.get("verification_note") or "")).strip()
        if ORD.index(f.get("severity", "Info")) > ORD.index(e.get("severity", "Info")):
            e["severity"] = f["severity"]
        if not e.get("cwe") and f.get("cwe"):
            e["cwe"] = f["cwe"]
    return list(m.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scanner", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--owasp-map")
    ap.add_argument("--summary-out")
    a = ap.parse_args()
    scanner = json.load(open(a.scanner)) if a.scanner else []
    agent = json.load(open(a.agent)) if a.agent else []
    merged = merge(scanner, agent)
    # Ensure every finding carries OWASP derived from its CWE (agent findings
    # arrive with only a cwe). Keeps findings.json self-consistent for LLMs.
    if a.owasp_map:
        cmap = json.load(open(a.owasp_map))
        cats = cmap["categories"]
        for f in merged:
            if f.get("owasp_2021") and f.get("owasp_2025"):
                continue
            e = cmap["cwe"].get(f.get("cwe") or "")
            if e:
                f["owasp_2021"] = cats["2021"][e["2021"]]
                f["owasp_2025"] = cats["2025"][e["2025"]]
            else:
                f.setdefault("owasp_2021", cats["2021"]["NA"])
                f.setdefault("owasp_2025", cats["2025"]["NA"])
    for f in merged:
        f["confidence"] = derive_confidence(f)
    merged.sort(key=lambda f: -ORD.index(f.get("severity", "Info")))
    json.dump(merged, open(a.out, "w"), indent=2)
    counts = collections.Counter(f.get("severity", "Info") for f in merged)
    counts = {s: counts.get(s, 0) for s in reversed(ORD)}
    verdict = "block" if counts["Critical"] else ("caution" if counts["High"] else "pass")
    if a.summary_out:
        json.dump({"counts": counts, "verdict": verdict,
                   "scanner_n": len(scanner), "agent_n": len(agent), "merged_n": len(merged)},
                  open(a.summary_out, "w"), indent=2)
    print(f"merged {len(scanner)} scanner + {len(agent)} agent -> {len(merged)} ({a.out})")
    print(f"counts: {counts}  verdict: {verdict}")


if __name__ == "__main__":
    main()
