#!/usr/bin/env python3
"""Compute a run summary — cost estimate, timer, findings funnel, coverage.

Cost is an ESTIMATE from token counts × public per-MTok rates (verified 2026-06).
Fast mode = faster Opus output, NOT a price change. Opus 4.8 1M context has no
long-context premium. Cache reads ~0.1x input, writes ~1.25x input (5-min TTL).
"""
import argparse, json, sys

# USD per 1,000,000 tokens (input, output). claude-api skill, 2026-06.
RATES = {
    "opus":   {"in": 5.0,  "out": 25.0},
    "sonnet": {"in": 3.0,  "out": 15.0},
    "haiku":  {"in": 1.0,  "out": 5.0},
}


def cost(model, inp, out, cache_read=0, cache_write=0):
    r = RATES.get(model, RATES["opus"])
    return (inp * r["in"] + out * r["out"]
            + cache_read * r["in"] * 0.1 + cache_write * r["in"] * 1.25) / 1_000_000


def fmt_dur(s):
    s = int(s or 0)
    return f"{s//60}m {s%60}s" if s >= 60 else f"{s}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", required=True, help="JSON: {phases, usage, funnel, coverage}")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t = json.load(open(a.telemetry))

    # cost by stage
    by_stage, total_cost, total_tokens = {}, 0.0, 0
    for u in t.get("usage", []):
        c = cost(u.get("model", "opus"), u.get("input", 0), u.get("output", 0),
                 u.get("cache_read", 0), u.get("cache_write", 0))
        stage = u.get("stage", "agents")
        by_stage[stage] = by_stage.get(stage, 0.0) + c
        total_cost += c
        total_tokens += u.get("input", 0) + u.get("output", 0)

    phases = t.get("phases", [])
    total_secs = sum(p.get("seconds", 0) for p in phases)
    funnel = t.get("funnel", {})

    summary = {
        "cost_usd": round(total_cost, 2),
        "cost_by_stage": {k: round(v, 2) for k, v in by_stage.items()},
        "cost_is_estimate": True,
        "total_tokens": total_tokens,
        "wall_clock": fmt_dur(total_secs),
        "phases": [{"name": p["name"], "duration": fmt_dur(p.get("seconds", 0))} for p in phases],
        "funnel": funnel,  # {candidates, verified, refuted}
        "coverage": t.get("coverage", {}),
    }
    json.dump(summary, open(a.out, "w"), indent=2)

    # human-readable
    print("── Run summary " + "─" * 30)
    print(f"  Cost (est):  ${summary['cost_usd']:.2f}   ({total_tokens:,} tokens)")
    for k, v in summary["cost_by_stage"].items():
        print(f"     {k:<12} ${v:.2f}")
    print(f"  Wall-clock:  {summary['wall_clock']}")
    for p in summary["phases"]:
        print(f"     {p['name']:<12} {p['duration']}")
    if funnel:
        print(f"  Funnel:      {funnel.get('candidates','?')} found → "
              f"{funnel.get('verified','?')} verified ({funnel.get('refuted','?')} refuted)")
    print("  NOTE: cost is an estimate from token counts × public rates.")


if __name__ == "__main__":
    main()
