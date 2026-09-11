"""HexTex Kaggriculture agent v5 - goose economy, zone-based labour, cash discipline.

Key facts (verified against the environment source, see notes/research.md):
  * HARVEST is a no-op before `first_yield_day` -> melons can never be cut before age 10, so
    fertiliser is worthless on melons. Fertiliser is worth ~+1 unit on wheat/carrot, i.e. it is
    only worth USING when it sells for < ~$25. Otherwise SELL it: ~$21k for the first 300 units.
  * A goose = 2 eggs/day (fed + cared) + 1 fertiliser/day -> ~$180/day early, ~$110/day late.
    Payback < 3 days. Geese are the best use of both cash and labour; cluster them at the shed.
  * MELON: ~$26k for the first ~150 units, then floor -> one wave on day 0, sold on day 10.
  * EGG / WHEAT glut curves are logarithmic -> unlimited sinks (~$38 / ~$19).
  * Hire cost is fibonacci -> 13 hands max (~$609/day). Walking is the real bottleneck.
  * The last processed action is step 718 (day 29, hour 22): drop + sell before that.

Parameters can be overridden with the HEXTEX_PARAMS env var (JSON) for local sweeps.
kaggle-environments uses the LAST callable defined in this file as the agent -> keep `agent` last.
"""

from __future__ import annotations

import json
import math
import os

PARAMS = {
    # opening (day 0): geese first, melons on the far tiles, wheat on whatever cash is left
    "open_geese": 3,
    "open_melons": 22,
    "open_land": False,
    # animals
    "geese_cap": 48,
    "geese_frac": 0.55,  # max share of owned tiles
    "last_goose_day": 18,
    "cows_per_shop": 1,
    "sheep_per_shop": 3,
    "max_cows": 3,
    "max_sheep": 6,
    "last_premium_day": 14,
    "premium_min_cash": 2500,
    "carrots_per_cafe": 8,
    "max_carrots": 16,
    # land & cash
    "last_land_day": 20,
    "land_min_free": 6,  # buy land when fewer free tiles than this (and cash allows)
    "cash_floor": 60,
    "feed_days_reserve": 2.0,  # keep cash for this many days of feed
    "wheat_stock_days": 1.0,  # wheat kept in the shed (per animal)
    # market
    "fert_use_below": 25,  # fertilise wheat/carrot only when fertiliser is worth less than this
    # labour
    "max_hands": 13,
    "open_hands": 7,
    "actions_per_unit": 20,
    "walk_factor": 1.3,
    "hire_cash_frac": 0.3,
    "dist_penalty": 5,
    "stay_bonus": 60,
    "sticky_bonus": 20,
    "zone_bonus": 25,
    "drop_threshold": 10,
    "egg_harvest_at": 3,
    "wheat_pickup_min": 2,
    "wheat_pickup_max": 6,
    "land_cash_margin": 1200,
    "carrot_hot_price": 50,
    "max_carrots_hot": 30,
}
if os.environ.get("HEXTEX_PARAMS"):
    PARAMS.update(json.loads(os.environ["HEXTEX_PARAMS"]))

CROPS = {
    "WHEAT": {"seed": 10, "first": 2, "harvest_age": 4, "fert_age": (2, 3)},
    "CARROT": {"seed": 20, "first": 2, "harvest_age": 3, "fert_age": (2, 2)},
    "MELON": {"seed": 80, "first": 10, "harvest_age": 10, "fert_age": (99, 99)},
}
ANIMALS = {
    "GOOSE": {
        "cost": 300,
        "structure": "COOP",
        "product": "EGG",
        "build": "BUILD_COOP",
        "max_held": 4,
    },
    "COW": {
        "cost": 400,
        "structure": "PASTURE",
        "product": "MILK",
        "build": "BUILD_PASTURE",
        "max_held": 6,
    },
    "SHEEP": {
        "cost": 500,
        "structure": "PASTURE",
        "product": "WOOL",
        "build": "BUILD_PASTURE",
        "max_held": 6,
    },
}
MILK_SHOPS = {"PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"}
SELL_ORDER = [
    "MELON",
    "MILK",
    "WOOL",
    "STRAWBERRY",
    "FERTILIZER",
    "EGG",
    "TOMATO",
    "CARROT",
    "WHEAT",
]
PREMIUM = {"MELON", "MILK", "WOOL", "STRAWBERRY"}
LAND_PRICES = [1000, 2000, 4000]
BOARD = 10
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
LAST_DAY = 29
LAST_HOUR = 22  # step 718 = day 29 hour 22 is the last processed action
MAX_ORDERS = 10


