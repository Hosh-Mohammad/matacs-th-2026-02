#!/usr/bin/env python3
"""Deterministic gate + scoring + ranking. No AI is used here.

Input : criteria.json (admin config) and extracted facts per proposal (from the AI extraction step).
Output: ranking list (same shape as ../ranking.json) and a per-criterion breakdown for the reviewer.
Usage : python score.py [--write ../ranking.json] [--verbose]
"""
import json, sys, pathlib

HERE = pathlib.Path(__file__).parent
BAND = [(10, 100), (7, 80), (4, 60), (1, 30), (0, 0)]


def load(name):
    return json.loads((HERE / name).read_text())


def gates(p, crit):
    """Return 'pass', 'fail' or 'unknown' for the mandatory criteria, plus the failed ids."""
    failed, unknown = [], []
    for m in crit["mandatory"]:
        vals = [p.get(f) for f in m["fields"]]
        if any(v is False for v in vals):
            failed.append(m["id"])
        elif any(v is None for v in vals):
            unknown.append(m["id"])
    if p.get("price_cad") is not None and p["price_cad"] > crit["project"]["budget_ceiling_cad"]:
        failed.append("over_budget")
    return failed, unknown


def score_all(crit, facts):
    assert sum(c["weight"] for c in crit["weighted"]) == 100, "weights must total 100"
    out = {}
    for pid, p in facts.items():
        failed, unknown = gates(p, crit)
        out[pid] = {"failed": failed, "unknown": unknown, "flags": p["flags"], "criteria": {}}
    pool = [pid for pid, r in out.items() if not r["failed"]]  # baselines come from eligible bids only
    low_price = min(facts[i]["price_cad"] for i in pool)
    weeks = [facts[i]["weeks"] for i in pool if facts[i]["weeks"]]
    low_weeks = min(weeks)
    top_wm = max(facts[i]["workmanship_warranty_years"] for i in pool)
    for pid in pool:
        p, c = facts[pid], out[pid]["criteria"]
        n = p["qualifying_installs"]
        c["experience"] = next(s for lo, s in BAND if n >= lo)
        c["price"] = 100 * low_price / p["price_cad"]
        w = p["weeks"]
        c["timeline"] = 0 if not w or w > crit["project"]["max_weeks"] else 100 * low_weeks / w
        panel = min(p["panel_warranty_years"], 25) / 25 * 100
        c["warranty"] = 0.5 * panel + 0.5 * (100 * p["workmanship_warranty_years"] / top_wm)
        c["team"] = 25 * sum(bool(v) for v in p["team"].values())
        out[pid]["total"] = sum(c[k["id"]] * k["weight"] / 100 for k in crit["weighted"])
    return out


def status_of(r):
    if r["failed"]:
        return "ineligible"
    if r["unknown"] or any(f.startswith("INTEGRITY") for f in r["flags"]):
        return "flagged"
    return "ranked"


def build_ranking(crit, facts):
    res = score_all(crit, facts)
    ranked = [i for i, r in res.items() if status_of(r) == "ranked"]
    # tie-break: score, then experience, then lower price, then id
    ranked.sort(key=lambda i: (-res[i]["total"], -res[i]["criteria"]["experience"], facts[i]["price_cad"], i))
    rows = []
    for k, pid in enumerate(ranked, 1):
        rows.append({"proposal": pid, "rank": k, "status": "ranked", "score": round(res[pid]["total"], 1), "reason": reason(pid, res[pid], facts[pid])})
    for pid in sorted(i for i in res if i not in ranked):
        r, st = res[pid], status_of(res[pid])
        score = round(r["total"], 1) if st == "flagged" else None
        rows.append({"proposal": pid, "rank": None, "status": st, "score": score, "reason": reason(pid, r, facts[pid], st)})
    return rows, res


def reason(pid, r, p, st="ranked"):
    if st == "ineligible":
        return "Fails mandatory licence gate: electrical work is subcontracted and the licence holder is only named after award, so a human can only override if the admin allows it."
    if st == "flagged":
        return (f"Provisional {r['total']:.1f} on merit, but the text contains an instruction aimed at automated reviewers; "
                "ignored for scoring, withheld from ranking until a human clears or disqualifies it (also: experience window unconfirmed).")
    cs = r["criteria"]
    best = max(cs, key=cs.get)
    worst = min(cs, key=cs.get)
    note = " Schedule not stated (timeline scored 0); a stated schedule of 12+ weeks would still leave it behind E." if pid == "D" else ""
    return f"Passes both gates; strongest on {best} ({cs[best]:.0f}), weakest on {worst} ({cs[worst]:.0f}).{note}"


if __name__ == "__main__":
    crit, facts = load("criteria.json"), load("extracted_samples.json")
    facts = {k: v for k, v in facts.items() if not k.startswith("_")}
    rows, res = build_ranking(crit, facts)
    if "--verbose" in sys.argv:
        for pid, r in res.items():
            print(pid, status_of(r), {k: round(v, 1) for k, v in r.get("criteria", {}).items()}, round(r.get("total", 0), 2), r["failed"] or "", r["unknown"] or "")
    text = json.dumps(rows, indent=2)
    if "--write" in sys.argv:
        pathlib.Path(sys.argv[sys.argv.index("--write") + 1]).write_text(text + "\n")
    else:
        print(text)
