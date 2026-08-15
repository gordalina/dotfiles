#!/usr/bin/env python3
"""Apply rule-class triage verdicts back to individual scanner findings.

Verdict → per-finding effect:
  confirmed         → verified=True
  adjust            → verified=True, severity=adjusted_severity
  dismissed         → dismissed=True (kept in JSON for completeness; hidden by default)
  context_dependent → needs_review=True (neither confirmed nor dropped)
  (no verdict)      → left untriaged (verified=False)
"""
import argparse, hashlib, json


def gid(f):
    tool = (f.get("tool") or ["?"])[0]
    rid = f.get("rule_id") or f.get("title", "")
    return hashlib.sha1(f"{tool}|{rid}|{f.get('severity','?')}".encode()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--verdicts", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    findings = json.load(open(a.findings))
    vlist = json.load(open(a.verdicts))
    vmap = {v["id"]: v for v in vlist}

    n = {"confirmed": 0, "adjust": 0, "dismissed": 0, "context_dependent": 0, "untriaged": 0}
    for f in findings:
        v = vmap.get(gid(f))
        if not v:
            f["triage"] = "untriaged"; n["untriaged"] += 1; continue
        verdict = v["verdict"]; note = v.get("reason", "")
        f["triage"] = verdict
        f["triage_note"] = note
        if verdict == "confirmed":
            f["verified"] = True
        elif verdict == "adjust":
            f["verified"] = True
            if v.get("adjusted_severity"):
                f["severity"] = v["adjusted_severity"]
        elif verdict == "dismissed":
            f["dismissed"] = True
        elif verdict == "context_dependent":
            f["needs_review"] = True
        n[verdict] = n.get(verdict, 0) + 1

    json.dump(findings, open(a.out, "w"), indent=2)
    print(f"applied triage to {len(findings)} scanner findings: {n}")


if __name__ == "__main__":
    main()
