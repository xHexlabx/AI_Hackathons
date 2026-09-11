"""HexTex Kaggriculture agent v2 - budgeted "melon opener -> goose & wheat" economy.

Strategy (details in notes/research.md):
  * Day 0: melon wave on the far tiles (first ~100 melons fetch $200+), a few geese near
    the shed, wheat on everything else. Strict cash discipline until income starts.
  * Geese fed + cared daily = 2 eggs/day forever; EGG/WHEAT glut curves are logarithmic,
    so they are near-unlimited sinks (~$38 / ~$19). A couple of cows/sheep tap the
    small but lucrative milk/wool markets.
  * Labour: hire cost is fibonacci -> ~12-14 hands/day is the economic ceiling.
  * Buy land when tiles run out; convert harvested wheat tiles into goose coops.
  * Fertilizer from animals: hold it, fertilize melons at age 6 (harvest at 8 instead of 10)
    and wheat at age 2; sell the surplus while the price is decent.
  * Sell every turn (prices persist, town demand is tiny). Day 29 has no end-of-day:
    drop inventories to the shed and sell before step 718.

kaggle-environments uses the LAST callable defined in this file as the agent -> keep `agent` last.
"""

from __future__ import annotations

import math

PARAMS = {
    "melon_tiles_day0": 12,
    "melon_fertilize": True,
    "geese_day0": 4,
    "max_geese_frac": 0.45,  # share of owned tiles that may hold geese
    "cows": 2,
    "sheep": 2,
    "premium_animal_day": (3, 14),  # buy cows/sheep only inside this day window
    "last_goose_day": 20,
    "last_land_day": 20,
    "max_quadrants": 4,  # 1..4 quadrants total
    "cash_reserve": 150,  # never spend below this (+ feed money)
    "wheat_reserve_days": 1.5,  # shed wheat to keep = animals * days
    "hold_price": {"FERTILIZER": 35},
    "work_per_unit": 20,  # tile-actions one unit manages per day (incl. walking)
    "max_hands": 14,
    "hire_budget_frac": 0.3,
    "drop_threshold": 10,
    "stay_bonus": 30,  # prefer finishing tasks on the current tile
}

CROPS = {
    "WHEAT": {"seed": 10, "first": 2, "harvest_age": 4, "fert_age": (2, 3)},
    "CARROT": {"seed": 20, "first": 2, "harvest_age": 3, "fert_age": (2, 2)},
    "MELON": {"seed": 80, "first": 10, "harvest_age": 10, "fert_age": (6, 6)},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "product": "EGG", "build": "BUILD_COOP"},
    "COW": {"cost": 400, "structure": "PASTURE", "product": "MILK", "build": "BUILD_PASTURE"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "product": "WOOL", "build": "BUILD_PASTURE"},
}
SELL_ORDER = [
    "MELON",
    "MILK",
    "WOOL",
    "STRAWBERRY",
    "EGG",
    "TOMATO",
    "CARROT",
    "WHEAT",
    "FERTILIZER",
]
PREMIUM = {"MELON", "MILK", "WOOL", "STRAWBERRY"}
LAND_PRICES = [1000, 2000, 4000]
BOARD = 10
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
LAST_DAY = 29
MAX_ORDERS = 10


