"""HexTex Kaggriculture agent v1 - "goose & wheat" economy with a greedy task scheduler.

Strategy (details in notes/research.md):
  * EGG and WHEAT glut curves are logarithmic -> near-unlimited sinks at ~$38 / ~$19.
  * A goose that is fed + cared daily yields 2 eggs/day forever, plus 1 free fertilizer/day.
  * MELON has a steep sq curve, but the first ~100 units still fetch $200+ -> one wave on day 0.
  * Labour is almost free (fibonacci hire cost) -> hire enough hands to touch every tile daily.
  * Buy land as soon as it is affordable, convert harvested wheat tiles into goose coops.
  * Sell every turn (prices persist; town demand is tiny); keep only feed wheat in the shed.
  * Day 29 has no end-of-day: drop inventories to the shed and sell before step 718.

kaggle-environments uses the LAST callable defined in this file as the agent -> keep `agent` last.
"""

from __future__ import annotations

import math

PARAMS = {
    "melon_tiles_day0": 10,  # melon wave planted on day 0 (farthest tiles)
    "geese_day0": 4,  # geese bought on day 0
    "max_geese_frac": 0.55,  # share of owned tiles that may hold geese
    "last_goose_day": 20,  # no new geese after this day (4 days to first egg)
    "last_land_day": 21,
    "land_reserve": 200,  # cash to keep after buying land
    "wheat_reserve_days": 2,  # shed wheat to keep = animals * days
    "hold_price": {"FERTILIZER": 30},  # hold these below price unless the shed fills up
    "work_per_unit": 15,  # tile-actions one unit manages per day (incl. walking)
    "max_hands": 16,
    "hire_budget_frac": 0.25,  # max share of cash spent on hires per day
    "drop_threshold": 8,  # items carried before heading to the shed
}

CROPS = {
    "WHEAT": {"seed": 10, "first": 2, "harvest_age": 4},
    "CARROT": {"seed": 20, "first": 2, "harvest_age": 3},
    "MELON": {"seed": 80, "first": 10, "harvest_age": 10},
}
ANIMALS = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
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


def can_plant(crop: str, day: int) -> bool:
    # leave at least one day to harvest + carry to the shed before the final step
    return day + CROPS[crop]["harvest_age"] <= LAST_DAY and day <= 26


