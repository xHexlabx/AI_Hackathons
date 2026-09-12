"""HexTex Kaggriculture agent v18b - v18 + fast reaction to demand: animal purchases per day scale with the demand gap.

What the ladder taught us (see notes/research.md, section 7):
  * Town shops create the money: every shop instance drains 6 units/day of each product it wants
    (single-product shops 12). Strawberry sits in 4 of the 8 shop types, milk in 3, wool in 1.
    Undersupplied premium goods climb to $250-340; oversupplied ones crash to $1 within days.
  * Winning line (~$90-130k): cows from day 0 (fertiliser cash, then milk from day 8), a melon wave
    sold on day 10, then 30-60 strawberry tiles planted on days 10-14 (4 yields each on days 20-28,
    doubled by fertiliser), sheep only when a yarn store exists, wheat for feed, 10-12 hands.
  * Sell premium goods with a reserve price (hold while the town drains the market), liquidate on
    the last days, sell staples and surplus fertiliser immediately.

Parameters can be overridden with the HEXTEX_PARAMS env var (JSON) for local sweeps.
kaggle-environments uses the LAST callable defined in this file as the agent -> keep `agent` last.
"""

from __future__ import annotations

import json
import math
import os

PARAMS = {
    # opening (day 0) - all in, like the ladder meta
    "open_cows": 3,
    "open_sheep": 1,
    "open_melons": 12,
    "open_wheat": 8,
    "open_hands": 6,
    # animals: target = (town drain - opponent's visible supply) / yield + speculative base
    "spec_cows": 3,
    "spec_sheep": 3,
    "milk_per_cow": 1.5,
    "wool_per_sheep": 1.33,
    "cow_cap": 14,
    "sheep_cap": 16,
    "last_cow_day": 14,
    "last_sheep_day": 16,
    "geese_cap": 10,
    "eggs_per_goose": 2.0,
    "last_goose_day": 16,
    "min_egg_drain": 7,  # at least one egg shop before geese are considered
    # crew schedule (minimum hands by day; workload can raise it, cash no longer caps it)
    "crew_schedule": {"0": 6, "1": 4, "5": 6, "7": 8, "8": 10, "10": 12},
    # strawberries
    "straw_start_day": 5,
    "straw_last_day": 13,
    "straw_base": 16,  # speculative tiles; the rest is sized by (town drain - opponent supply)
    "straw_per_shop": 6,  # unused since v14 (kept for sweeps)
    "straw_per_tile": 0.65,  # units/day one producing tile adds to the market
    "straw_cap": 44,
    "straw_fert_ages": [
        9,
        13,
    ],  # productions fire at END of ages 9/11/13/15 -> 9 and 13 each cover two
    "straw_fert_fallback": True,
    # tomatoes: only when pizza shops / farmers markets exist (hinge scarcity -> $100-200)
    "tomato_start_day": 3,
    "tomato_last_day": 18,
    "tomato_cap": 20,
    "tomato_min_drain": 7,
    "tomato_per_tile": 0.7,
    # land & cash
    "land_day": 8,  # from this day on, buy land whenever cash allows
    "max_quadrants": 3,
    "land_overflow": False,  # allow a 4th quadrant when roles are waiting for free tiles
    "last_land_day": 18,
    "land_min_free": 4,
    "land_cash_margin": 600,
    "cash_floor": 40,
    "feed_days_reserve": 0.8,
    "wheat_stock_days": 1.2,
    "feed_buy_max_price": 60,
    # market
    "reserve_frac": {"MILK": 1.0, "STRAWBERRY": 1.0, "WOOL": 0.9, "MELON": 0.0},
    "reserve_no_shop_frac": {"MILK": 0.6, "STRAWBERRY": 0.6, "WOOL": 0.5},
    "liq_start_step": 636,  # day 26 h12: reserve decays linearly to 0 ...
    "liq_end_step": 708,  # ... by day 29 h12
    "shed_pressure": 70,
    "evening_dump_hour": 21,  # from this hour sell everything: the end-of-day drop would overflow the shed
    "opp_aware_reserve": True,
    "fert_use_below": 30,
    "max_animal_buys_per_day": 2,  # after day 0, so strawberries get cash too
    "rush_buys_per_day": 8,  # ... unless the demand gap is large (a new shop): then buy up to this many
    "rush_gap": 4,  # demand gap (animals) that triggers the rush
    "rush_seed_share": 0.2,  # strawberry seeds get only this share of cash during a rush
    "seed_cash_share": 0.5,  # share of spendable cash reserved for strawberry seeds while both are wanted
    "melon_wave2_days": [10, 19],
    "melon_wave2_min_price": 100,
    "melon_wave2_tiles": 12,
    "wheat_tiles_cap": 12,
    # labour
    "max_hands": 12,
    "actions_per_unit": 20,
    "walk_factor": 1.3,
    "hire_cash_frac": 0.3,
    "animal_actions": 3.4,
    "crop_actions": {"WHEAT": 2.6, "CARROT": 2.4, "STRAWBERRY": 1.4, "MELON": 1.4, "TOMATO": 1.6},
    "min_crop_tiles": 8,
    "dist_penalty": 7,
    "stay_bonus": 60,
    "sticky_bonus": 40,
    "zone_bonus": 50,
    "drop_threshold": 10,
    "melon_rush_prio": 150,
    "melon_harvest_prio": 180,  # harvest ripe melons before anything but feeding  # a unit holding melons walks straight to the shed (first seller wins the pot)
    "drop_near": 4,
    "wheat_pickup_max": 8,
    "feed_prio": 140,
    "carrot_hot_price": 50,
    "carrots_per_cafe": 8,
    "max_carrots": 24,
}
if os.environ.get("HEXTEX_PARAMS"):
    PARAMS.update(json.loads(os.environ["HEXTEX_PARAMS"]))

