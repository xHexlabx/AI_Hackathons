"""Successive-halving parameter search for an agent that reads HEXTEX_PARAMS (JSON).

    uv run python sim/optimize.py agents/hextex_v18.py --opp agents/reference/broker_bea.py \
        --space sim/space_v18.json --n1 16 --n2 48 --configs 40 --jobs 5 --seed 1000 \
        --out episodes/opt_v18_r1.csv

    # round 2: perturb 3-5 parameters of the previous winner
    uv run python sim/optimize.py agents/hextex_v18.py --opp agents/reference/broker_bea.py \
        --space sim/space_v18.json --around episodes/opt_v18_r1_best.json --configs 40 \
        --out episodes/opt_v18_r2.csv

Space file: {"param": [v1, v2, ...]} or {"param": {"low": a, "high": b, "int": true}}.
Configs are sampled uniformly (the empty config = agent defaults is always included as a control).

Stage 1: every config plays n1 games on seeds seed..seed+n1-1 (the agent sits in seat 1 on odd
games, as in sweep.py). Score = (win-rate, mean margin = our money - opponent money).
Stage 2: the top `keep` fraction replays seeds seed..seed+n2-1 (stage-1 games are reused).

Outputs: <out> (one row per game), <out stem>_summary.csv (one row per config and stage),
<out stem>_best.json (the winning override dict).
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import os
import random
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ENV_NAME = "kaggriculture"
HERE = Path(__file__).resolve().parent.parent
BAD_STATUS = {"ERROR", "INVALID", "TIMEOUT"}


def _resolve(agent: str) -> str:
    p = Path(agent) if Path(agent).is_absolute() else HERE / agent
    return str(p) if p.exists() else agent


# ----------------------------------------------------------------------------- workers
def play(job: tuple[str, str, int, bool, dict]) -> dict:
    """Play one game; never raises (a crash counts as a loss with 0 money)."""
    agent_path, opp, seed, flipped, params = job
    os.environ["HEXTEX_PARAMS"] = json.dumps(params)
    t0 = time.perf_counter()
    out = {"seed": seed, "flipped": flipped, "ours": 0.0, "theirs": 0.0, "error": "", "secs": 0.0}
    try:
        from kaggle_environments import make

        env = make(ENV_NAME, configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        pair = [opp, agent_path] if flipped else [agent_path, opp]
        env.run(pair)
        final = env.steps[-1]
        rewards = [float(s.reward or 0.0) for s in final]
        statuses = [str(s.status) for s in final]
        if flipped:
            rewards, statuses = rewards[::-1], statuses[::-1]
        out["ours"], out["theirs"] = rewards
        if statuses[0] in BAD_STATUS:
            out["error"] = f"status={statuses[0]}"
            out["ours"] = 0.0  # an agent that crashed loses, whatever the env says
        elif len(env.steps) < 720:
            out["error"] = f"short_game={len(env.steps)}"
    except Exception as e:  # noqa: BLE001 - anything goes wrong -> loss
        out["error"] = f"{type(e).__name__}: {e}"[:200]
        out["ours"], out["theirs"] = 0.0, 0.0
    out["secs"] = round(time.perf_counter() - t0, 1)
    return out


# ----------------------------------------------------------------------------- sampling
def agent_defaults(agent_path: str) -> dict:
    """The agent's top-level PARAMS dict literal (empty if the file has none)."""
    try:
        tree = ast.parse(Path(agent_path).read_text())
    except (OSError, SyntaxError):
        return {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PARAMS" for t in node.targets
        ):
            try:
                return ast.literal_eval(node.value)
            except ValueError:
                return {}
    return {}


def load_space(path: str) -> dict:
    space = json.loads(Path(path).read_text())
    out = {}
    for k, v in space.items():
        if isinstance(v, list):
            if len(v) < 2:
                continue
            out[k] = v
        elif isinstance(v, dict) and "low" in v and "high" in v:
            out[k] = v
        else:  # nested dicts (reserve_frac, crew_schedule...) are skipped
            print(f"  skipping {k!r}: unsupported space entry", file=sys.stderr)
    return out


