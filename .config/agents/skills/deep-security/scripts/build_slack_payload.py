#!/usr/bin/env python3
"""Build the weekly Slack Block Kit payload — delta first, detail one click away.

Leads with what changed this week (new/resolved), then the verdict + headline, then
the top new findings. The full report is linked, never inlined (it names live vulns —
keep it behind the channel/run, not sprayed into chat). Block Kit is built here in
Python (not a brittle workflow expression) so the model-authored text is safely
JSON-encoded, mirroring the upgrade-vulnerable-dependencies action.
"""
import argparse
import json
import os

SEV_EMOJI = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "⚪", "Info": "⚫"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--delta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report-url", default=os.environ.get("REPORT_URL", ""))
    a = ap.parse_args()

    s = json.load(open(a.summary))
    d = json.load(open(a.delta))
    repo = os.environ.get("GITHUB_REPOSITORY", "the repo")
    counts = s.get("counts", {})

    if d.get("first_run"):
        delta_line = "*Baseline established* — first run, so everything is new. Future posts lead with the week's change."
    else:
        nb = d.get("new_by_severity", {})
        new_hi = nb.get("Critical", 0) + nb.get("High", 0)
        delta_line = (f"*🆕 {d['new_count']} new* ({new_hi} Critical/High) · "
                      f"*✅ {d['resolved_count']} resolved* · "
                      f"*{d['standing_count']} standing*")

    verdict = s.get("verdict", "pass")
    vmark = {"block": "🔴 Block", "caution": "🟡 Caution", "pass": "🟢 Pass"}.get(verdict, verdict)

    blocks = [
        {"type": "header",
         "text": {"type": "plain_text", "text": "🛡️ Weekly security audit", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": delta_line}},
        {"type": "section", "text": {"type": "mrkdwn",
         "text": f"*Verdict:* {vmark}  ·  Standing: "
                 f"{counts.get('Critical', 0)} Critical / {counts.get('High', 0)} High / "
                 f"{counts.get('Medium', 0)} Medium"}},
    ]

    top = d.get("new", [])[:8]
    if top and not d.get("first_run"):
        lines = "\n".join(
            f"{SEV_EMOJI.get(f['severity'], '•')} *{f['severity']}* "
            f"{f.get('title', '')[:80]} — `{f.get('file', '?')}:{f.get('line', 0)}`"
            for f in top)
        blocks.append({"type": "section",
                       "text": {"type": "mrkdwn", "text": f"*New this week:*\n{lines}"}})

    if a.report_url:
        blocks.append({"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Open full report"},
             "url": a.report_url}]})
    blocks.append({"type": "context", "elements": [
        {"type": "mrkdwn", "text": f"{repo} · hybrid scan (FOSS scanners + AI lenses, "
                                   f"adversarially verified) · informational, gates nothing"}]})

    fallback = f"🛡️ Weekly security audit on {repo}: {delta_line.replace('*', '')}"
    json.dump({"text": fallback, "blocks": blocks}, open(a.out, "w"))
    print(f"slack payload -> {a.out}")


if __name__ == "__main__":
    main()
