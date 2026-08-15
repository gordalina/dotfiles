#!/usr/bin/env python3
"""Normalize SARIF (+ simple JSON shims) from FOSS scanners into canonical Findings.

Severity → editorial 5-level. CWE extracted best-effort (load-bearing key).
OWASP categories DERIVED from CWE. CVSS only ever passed through, never fabricated.
"""
import argparse, glob, hashlib, json, os, re

CWE_RE = re.compile(r"CWE[-_ ]?(\d+)", re.I)
LEVELS = ["Info", "Low", "Medium", "High", "Critical"]


def sev_from_security_severity(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f >= 9.0: return "Critical"
    if f >= 7.0: return "High"
    if f >= 4.0: return "Medium"
    if f > 0.0:  return "Low"
    return "Info"


def sev_from_level(level):
    return {"error": "High", "warning": "Medium", "note": "Low", "none": "Info"}.get(
        (level or "warning").lower(), "Medium")


def sev_from_trivy_tag(tags):
    for t in tags or []:
        u = str(t).upper()
        if u in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            return u.capitalize()
    return None


def extract_cwe(*blobs):
    for b in blobs:
        if not b:
            continue
        m = CWE_RE.search(json.dumps(b) if not isinstance(b, str) else b)
        if m:
            return f"CWE-{m.group(1)}"
    return None


def fallback_cwe(tool, rule_id):
    """Many scanners don't emit an explicit CWE. Infer a representative one from
    the tool + rule shape so OWASP categorization still works."""
    t = (tool or "").lower()
    r = (rule_id or "").upper()
    if "gitleaks" in t or "trufflehog" in t:
        return "CWE-798"  # hardcoded credentials
    if "trivy" in t or "grype" in t or "osv" in t:
        if r.startswith("CVE") or r.startswith("GHSA") or "VULN" in r:
            return "CWE-1395"  # vulnerable dependency
        return "CWE-16"  # misconfiguration
    if "checkov" in t or "kics" in t or "tfsec" in t:
        return "CWE-16"
    if "bandit" in t:
        return "CWE-710"
    return None


def extract_cvss(rule):
    # passthrough only — read an authoritative score if the scanner provided one
    props = (rule or {}).get("properties", {}) or {}
    for k in ("cvssv3_score", "cvss_score", "cvss"):
        if k in props:
            try:
                return float(props[k])
            except (TypeError, ValueError):
                pass
    ss = props.get("security-severity")
    if ss is not None:
        try:
            return float(ss)
        except (TypeError, ValueError):
            return None
    return None


def load_changed(path):
    if not path or not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    # {file: [lines...]} -> {file: set(lines)}
    return {k: set(v) for k, v in data.items()}


def is_new(changed, file, line):
    if changed is None:
        return None
    lines = changed.get(file) or changed.get(file.lstrip("./"))
    return bool(lines and line in lines)


def derive_owasp(cwe, cmap):
    entry = cmap["cwe"].get(cwe) if cwe else None
    cats = cmap["categories"]
    if not entry:
        return cats["2021"]["NA"], cats["2025"]["NA"]
    return cats["2021"][entry["2021"]], cats["2025"][entry["2025"]]


def stable_id(file, line, cwe, rule):
    return hashlib.sha1(f"{file}:{line}:{cwe}:{rule}".encode()).hexdigest()[:16]


def rules_index(run):
    idx = {}
    for comp in [run.get("tool", {}).get("driver", {})] + run.get("tool", {}).get("extensions", []):
        for r in (comp or {}).get("rules", []) or []:
            idx[r.get("id")] = r
    return idx


def parse_sarif(path, changed, cmap):
    with open(path) as f:
        doc = json.load(f)
    out = []
    for run in doc.get("runs", []):
        tool = run.get("tool", {}).get("driver", {}).get("name", os.path.basename(path)).lower()
        ridx = rules_index(run)
        for res in run.get("results", []):
            rule_id = res.get("ruleId") or res.get("rule", {}).get("id") or ""
            rule = ridx.get(rule_id, {})
            tags = (rule.get("properties", {}) or {}).get("tags", [])
            # location
            file, line = "(unknown)", 0
            locs = res.get("locations") or []
            if locs:
                pl = locs[0].get("physicalLocation", {})
                file = pl.get("artifactLocation", {}).get("uri", file)
                line = pl.get("region", {}).get("startLine", 0) or 0
            file = file.replace("file://", "")
            msg = res.get("message", {}).get("text", rule.get("shortDescription", {}).get("text", rule_id))
            # severity: prefer security-severity, then trivy tag, then SARIF level
            cvss = extract_cvss(rule)
            sev = (sev_from_security_severity((rule.get("properties", {}) or {}).get("security-severity"))
                   or sev_from_trivy_tag(tags + [res.get("level")])
                   or sev_from_level(res.get("level")))
            cwe = extract_cwe(rule_id, tags, rule, msg) or fallback_cwe(tool, rule_id)
            o21, o25 = derive_owasp(cwe, cmap)
            out.append({
                "id": stable_id(file, line, cwe, rule_id),
                "title": (rule.get("shortDescription", {}).get("text") or rule_id or msg)[:140],
                "description": msg,
                "remediation": (rule.get("help", {}) or {}).get("text", "") or
                               (rule.get("fullDescription", {}) or {}).get("text", ""),
                "severity": sev,
                "confidence": 7,  # scanners: fixed baseline; agreement/verify adjusts
                "cwe": cwe,
                "owasp_2021": o21,
                "owasp_2025": o25,
                "cvss_from_advisory": cvss,
                "tool": [tool],
                "source_kind": "scanner",
                "file": file,
                "line": line,
                "is_new": is_new(changed, file, line),
                "verified": False,
                "verification_note": None,
                "rule_id": rule_id,
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sarif-dir", required=True)
    ap.add_argument("--changed")
    ap.add_argument("--owasp-map", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(a.owasp_map) as f:
        cmap = json.load(f)
    changed = load_changed(a.changed)

    findings, seen = [], set()
    for path in sorted(glob.glob(os.path.join(a.sarif_dir, "**", "*.sarif"), recursive=True)):
        try:
            for fnd in parse_sarif(path, changed, cmap):
                if fnd["id"] in seen:
                    continue
                seen.add(fnd["id"])
                findings.append(fnd)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"warn: skipping {path}: {e}")

    with open(a.out, "w") as f:
        json.dump(findings, f, indent=2)
    print(f"normalized {len(findings)} scanner findings -> {a.out}")


if __name__ == "__main__":
    main()