def sample_value(rng: random.Random, spec, avoid=None):
    for _ in range(20):
        if isinstance(spec, list):
            v = rng.choice(spec)
        elif spec.get("int"):
            v = rng.randint(int(spec["low"]), int(spec["high"]))
        else:
            v = round(rng.uniform(float(spec["low"]), float(spec["high"])), 4)
        if avoid is None or v != avoid:
            return v
    return v


def sample_configs(rng: random.Random, space: dict, n: int) -> list[dict]:
    cfgs, seen = [], set()
    while len(cfgs) < n:
        cfg = {k: sample_value(rng, spec) for k, spec in space.items()}
        key = json.dumps(cfg, sort_keys=True)
        if key not in seen:
            seen.add(key)
            cfgs.append(cfg)
    return cfgs


def perturb_configs(
    rng: random.Random, space: dict, base: dict, defaults: dict, n: int, kmin: int, kmax: int
) -> list[dict]:
    """n configs = base with k (kmin..kmax) parameters re-sampled to a different value.

    A key missing from `base` is implicitly the agent default, so that value is avoided too.
    """
    cfgs, seen = [], {json.dumps(base, sort_keys=True)}
    keys = list(space)
    while len(cfgs) < n:
        cfg = dict(base)
        for k in rng.sample(keys, min(rng.randint(kmin, kmax), len(keys))):
            cfg[k] = sample_value(rng, space[k], avoid=base.get(k, defaults.get(k)))
        key = json.dumps(cfg, sort_keys=True)
        if key not in seen:
            seen.add(key)
            cfgs.append(cfg)
    return cfgs


# ----------------------------------------------------------------------------- scoring
def summarize(games: list[dict]) -> dict:
    n = len(games)
    wins = sum(1 for g in games if not g["error"] and g["ours"] > g["theirs"])
    ties = sum(1 for g in games if not g["error"] and g["ours"] == g["theirs"])
    margins = [g["ours"] - g["theirs"] for g in games]
    return {
        "n": n,
        "win": (wins + 0.5 * ties) / n if n else 0.0,
        "margin": statistics.fmean(margins) if n else 0.0,
        "margin_se": statistics.stdev(margins) / math.sqrt(n) if n > 1 else 0.0,
        "ours": statistics.fmean(g["ours"] for g in games) if n else 0.0,
        "theirs": statistics.fmean(g["theirs"] for g in games) if n else 0.0,
        "errors": sum(1 for g in games if g["error"]),
    }


def score_key(s: dict) -> tuple:
    return (s["win"], s["margin"])


def cfg_label(cfg: dict, base: dict | None = None) -> str:
    if not cfg:
        return "{}  (agent defaults)"
    if base is not None and cfg == base:
        return "{}  (round base)"
    shown = cfg if base is None else {k: v for k, v in cfg.items() if base.get(k) != v}
    return json.dumps(shown, sort_keys=True)


def print_table(title: str, rows: list[tuple[int, dict, dict]], base: dict | None) -> None:
    print(f"\n{title}")
    print(
        f"{'rk':>3} {'cfg':>4} {'n':>3} {'win':>5} {'margin':>8} {'+-se':>6} {'ours':>8} {'opp':>8} {'err':>3}  params"
    )
    for rank, (ci, s, cfg) in enumerate(rows, 1):
        print(
            f"{rank:>3} {ci:>4} {s['n']:>3} {s['win']:>5.0%} {s['margin']:>8,.0f} {s['margin_se']:>6,.0f} "
            f"{s['ours']:>8,.0f} {s['theirs']:>8,.0f} {s['errors']:>3}  {cfg_label(cfg, base)}"
        )
    sys.stdout.flush()