def fib(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def dist(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def shed_dist(pos) -> int:
    return min(dist(pos, s) for s in SHED_TILES)


def nearest_shed(pos):
    return min(SHED_TILES, key=lambda s: dist(pos, s))


def move_toward(pos, target) -> str:
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    if dx != 0 and abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    if dy != 0:
        return "SOUTH" if dy > 0 else "NORTH"
    return "PASS"


def is_plant(t) -> bool:
    return isinstance(t, dict) and t.get("kind") == "PLANT"


def is_weed(t) -> bool:
    return isinstance(t, dict) and t.get("kind") == "WEED"


def is_animal(t) -> bool:
    return isinstance(t, dict) and "animal" in t


def is_empty_structure(t) -> bool:
    return isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and "animal" not in t


def is_free(t) -> bool:
    return t is None or is_weed(t)


class Brain:
    def __init__(self, params=None):
        self.p = dict(PARAMS)
        if params:
            self.p.update(params)
        self.roles: dict[
            tuple[int, int], str
        ] = {}  # (x, y) -> GOOSE|COW|SHEEP|MELON ; default WHEAT
        self.hires_wanted = 0
        self.planned_day = -1
        self.melon_done = False

    # ------------------------------------------------------------------ helpers
    def role(self, pos) -> str:
        return self.roles.get(pos, "WHEAT")

    @staticmethod
    def owned(tiles):
        return [(x, y) for y in range(BOARD) for x in range(BOARD) if tiles[y][x] != "LOCKED"]

    def can_plant(self, crop: str, day: int) -> bool:
        age = CROPS[crop]["harvest_age"]
        if crop == "MELON" and self.p["melon_fertilize"]:
            age = 8
        return day + age <= LAST_DAY - 1 and day <= 26

    def harvest_age(self, tile, day) -> int:
        cd = CROPS[tile["crop"]]
        if tile["crop"] == "MELON" and tile.get("fertilized_until_day", -1) >= day - 2:
            return 8
        return cd["harvest_age"]

    # ------------------------------------------------------------------ daily plan
    def plan_day(self, me, day):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        for pos in [p for p, r in self.roles.items() if r == "MELON"]:
            if day > 0 and not is_plant(tiles[pos[1]][pos[0]]):
                del self.roles[pos]
        if day == 0 and not self.melon_done:
            empties = [p for p in owned if tiles[p[1]][p[0]] is None and p not in self.roles]
            empties.sort(key=lambda p: -shed_dist(p))
            for p in empties[: self.p["melon_tiles_day0"]]:
                self.roles[p] = "MELON"
            self.melon_done = True
        work = 0.0
        for x, y in owned:
            t = tiles[y][x]
            if is_animal(t):
                work += 3 if day >= LAST_DAY else 5
            elif is_plant(t) or is_free(t) and self.role((x, y)) != "MELON":
                work += 2.5
        units_needed = math.ceil(work / self.p["work_per_unit"])
        hands = max(0, min(self.p["max_hands"], units_needed - 1))
        budget = me["money"] * self.p["hire_budget_frac"]
        while hands > 0 and sum(fib(i) for i in range(hands)) > budget:
            hands -= 1
        self.hires_wanted = hands

    # ------------------------------------------------------------------ animals bookkeeping
    def animal_stats(self, me, private, carried):
        tiles = me["tiles"]
        stats = {}
        for a in ANIMALS:
            placed = stock = slots = structs = 0
            for (x, y), r in self.roles.items():
                if r != a:
                    continue
                t = tiles[y][x]
                if is_animal(t) and t["animal"] == a:
                    placed += 1
                elif is_empty_structure(t):
                    structs += 1
                    slots += 1
                elif is_free(t):
                    slots += 1
            stock = private["shed"].get(a, 0) + carried.get(a, 0)
            stats[a] = {"placed": placed, "stock": stock, "slots": slots, "structs": structs}
        return stats

    def release_unfilled_roles(self, me, stats, hour):
        """Purchases can fail (cash) - free role tiles that have nothing to fill them."""
        if hour < 3:
            return
        tiles = me["tiles"]
        for a, s in stats.items():
            extra = s["slots"] - s["structs"] - s["stock"]
            if extra <= 0:
                continue
            free_roles = [p for p, r in self.roles.items() if r == a and is_free(tiles[p[1]][p[0]])]
            free_roles.sort(key=shed_dist)
            for p in free_roles[len(free_roles) - extra :]:
                del self.roles[p]

    # ------------------------------------------------------------------ market
    def market_orders(self, obs, me, private, day, hour, carried, stats):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        shed, seeds, prices = private["shed"], private["seeds"], obs["market"]["prices"]
        final_day = day >= LAST_DAY
        animals = [p for p in owned if is_animal(tiles[p[1]][p[0]])]
        n_animals = len(animals)
        shed_total = sum(shed.values())
        orders: list[list] = []

        # 1) sell
        wheat_reserve = 0 if final_day else math.ceil(n_animals * self.p["wheat_reserve_days"])
        fert_reserve = 0
        if not final_day:
            fert_reserve = sum(
                1
                for p in owned
                if is_plant(tiles[p[1]][p[0]])
                and tiles[p[1]][p[0]]["crop"] == "MELON"
                and self.p["melon_fertilize"]
                and tiles[p[1]][p[0]]["fertilized_until_day"] < day
                and day - tiles[p[1]][p[0]]["planted_day"] <= 6
            )
        for item in SELL_ORDER:
            qty = shed.get(item, 0)
            if item == "WHEAT":
                qty -= wheat_reserve
            if item == "FERTILIZER":
                qty -= fert_reserve
                hold = self.p["hold_price"].get(item, 0)
                if not final_day and shed_total < 70 and prices.get(item, 0) < hold:
                    qty = 0
            if qty > 0:
                orders.append(["SELL", item, qty])
        if final_day:
            return orders[:MAX_ORDERS]

        money = me["money"]
        # 2) feed: only what is missing for today (and for tomorrow late in the day)
        unfed = sum(1 for p in animals if not tiles[p[1]][p[0]]["fed_today"])
        wheat_avail = shed.get("WHEAT", 0) + carried.get("WHEAT", 0)
        need = unfed - wheat_avail
        if hour >= 20:
            need = max(need, n_animals - wheat_avail)
        if need > 0 and money > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", need])
            money -= need * prices.get("WHEAT", 25) * 1.3
        reserve = self.p["cash_reserve"] + 20 * n_animals

        empties = [p for p in owned if is_free(tiles[p[1]][p[0]])]
        # 3) land
        n_quads = len(me["unlocked_quadrants"])
        if (
            hour >= 1
            and n_quads < self.p["max_quadrants"]
            and day <= self.p["last_land_day"]
            and len(empties) <= 3
        ):
            cost = LAND_PRICES[n_quads - 1]
            if money - cost >= reserve:
                orders.append(["BUY_LAND"])
                money -= cost
        # 4) animals
        if hour >= 1:
            lo, hi = self.p["premium_animal_day"]
            targets = {
                "GOOSE": int(len(owned) * self.p["max_geese_frac"])
                if day <= self.p["last_goose_day"]
                else 0,
                "COW": self.p["cows"] if lo <= day <= hi else 0,
                "SHEEP": self.p["sheep"] if lo <= day <= hi else 0,
            }
            if day == 0:
                targets["GOOSE"] = min(targets["GOOSE"], self.p["geese_day0"])
            candidates = [p for p in empties if p not in self.roles]
            candidates.sort(key=shed_dist)
            for a in ("COW", "SHEEP", "GOOSE"):
                s = stats[a]
                have = s["placed"] + s["stock"]
                affordable = int((money - reserve) // ANIMALS[a]["cost"])
                want = min(targets[a] - have, affordable)
                if want <= 0:
                    continue
                new_sites = max(0, want - (s["slots"] - s["stock"]))
                if new_sites > len(candidates):
                    want -= new_sites - len(candidates)
                    new_sites = len(candidates)
                if want <= 0:
                    continue
                for p in candidates[:new_sites]:
                    self.roles[p] = a
                candidates = candidates[new_sites:]
                orders.append(["BUY_ANIMAL", a, want])
                money -= want * ANIMALS[a]["cost"]
        # 5) seeds
        for crop in ("MELON", "WHEAT"):
            if not self.can_plant(crop, day):
                continue
            n_tiles = sum(1 for p in empties if self.role(p) == crop)
            short = n_tiles - seeds.get(crop, 0)
            if short > 0:
                spend_cap = money - (self.p["cash_reserve"] if crop == "WHEAT" else 0)
                qty = min(short, int(max(0, spend_cap) // CROPS[crop]["seed"]))
                if qty > 0:
                    orders.append(["BUY_SEED", crop, qty])
                    money -= qty * CROPS[crop]["seed"]
        # 6) hires
        to_hire = self.hires_wanted - me["hires_today"]
        for _ in range(max(0, min(to_hire, MAX_ORDERS - len(orders)))):
            orders.append(["HIRE"])
        return orders[:MAX_ORDERS]

    # ------------------------------------------------------------------ units
    def unit_actions(self, obs, me, private, day, hour, units, invs, carried, stats):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        shed = private["shed"]
        seeds = dict(private["seeds"])
        prices = obs["market"]["prices"]
        final_day = day >= LAST_DAY
        tasks: list[dict] = []

        def add(pos, op, prio, need=None, seed=None, only_without=None, key=None):
            tasks.append(
                {
                    "pos": pos,
                    "op": op,
                    "prio": prio,
                    "need": need,
                    "seed": seed,
                    "only_without": only_without,
                    "key": key or (op[0], pos),
                }
            )

        unfed = 0
        build_sites: dict[str, list] = {a: [] for a in ANIMALS}
        fert_targets = 0
        for x, y in owned:
            t = tiles[y][x]
            pos = (x, y)
            role = self.role(pos)
            if t is None or is_weed(t):
                if is_weed(t):
                    needed = role in ANIMALS or (role in CROPS and self.can_plant(role, day))
                    add(pos, ["DIG"], 57 if needed else 15)
                    continue
                if role in ANIMALS:
                    build_sites[role].append(pos)
                elif role in CROPS and self.can_plant(role, day):
                    add(pos, ["PLANT", role], 58, seed=role)
            elif is_plant(t):
                crop = t["crop"]
                cd = CROPS.get(crop)
                age = day - t["planted_day"]
                ready = False
                if cd is not None:
                    ready = t["watered_today"] and age >= self.harvest_age(t, day)
                    if final_day and age >= cd["first"] and t["yield_units"] > 0:
                        ready = True
                elif t["yield_units"] > 0:
                    ready = True
                if ready:
                    add(pos, ["HARVEST"], 96 if crop == "MELON" else 72)
                    continue
                if not t["watered_today"]:
                    add(pos, ["WATER"], 90 if t["consecutive_unwatered"] >= 1 else 60)
                if (
                    cd is not None
                    and not final_day
                    and t["fertilized_until_day"] < day
                    and cd["fert_age"][0] <= age <= cd["fert_age"][1]
                    and (crop == "MELON" and self.p["melon_fertilize"] or crop == "WHEAT")
                ):
                    fert_targets += 1
                    add(pos, ["FERTILIZE"], 64 if crop == "MELON" else 44, need="FERTILIZER")
            elif is_animal(t):
                if not final_day and not t["fed_today"]:
                    add(pos, ["FEED"], 100, need="WHEAT")
                    unfed += 1
                if t["yield_units"] > 0:
                    prod = ANIMALS[t["animal"]]["product"]
                    add(pos, ["HARVEST"], 78 if (prod in PREMIUM or t["yield_units"] >= 3) else 66)
                if not final_day and not t["cared_today"]:
                    add(pos, ["CARE"], 42)
                if t["fertilizer_available"] and (not final_day or hour < 12):
                    add(
                        pos, ["COLLECT_FERTILIZER"], 32 if prices.get("FERTILIZER", 0) >= 15 else 12
                    )
            elif is_empty_structure(t):
                animal = role if role in ANIMALS else ("GOOSE" if t["kind"] == "COOP" else "COW")
                add(pos, ["PLACE", animal], 80, need=animal)

        for a, sites in build_sites.items():
            s = stats[a]
            sites.sort(key=shed_dist)
            for pos in sites[: max(0, s["stock"] - s["structs"])]:
                add(pos, [ANIMALS[a]["build"]], 62)
            if shed.get(a, 0) > 0 and (s["structs"] + len(sites)) - carried.get(a, 0) > 0:
                for st in SHED_TILES:
                    add(st, ["PICKUP", a, 1], 85, only_without=a, key=("PICKUP_" + a, st))

        wheat_short = unfed - carried.get("WHEAT", 0)
        if wheat_short > 0 and shed.get("WHEAT", 0) > 0:
            per = min(shed["WHEAT"], max(1, math.ceil(wheat_short / max(1, len(units)))))
            for st in SHED_TILES:
                add(
                    st, ["PICKUP", "WHEAT", per], 95, only_without="WHEAT", key=("PICKUP_WHEAT", st)
                )
        fert_short = fert_targets - carried.get("FERTILIZER", 0)
        if fert_short > 0 and shed.get("FERTILIZER", 0) > 0:
            per = min(shed["FERTILIZER"], max(1, math.ceil(fert_short / max(1, len(units)))), 6)
            for st in SHED_TILES:
                add(
                    st,
                    ["PICKUP", "FERTILIZER", per],
                    36,
                    only_without="FERTILIZER",
                    key=("PICKUP_FERT", st),
                )

        claimed: set = set()
        actions: list[list] = []
        stay = self.p["stay_bonus"]
        for i, pos in enumerate(units):
            inv = invs[i] if i < len(invs) else {}
            best, best_score = None, -(10**9)
            for tk in tasks:
                if tk["key"] in claimed:
                    continue
                if tk["need"] and inv.get(tk["need"], 0) <= 0:
                    continue
                if tk["only_without"] and inv.get(tk["only_without"], 0) > 0:
                    continue
                if tk["seed"] and seeds.get(tk["seed"], 0) <= 0:
                    continue
                d = dist(pos, tk["pos"])
                score = tk["prio"] - 4 * d + (stay if d == 0 else 0)
                if score > best_score:
                    best, best_score = tk, score
            load = sum(inv.values())
            if load > 0:
                goods = sum(
                    v
                    for k, v in inv.items()
                    if k not in ANIMALS and k not in ("WHEAT", "FERTILIZER")
                )
                premium_load = sum(v for k, v in inv.items() if k in PREMIUM)
                if final_day and hour >= 14:
                    dprio = 99
                elif hour >= 21:
                    dprio = 85
                elif premium_load > 0:
                    dprio = 82
                elif goods >= self.p["drop_threshold"]:
                    dprio = 50
                else:
                    dprio = None
                if dprio is not None and dprio - 4 * shed_dist(pos) > best_score:
                    best = {"pos": nearest_shed(pos), "op": ["DROP"], "key": None, "seed": None}
                    best_score = 0
            if best is None:
                actions.append(["PASS"])
                continue
            if best["key"]:
                claimed.add(best["key"])
            if best["seed"]:
                seeds[best["seed"]] -= 1
            actions.append(best["op"] if pos == best["pos"] else [move_toward(pos, best["pos"])])
        return actions

    # ------------------------------------------------------------------ step
    def act(self, obs):
        player = obs["player"]
        me = obs["farms"][player]
        private = obs["private"]
        day, hour = obs.get("day", 0), obs.get("hour", 0)
        if day != self.planned_day:
            self.plan_day(me, day)
            self.planned_day = day
        units = [tuple(me["farmer"])] + [tuple(h) for h in me["hands"]]
        invs = list(private.get("inventories", []))
        while len(invs) < len(units):
            invs.append({})
        carried: dict[str, int] = {}
        for inv in invs:
            for k, v in inv.items():
                carried[k] = carried.get(k, 0) + v
        stats = self.animal_stats(me, private, carried)
        self.release_unfilled_roles(me, stats, hour)
        stats = self.animal_stats(me, private, carried)
        actions = self.unit_actions(obs, me, private, day, hour, units, invs, carried, stats)
        market = self.market_orders(obs, me, private, day, hour, carried, stats)
        return {"farmer": actions[0], "hands": actions[1:], "market": market}


_BRAINS: dict[int, Brain] = {}


def agent(obs, config=None):
    del config
    player = obs["player"]
    brain = _BRAINS.get(player)
    if brain is None or obs.get("step", 0) == 0:
        brain = _BRAINS[player] = Brain()
    try:
        return brain.act(obs)
    except Exception as exc:  # noqa: BLE001 - never crash the episode
        print(f"[hextex_v2] step {obs.get('step')} error: {exc!r}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
