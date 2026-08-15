#!/usr/bin/env python3
"""Week-over-week delta between two deep-security findings sets.

The weekly audit leads with WHAT CHANGED (new + resolved), not the full standing
list — that's what keeps the Slack post signal-rich instead of a wall of ~590
repeats. Findings are matched on a stable signature (file, cwe, rule_id-or-title)
so a line shift reads as "standing", not a spurious resolve+new churn pair.
"""
import argparse
import json
import re

ORD = ["Critical", "High", "Medium", "Low", "Info"]


def sig(f):
    """Stable identity of a finding across runs (line numbers drift; this doesn't)."""
    rid = f.get("rule_id") or re.sub(r"\s+", " ", (f.get("title") or "")).strip().lower()[:80]
    return (str(f.get("file", "")).lstrip("./"), f.get("cwe") or "", rid)


def active(findings):
    return [f for f in findings if not f.get("dismissed")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True)
    ap.add_argument("--baseline", help="prior findings.json; empty/missing = first run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cur = active(json.load(open(a.current)))
    try:
        raw_base = json.load(open(a.baseline)) if a.baseline else []
    except (FileNotFoundError, json.JSONDecodeError):
        raw_base = []
    base = active(raw_base)
    # "First run" = no prior baseline FILE (latest.json stores every finding incl.
    # dismissed), NOT "no active findings after filtering" — else a week where triage
    # dismissed everything would falsely re-announce a baseline and suppress the delta.
    first_run = len(raw_base) == 0

    cur_by, base_by = {sig(f): f for f in cur}, {sig(f): f for f in base}
    new = [cur_by[k] for k in cur_by.keys() - base_by.keys()]
    resolved = [base_by[k] for k in base_by.keys() - cur_by.keys()]
    standing = [cur_by[k] for k in cur_by.keys() & base_by.keys()]

    def by_sev(items):
        return {s: sum(1 for f in items if f.get("severity") == s) for s in ORD}

    order = {s: i for i, s in enumerate(ORD)}
    new.sort(key=lambda f: order.get(f.get("severity"), 99))

    delta = {
        "first_run": first_run,
        "new_count": len(new),
        "resolved_count": len(resolved),
        "standing_count": len(standing),
        "new_by_severity": by_sev(new),
        "resolved_by_severity": by_sev(resolved),
        "new": [
            {"severity": f.get("severity"), "title": (f.get("title") or "")[:120],
             "file": f.get("file"), "line": f.get("line"), "cwe": f.get("cwe"),
             "verified": f.get("verified", False)}
            for f in new
        ][:25],
    }
    json.dump(delta, open(a.out, "w"), indent=2)
    tag = "first run (no baseline)" if delta["first_run"] else \
        f"{len(new)} new, {len(resolved)} resolved, {len(standing)} standing"
    print(f"delta: {tag}")


if __name__ == "__main__":
    main()