def marginal_effects(space: dict, configs: list[dict], stats: dict[int, dict]) -> None:
    """Per parameter value: mean stage-1 (win, margin) over the configs that used it."""
    print("\nStage-1 marginal effects (mean win / mean margin per parameter value; * = best)")
    for k, spec in space.items():
        buckets: dict = {}
        for ci, cfg in enumerate(configs):
            if ci in stats and k in cfg:
                buckets.setdefault(cfg[k], []).append(stats[ci])
        if len(buckets) < 2:
            continue
        if isinstance(spec, list):
            items = [(v, buckets[v]) for v in spec if v in buckets]
        else:
            items = sorted(buckets.items())
        best = max(items, key=lambda it: statistics.fmean(s["margin"] for s in it[1]))[0]
        cells = []
        for v, ss in items:
            w = statistics.fmean(s["win"] for s in ss)
            m = statistics.fmean(s["margin"] for s in ss)
            flag = "*" if v == best else " "
            cells.append(f"{v}{flag}:{w:.0%}/{m:,.0f}(n{len(ss)})")
        print(f"  {k:<24} " + "  ".join(cells))
    sys.stdout.flush()


# ----------------------------------------------------------------------------- driver
def run_stage(
    ex: ProcessPoolExecutor,
    agent: str,
    opp: str,
    configs: list[dict],
    cfg_ids: list[int],
    seeds: range,
    have: dict[int, dict[int, dict]],
    writer: csv.DictWriter,
    fh,
    stage: str,
) -> None:
    """Play every (cfg, seed) pair not in `have`; results go into `have` and the CSV."""
    futs = {}
    for ci in cfg_ids:
        for i, seed in enumerate(seeds):
            if seed in have.setdefault(ci, {}):
                continue
            job = (agent, opp, seed, i % 2 == 1, configs[ci])
            futs[ex.submit(play, job)] = (ci, seed)
    total, t0 = len(futs), time.perf_counter()
    print(f"[{stage}] {len(cfg_ids)} configs x {len(seeds)} seeds -> {total} new games")
    sys.stdout.flush()
    for done, fut in enumerate(as_completed(futs), 1):
        ci, seed = futs[fut]
        res = fut.result()
        have[ci][seed] = res
        writer.writerow({"stage": stage, "cfg": ci, **res, "params": json.dumps(configs[ci])})
        if done % 25 == 0 or done == total:
            el = time.perf_counter() - t0
            eta = el / done * (total - done)
            print(f"  {done}/{total} games  {el / 60:.1f} min elapsed, ~{eta / 60:.1f} min left")
            sys.stdout.flush()
    fh.flush()


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("agent")
    ap.add_argument("--opp", default="agents/reference/broker_bea.py")
    ap.add_argument("--space", required=True, help="JSON search space")
    ap.add_argument("--configs", type=int, default=40, help="random configs (plus the control)")
    ap.add_argument("--n1", type=int, default=16, help="games per config in stage 1")
    ap.add_argument("--n2", type=int, default=48, help="games per finalist in stage 2")
    ap.add_argument("--keep", type=float, default=0.25, help="fraction promoted to stage 2")
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1000, help="first game seed")
    ap.add_argument("--rng", type=int, default=0, help="sampling seed")
    ap.add_argument("--out", default="episodes/optimize.csv")
    ap.add_argument("--around", default=None, help="JSON config to perturb (round 2)")
    ap.add_argument("--perturb", default="3,5", help="min,max parameters changed per config")
    ap.add_argument("--include", default=None, help="JSON list of extra configs to evaluate")
    args = ap.parse_args()

    agent, opp = _resolve(args.agent), _resolve(args.opp)
    space = load_space(_resolve(args.space))
    rng = random.Random(args.rng)
    base: dict | None = None
    configs: list[dict] = [{}]  # cfg 0 = control
    if args.around:
        base = json.loads(Path(_resolve(args.around)).read_text())
        kmin, kmax = (int(x) for x in args.perturb.split(","))
        if base:
            configs.append(base)
        configs += perturb_configs(
            rng, space, base, agent_defaults(agent), args.configs, kmin, kmax
        )
    else:
        configs += sample_configs(rng, space, args.configs)
    if args.include:
        for cfg in json.loads(Path(_resolve(args.include)).read_text()):
            if cfg not in configs:
                configs.append(cfg)

    out = Path(args.out) if Path(args.out).is_absolute() else HERE / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    summary_path = out.with_name(out.stem + "_summary.csv")
    best_path = out.with_name(out.stem + "_best.json")
    cfgs_path = out.with_name(out.stem + "_configs.json")
    cfgs_path.write_text(json.dumps(configs, indent=1))

    n_keep = max(1, math.ceil(args.keep * len(configs)))
    games_total = len(configs) * args.n1 + n_keep * max(0, args.n2 - args.n1)
    print(
        f"{args.agent} vs {args.opp}: {len(configs)} configs ({len(space)} params), "
        f"stage 1 x{args.n1}, top {n_keep} -> stage 2 x{args.n2}, {games_total} games, {args.jobs} jobs"
    )
    sys.stdout.flush()

    have: dict[int, dict[int, dict]] = {}
    fields = ["stage", "cfg", "seed", "flipped", "ours", "theirs", "error", "secs", "params"]
    t0 = time.perf_counter()
    with (
        out.open("w", newline="") as fh,
        ProcessPoolExecutor(max_workers=args.jobs) as ex,
    ):
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()

        all_ids = list(range(len(configs)))
        run_stage(
            ex,
            agent,
            opp,
            configs,
            all_ids,
            range(args.seed, args.seed + args.n1),
            have,
            writer,
            fh,
            "s1",
        )
        s1 = {ci: summarize(list(have[ci].values())) for ci in all_ids}
        ranked1 = sorted(all_ids, key=lambda ci: score_key(s1[ci]), reverse=True)
        print_table(
            f"Stage 1 ({args.n1} games, seeds {args.seed}-{args.seed + args.n1 - 1})  [{(time.perf_counter() - t0) / 60:.1f} min]",
            [(ci, s1[ci], configs[ci]) for ci in ranked1],
            base,
        )
        marginal_effects(space, configs, s1)

        finalists = ranked1[:n_keep]
        if 0 not in finalists:  # always carry the control through stage 2 for reference
            finalists.append(0)
        run_stage(
            ex,
            agent,
            opp,
            configs,
            finalists,
            range(args.seed, args.seed + args.n2),
            have,
            writer,
            fh,
            "s2",
        )
        s2 = {ci: summarize(list(have[ci].values())) for ci in finalists}
        ranked2 = sorted(finalists, key=lambda ci: score_key(s2[ci]), reverse=True)
        print_table(
            f"Stage 2 ({args.n2} games, seeds {args.seed}-{args.seed + args.n2 - 1})  [{(time.perf_counter() - t0) / 60:.1f} min]",
            [(ci, s2[ci], configs[ci]) for ci in ranked2],
            base,
        )

    with summary_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "stage",
                "rank",
                "cfg",
                "n",
                "win",
                "margin",
                "margin_se",
                "ours",
                "theirs",
                "errors",
                "params",
            ]
        )
        for stage, ranked, stats in (("s1", ranked1, s1), ("s2", ranked2, s2)):
            for rank, ci in enumerate(ranked, 1):
                s = stats[ci]
                w.writerow(
                    [
                        stage,
                        rank,
                        ci,
                        s["n"],
                        f"{s['win']:.4f}",
                        f"{s['margin']:.1f}",
                        f"{s['margin_se']:.1f}",
                        f"{s['ours']:.1f}",
                        f"{s['theirs']:.1f}",
                        s["errors"],
                        json.dumps(configs[ci]),
                    ]
                )
    best = ranked2[0]
    best_path.write_text(json.dumps(configs[best], indent=1, sort_keys=True))
    print(
        f"\nbest = cfg {best}: win {s2[best]['win']:.0%}, margin {s2[best]['margin']:,.0f}  -> {best_path}"
    )
    print(f"games: {out}   summary: {summary_path}   configs: {cfgs_path}")
    print(f"total {(time.perf_counter() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
