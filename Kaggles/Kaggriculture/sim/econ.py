"""Market economics calculator - reproduces the env price curves.

    uv run python sim/econ.py            # cumulative revenue table per product
    uv run python sim/econ.py --units 300

For each product: price after selling x units (no town demand), the average price
over those x units, and the number of units until the price hits the $1 floor /
drops below a reference value.
"""

from __future__ import annotations

import argparse
import math

PARAMS = {
    "WHEAT": {"base": 25, "T": 400, "above": ("log", 0.20), "below": ("sqrt", 0.80)},
    "CARROT": {"base": 35, "T": 450, "above": ("sqrt", 0.70), "below": ("hinge", 1.00)},
    "TOMATO": {"base": 60, "T": 200, "above": ("sqrt", 0.60), "below": ("hinge", 0.40)},
    "STRAWBERRY": {"base": 120, "T": 100, "above": ("linear", 1.60), "below": ("sqrt", 0.70)},
    "MELON": {"base": 250, "T": 300, "above": ("sq", 3.60), "below": ("log", 0.20)},
    "EGG": {"base": 50, "T": 332, "above": ("log", 0.20), "below": ("hinge", 0.40)},
    "MILK": {"base": 160, "T": 122, "above": ("linear", 1.60), "below": ("sqrt", 0.60)},
    "WOOL": {"base": 200, "T": 105, "above": ("sq", 3.20), "below": ("log", 0.20)},
    "FERTILIZER": {"base": 100, "T": 200, "above": ("linear", 0.40), "below": ("linear", 0.40)},
}


def shape(func: str, x: float, t: float) -> float:
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1 + x)
    if func == "hinge":
        u = x / t
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    raise ValueError(func)


def price(item: str, delta: int) -> int:
    """delta = units sold (+) or units drained (-) relative to I0."""
    p = PARAMS[item]
    side = "above" if delta > 0 else "below"
    func, target = p[side]
    amp = target * p["base"] / shape(func, p["T"], p["T"])
    val = (
        p["base"] - amp * shape(func, abs(delta), p["T"])
        if delta > 0
        else p["base"] + amp * shape(func, abs(delta), p["T"])
    )
    return max(1, round(val))


def revenue_curve(item: str, units: int) -> list[int]:
    """price received for the k-th unit sold, k = 1..units, starting from I0."""
    out = []
    inv = 0
    for _ in range(units):
        pr = price(item, inv)
        out.append(pr)
        if pr > 1:
            inv += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", type=int, default=400)
    ap.add_argument("--ref", type=int, default=38, help="reference marginal price (~egg floor)")
    args = ap.parse_args()
    print(
        f"{'product':<11}{'base':>6}{'p@50':>7}{'p@100':>7}{'p@200':>7}{'p@400':>7} | {'units>ref':>9}{'rev>ref':>9} | {'units>$1':>9}{'rev@floor':>10}"
    )
    for item in PARAMS:
        curve = revenue_curve(item, 5000)
        n_ref = sum(1 for c in curve if c >= args.ref)
        n_floor = sum(1 for c in curve if c > 1)
        rev_ref = sum(curve[:n_ref])
        rev_floor = sum(curve[:n_floor])
        pts = [price(item, k) for k in (50, 100, 200, 400)]
        print(
            f"{item:<11}{PARAMS[item]['base']:>6}{pts[0]:>7}{pts[1]:>7}{pts[2]:>7}{pts[3]:>7} | {n_ref:>9}{rev_ref:>9,} | {n_floor:>9}{rev_floor:>10,}"
        )
    print("\nscarcity side (town drains inventory):  price after -100 / -300 units")
    for item in PARAMS:
        print(f"  {item:<11} {price(item, -100):>5} {price(item, -300):>5}")


if __name__ == "__main__":
    main()