class Brain:
    def __init__(self, params=None):
        self.p = dict(PARAMS)
        if params:
            self.p.update(params)
        self.roles: dict[tuple[int, int], str] = {}  # (x, y) -> GOOSE | MELON ; default WHEAT
        self.hires_wanted = 0
        self.planned_day = -1
        self.melon_done = False

    # ------------------------------------------------------------------ helpers
    def role(self, pos) -> str:
        return self.roles.get(pos, "WHEAT")

    @staticmethod
    def owned(tiles):
        return [(x, y) for y in range(BOARD) for x in range(BOARD) if tiles[y][x] != "LOCKED"]

    # ------------------------------------------------------------------ daily plan
    def plan_day(self, me, day):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        # melon tiles revert to wheat once harvested
        for pos in [p for p, r in self.roles.items() if r == "MELON"]:
            t = tiles[pos[1]][pos[0]]
            if day > 0 and not is_plant(t):
                del self.roles[pos]
        if day == 0 and not self.melon_done:
            empties = [p for p in owned if tiles[p[1]][p[0]] is None and p not in self.roles]
            empties.sort(key=lambda p: -shed_dist(p))
            for p in empties[: self.p["melon_tiles_day0"]]:
                self.roles[p] = "MELON"
            self.melon_done = True
        # workload estimate -> number of hands
        work = 0
        for x, y in owned:
            t = tiles[y][x]
            if is_animal(t):
                work += 2 if day >= LAST_DAY else 4
            else:
                work += 2
        units_needed = math.ceil(work / self.p["work_per_unit"])
        hands = max(0, min(self.p["max_hands"], units_needed - 1))
        budget = me["money"] * self.p["hire_budget_frac"]
        while hands > 0 and sum(fib(i) for i in range(hands)) > budget:
            hands -= 1
        self.hires_wanted = hands

    def reconcile_goose_roles(self, me, private, carried, hour):
        """Drop GOOSE roles that have no goose to fill them (e.g. a purchase failed)."""
        if hour < 3:
            return
        tiles = me["tiles"]
        supply = private["shed"].get("GOOSE", 0) + carried.get("GOOSE", 0)
        open_slots = [
            p
            for p, r in self.roles.items()
            if r == "GOOSE" and (tiles[p[1]][p[0]] is None or is_weed(tiles[p[1]][p[0]]))
        ]
        open_slots.sort(key=shed_dist)
        for p in open_slots[supply:]:
            del self.roles[p]

    # ------------------------------------------------------------------ market
    def market_orders(self, obs, me, private, day, hour, carried):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        shed, seeds, prices = private["shed"], private["seeds"], obs["market"]["prices"]
        final_day = day >= LAST_DAY
        animals = [p for p in owned if is_animal(tiles[p[1]][p[0]])]
        n_animals = len(animals)
        shed_total = sum(shed.values())
        orders: list[list] = []

        # 1) sell (everything but feed wheat and held items)
        reserve = 0 if final_day else n_animals * self.p["wheat_reserve_days"]
        for item in PRODUCTS:
            qty = shed.get(item, 0) - (reserve if item == "WHEAT" else 0)
            if qty <= 0:
                continue
            hold = self.p["hold_price"].get(item)
            if hold and not final_day and shed_total < 70 and prices.get(item, 0) < hold:
                continue
            orders.append(["SELL", item, qty])
        if final_day:
            return orders[:MAX_ORDERS]

        money = me["money"]
        # 2) feed: keep one day ahead
        unfed = sum(1 for p in animals if not tiles[p[1]][p[0]]["fed_today"])
        wheat_avail = shed.get("WHEAT", 0) + carried.get("WHEAT", 0)
        need = unfed + (n_animals if hour < 12 else 0) - wheat_avail
        if need > 0 and money > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", need])
            money -= need * prices.get("WHEAT", 25) * 1.3

        empties = [p for p in owned if tiles[p[1]][p[0]] is None or is_weed(tiles[p[1]][p[0]])]
        # 3) land
        n_extra = len(me["unlocked_quadrants"]) - 1
        if hour >= 1 and n_extra < 3 and day <= self.p["last_land_day"] and len(empties) <= 3:
            cost = LAND_PRICES[n_extra]
            if money >= cost + self.p["land_reserve"]:
                orders.append(["BUY_LAND"])
                money -= cost
        # 4) geese
        if hour >= 1 and day <= self.p["last_goose_day"]:
            empty_structs = sum(1 for p in owned if is_empty_structure(tiles[p[1]][p[0]]))
            pending_roles = sum(
                1
                for p, r in self.roles.items()
                if r == "GOOSE" and not is_animal(tiles[p[1]][p[0]])
            )
            geese_total = n_animals + shed.get("GOOSE", 0) + carried.get("GOOSE", 0) + empty_structs
            geese_total = max(geese_total, n_animals + pending_roles)
            cap = int(len(owned) * self.p["max_geese_frac"])
            candidates = [p for p in empties if p not in self.roles]
            affordable = int((money - self.p["land_reserve"]) // ANIMAL_COST["GOOSE"])
            want = min(cap - geese_total, len(candidates), affordable)
            if day == 0:
                want = min(want, self.p["geese_day0"])
            if want > 0:
                candidates.sort(key=shed_dist)
                for p in candidates[:want]:
                    self.roles[p] = "GOOSE"
                orders.append(["BUY_ANIMAL", "GOOSE", want])
                money -= want * ANIMAL_COST["GOOSE"]
        # 5) seeds for plantable empty tiles
        for crop in ("MELON", "WHEAT"):
            if not can_plant(crop, day):
                continue
            n_tiles = sum(1 for p in empties if self.role(p) == crop)
            short = n_tiles - seeds.get(crop, 0)
            if short > 0:
                qty = min(short, int(money // CROPS[crop]["seed"]))
                if qty > 0:
                    orders.append(["BUY_SEED", crop, qty])
                    money -= qty * CROPS[crop]["seed"]
        # 6) hires fill the remaining slots
        to_hire = self.hires_wanted - me["hires_today"]
        for _ in range(max(0, min(to_hire, MAX_ORDERS - len(orders)))):
            orders.append(["HIRE"])
        return orders[:MAX_ORDERS]

    # ------------------------------------------------------------------ units
    def unit_actions(self, me, private, day, hour, units, invs):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        shed = private["shed"]
        seeds = dict(private["seeds"])
        final_day = day >= LAST_DAY
        carried_wheat = sum(inv.get("WHEAT", 0) for inv in invs)
        carried_geese = sum(inv.get("GOOSE", 0) for inv in invs)

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

        unfed = empty_structs = 0
        build_sites = []
        for x, y in owned:
            t = tiles[y][x]
            pos = (x, y)
            if t is None:
                role = self.role(pos)
                if role == "GOOSE":
                    build_sites.append(pos)
                elif role in CROPS and can_plant(role, day):
                    add(pos, ["PLANT", role], 58, seed=role)
            elif is_weed(t):
                add(pos, ["DIG"], 20)
            elif is_plant(t):
                cd = CROPS.get(t["crop"])
                age = day - t["planted_day"]
                ready = False
                if cd is not None:
                    ready = t["watered_today"] and age >= cd["harvest_age"]
                    if final_day and age >= cd["first"] and t["yield_units"] > 0:
                        ready = True
                elif t["yield_units"] > 0:
                    ready = True
                if ready:
                    add(pos, ["HARVEST"], 72)
                elif not t["watered_today"]:
                    add(pos, ["WATER"], 90 if t["consecutive_unwatered"] >= 1 else 60)
            elif is_animal(t):
                if not final_day and not t["fed_today"]:
                    add(pos, ["FEED"], 100, need="WHEAT")
                    unfed += 1
                if t["yield_units"] > 0:
                    add(pos, ["HARVEST"], 75 if t["yield_units"] >= 3 else 66)
                if not final_day and not t["cared_today"]:
                    add(pos, ["CARE"], 40)
                if t["fertilizer_available"]:
                    add(pos, ["COLLECT_FERTILIZER"], 30)
            elif is_empty_structure(t):
                empty_structs += 1
                add(pos, ["PLACE", "GOOSE"], 80, need="GOOSE")

        goose_supply = shed.get("GOOSE", 0) + carried_geese
        build_sites.sort(key=shed_dist)
        for pos in build_sites[: max(0, goose_supply - empty_structs)]:
            add(pos, ["BUILD_COOP"], 62)

        wheat_short = unfed - carried_wheat
        if wheat_short > 0 and shed.get("WHEAT", 0) > 0:
            per = min(shed["WHEAT"], max(1, math.ceil(wheat_short / max(1, len(units)))))
            for s in SHED_TILES:
                add(s, ["PICKUP", "WHEAT", per], 95, only_without="WHEAT", key=("PICKUP_WHEAT", s))
        geese_to_carry = min(goose_supply, empty_structs + len(build_sites)) - carried_geese
        if shed.get("GOOSE", 0) > 0 and geese_to_carry > 0:
            for s in SHED_TILES:
                add(s, ["PICKUP", "GOOSE", 1], 85, only_without="GOOSE", key=("PICKUP_GOOSE", s))

        claimed: set = set()
        actions: list[list] = []
        for i, pos in enumerate(units):
            inv = invs[i] if i < len(invs) else {}
            load = sum(inv.values())
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
                score = tk["prio"] - 4 * dist(pos, tk["pos"])
                if score > best_score:
                    best, best_score = tk, score
            if load > 0:
                sellable = load - inv.get("WHEAT", 0) - inv.get("GOOSE", 0)
                if final_day and hour >= 14:
                    dprio = 99
                elif hour >= 21:
                    dprio = 85
                elif sellable >= self.p["drop_threshold"]:
                    dprio = 50
                else:
                    dprio = None
                if dprio is not None and dprio - 4 * shed_dist(pos) > best_score:
                    best, best_score = (
                        {"pos": nearest_shed(pos), "op": ["DROP"], "key": None, "seed": None},
                        0,
                    )
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
        self.reconcile_goose_roles(me, private, carried, hour)
        actions = self.unit_actions(me, private, day, hour, units, invs)
        market = self.market_orders(obs, me, private, day, hour, carried)
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
        print(f"[hextex_v1] step {obs.get('step')} error: {exc!r}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
