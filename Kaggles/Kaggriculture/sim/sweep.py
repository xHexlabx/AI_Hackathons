"""Parameter sweep for an agent that reads HEXTEX_PARAMS (JSON) from the environment.

    uv run python sim/sweep.py agents/hextex_v4.py --opp starter -n 4 \
        --grid '{"open_geese": [2, 3, 4, 6], "open_melons": [15, 20, 22]}'
    uv run python sim/sweep.py agents/hextex_v4.py --opp agents/hextex_v3.py -n 4 \
        --configs '[{"geese_cap": 40}, {"geese_cap": 60}]'

Each config plays n games (seats swapped on odd games) and is ranked by mean money.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ENV_NAME = "kaggriculture"
HERE = Path(__file__).resolve().parent.parent


def _resolve(agent: str) -> str:
    p = Path(agent) if Path(agent).is_absolute() else HERE / agent
    return str(p) if p.exists() else agent


def play(job):
    agent_path, opp, seed, flipped, params = job
    os.environ["HEXTEX_PARAMS"] = json.dumps(params)
    from kaggle_environments import make

    env = make(ENV_NAME, configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    pair = [opp, agent_path] if flipped else [agent_path, opp]
    env.run(pair)
    final = env.steps[-1]
    rewards = [float(s.reward or 0.0) for s in final]
    if flipped:
        rewards = rewards[::-1]
    return rewards


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("--opp", default="starter")
    ap.add_argument("-n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--grid", default=None, help="JSON dict of param -> list of values (cartesian)")
    ap.add_argument("--configs", default=None, help="JSON list of param dicts")
    args = ap.parse_args()

    configs: list[dict] = [{}]
    if args.grid:
        grid = json.loads(args.grid)
        keys = list(grid)
        configs = [dict(zip(keys, vals, strict=True)) for vals in itertools.product(*grid.values())]
    if args.configs:
        configs = json.loads(args.configs)

    agent, opp = _resolve(args.agent), _resolve(args.opp)
    jobs = []
    for ci, cfg in enumerate(configs):
        for i in range(args.n):
            jobs.append((ci, (agent, opp, args.seed + i, i % 2 == 1, cfg)))

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        results = list(ex.map(play, [j for _, j in jobs]))

    per_cfg: dict[int, list] = {}
    for (ci, _), r in zip(jobs, results, strict=True):
        per_cfg.setdefault(ci, []).append(r)
    rows = []
    for ci, rs in per_cfg.items():
        mine = [r[0] for r in rs]
        theirs = [r[1] for r in rs]
        wins = sum(1 for r in rs if r[0] > r[1]) + 0.5 * sum(1 for r in rs if r[0] == r[1])
        rows.append(
            (
                statistics.fmean(mine),
                wins / len(rs),
                min(mine),
                statistics.fmean(theirs),
                configs[ci],
            )
        )
    rows.sort(key=lambda r: -r[0])
    print(
        f"{len(configs)} configs x {args.n} games vs {args.opp}  ({time.perf_counter() - t0:.0f}s)"
    )
    print(f"{'mean':>9} {'win':>5} {'min':>9} {'opp mean':>9}  params")
    for mean, wr, lo, om, cfg in rows:
        print(f"{mean:>9,.0f} {wr:>5.0%} {lo:>9,.0f} {om:>9,.0f}  {json.dumps(cfg)}")


if __name__ == "__main__":
    main()
