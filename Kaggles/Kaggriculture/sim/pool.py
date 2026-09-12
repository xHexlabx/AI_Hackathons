"""Benchmark an agent against a POOL of opponents (the ladder is diverse, Bea alone is not).

    uv run python sim/pool.py agents/hextex_v18b.py -n 12 --jobs 4
    uv run python sim/pool.py agents/hextex_v18b.py --opps agents/reference/broker_bea.py agents/hextex_v15.py

Prints per-opponent win-rate / mean money / mean margin and a pooled win-rate.
"""

from __future__ import annotations

import argparse
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DEFAULT_POOL = [
    "episodes/kaggle/top/clone_terry.py",  # ladder meta line replay (local file, git-ignored)
    "agents/reference/broker_bea.py",
    "agents/reference/slotter_silas.py",
    "agents/hextex_v15.py",
    "agents/hextex_v10.py",
    "agents/reference/rancher_rita.py",
]


def _resolve(agent: str) -> str:
    p = Path(agent) if Path(agent).is_absolute() else HERE / agent
    return str(p) if p.exists() else agent


def play(job):
    agent, opp, seed, flipped = job
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    pair = [opp, agent] if flipped else [agent, opp]
    try:
        env.run(pair)
        r = [float(s.reward or 0.0) for s in env.steps[-1]]
    except Exception:  # noqa: BLE001
        r = [0.0, 1.0]
    if flipped:
        r = r[::-1]
    return opp, r[0], r[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("--opps", nargs="*", default=DEFAULT_POOL)
    ap.add_argument("-n", type=int, default=12, help="games per opponent")
    ap.add_argument("--seed", type=int, default=3000)
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    agent = _resolve(args.agent)
    jobs = []
    for opp in args.opps:
        for i in range(args.n):
            jobs.append((agent, _resolve(opp), args.seed + i, i % 2 == 1))
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        res = list(ex.map(play, jobs))
    print(f"{args.agent}  ({len(jobs)} games, {time.perf_counter() - t0:.0f}s)")
    print(f"{'opponent':<40} {'win':>5} {'mine':>9} {'opp':>9} {'margin':>9}")
    tot_w = 0.0
    for opp in args.opps:
        rows = [(a, b) for o, a, b in res if o == _resolve(opp)]
        w = sum(1 for a, b in rows if a > b) + 0.5 * sum(1 for a, b in rows if a == b)
        tot_w += w
        ma, mb = statistics.fmean(a for a, _ in rows), statistics.fmean(b for _, b in rows)
        print(
            f"{Path(opp).stem:<40} {w / len(rows):>5.0%} {ma:>9,.0f} {mb:>9,.0f} {ma - mb:>+9,.0f}"
        )
    print(f"{'POOL':<40} {tot_w / len(res):>5.0%}")


if __name__ == "__main__":
    main()
