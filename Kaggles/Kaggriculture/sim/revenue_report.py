"""Per-player revenue by product, harvest totals and build-up timeline from a replay.

    uv run python sim/revenue_report.py episodes/v9_vs_bea.json

Revenue is inferred per step as money delta + known purchase costs, attributed to that step's
SELL orders in proportion to quantity x quoted price (exact when one product is sold per step).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

SEED = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
LAND = [1000, 2000, 4000]


def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("replay")
    args = ap.parse_args()
    with open(args.replay) as f:
        rep = json.load(f)
    steps = rep["steps"]
    names = rep.get("info", {}).get("TeamNames") or ["P0", "P1"]
    for p in (0, 1):
        revenue: Counter = Counter()
        spend: Counter = Counter()
        harvested: Counter = Counter()
        moves = acts = 0
        timeline = {}
        for s in range(len(steps) - 1):
            ob = steps[s][0]["observation"]
            farm = ob["farms"][p]
            nxt = steps[s + 1][0]["observation"]["farms"][p]
            act = steps[s + 1][p].get("action") or {}
            prices = ob["market"]["prices"]
            cost = 0.0
            sells = []
            hires_now = 0
            for o in act.get("market") or []:
                if not o:
                    continue
                if o[0] == "BUY_SEED":
                    c = SEED.get(o[1], 0) * int(o[2])
                    cost += c
                    spend["seed:" + o[1]] += c
                elif o[0] == "BUY_ANIMAL":
                    c = ANIMAL.get(o[1], 0) * int(o[2])
                    cost += c
                    spend["animal:" + o[1]] += c
                elif o[0] == "BUY_PRODUCT":
                    c = prices.get(o[1], 50) * int(o[2])
                    cost += c
                    spend["buy:" + o[1]] += c
                elif o[0] == "BUY_LAND":
                    n = len(farm["unlocked_quadrants"]) - 1
                    if n < 3 and farm["money"] >= LAND[n]:
                        cost += LAND[n]
                        spend["land"] += LAND[n]
                elif o[0] == "HIRE":
                    c = fib(farm["hires_today"] + hires_now)
                    hires_now += 1
                    cost += c
                    spend["hires"] += c
                elif o[0] == "SELL":
                    shed = steps[s][p]["observation"]["private"]["shed"]
                    q = min(int(o[2]), shed.get(o[1], 0))
                    if q > 0:
                        sells.append((o[1], q * prices.get(o[1], 1)))
            delta = nxt["money"] - farm["money"] + cost
            # purchases that failed (no cash) inflate `cost`; clamp revenue at >= 0
            delta = max(0.0, delta)
            weights = list(sells)
            tot = sum(w for _, w in weights)
            if tot > 0:
                for i, w in weights:
                    revenue[i] += delta * w / tot
            elif delta > 0:
                revenue["?"] += delta
            units = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
            for u, a in zip(
                units, [act.get("farmer")] + list(act.get("hands") or []), strict=False
            ):
                if not a:
                    continue
                acts += 1
                if a[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                    moves += 1
                if a[0] == "HARVEST":
                    t = farm["tiles"][u[1]][u[0]]
                    if isinstance(t, dict):
                        key = t.get("crop") or t.get("animal")
                        harvested[key] += t.get("yield_units", 0)
            if s % 24 == 0:
                d = s // 24
                c = Counter()
                for row in farm["tiles"]:
                    for t in row:
                        if isinstance(t, dict):
                            c[t.get("animal") or t.get("crop") or t.get("kind")] += 1
                timeline[d] = (
                    farm["money"],
                    len(farm["unlocked_quadrants"]),
                    c["COW"],
                    c["SHEEP"],
                    c["STRAWBERRY"],
                    c["MELON"],
                    c["WHEAT"],
                )
        final = steps[-1][p]["reward"]
        print(
            f"\n===== player {p} ({names[p]}) final ${final:,.0f}  actions={acts} moves={moves} ({moves / max(1, acts):.0%})"
        )
        print(
            "revenue by product:",
            {k: round(v) for k, v in sorted(revenue.items(), key=lambda kv: -kv[1])},
        )
        print("spend:", {k: round(v) for k, v in sorted(spend.items(), key=lambda kv: -kv[1])})
        print("units harvested:", dict(harvested))
        print("day: money quads cows sheep straw melon wheat")
        for d in range(0, 30, 2):
            if d in timeline:
                m, q, cw, sh, st, me, wh = timeline[d]
                print(f"  d{d:>2}: {m:>8,.0f} {q} {cw:>2} {sh:>2} {st:>2} {me:>2} {wh:>2}")


if __name__ == "__main__":
    main()
