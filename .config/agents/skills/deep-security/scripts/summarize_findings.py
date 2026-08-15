#!/usr/bin/env python3
"""Build the WHOLE-SURFACE executive summary over the merged finding set.

Covers every source (all scanners + all AI lenses), so the narrative is
consistent with the severity tiles. The AI synthesis (qualitative themes) is
demoted to a clearly-labeled sub-section — it only ever saw the agent findings.

Verdict honesty: scanner findings bypass adversarial verification, so a scanner
"Critical" is UNVERIFIED (e.g. trivy over-rating a Dockerfile COPY-syntax rule).
A hard block requires a VERIFIED Critical; unverified scanner Criticals/Highs
are surfaced but flagged, not used to force a block.
"""
import argparse, collections, json

ORD = ["Critical", "High", "Medium", "Low", "Info"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--ai-summary", help="synthesis_summary.json (agent-only themes)")
    ap.add_argument("--ran")
    ap.add_argument("--skipped")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    f_all = json.load(open(a.findings))
    ai = json.load(open(a.ai_summary)) if a.ai_summary else {}
    ran = [t.get("name", t) for t in (json.load(open(a.ran)) if a.ran else [])]
    skipped = [t.get("name", t) for t in (json.load(open(a.skipped)) if a.skipped else [])]

    # Triage-dismissed scanner noise is excluded from counts/verdict/view (kept in JSON).
    dismissed = [x for x in f_all if x.get("dismissed")]
    needs_review = [x for x in f_all if x.get("needs_review") and not x.get("dismissed")]
    f = [x for x in f_all if not x.get("dismissed")]

    counts = {s: sum(1 for x in f if x.get("severity") == s) for s in ORD}
    by_tool = collections.Counter(t for x in f for t in (x.get("tool") or ["?"]))
    by_owasp = collections.Counter(x.get("owasp_2025", "Unmapped") for x in f)
    by_owasp_llm = collections.Counter(x["owasp_llm"] for x in f if x.get("owasp_llm"))
    source = collections.Counter(x.get("source_kind", "?") for x in f)

    verified_crit = [x for x in f if x.get("severity") == "Critical" and x.get("verified")]
    scanner_crit = [x for x in f if x.get("severity") == "Critical" and not x.get("verified")]
    verified_high = [x for x in f if x.get("severity") == "High" and x.get("verified")]

    if verified_crit:
        verdict = "block"
        why = f"{len(verified_crit)} verified Critical finding(s)."
    elif verified_high or scanner_crit:
        verdict = "caution"
        bits = []
        if verified_high:
            bits.append(f"{len(verified_high)} verified High")
        if scanner_crit:
            bits.append(f"{len(scanner_crit)} scanner-flagged Critical (UNVERIFIED — confirm before trusting; scanner severity is often inflated, e.g. Dockerfile-syntax rules)")
        why = "; ".join(bits) + "."
    else:
        verdict = "pass"
        why = "Only Low/Info, or nothing."

    agent_n = source.get("agent", 0) + source.get("both", 0)
    scan_n = source.get("scanner", 0) + source.get("both", 0)
    top_owasp = by_owasp.most_common(4)
    noise_note = f" ({len(dismissed)} scanner findings triaged out as noise/not-applicable)" if dismissed else ""
    headline = (f"{len(f)} active findings across {len(ran)} scanners + AI lenses "
                f"({scan_n} scanner, {agent_n} agent-discovered): "
                f"{counts['Critical']} Critical / {counts['High']} High / {counts['Medium']} Medium. "
                f"Top areas: {', '.join(c for c,_ in top_owasp)}.{noise_note}")

    summary = {
        "counts": counts,
        "dismissed_count": len(dismissed),
        "needs_review_count": len(needs_review),
        "verdict": verdict,
        "verdict_rationale": why,
        "headline": headline,
        "source_split": {"scanner": source.get("scanner", 0), "agent": source.get("agent", 0), "both": source.get("both", 0)},
        "by_tool": dict(by_tool.most_common()),
        "by_owasp_2025": dict(by_owasp.most_common()),
        "by_owasp_llm_2025": dict(by_owasp_llm.most_common()),
        "scanners_run": ran,
        "scanners_skipped": skipped,
        "notable": [
            {"severity": x["severity"], "title": x["title"][:90], "cwe": x.get("cwe"),
             "tool": x.get("tool"), "verified": x.get("verified", False),
             "file": x.get("file"), "line": x.get("line")}
            for x in sorted(f, key=lambda y: (ORD.index(y.get("severity", "Info")), not y.get("verified")))
            if x["severity"] in ("Critical", "High")
        ][:12],
        # AI synthesis demoted + clearly scoped to the agent findings only
        "ai_highlights": {
            "scope": "AI lens findings only (semantic/cross-function issues scanners miss)",
            "themes": ai.get("top_themes", []),
            "owasp_hotspots": ai.get("owasp_hotspots", []),
        },
    }
    json.dump(summary, open(a.out, "w"), indent=2)
    print(f"verdict: {verdict} — {why}")
    print(f"headline: {headline}")


if __name__ == "__main__":
    main()
