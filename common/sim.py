"""Minimal harness for kaggle-environments simulation competitions.

from common.sim import run_matches
res = run_matches("kaggriculture", "agents/v1.py", "starter", n=10)
print(res.summary())
"""

from __future__ import annotations

import statistics
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

Agent = str | Callable[..., Any]


@dataclass
class MatchResult:
    env_name: str
    agents: tuple[str, str]
    rewards: list[tuple[float, float]] = field(default_factory=list)
    seeds: list[int | None] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.rewards)

    def win_rate(self, player: int = 0) -> float:
        if not self.rewards:
            return 0.0
        wins = sum(1 for r in self.rewards if r[player] > r[1 - player])
        ties = sum(1 for r in self.rewards if r[player] == r[1 - player])
        return (wins + 0.5 * ties) / self.n

    def mean_reward(self, player: int = 0) -> float:
        return statistics.fmean(r[player] for r in self.rewards) if self.rewards else 0.0

    def summary(self) -> str:
        a, b = self.agents
        lines = [
            f"{self.env_name}: {a} vs {b}  ({self.n} games)",
            f"  win rate  P0={self.win_rate(0):.1%}  P1={self.win_rate(1):.1%}",
            f"  mean      P0={self.mean_reward(0):,.0f}  P1={self.mean_reward(1):,.0f}",
        ]
        if self.rewards:
            p0 = [r[0] for r in self.rewards]
            med = statistics.median(p0)
            lines.append(f"  P0 min/median/max = {min(p0):,.0f} / {med:,.0f} / {max(p0):,.0f}")
        if self.errors:
            lines.append(f"  errors: {len(self.errors)} (first: {self.errors[0][:120]})")
        return "\n".join(lines)


def _label(agent: Agent) -> str:
    return agent if isinstance(agent, str) else getattr(agent, "__name__", "agent")


def run_matches(
    env_name: str,
    agent_a: Agent,
    agent_b: Agent,
    *,
    n: int = 5,
    seeds: list[int] | None = None,
    configuration: dict[str, Any] | None = None,
    swap_sides: bool = True,
    debug: bool = False,
) -> MatchResult:
    """Play `n` episodes of `agent_a` vs `agent_b`.

    With `swap_sides`, odd games flip seats so both agents see both player ids; the
    rewards are re-ordered so index 0 is always `agent_a`.
    """
    from kaggle_environments import make

    result = MatchResult(env_name, (_label(agent_a), _label(agent_b)))
    seeds = seeds or [None] * n
    for i, seed in enumerate(seeds[:n]):
        cfg = dict(configuration or {})
        if seed is not None:
            cfg["seed"] = seed
        env = make(env_name, configuration=cfg, debug=debug)
        flipped = swap_sides and i % 2 == 1
        pair = [agent_b, agent_a] if flipped else [agent_a, agent_b]
        try:
            env.run(pair)
        except Exception as exc:  # noqa: BLE001 - we want the harness to keep going
            result.errors.append(repr(exc))
            continue
        final = env.steps[-1]
        rewards = [s.reward if s.reward is not None else float("-inf") for s in final]
        for s in final:
            if s.status == "ERROR":
                result.errors.append(f"game {i}: agent status ERROR")
        if flipped:
            rewards = rewards[::-1]
        result.rewards.append((rewards[0], rewards[1]))
        result.seeds.append(env.info.get("seed") if hasattr(env, "info") else seed)
    return result