CROPS = {
    "WHEAT": {"seed": 10, "first": 2, "harvest_age": 4, "fert_age": (2, 3), "ongoing": False},
    "CARROT": {"seed": 20, "first": 2, "harvest_age": 3, "fert_age": (2, 2), "ongoing": False},
    "MELON": {"seed": 80, "first": 10, "harvest_age": 10, "fert_age": (99, 99), "ongoing": False},
    "STRAWBERRY": {
        "seed": 100,
        "first": 10,
        "harvest_age": 10,
        "fert_age": (99, 99),
        "ongoing": True,
        "last_age": 16,
    },
    "TOMATO": {
        "seed": 50,
        "first": 8,
        "harvest_age": 8,
        "fert_age": (99, 99),
        "ongoing": True,
        "last_age": 10,
    },
}
# end-of-day production ticks of the ongoing crops (age on the day the tick fires)
PROD_AGES = {"STRAWBERRY": (9, 11, 13, 15), "TOMATO": (7, 8, 9, 10)}
FERT_PRIMARY = {"STRAWBERRY": (9, 13), "TOMATO": (7, 8)}  # one unit covers 2-3 ticks here
FERT_FALLBACK = {"STRAWBERRY": (10, 11, 14, 15), "TOMATO": (9, 10)}
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
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
PREMIUM = {"MELON", "MILK", "WOOL", "STRAWBERRY"}
SHOP_DEMAND = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}
MARKET_I0 = 10000
MARKET_PARAMS = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
LAND_PRICES = [1000, 2000, 4000]
BOARD = 10
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
LAST_DAY = 29
LAST_HOUR = 22  # step 718 = day 29 hour 22 is the last processed action
MAX_ORDERS = 10


# ---------------------------------------------------------------------------- market maths
def _shape(func, x, t):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "hinge":
        u = x / t
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def market_price(item, inventory):
    base, t, bf, bt, af, at = MARKET_PARAMS[item]
    if inventory < MARKET_I0:
        amp = bt * base / _shape(bf, t, t)
        price = base + amp * _shape(bf, MARKET_I0 - inventory, t)
    else:
        amp = at * base / _shape(af, t, t)
        price = base - amp * _shape(af, inventory - MARKET_I0, t)
    return max(1, int(round(price)))


def shop_drain(shops, item):
    """Units/day the town removes from the market for `item`."""
    total = 1 if item != "FERTILIZER" else 0
    for s in shops:
        wants = SHOP_DEMAND.get(s, [])
        if item in wants:
            total += 12 if len(wants) == 1 else 6
    return total


# ---------------------------------------------------------------------------- helpers
def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def hire_cost(n):
    return sum(fib(i) for i in range(n))


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def shed_dist(pos):
    return min(dist(pos, s) for s in SHED_TILES)


def nearest_shed(pos):
    return min(SHED_TILES, key=lambda s: dist(pos, s))


def move_toward(pos, target):
    dx, dy = target[0] - pos[0], target[1] - pos[1]
    if dx != 0 and abs(dx) >= abs(dy):
        return "EAST" if dx > 0 else "WEST"
    if dy != 0:
        return "SOUTH" if dy > 0 else "NORTH"
    return "PASS"


def is_plant(t):
    return isinstance(t, dict) and t.get("kind") == "PLANT"


def is_weed(t):
    return isinstance(t, dict) and t.get("kind") == "WEED"


def is_animal(t):
    return isinstance(t, dict) and "animal" in t


def is_empty_structure(t):
    return isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE") and "animal" not in t


def is_free(t):
    return t is None or is_weed(t)


