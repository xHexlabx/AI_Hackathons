"""Play local Kaggriculture matches in parallel and summarise.

    uv run python sim/run.py agents/hextex_v1.py starter -n 8
    uv run python sim/run.py agents/hextex_v1.py agents/hextex_v1.py -n 8 --jobs 8
    uv run python sim/run.py main.py starter -n 1 --replay episodes/test.json

Agents: a path to a .py file, or a built-in name (pass | random | starter).
Rewards are re-ordered so index 0 is always agent_a even when seats are swapped.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ENV_NAME = "kaggriculture"
HERE = Path(__file__).resolve().parent.parent


def _resolve(agent: str) -> str:
    p = (HERE / agent) if not Path(agent).is_absolute() else Path(agent)
    return str(p) if p.exists() else agent


def play_one(args: tuple[str, str, int | None, bool, dict, str | None]) -> dict:
    agent_a, agent_b, seed, flipped, extra_cfg, replay_path = args
    from kaggle_environments import make

    cfg = {"episodeSteps": 720, **extra_cfg}
    if seed is not None:
        cfg["seed"] = seed
    env = make(ENV_NAME, configuration=cfg, debug=False)
    pair = [agent_b, agent_a] if flipped else [agent_a, agent_b]
    t0 = time.perf_counter()
    env.run(pair)
    final = env.steps[-1]
    rewards = [float(s.reward or 0.0) for s in final]
    statuses = [s.status for s in final]
    if flipped:
        rewards, statuses = rewards[::-1], statuses[::-1]
    if replay_path:
        Path(replay_path).write_text(json.dumps(env.toJSON()))
    return {
        "seed": seed,
        "flipped": flipped,
        "a": rewards[0],
        "b": rewards[1],
        "status": statuses,
        "secs": round(time.perf_counter() - t0, 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent_a")
    ap.add_argument("agent_b", nargs="?", default="starter")
    ap.add_argument("-n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--no-swap", action="store_true")
    ap.add_argument("--replay", default=None, help="save replay json of the first game")
    args = ap.parse_args()

    a, b = _resolve(args.agent_a), _resolve(args.agent_b)
    jobs = []
    for i in range(args.n):
        flipped = (not args.no_swap) and i % 2 == 1
        replay = args.replay if i == 0 else None
        jobs.append((a, b, args.seed + i, flipped, {"episodeSteps": args.steps}, replay))

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=min(args.jobs, len(jobs))) as ex:
        results = list(ex.map(play_one, jobs))

    wins = sum(r["a"] > r["b"] for r in results)
    ties = sum(r["a"] == r["b"] for r in results)
    am = [r["a"] for r in results]
    bm = [r["b"] for r in results]
    errors = [r for r in results if "ERROR" in r["status"] or "INVALID" in r["status"]]
    print(
        f"{args.agent_a}  vs  {args.agent_b}   ({len(results)} games, {time.perf_counter() - t0:.0f}s)"
    )
    print(
        f"  A win-rate : {(wins + 0.5 * ties) / len(results):.0%}   (W{wins} T{ties} L{len(results) - wins - ties})"
    )
    print(
        f"  A money    : mean {statistics.fmean(am):>9,.0f}   median {statistics.median(am):>9,.0f}   min {min(am):>9,.0f}   max {max(am):>9,.0f}"
    )
    print(
        f"  B money    : mean {statistics.fmean(bm):>9,.0f}   median {statistics.median(bm):>9,.0f}   min {min(bm):>9,.0f}   max {max(bm):>9,.0f}"
    )
    for r in results:
        flag = " <- ERROR" if r in errors else ""
        print(
            f"    seed {r['seed']:>4} {'(swapped)' if r['flipped'] else '         '}  A={r['a']:>9,.0f}  B={r['b']:>9,.0f}  {r['secs']:>5}s{flag}"
        )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
