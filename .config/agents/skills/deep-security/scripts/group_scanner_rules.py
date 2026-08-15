#!/usr/bin/env python3
"""Collapse scanner findings into rule-classes for cheap batch triage.

Scanner noise is rule-shaped: one noisy rule emits many instances. Grouping by
(tool, rule) turns ~1000 findings into ~100 rule-classes, so a handful of agents
can triage the whole surface (real vs noise vs mis-severity) instead of one
skeptic per finding.
"""
import argparse, collections, hashlib, json


def rule_key(f):
    tool = (f.get("tool") or ["?"])[0]
    rid = f.get("rule_id") or f.get("title", "")
    return (tool, rid, f.get("severity", "?"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=3)
    a = ap.parse_args()
    findings = json.load(open(a.findings))

    groups = collections.OrderedDict()
    for f in findings:
        k = rule_key(f)
        g = groups.setdefault(k, {"members": []})
        g["members"].append(f)

    out = []
    for (tool, rid, sev), g in groups.items():
        m = g["members"]
        gid = hashlib.sha1(f"{tool}|{rid}|{sev}".encode()).hexdigest()[:12]
        out.append({
            "id": gid, "tool": tool, "rule_id": rid, "severity": sev,
            "cwe": m[0].get("cwe"), "owasp_2025": m[0].get("owasp_2025"),
            "count": len(m),
            "title": m[0].get("title", "")[:120],
            "samples": [{"file": x.get("file"), "line": x.get("line"),
                         "message": (x.get("description") or x.get("title") or "")[:300]}
                        for x in m[:a.samples]],
        })
    out.sort(key=lambda x: -x["count"])
    json.dump(out, open(a.out, "w"), indent=2)
    print(f"{len(findings)} findings → {len(out)} rule-classes → {a.out}")
    print(f"top classes: " + ", ".join(f"{g['tool']}:{g['rule_id'][:24]}({g['count']})" for g in out[:6]))


if __name__ == "__main__":
    main()