class Brain:
    def __init__(self, params=None):
        self.p = dict(PARAMS)
        if params:
            self.p.update(params)
        self.roles = {}  # pos -> COW|SHEEP|GOOSE|MELON|STRAWBERRY|CARROT (default WHEAT)
        self.planted_once = set()  # one-wave crops that were planted on this tile
        self.hires_wanted = 0
        self.planned_day = -1
        self.last_target = {}
        self.zones = {}
        self.crop_allowed = set()

    # ------------------------------------------------------------------ helpers
    def role(self, pos):
        return self.roles.get(pos, "WHEAT")

    @staticmethod
    def owned(tiles):
        return [(x, y) for y in range(BOARD) for x in range(BOARD) if tiles[y][x] != "LOCKED"]

    def can_plant(self, crop, day):
        if crop == "MELON":
            lo, hi = self.p["melon_wave2_days"]
            return day <= 1 or (lo <= day <= hi and getattr(self, "melon_hot", False))
        if crop == "STRAWBERRY":
            return self.p["straw_start_day"] <= day <= self.p["straw_last_day"]
        if crop == "TOMATO":
            return self.p["tomato_start_day"] <= day <= self.p["tomato_last_day"] and getattr(
                self, "tomato_hot", False
            )
        return day + CROPS[crop]["harvest_age"] <= LAST_DAY - 1

    STRAW_PRODUCTION_AGES = PROD_AGES["STRAWBERRY"]

    def ongoing_fert_now(self, t, day):
        """True when fertilising this ongoing crop now covers an uncovered production tick."""
        if t.get("fertilized_until_day", -1) >= day:
            return False
        crop = t["crop"]
        if crop not in PROD_AGES:
            return False
        age = day - t["planted_day"]
        if age in FERT_PRIMARY[crop]:
            return True
        return bool(self.p["straw_fert_fallback"]) and age in FERT_FALLBACK[crop]

    def straw_fert_now(self, t, day):
        return self.ongoing_fert_now(t, day)

    @staticmethod
    def shops_of(obs):
        return (obs.get("town") or {}).get("unlocked_shops", []) or []

    def animal_targets(self, obs, day):
        shops = self.shops_of(obs)
        player = obs["player"]
        farms = obs["farms"]
        opp_cows = opp_sheep = 0
        if len(farms) > 1:
            for row in farms[1 - player]["tiles"]:
                for t in row:
                    if isinstance(t, dict):
                        if t.get("animal") == "COW":
                            opp_cows += 1
                        elif t.get("animal") == "SHEEP":
                            opp_sheep += 1
        opp_geese = 0
        if len(farms) > 1:
            for row in farms[1 - player]["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("animal") == "GOOSE":
                        opp_geese += 1
        egg_drain = shop_drain(shops, "EGG")
        room_geese = (egg_drain - self.p["eggs_per_goose"] * opp_geese) / self.p["eggs_per_goose"]
        geese = 0
        if egg_drain >= self.p["min_egg_drain"]:
            geese = int(max(0, min(self.p["geese_cap"], round(room_geese))))
        room_cows = (shop_drain(shops, "MILK") - self.p["milk_per_cow"] * opp_cows) / self.p[
            "milk_per_cow"
        ]
        room_sheep = (shop_drain(shops, "WOOL") - self.p["wool_per_sheep"] * opp_sheep) / self.p[
            "wool_per_sheep"
        ]
        cows = int(
            max(self.p["spec_cows"], min(self.p["cow_cap"], round(room_cows) + self.p["spec_cows"]))
        )
        sheep = int(
            max(
                self.p["spec_sheep"],
                min(self.p["sheep_cap"], round(room_sheep) + self.p["spec_sheep"]),
            )
        )
        if day == 0:
            cows, sheep = self.p["open_cows"], self.p["open_sheep"]
        return {
            "COW": cows if day <= self.p["last_cow_day"] else 0,
            "SHEEP": sheep if day <= self.p["last_sheep_day"] else 0,
            "GOOSE": geese if day <= self.p["last_goose_day"] else 0,
        }

    def plan_day(self, obs, me, day):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        shops = self.shops_of(obs)
        prices = obs["market"]["prices"]
        # one-wave crops: role expires once the tile was planted and is free again
        for pos in list(self.roles):
            t = tiles[pos[1]][pos[0]]
            r = self.roles[pos]
            if r in ("MELON", "STRAWBERRY", "TOMATO"):
                if is_plant(t) and t["crop"] == r:
                    self.planted_once.add(pos)
                elif pos in self.planted_once or not self.can_plant(r, day):
                    del self.roles[pos]
                    self.planted_once.discard(pos)
            elif r == "CARROT" and not self.can_plant("CARROT", day):
                del self.roles[pos]
        if day == 0 and not self.roles:
            by_shed = sorted(owned, key=shed_dist)
            for pos in by_shed[: self.p["open_cows"]]:
                self.roles[pos] = "COW"
            rest = [p for p in by_shed if p not in self.roles]
            for pos in rest[: self.p["open_sheep"]]:
                self.roles[pos] = "SHEEP"
            rest = [p for p in by_shed if p not in self.roles]
            rest.sort(key=lambda p: -shed_dist(p))
            for pos in rest[: self.p["open_melons"]]:
                self.roles[pos] = "MELON"
        # strawberries: sized by the town's appetite
        if self.can_plant("STRAWBERRY", day):
            opp_straw = 0
            if len(obs["farms"]) > 1:
                for row in obs["farms"][1 - obs["player"]]["tiles"]:
                    for t in row:
                        if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                            opp_straw += 1
            drain = shop_drain(shops, "STRAWBERRY")
            room = (drain - self.p["straw_per_tile"] * opp_straw) / self.p["straw_per_tile"]
            want = int(
                max(
                    self.p["straw_base"],
                    min(self.p["straw_cap"], round(room) + self.p["straw_base"]),
                )
            )
            have = sum(1 for r in self.roles.values() if r == "STRAWBERRY")
            if want > have:
                cands = [
                    p
                    for p in owned
                    if p not in self.roles
                    and not is_animal(tiles[p[1]][p[0]])
                    and not is_empty_structure(tiles[p[1]][p[0]])
                ]
                cands.sort(key=shed_dist)
                for pos in cands[: want - have]:
                    self.roles[pos] = "STRAWBERRY"
        # melon second wave when the first dump left the price high enough
        lo, hi = self.p["melon_wave2_days"]
        self.melon_hot = prices.get("MELON", 0) >= self.p["melon_wave2_min_price"]
        if lo <= day <= hi and self.melon_hot:
            have_m = sum(1 for r in self.roles.values() if r == "MELON")
            if have_m < self.p["melon_wave2_tiles"]:
                cands = [p for p in owned if p not in self.roles and is_free(tiles[p[1]][p[0]])]
                cands.sort(key=lambda p: -shed_dist(p))
                for pos in cands[: self.p["melon_wave2_tiles"] - have_m]:
                    self.roles[pos] = "MELON"
        # tomatoes when pizza shops / farmers markets exist and the opponent leaves room
        t_drain = shop_drain(shops, "TOMATO")
        self.tomato_hot = t_drain >= self.p["tomato_min_drain"]
        if self.can_plant("TOMATO", day):
            opp_tom = 0
            if len(obs["farms"]) > 1:
                for row in obs["farms"][1 - obs["player"]]["tiles"]:
                    for t in row:
                        if isinstance(t, dict) and t.get("crop") == "TOMATO":
                            opp_tom += 1
            want_t = int(
                max(
                    0,
                    min(
                        self.p["tomato_cap"],
                        round(
                            (t_drain - self.p["tomato_per_tile"] * opp_tom)
                            / self.p["tomato_per_tile"]
                        ),
                    ),
                )
            )
            have_t = sum(1 for r in self.roles.values() if r == "TOMATO")
            if want_t > have_t:
                cands = [
                    p
                    for p in owned
                    if p not in self.roles
                    and not is_animal(tiles[p[1]][p[0]])
                    and not is_empty_structure(tiles[p[1]][p[0]])
                ]
                cands.sort(key=shed_dist)
                for pos in cands[: want_t - have_t]:
                    self.roles[pos] = "TOMATO"
        # carrots when pet cafes make them hot
        cafes = sum(1 for s in shops if s == "PET_CAFE")
        want_c = min(self.p["max_carrots"], cafes * self.p["carrots_per_cafe"])
        if prices.get("CARROT", 0) >= self.p["carrot_hot_price"]:
            want_c = max(want_c, min(self.p["max_carrots"], cafes * 12))
        have_c = sum(1 for r in self.roles.values() if r == "CARROT")
        if want_c > have_c and self.can_plant("CARROT", day):
            cands = [p for p in owned if p not in self.roles and not is_animal(tiles[p[1]][p[0]])]
            cands.sort(key=shed_dist)
            for pos in cands[: want_c - have_c]:
                self.roles[pos] = "CARROT"
        self.hires_wanted = self.labour_plan(me, day)
        if day == 0:
            self.hires_wanted = max(
                self.hires_wanted, min(self.p["max_hands"], self.p["open_hands"])
            )
        self.crop_allowed = self.crop_budget(me, day)
        self.zones = self.make_zones(me, day)

    def tile_work(self, t, r, day):
        if is_animal(t):
            return 2.0 if day >= LAST_DAY else self.p["animal_actions"]
        if is_plant(t):
            return 1.0 if day >= LAST_DAY else self.p["crop_actions"].get(t["crop"], 2.6)
        if is_empty_structure(t) or r in ANIMALS:
            return 4.0
        if r in CROPS and self.can_plant(r, day):
            return self.p["crop_actions"].get(r, 2.6) + 0.5
        return 0.0

    def labour_plan(self, me, day):
        tiles = me["tiles"]
        work = sum(
            self.tile_work(tiles[y][x], self.role((x, y)), day) for x, y in self.owned(tiles)
        )
        work *= self.p["walk_factor"]
        units = math.ceil(work / self.p["actions_per_unit"])
        hands = max(0, units - 1)
        sched = {int(k): v for k, v in self.p["crew_schedule"].items()}
        keys = [k for k in sched if k <= day]
        floor_hands = sched[max(keys)] if keys else 0
        return min(self.p["max_hands"], max(hands, floor_hands))

    def crop_budget(self, me, day):
        """Only tend as many crop tiles as the labour left after the animals allows."""
        tiles = me["tiles"]
        n_units = 1 + self.hires_wanted
        n_animals = sum(
            1
            for x, y in self.owned(tiles)
            if is_animal(tiles[y][x]) or self.role((x, y)) in ANIMALS
        )
        budget = (
            n_units * self.p["actions_per_unit"] / self.p["walk_factor"]
            - n_animals * self.p["animal_actions"]
        )
        cands = []
        for x, y in self.owned(tiles):
            t = tiles[y][x]
            r = self.role((x, y))
            if r in ANIMALS or is_animal(t) or is_empty_structure(t):
                continue
            if is_plant(t):
                cands.append(
                    (0, shed_dist((x, y)), (x, y), self.p["crop_actions"].get(t["crop"], 2.6))
                )
            elif r in CROPS and self.can_plant(r, day):
                pri = 1 if r in ("MELON", "STRAWBERRY", "TOMATO", "CARROT") else 2
                cands.append((pri, shed_dist((x, y)), (x, y), self.p["crop_actions"].get(r, 2.6)))
        cands.sort()
        allowed, used, n, wheat_n = set(), 0.0, 0, 0
        for _, _, pos, w in cands:
            t = tiles[pos[1]][pos[0]]
            crop = t["crop"] if is_plant(t) else self.role(pos)
            if crop == "WHEAT":
                if wheat_n >= max(self.p["wheat_tiles_cap"], n_animals) and not is_plant(t):
                    continue
                wheat_n += 1
            if used + w > budget and n >= self.p["min_crop_tiles"]:
                break
            allowed.add(pos)
            used += w
            n += 1
        return allowed

    def make_zones(self, me, day):
        tiles = me["tiles"]
        n_units = 1 + self.hires_wanted
        active = []
        for x, y in self.owned(tiles):
            t = tiles[y][x]
            r = self.role((x, y))
            w = self.tile_work(t, r, day)
            if w <= 0:
                continue
            if (is_plant(t) or (r in CROPS and not is_animal(t))) and (
                x,
                y,
            ) not in self.crop_allowed:
                continue
            active.append(((x >= 5, y >= 5, y, x), (x, y), w))
        active.sort()
        total = sum(w for _, _, w in active)
        per = total / max(1, n_units)
        zones, acc, z = {}, 0.0, 0
        for _, pos, w in active:
            zones[pos] = min(z, n_units - 1)
            acc += w
            if acc >= per * (z + 1):
                z += 1
        return zones

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
    @staticmethod
    def supply_per_day(farm, item):
        """Expected daily production of `item` from one farm (both farms are public)."""
        n = 0.0
        for row in farm["tiles"]:
            for t in row:
                if not isinstance(t, dict):
                    continue
                if item == "MILK" and t.get("animal") == "COW":
                    n += 1.5
                elif item == "WOOL" and t.get("animal") == "SHEEP":
                    n += 1.33
                elif item == "STRAWBERRY" and t.get("crop") == "STRAWBERRY":
                    n += 0.6
                elif item == "MELON" and t.get("crop") == "MELON":
                    n += 0.6
        return n

    def reserve_price(self, item, step, shops, farms=None, player=0):
        frac = self.p["reserve_frac"].get(item, 0.0)
        drain = shop_drain(shops, item)
        if item in self.p["reserve_no_shop_frac"] and drain <= 1:
            frac = self.p["reserve_no_shop_frac"][item]
        if self.p["opp_aware_reserve"] and farms is not None and len(farms) > 1 and frac > 0:
            supply = self.supply_per_day(farms[player], item) + self.supply_per_day(
                farms[1 - player], item
            )
            if supply > drain > 0:
                frac *= drain / supply  # structurally oversupplied -> a race to sell, not a hold
        ls, le = self.p["liq_start_step"], self.p["liq_end_step"]
        if step >= ls:
            frac *= max(0.0, (le - step) / float(max(1, le - ls)))
        return MARKET_PARAMS[item][0] * frac

    def sell_qty(self, item, held, inv, step, shops, forced, farms=None, player=0):
        if held <= 0:
            return 0
        if forced or item not in PREMIUM:
            return held
        reserve = self.reserve_price(item, step, shops, farms, player)
        n = 0
        while n < held and market_price(item, inv + n) >= reserve:
            n += 1
        return n

    def market_orders(self, obs, me, private, day, hour, carried, stats, dropping):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        shed, seeds, prices = private["shed"], private["seeds"], obs["market"]["prices"]
        inventory = obs["market"].get("inventory", {})
        shops = self.shops_of(obs)
        step = day * 24 + hour
        final_day = day >= LAST_DAY
        animals = [p for p in owned if is_animal(tiles[p[1]][p[0]])]
        n_animals = len(animals)
        wheat_price = prices.get("WHEAT", 25)
        fert_price = prices.get("FERTILIZER", 0)
        shed_load = sum(shed.values()) + sum(dropping.values())
        forced = (
            final_day or shed_load >= self.p["shed_pressure"] or hour >= self.p["evening_dump_hour"]
        )

        # 1) sells (premium goods gated by a reserve price; staples always)
        wheat_keep = 0 if final_day else math.ceil(n_animals * self.p["wheat_stock_days"])
        fert_keep = 0
        if not final_day:
            for x, y in owned:
                t = tiles[y][x]
                if not is_plant(t) or t["fertilized_until_day"] >= day:
                    continue
                age = day - t["planted_day"]
                if (
                    (t["crop"] == "STRAWBERRY" and 7 <= age <= 15)
                    or (t["crop"] == "TOMATO" and 5 <= age <= 10)
                    or (
                        t["crop"] in ("WHEAT", "CARROT")
                        and age <= 2
                        and fert_price < self.p["fert_use_below"]
                    )
                ):
                    fert_keep += 1
        sells = []
        for item in PRODUCTS:
            held = shed.get(item, 0) + dropping.get(item, 0)
            if item == "WHEAT":
                held -= wheat_keep
            elif item == "FERTILIZER":
                held -= fert_keep
            qty = self.sell_qty(
                item,
                held,
                inventory.get(item, MARKET_I0),
                step,
                shops,
                forced,
                obs["farms"],
                obs["player"],
            )
            if qty > 0:
                unit = prices.get(item, 1)
                impact = qty * (unit - market_price(item, inventory.get(item, MARKET_I0) + qty))
                sells.append((impact, unit * qty, item, qty))
        sells.sort(reverse=True)
        orders = [["SELL", item, qty] for _, _, item, qty in sells]
        if final_day:
            return orders[:MAX_ORDERS]

        money = me["money"]
        # 2) feed
        unfed = sum(1 for p in animals if not tiles[p[1]][p[0]]["fed_today"])
        wheat_avail = shed.get("WHEAT", 0) + carried.get("WHEAT", 0)
        need = unfed - wheat_avail
        if hour >= 20 and day < LAST_DAY - 1:
            need = max(need, n_animals - wheat_avail)
        elif unfed > 0 and shed.get("WHEAT", 0) == 0 and hour >= 4:
            need = max(need, min(unfed, 4))
        if need > 0 and money > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", need])
            money -= need * wheat_price * 1.3
        reserve = (
            self.p["cash_floor"]
            + n_animals * self.p["feed_days_reserve"] * wheat_price * 1.2
            + hire_cost(self.hires_wanted)
        )

        empties = [p for p in owned if is_free(tiles[p[1]][p[0]])]
        n_quads = len(me["unlocked_quadrants"])
        # 3) land: when free tiles run short (roles waiting) or cash is plentiful
        pending_roles = sum(
            1 for p, r in self.roles.items() if is_free(tiles[p[1]][p[0]]) and r != "WHEAT"
        )
        if hour >= 1 and n_quads < 4 and day <= self.p["last_land_day"]:
            cost = LAND_PRICES[n_quads - 1]
            short_of_land = len(empties) - pending_roles < self.p["land_min_free"]
            margin = 0 if short_of_land else self.p["land_cash_margin"] * n_quads
            allowed = n_quads < self.p["max_quadrants"] or (
                self.p["land_overflow"] and short_of_land and pending_roles > 0
            )
            if (
                allowed
                and money - cost >= reserve + margin
                and (short_of_land or day >= self.p["land_day"])
            ):
                orders.append(["BUY_LAND"])
                money -= cost
        # 4) animals (leave a share of the cash for strawberry seeds while those are wanted)
        straw_short = 0
        if self.can_plant("STRAWBERRY", day):
            straw_short = max(
                0,
                sum(1 for p in empties if self.role(p) == "STRAWBERRY")
                - seeds.get("STRAWBERRY", 0),
            )
        animal_money = money
        targets_now = self.animal_targets(obs, day) if (hour >= 1 or day == 0) else {}
        gap = sum(
            max(0, targets_now.get(a, 0) - (stats[a]["placed"] + stats[a]["stock"]))
            for a in ANIMALS
        )
        rush = day > 0 and gap >= self.p["rush_gap"]
        if straw_short > 0 and day > 0:
            share = self.p["rush_seed_share"] if rush else self.p["seed_cash_share"]
            animal_money = money - share * max(0.0, money - reserve)
        if hour >= 1 or day == 0:
            targets = self.animal_targets(obs, day)
            candidates = [p for p in empties if p not in self.roles]
            candidates.sort(key=shed_dist)
            bought_today = getattr(self, "animal_buys_today", (day, 0))
            bought_today = bought_today[1] if bought_today[0] == day else 0
            for a in ("COW", "SHEEP", "GOOSE"):
                s = stats[a]
                have = s["placed"] + s["stock"]
                unit_cost = ANIMALS[a]["cost"] + 2 * wheat_price * self.p["feed_days_reserve"]
                affordable = int((animal_money - reserve) // unit_cost)
                want = min(targets[a] - have, affordable)
                if day > 0:
                    cap_today = (
                        self.p["rush_buys_per_day"] if rush else self.p["max_animal_buys_per_day"]
                    )
                    want = min(want, cap_today - bought_today)
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
                animal_money -= want * ANIMALS[a]["cost"]
                bought_today += want
                self.animal_buys_today = (day, bought_today)
        # 5) seeds
        for crop in ("MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"):
            if not self.can_plant(crop, day):
                continue
            n_tiles = sum(
                1 for p in empties if self.role(p) == crop and (p in self.crop_allowed or day == 0)
            )
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
        use_fert_staple = fert_price < self.p["fert_use_below"]
        straw_ages = set(self.p["straw_fert_ages"])
        tasks = []

        def add(pos, op, prio, need=None, seed=None, only_without=None, key=None, unit=None):
            tasks.append(
                {
                    "pos": pos,
                    "op": op,
                    "prio": prio,
                    "need": need,
                    "seed": seed,
                    "only_without": only_without,
                    "key": key or (op[0], pos),
                    "unit": unit,
                }
            )

        unfed = 0
        fert_targets = 0
        build_sites = {a: [] for a in ANIMALS}
        can_plant_now = hour <= 22
        for x, y in owned:
            t = tiles[y][x]
            pos = (x, y)
            role = self.role(pos)
            if is_free(t):
                plantable = (
                    role in CROPS
                    and self.can_plant(role, day)
                    and can_plant_now
                    and (pos in self.crop_allowed or day == 0)
                )
                if is_weed(t):
                    if role in ANIMALS or plantable:
                        add(pos, ["DIG"], 57)
                    continue
                if role in ANIMALS:
                    build_sites[role].append(pos)
                elif plantable:
                    add(
                        pos,
                        ["PLANT", role],
                        72 if role in ("MELON", "STRAWBERRY") else 58,
                        seed=role,
                    )
            elif is_plant(t):
                crop, age = t["crop"], day - t["planted_day"]
                cd = CROPS.get(crop)
                if cd is None:  # unknown crop
                    if t["yield_units"] > 0:
                        add(pos, ["HARVEST"], 60)
                    elif not t["watered_today"] and not final_day:
                        add(pos, ["WATER"], 50)
                    continue
                if cd["ongoing"]:
                    ticks = PROD_AGES[crop]
                    if t["yield_units"] > 0:
                        urgent = t["yield_units"] >= 2 or final_day or hour >= 18 or age > ticks[-1]
                        add(pos, ["HARVEST"], 74 if urgent else 52)
                    if final_day:
                        continue
                    if age > cd["last_age"] and t["yield_units"] == 0:
                        if self.can_plant("WHEAT", day) and pos in self.crop_allowed:
                            add(pos, ["DIG"], 30)
                        continue
                    if not t["watered_today"]:
                        # an unwatered production tick forfeits the fertiliser doubling
                        base_w = 86 if age in ticks else (70 if age >= ticks[0] - 1 else 60)
                        add(
                            pos,
                            ["WATER"],
                            (90 + hour // 2)
                            if t["consecutive_unwatered"] >= 1
                            else (base_w + hour),
                        )
                    if self.ongoing_fert_now(t, day):
                        fert_targets += 1
                        primary = age in FERT_PRIMARY[crop]
                        add(pos, ["FERTILIZE"], 78 if primary else 60, need="FERTILIZER")
                    continue
                if age >= cd["first"] and t["yield_units"] > 0:
                    ready = age >= cd["harvest_age"] and (t["watered_today"] or crop == "MELON")
                    if final_day or ready:
                        add(
                            pos,
                            ["HARVEST"],
                            self.p["melon_harvest_prio"] if crop == "MELON" else 72,
                        )
                        continue
                if final_day:
                    continue
                if not t["watered_today"]:
                    base_w = 82 if (crop == "MELON" and age >= 6) else 60
                    add(
                        pos,
                        ["WATER"],
                        (90 + hour // 2) if t["consecutive_unwatered"] >= 1 else (base_w + hour),
                    )
                if (
                    use_fert_staple
                    and crop in ("WHEAT", "CARROT")
                    and t["fertilized_until_day"] < day
                    and cd["fert_age"][0] <= age <= cd["fert_age"][1]
                ):
                    fert_targets += 1
                    add(pos, ["FERTILIZE"], 44, need="FERTILIZER")
            elif is_animal(t):
                a = ANIMALS[t["animal"]]
                gate = "WHEAT" if (not final_day and not t["fed_today"] and hour < 18) else None
                if not final_day:
                    if not t["fed_today"]:
                        add(pos, ["FEED"], self.p["feed_prio"], need="WHEAT")
                        unfed += 1
                    if not t["cared_today"]:
                        add(pos, ["CARE"], 46, need=gate)
                if t["yield_units"] > 0:
                    add(
                        pos,
                        ["HARVEST"],
                        78
                        if (
                            a["product"] in PREMIUM
                            or t["yield_units"] >= a["max_held"] - 1
                            or final_day
                        )
                        else 40,
                        need=gate,
                    )
                if t["fertilizer_available"] and (not final_day or hour < 12):
                    add(pos, ["COLLECT_FERTILIZER"], 70 if fert_price >= 40 else 45, need=gate)
            elif is_empty_structure(t):
                if role in ANIMALS and ANIMALS[role]["structure"] == t["kind"]:
                    animal = role
                else:
                    animal = "GOOSE" if t["kind"] == "COOP" else "COW"
                add(pos, ["PLACE", animal], 80, need=animal)

        for a, sites in build_sites.items():
            s = stats[a]
            sites.sort(key=shed_dist)
            for pos in sites[: max(0, s["stock"] - s["structs"])]:
                add(pos, [ANIMALS[a]["build"]], 80, need=a)
            if shed.get(a, 0) > 0 and (s["structs"] + len(sites)) - carried.get(a, 0) > 0:
                for st in SHED_TILES:
                    add(st, ["PICKUP", a, 1], 85, only_without=a, key=("PICKUP_" + a, st))

        # zone-aware wheat pickup
        wheat_need, unassigned = {}, 0
        for x, y in owned:
            t = tiles[y][x]
            if is_animal(t) and not t["fed_today"] and not final_day:
                z = self.zones.get((x, y))
                if z is None or z >= len(units):
                    unassigned += 1
                else:
                    wheat_need[z] = wheat_need.get(z, 0) + 1
        idle = [i for i in range(len(units)) if wheat_need.get(i, 0) == 0]
        if unassigned > 0 and idle:
            for i in idle:
                wheat_need[i] = math.ceil(unassigned / len(idle))
        shed_wheat = shed.get("WHEAT", 0)
        for i in range(len(units)):
            inv = invs[i] if i < len(invs) else {}
            want = wheat_need.get(i, 0) - inv.get("WHEAT", 0)
            if hour >= 14 and unfed - carried.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                want = max(want, 2)
            want = min(want, self.p["wheat_pickup_max"], shed_wheat)
            if want > 0:
                for st in SHED_TILES:
                    add(
                        st,
                        ["PICKUP", "WHEAT", want],
                        95,
                        only_without="WHEAT",
                        key=("PICKUP_WHEAT", i, st),
                        unit=i,
                    )
        # zone-aware fertiliser pickup: each unit fetches what its zone's plants need today
        fert_need, fert_unassigned = {}, 0
        for x, y in owned:
            t = tiles[y][x]
            if not is_plant(t) or final_day:
                continue
            needs = False
            if t["crop"] == "STRAWBERRY":
                needs = self.straw_fert_now(t, day)
            elif t["crop"] in ("WHEAT", "CARROT") and use_fert_staple:
                a = day - t["planted_day"]
                cd = CROPS[t["crop"]]
                needs = (
                    t["fertilized_until_day"] < day and cd["fert_age"][0] <= a <= cd["fert_age"][1]
                )
            if not needs:
                continue
            z = self.zones.get((x, y))
            if z is None or z >= len(units):
                fert_unassigned += 1
            else:
                fert_need[z] = fert_need.get(z, 0) + 1
        shed_fert = shed.get("FERTILIZER", 0)
        for i in range(len(units)):
            inv = invs[i] if i < len(invs) else {}
            want = fert_need.get(i, 0) - inv.get("FERTILIZER", 0)
            if i == 0 and fert_unassigned > 0:
                want += fert_unassigned
            want = min(want, 8, shed_fert)
            if want > 0:
                for st in SHED_TILES:
                    add(
                        st,
                        ["PICKUP", "FERTILIZER", want],
                        72,
                        only_without="FERTILIZER",
                        key=("PICKUP_FERT", i, st),
                        unit=i,
                    )

        claimed, actions, new_targets = set(), [], {}
        stay, sticky, zone_b, dp = (
            self.p["stay_bonus"],
            self.p["sticky_bonus"],
            self.p["zone_bonus"],
            self.p["dist_penalty"],
        )
        for i, pos in enumerate(units):
            inv = invs[i] if i < len(invs) else {}
            best, best_score = None, -(10**9)
            prev = self.last_target.get(i)
            for tk in tasks:
                if tk["key"] in claimed:
                    continue
                if tk["unit"] is not None and tk["unit"] != i:
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
                    - dp * d
                    + (stay if d == 0 else 0)
                    + (sticky if tk["key"] == prev else 0)
                )
                if self.zones.get(tk["pos"]) == i:
                    score += zone_b
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
                elif inv.get("MELON", 0) > 0:
                    dprio = self.p["melon_rush_prio"]
                elif hour + sd >= 21:
                    dprio = 120
                elif premium_load >= 3 or (premium_load > 0 and sd <= 1):
                    dprio = 84
                elif goods + inv.get("FERTILIZER", 0) >= self.p["drop_threshold"]:
                    dprio = 50
                elif sd <= 1 and goods + inv.get("FERTILIZER", 0) >= self.p["drop_near"]:
                    dprio = 45
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
        carried = {}
        for inv in invs:
            for k, v in inv.items():
                carried[k] = carried.get(k, 0) + v
        stats = self.animal_stats(me, private, carried)
        self.release_unfilled_roles(me, stats, hour)
        stats = self.animal_stats(me, private, carried)
        actions = self.unit_actions(obs, me, private, day, hour, units, invs, carried, stats)
        dropping = {}
        for i, act in enumerate(actions):
            if act and act[0] == "DROP":
                for k, v in invs[i].items():
                    dropping[k] = dropping.get(k, 0) + v
        market = self.market_orders(obs, me, private, day, hour, carried, stats, dropping)
        return {"farmer": actions[0], "hands": actions[1:], "market": market}


_BRAINS = {}


def agent(obs, config=None):
    del config
    player = obs["player"]
    brain = _BRAINS.get(player)
    if brain is None or obs.get("step", 0) == 0:
        brain = _BRAINS[player] = Brain()
    try:
        return brain.act(obs)
    except Exception as exc:  # noqa: BLE001 - never crash the episode
        print(f"[hextex_v18b] step {obs.get('step')} error: {exc!r}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
