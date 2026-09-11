"""Play local matches:  uv run python sim/run.py <agent_a> <agent_b> [-n N] [--seed S]"""

from __future__ import annotations

import argparse

from common.sim import run_matches

ENV_NAME = "{{ENV}}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent_a")
    ap.add_argument("agent_b", nargs="?", default="random")
    ap.add_argument("-n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    seeds = [args.seed + i for i in range(args.n)]
    print(run_matches(ENV_NAME, args.agent_a, args.agent_b, n=args.n, seeds=seeds).summary())


if __name__ == "__main__":
    main()
