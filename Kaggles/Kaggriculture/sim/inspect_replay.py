"""Per-day summary of a replay json (from sim/run.py --replay or `kaggle competitions replay`).

uv run python sim/inspect_replay.py episodes/v1_vs_starter.json [--player 0] [--actions DAY]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter


def tile_summary(tiles):
    c = Counter()
    for row in tiles:
        for t in row:
            if t is None:
                c["empty"] += 1
            elif t == "LOCKED":
                c["locked"] += 1
            elif t.get("kind") == "WEED":
                c["weed"] += 1
            elif t.get("kind") == "PLANT":
                c[t["crop"].lower()] += 1
            elif "animal" in t:
                c[t["animal"].lower()] += 1
            else:
                c["empty_" + t["kind"].lower()] += 1
    return c


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("replay")
    ap.add_argument("--player", type=int, default=0)
    ap.add_argument("--actions", type=int, default=None, help="dump this day's actions")
    args = ap.parse_args()
    with open(args.replay) as f:
        rep = json.load(f)
    steps = rep["steps"]
    p = args.player
    tpd = rep["configuration"].get("turnsPerDay", 24)
    print(
        f"steps={len(steps)} seed={rep.get('info', {}).get('seed')} shops={steps[-1][0]['observation']['town']['unlocked_shops']}"
    )
    print(f"{'day':>3} {'money':>8} {'hands':>5} {'shed':>5} | tiles | market sells (this day)")
    prev_money = None
    for d in range(0, len(steps) // tpd + 1):
        s0 = d * tpd
        if s0 >= len(steps):
            break
        ob = steps[s0][0]["observation"]
        farm = ob["farms"][p]
        priv = steps[s0][p]["observation"].get("private", {})
        shed = {k: v for k, v in priv.get("shed", {}).items() if v}
        # aggregate market SELL orders by the agent during the day
        sells = Counter()
        hires = 0
        acts = Counter()
        for s in range(s0, min(s0 + tpd, len(steps))):
            # steps[s+1].action was decided on steps[s].observation
            act = (steps[s + 1][p].get("action") if s + 1 < len(steps) else None) or {}
            for u in [act.get("farmer")] + list(act.get("hands") or []):
                if u:
                    acts["move" if u[0] in ("NORTH", "SOUTH", "EAST", "WEST") else u[0]] += 1
            for o in act.get("market", []) or []:
                if o and o[0] == "SELL":
                    sells[o[1]] += int(o[2])
                elif o and o[0] == "HIRE":
                    hires += 1
        ts = tile_summary(farm["tiles"])
        ts.pop("locked", None)
        delta = "" if prev_money is None else f"({farm['money'] - prev_money:+,.0f})"
        print(
            f"{d:>3} {farm['money']:>8,.0f} {hires:>5} {sum(shed.values()):>5} | "
            f"{dict(ts)} | {dict(sells)} {delta}\n      actions: {dict(acts)}"
        )
        prev_money = farm["money"]
    last = steps[-1]
    print("final:", [(i, s["reward"], s["status"]) for i, s in enumerate(last)])
    print("prices end:", steps[-1][0]["observation"]["market"]["prices"])
    if args.actions is not None:
        for s in range(args.actions * tpd, min((args.actions + 1) * tpd, len(steps))):
            act = steps[s + 1][p].get("action") if s + 1 < len(steps) else None
            ob = steps[s][0]["observation"]
            farm = ob["farms"][p]
            print(f"step {s} h{s % tpd:>2} farmer@{farm['farmer']} hands={farm['hands']} -> {act}")


if __name__ == "__main__":
    main()