def fib(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def hire_cost(n: int) -> int:
    return sum(fib(i) for i in range(n))


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
        ] = {}  # pos -> MELON|GOOSE|COW|SHEEP|CARROT (default WHEAT)
        self.melon_planted: set = set()
        self.hires_wanted = 0
        self.planned_day = -1
        self.last_target: dict[int, tuple] = {}
        self.zones: dict[tuple[int, int], int] = {}

    # ------------------------------------------------------------------ helpers
    def role(self, pos) -> str:
        return self.roles.get(pos, "WHEAT")

    @staticmethod
    def owned(tiles):
        return [(x, y) for y in range(BOARD) for x in range(BOARD) if tiles[y][x] != "LOCKED"]

    def can_plant(self, crop: str, day: int) -> bool:
        if crop == "MELON":
            return day <= 1  # one wave only - the market never recovers
        return day + CROPS[crop]["harvest_age"] <= LAST_DAY - 1

    # ------------------------------------------------------------------ daily plan
    def plan_day(self, obs, me, day):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        for pos in list(self.roles):
            t = tiles[pos[1]][pos[0]]
            r = self.roles[pos]
            if r == "MELON":
                if is_plant(t) and t["crop"] == "MELON":
                    self.melon_planted.add(pos)
                elif pos in self.melon_planted or not self.can_plant("MELON", day):
                    del self.roles[pos]
            elif r == "CARROT" and not self.can_plant("CARROT", day):
                del self.roles[pos]
        if day == 0 and not self.roles:
            by_shed = sorted(owned, key=shed_dist)
            for pos in by_shed[: self.p["open_geese"]]:
                self.roles[pos] = "GOOSE"
            rest = [p for p in by_shed if p not in self.roles]
            rest.sort(key=lambda p: -shed_dist(p))
            for pos in rest[: self.p["open_melons"]]:
                self.roles[pos] = "MELON"
        cafes = sum(1 for s in obs["town"]["unlocked_shops"] if s == "PET_CAFE")
        want_carrots = min(self.p["max_carrots"], cafes * self.p["carrots_per_cafe"])
        if obs["market"]["prices"].get("CARROT", 0) >= self.p["carrot_hot_price"]:
            want_carrots = max(want_carrots, min(self.p["max_carrots_hot"], cafes * 12))
        have = sum(1 for r in self.roles.values() if r == "CARROT")
        if want_carrots > have and self.can_plant("CARROT", day):
            cands = [p for p in owned if p not in self.roles and not is_animal(tiles[p[1]][p[0]])]
            cands.sort(key=shed_dist)
            for pos in cands[: want_carrots - have]:
                self.roles[pos] = "CARROT"
        self.hires_wanted = self.labour_plan(me, day)
        if day == 0:
            self.hires_wanted = max(
                self.hires_wanted, min(self.p["max_hands"], self.p["open_hands"])
            )
        self.zones = self.make_zones(me, day)

    def make_zones(self, me, day):
        """Split the active tiles into n_units contiguous groups (by quadrant, row, col)."""
        tiles = me["tiles"]
        n_units = 1 + self.hires_wanted
        active = []
        for x, y in self.owned(tiles):
            t = tiles[y][x]
            r = self.role((x, y))
            if is_animal(t) or is_plant(t) or is_empty_structure(t) or r in ANIMALS:
                w = 3.5 if (is_animal(t) or r in ANIMALS) else 2.5
            elif r in CROPS and self.can_plant(r, day):
                w = 3.0
            else:
                continue
            active.append(((x >= 5, y >= 5, y, x), (x, y), w))
        active.sort()
        total = sum(w for _, _, w in active)
        per = total / max(1, n_units)
        zones: dict[tuple[int, int], int] = {}
        acc, z = 0.0, 0
        for _, pos, w in active:
            zones[pos] = min(z, n_units - 1)
            acc += w
            if acc >= per * (z + 1):
                z += 1
        return zones

    def labour_plan(self, me, day) -> int:
        tiles = me["tiles"]
        work = 0.0
        for x, y in self.owned(tiles):
            t = tiles[y][x]
            r = self.role((x, y))
            if is_animal(t):
                work += 2.0 if day >= LAST_DAY else 3.6
            elif is_plant(t):
                work += 1.0 if day >= LAST_DAY else 2.6
            elif is_empty_structure(t) or r in ANIMALS:
                work += 4.0
            elif r in CROPS and self.can_plant(r, day):
                work += 3.0
        work *= self.p["walk_factor"]
        units = math.ceil(work / self.p["actions_per_unit"])
        hands = max(0, min(self.p["max_hands"], units - 1))
        cash_cap = max(60.0, me["money"] * self.p["hire_cash_frac"])
        while hands > 0 and hire_cost(hands) > cash_cap:
            hands -= 1
        return hands

    # ------------------------------------------------------------------ bookkeeping
    def animal_stats(self, me, private, carried):
        tiles = me["tiles"]
        stats = {}
        for a in ANIMALS:
            placed = slots = structs = 0
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
    def market_orders(self, obs, me, private, day, hour, carried, stats, dropping):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        shed, seeds, prices = private["shed"], private["seeds"], obs["market"]["prices"]
        shops = obs["town"]["unlocked_shops"]
        final_day = day >= LAST_DAY
        animals = [p for p in owned if is_animal(tiles[p[1]][p[0]])]
        n_animals = len(animals)
        wheat_price = prices.get("WHEAT", 25)
        fert_price = prices.get("FERTILIZER", 0)
        orders: list[list] = []

        # 1) sell: shed + whatever is dropped this turn (units act before the market)
        wheat_keep = 0 if final_day else math.ceil(n_animals * self.p["wheat_stock_days"])
        fert_keep = 0
        if not final_day and fert_price < self.p["fert_use_below"]:
            fert_keep = sum(
                1
                for x, y in owned
                if is_plant(tiles[y][x])
                and tiles[y][x]["crop"] in ("WHEAT", "CARROT")
                and tiles[y][x]["fertilized_until_day"] < day
                and day - tiles[y][x]["planted_day"] <= 2
            )
        for item in SELL_ORDER:
            qty = shed.get(item, 0) + dropping.get(item, 0)
            if item == "WHEAT":
                qty -= wheat_keep
            elif item == "FERTILIZER":
                qty -= fert_keep
            if qty > 0:
                orders.append(["SELL", item, qty])
        if final_day:
            return orders[:MAX_ORDERS]

        money = me["money"]
        # 2) feed: what is missing today (+ tomorrow's ration late in the day)
        unfed = sum(1 for p in animals if not tiles[p[1]][p[0]]["fed_today"])
        wheat_avail = shed.get("WHEAT", 0) + carried.get("WHEAT", 0)
        need = unfed - wheat_avail
        if hour >= 20 and day < LAST_DAY - 1:
            need = max(need, n_animals - wheat_avail)
        if need > 0 and money > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", need])
            money -= need * wheat_price * 1.3
        # cash reserve: feed for a couple of days + hires + floor
        reserve = (
            self.p["cash_floor"]
            + n_animals * self.p["feed_days_reserve"] * wheat_price * 1.2
            + hire_cost(self.hires_wanted)
        )

        empties = [p for p in owned if is_free(tiles[p[1]][p[0]])]
        n_quads = len(me["unlocked_quadrants"])
        # 3) land
        if (day == 0 and self.p["open_land"] and n_quads < 2) or (
            hour >= 1 and n_quads < 4 and day <= self.p["last_land_day"]
        ):
            cost = LAND_PRICES[n_quads - 1]
            margin = 0 if len(empties) < self.p["land_min_free"] else self.p["land_cash_margin"]
            if money - cost >= reserve + margin:
                orders.append(["BUY_LAND"])
                money -= cost
        # 4) animals
        if hour >= 1 or day == 0:
            milk_shops = sum(1 for s in shops if s in MILK_SHOPS)
            yarn = sum(1 for s in shops if s == "YARN_STORE")
            prem_ok = day <= self.p["last_premium_day"] and money >= self.p["premium_min_cash"]
            geese_target = min(self.p["geese_cap"], int(len(owned) * self.p["geese_frac"]))
            targets = {
                "GOOSE": geese_target if day <= self.p["last_goose_day"] else 0,
                "COW": min(self.p["max_cows"], milk_shops * self.p["cows_per_shop"])
                if prem_ok
                else 0,
                "SHEEP": min(self.p["max_sheep"], yarn * self.p["sheep_per_shop"])
                if prem_ok
                else 0,
            }
            if day == 0:
                targets["GOOSE"] = min(targets["GOOSE"], self.p["open_geese"])
            candidates = [p for p in empties if p not in self.roles]
            candidates.sort(key=shed_dist)
            for a in ("SHEEP", "COW", "GOOSE"):
                s = stats[a]
                have = s["placed"] + s["stock"]
                unit_cost = ANIMALS[a]["cost"] + 2 * wheat_price * self.p["feed_days_reserve"]
                affordable = int((money - reserve) // unit_cost)
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
        # 5) seeds (melon first: it is the opening, then carrots, then wheat)
        for crop in ("MELON", "CARROT", "WHEAT"):
            if not self.can_plant(crop, day):
                continue
            n_tiles = sum(1 for p in empties if self.role(p) == crop)
            short = n_tiles - seeds.get(crop, 0)
            if short > 0:
                spend_cap = money - (reserve if day > 0 else self.p["cash_floor"])
                qty = min(short, int(max(0.0, spend_cap) // CROPS[crop]["seed"]))
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
        fert_price = prices.get("FERTILIZER", 0)
        use_fert = fert_price < self.p["fert_use_below"]
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
        fert_targets = 0
        build_sites: dict[str, list] = {a: [] for a in ANIMALS}
        can_plant_now = hour <= 22  # a plant put down at hour 23 cannot be watered -> weed
        for x, y in owned:
            t = tiles[y][x]
            pos = (x, y)
            role = self.role(pos)
            if is_free(t):
                plantable = role in CROPS and self.can_plant(role, day) and can_plant_now
                if is_weed(t):
                    if role in ANIMALS or plantable:
                        add(pos, ["DIG"], 57)
                    continue
                if role in ANIMALS:
                    build_sites[role].append(pos)
                elif plantable:
                    add(pos, ["PLANT", role], 70 if role == "MELON" else 58, seed=role)
            elif is_plant(t):
                crop, age = t["crop"], day - t["planted_day"]
                cd = CROPS.get(crop)
                if cd is None:
                    if t["yield_units"] > 0:
                        add(pos, ["HARVEST"], 60)
                    elif not t["watered_today"] and not final_day:
                        add(pos, ["WATER"], 50)
                    continue
                if age >= cd["first"] and t["yield_units"] > 0:
                    ready = age >= cd["harvest_age"] and (t["watered_today"] or crop == "MELON")
                    if final_day or ready:
                        add(pos, ["HARVEST"], 96 if crop == "MELON" else 72)
                        continue
                if final_day:
                    continue
                if not t["watered_today"]:
                    add(pos, ["WATER"], 90 if t["consecutive_unwatered"] >= 1 else 60)
                if (
                    use_fert
                    and t["fertilized_until_day"] < day
                    and cd["fert_age"][0] <= age <= cd["fert_age"][1]
                ):
                    fert_targets += 1
                    add(pos, ["FERTILIZE"], 44, need="FERTILIZER")
            elif is_animal(t):
                a = ANIMALS[t["animal"]]
                if not final_day:
                    if not t["fed_today"]:
                        add(pos, ["FEED"], 100, need="WHEAT")
                        unfed += 1
                    if not t["cared_today"]:
                        add(pos, ["CARE"], 46)
                if t["yield_units"] > 0:
                    at = self.p["egg_harvest_at"] if t["animal"] == "GOOSE" else a["max_held"] - 2
                    full = t["yield_units"] >= at
                    add(
                        pos,
                        ["HARVEST"],
                        78 if (a["product"] in PREMIUM or full or final_day) else 40,
                    )
                if t["fertilizer_available"] and (not final_day or hour < 12):
                    add(pos, ["COLLECT_FERTILIZER"], 50 if fert_price >= 30 else 30)
            elif is_empty_structure(t):
                animal = role if role in ANIMALS else ("GOOSE" if t["kind"] == "COOP" else "COW")
                add(pos, ["PLACE", animal], 80, need=animal)

        for a, sites in build_sites.items():
            s = stats[a]
            sites.sort(key=shed_dist)
            # the unit carrying the animal builds the structure itself, then places
            for pos in sites[: max(0, s["stock"] - s["structs"])]:
                add(pos, [ANIMALS[a]["build"]], 80, need=a)
            if shed.get(a, 0) > 0 and (s["structs"] + len(sites)) - carried.get(a, 0) > 0:
                for st in SHED_TILES:
                    add(st, ["PICKUP", a, 1], 85, only_without=a, key=("PICKUP_" + a, st))

        n_units = max(1, len(units))
        wheat_short = unfed - carried.get("WHEAT", 0)
        if wheat_short > 0 and shed.get("WHEAT", 0) > 0:
            per = math.ceil(wheat_short / n_units)
            per = min(
                shed["WHEAT"], max(self.p["wheat_pickup_min"], min(self.p["wheat_pickup_max"], per))
            )
            for st in SHED_TILES:
                add(
                    st, ["PICKUP", "WHEAT", per], 95, only_without="WHEAT", key=("PICKUP_WHEAT", st)
                )
        fert_short = fert_targets - carried.get("FERTILIZER", 0)
        if fert_short > 0 and shed.get("FERTILIZER", 0) > 0:
            per = min(shed["FERTILIZER"], max(1, math.ceil(fert_short / n_units)), 6)
            for st in SHED_TILES:
                add(
                    st,
                    ["PICKUP", "FERTILIZER", per],
                    40,
                    only_without="FERTILIZER",
                    key=("PICKUP_FERT", st),
                )

        claimed: set = set()
        actions: list[list] = []
        new_targets: dict[int, tuple] = {}
        # NOTE: v5 computed zones but never applied them in the scoring (fixed in v6)
        stay, sticky = self.p["stay_bonus"], self.p["sticky_bonus"]
        for i, pos in enumerate(units):
            inv = invs[i] if i < len(invs) else {}
            best, best_score = None, -(10**9)
            prev = self.last_target.get(i)
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
                score = (
                    tk["prio"]
                    - 4 * d
                    + (stay if d == 0 else 0)
                    + (sticky if tk["key"] == prev else 0)
                )
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
                sd = shed_dist(pos)
                if final_day and hour + sd >= LAST_HOUR - 2:
                    dprio = 200
                elif hour + sd >= 21:
                    dprio = 120
                elif premium_load > 0:
                    dprio = 84
                elif goods + inv.get("FERTILIZER", 0) >= self.p["drop_threshold"]:
                    dprio = 50
                else:
                    dprio = None
                if dprio is not None and dprio - dp * sd > best_score:
                    best = {
                        "pos": nearest_shed(pos),
                        "op": ["DROP"],
                        "key": ("DROP", i),
                        "seed": None,
                    }
            if best is None:
                actions.append(["PASS"])
                continue
            if best["key"]:
                claimed.add(best["key"])
                new_targets[i] = best["key"]
            if best["seed"]:
                seeds[best["seed"]] -= 1
            actions.append(best["op"] if pos == best["pos"] else [move_toward(pos, best["pos"])])
        self.last_target = new_targets
        return actions

    # ------------------------------------------------------------------ step
    def act(self, obs):
        player = obs["player"]
        me = obs["farms"][player]
        private = obs["private"]
        day, hour = obs.get("day", 0), obs.get("hour", 0)
        if day != self.planned_day:
            self.plan_day(obs, me, day)
            self.planned_day = day
            self.last_target = {}
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
        dropping: dict[str, int] = {}
        for i, act in enumerate(actions):
            if act and act[0] == "DROP":
                for k, v in invs[i].items():
                    dropping[k] = dropping.get(k, 0) + v
        market = self.market_orders(obs, me, private, day, hour, carried, stats, dropping)
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
        print(f"[hextex_v5] step {obs.get('step')} error: {exc!r}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
