"""Animal-care report per day from a replay: are the geese fed/cared, how much walking, money curve.

uv run python sim/feed_report.py episodes/v5_vs_starter.json [--player 0]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("replay")
    ap.add_argument("--player", type=int, default=0)
    args = ap.parse_args()
    with open(args.replay) as f:
        rep = json.load(f)
    steps, p = rep["steps"], args.player
    tpd = rep["configuration"].get("turnsPerDay", 24)
    print(
        "day | animals fed cared | shed_wheat@h0 bought | feeds moves acts | money@h0  hands | sells"
    )
    for d in range(len(steps) // tpd + 1):
        s0 = d * tpd
        if s0 >= len(steps):
            break
        s_end = min(s0 + tpd - 1, len(steps) - 1)
        farm_end = steps[s_end][0]["observation"]["farms"][p]
        animals = [
            t for row in farm_end["tiles"] for t in row if isinstance(t, dict) and "animal" in t
        ]
        fed = sum(1 for t in animals if t["fed_today"])
        cared = sum(1 for t in animals if t["cared_today"])
        shed0 = steps[s0][p]["observation"]["private"]["shed"].get("WHEAT", 0)
        bought = feeds = moves = acts = 0
        sells: Counter = Counter()
        for s in range(s0, min(s0 + tpd, len(steps))):
            act = (steps[s + 1][p].get("action") if s + 1 < len(steps) else None) or {}
            for o in act.get("market") or []:
                if o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                    bought += int(o[2])
                if o[0] == "SELL":
                    sells[o[1]] += int(o[2])
            for u in [act.get("farmer")] + list(act.get("hands") or []):
                if not u:
                    continue
                acts += 1
                if u[0] == "FEED":
                    feeds += 1
                if u[0] in ("NORTH", "SOUTH", "EAST", "WEST"):
                    moves += 1
        money = steps[s0][0]["observation"]["farms"][p]["money"]
        print(
            f"{d:>3} | {len(animals):>7} {fed:>3} {cared:>5} | {shed0:>13} {bought:>6} | "
            f"{feeds:>5} {moves:>5} {acts:>4} | {money:>8,.0f} {len(farm_end['hands']):>5} | {dict(sells)}"
        )


if __name__ == "__main__":
    main()
