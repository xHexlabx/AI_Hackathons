"""HexTex Kaggriculture agent v3 - "melon rush -> goose empire" with an adaptive planner.

Economics (see notes/research.md, numbers from sim/econ.py):
  * MELON: ~$26k for the first ~150 units then the price is on the $1 floor -> a single wave of
    ~22 tiles on day 0, fertilised on day 6-7 (harvest day 8), is a race the first seller wins.
  * EGG / WHEAT: logarithmic glut curves (~$38 / ~$19 forever) -> unlimited sinks. A fed + cared
    goose gives 2 eggs/day + 1 fertiliser/day for ~$300, so geese are the best use of labour.
  * FERTILIZER: linear curve, ~$21k for the first ~300 units -> sell every unit we do not need.
  * MILK / WOOL / CARROT pots are small unless the town unlocks matching shops -> adapt to
    `town.unlocked_shops` (yarn store -> sheep, pizza/ice-cream/smoothie -> cows, pet cafe -> carrots).
  * Hire cost is fibonacci: 10 hands = $143/day, 13 = $609/day -> cap hands, cluster geese near
    the shed to minimise walking.

kaggle-environments uses the LAST callable defined in this file as the agent -> keep `agent` last.
"""

from __future__ import annotations

import math

PARAMS = {
    # opening
    "open_melons": 22,
    "open_geese": 3,
    "melon_fert": True,
    # animals
    "geese_frac": 0.5,  # max share of owned tiles for geese
    "last_goose_day": 18,
    "cows_per_shop": 1,
    "sheep_per_shop": 3,
    "max_cows": 4,
    "max_sheep": 6,
    "last_premium_day": 16,
    "carrots_per_cafe": 8,
    "max_carrots": 16,
    # land & cash
    "last_land_day": 21,
    "cash_reserve": 100,
    "wheat_reserve_days": 1.0,
    # market
    "fert_sell_min": 20,  # hold fertiliser below this price (unless shed is filling up)
    "fert_wheat_below": 30,  # fertilise wheat when fertiliser is worth less than this
    # labour
    "max_hands": 13,
    "actions_per_unit": 21,
    "hire_cash_frac": 0.25,
    "stay_bonus": 30,
    "sticky_bonus": 10,
    "drop_threshold": 12,
}

CROPS = {
    "WHEAT": {"seed": 10, "first": 2, "harvest_age": 4, "fert_age": (2, 3)},
    "CARROT": {"seed": 20, "first": 2, "harvest_age": 3, "fert_age": (2, 2)},
    "MELON": {"seed": 80, "first": 10, "harvest_age": 10, "fert_age": (6, 7)},
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
LAST_STEP_HOUR = 22  # step 718 = day 29 hour 22 is the last processed action
MAX_ORDERS = 10
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}


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

    # ------------------------------------------------------------------ helpers
    def role(self, pos) -> str:
        return self.roles.get(pos, "WHEAT")

    @staticmethod
    def owned(tiles):
        return [(x, y) for y in range(BOARD) for x in range(BOARD) if tiles[y][x] != "LOCKED"]

    def can_plant(self, crop: str, day: int) -> bool:
        age = CROPS[crop]["harvest_age"]
        if crop == "MELON":
            if day > 0:
                return False  # one wave only - the market never recovers
            age = 8 if self.p["melon_fert"] else 10
        return day + age <= LAST_DAY - 1

    @staticmethod
    def harvest_age(tile, day) -> int:
        crop = tile["crop"]
        if crop == "MELON":
            fert_day = tile.get("fertilized_until_day", -1) - 2
            if 0 <= fert_day <= tile["planted_day"] + 7:
                return 8
        return CROPS[crop]["harvest_age"]

    # ------------------------------------------------------------------ daily plan
    def plan_day(self, obs, me, day):
        tiles = me["tiles"]
        owned = self.owned(tiles)
        # melon tiles revert to wheat after the harvest
        for pos in list(self.roles):
            t = tiles[pos[1]][pos[0]]
            if self.roles[pos] == "MELON":
                if is_plant(t) and t["crop"] == "MELON":
                    self.melon_planted.add(pos)
                elif pos in self.melon_planted or day > 0:
                    del self.roles[pos]
            elif self.roles[pos] == "CARROT" and not self.can_plant("CARROT", day):
                del self.roles[pos]
        if day == 0 and not self.roles:
            empties = sorted(owned, key=shed_dist)
            for pos in empties[: self.p["open_geese"]]:
                self.roles[pos] = "GOOSE"
            rest = [p for p in empties if p not in self.roles]
            rest.sort(key=lambda p: -shed_dist(p))
            for pos in rest[: self.p["open_melons"]]:
                self.roles[pos] = "MELON"
        # carrots if the town has pet cafes
        cafes = sum(1 for s in obs["town"]["unlocked_shops"] if s == "PET_CAFE")
        want_carrots = min(self.p["max_carrots"], cafes * self.p["carrots_per_cafe"])
        have = sum(1 for r in self.roles.values() if r == "CARROT")
        if want_carrots > have and self.can_plant("CARROT", day):
            cands = [p for p in owned if p not in self.roles and not is_animal(tiles[p[1]][p[0]])]
            cands.sort(key=shed_dist)
            for pos in cands[: want_carrots - have]:
                self.roles[pos] = "CARROT"
        # labour
        work = 0.0
        for x, y in owned:
            t = tiles[y][x]
            if is_animal(t):
                work += 3.0 if day >= LAST_DAY else 4.0
            elif is_plant(t) or is_empty_structure(t):
                work += 3.0
            elif self.role((x, y)) in ANIMALS:
                work += 4.0
            elif self.role((x, y)) in CROPS and self.can_plant(self.role((x, y)), day):
                work += 3.0
        units = math.ceil(work / self.p["actions_per_unit"])
        hands = max(0, min(self.p["max_hands"], units - 1))
        cash_cap = max(60.0, me["money"] * self.p["hire_cash_frac"])
        while hands > 0 and hire_cost(hands) > cash_cap:
            hands -= 1
        self.hires_wanted = hands

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
        """Purchases can fail (cash) - free the role tiles that have nothing to fill them."""
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
        shed_total = sum(shed.values())
        orders: list[list] = []

        # 1) sell: shed + whatever is being dropped this turn (units act before the market)
        wheat_reserve = 0 if final_day else math.ceil(n_animals * self.p["wheat_reserve_days"])
        fert_reserve = 0
        if not final_day:
            for x, y in owned:
                t = tiles[y][x]
                if not is_plant(t) or t["fertilized_until_day"] >= day:
                    continue
                age = day - t["planted_day"]
                if (
                    t["crop"] == "MELON"
                    and self.p["melon_fert"]
                    and age <= 7
                    or (
                        t["crop"] == "WHEAT"
                        and age <= 3
                        and prices.get("FERTILIZER", 0) < self.p["fert_wheat_below"]
                    )
                ):
                    fert_reserve += 1
        for item in SELL_ORDER:
            qty = shed.get(item, 0) + dropping.get(item, 0)
            if item == "WHEAT":
                qty -= wheat_reserve
            elif item == "FERTILIZER":
                qty -= fert_reserve
                if (
                    not final_day
                    and shed_total < 60
                    and prices.get(item, 0) < self.p["fert_sell_min"]
                ):
                    qty = 0
            if qty > 0:
                orders.append(["SELL", item, qty])
        if final_day:
            return orders[:MAX_ORDERS]

        money = me["money"]
        # 2) feed: what is still missing today (+ tomorrow's ration late in the day)
        unfed = sum(1 for p in animals if not tiles[p[1]][p[0]]["fed_today"])
        wheat_avail = shed.get("WHEAT", 0) + carried.get("WHEAT", 0)
        need = unfed - wheat_avail
        if hour >= 20 and day < LAST_DAY - 1:
            need = max(need, n_animals - wheat_avail)
        if need > 0 and money > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", need])
            money -= need * prices.get("WHEAT", 25) * 1.3
        reserve = self.p["cash_reserve"] + 25 * n_animals

        empties = [p for p in owned if is_free(tiles[p[1]][p[0]])]
        # 3) land: expand whenever affordable (income scales with tiles)
        n_quads = len(me["unlocked_quadrants"])
        if hour >= 1 and n_quads < 4 and day <= self.p["last_land_day"]:
            cost = LAND_PRICES[n_quads - 1]
            if money - cost >= reserve + 300:
                orders.append(["BUY_LAND"])
                money -= cost
        # 4) animals
        if hour >= 1:
            milk_shops = sum(1 for s in shops if s in MILK_SHOPS)
            yarn = sum(1 for s in shops if s == "YARN_STORE")
            lo_ok = day <= self.p["last_premium_day"]
            targets = {
                "GOOSE": int(len(owned) * self.p["geese_frac"])
                if day <= self.p["last_goose_day"]
                else 0,
                "COW": min(self.p["max_cows"], milk_shops * self.p["cows_per_shop"])
                if lo_ok
                else 0,
                "SHEEP": min(self.p["max_sheep"], yarn * self.p["sheep_per_shop"]) if lo_ok else 0,
            }
            if day == 0:
                targets["GOOSE"] = min(targets["GOOSE"], self.p["open_geese"])
            candidates = [p for p in empties if p not in self.roles]
            candidates.sort(key=shed_dist)
            for a in ("SHEEP", "COW", "GOOSE"):
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
        for crop in ("MELON", "CARROT", "WHEAT"):
            if not self.can_plant(crop, day):
                continue
            n_tiles = sum(1 for p in empties if self.role(p) == crop)
            short = n_tiles - seeds.get(crop, 0)
            if short > 0:
                spend_cap = money - (0 if crop == "MELON" else self.p["cash_reserve"])
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
        fert_price = prices.get("FERTILIZER", 0)
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
        for x, y in owned:
            t = tiles[y][x]
            pos = (x, y)
            role = self.role(pos)
            if is_free(t):
                plantable = role in CROPS and self.can_plant(role, day)
                if is_weed(t):
                    add(pos, ["DIG"], 57 if (role in ANIMALS or plantable) else 10)
                    continue
                if role in ANIMALS:
                    build_sites[role].append(pos)
                elif plantable:
                    add(pos, ["PLANT", role], 70 if role == "MELON" else 58, seed=role)
            elif is_plant(t):
                crop, age = t["crop"], day - t["planted_day"]
                cd = CROPS.get(crop)
                if (
                    cd is None
                ):  # crop we never plant (tomato/strawberry) - harvest if anything is there
                    if t["yield_units"] > 0:
                        add(pos, ["HARVEST"], 60)
                    elif not t["watered_today"] and not final_day:
                        add(pos, ["WATER"], 50)
                    continue
                ready = t["watered_today"] and age >= self.harvest_age(t, day)
                if final_day and age >= cd["first"] and t["yield_units"] > 0:
                    ready = True
                if ready:
                    add(pos, ["HARVEST"], 96 if crop == "MELON" else 72)
                    continue
                if final_day:
                    continue
                if not t["watered_today"]:
                    add(pos, ["WATER"], 90 if t["consecutive_unwatered"] >= 1 else 60)
                if (
                    t["fertilized_until_day"] < day
                    and cd["fert_age"][0] <= age <= cd["fert_age"][1]
                ):
                    if crop == "MELON" and self.p["melon_fert"]:
                        fert_targets += 1
                        add(pos, ["FERTILIZE"], 66, need="FERTILIZER")
                    elif crop == "WHEAT" and fert_price < self.p["fert_wheat_below"]:
                        fert_targets += 1
                        add(pos, ["FERTILIZE"], 44, need="FERTILIZER")
            elif is_animal(t):
                a = ANIMALS[t["animal"]]
                if not final_day:
                    if not t["fed_today"]:
                        add(pos, ["FEED"], 100, need="WHEAT")
                        unfed += 1
                    if not t["cared_today"]:
                        add(pos, ["CARE"], 42)
                if t["yield_units"] > 0:
                    full = t["yield_units"] >= a["max_held"] - 2
                    add(
                        pos,
                        ["HARVEST"],
                        78 if (a["product"] in PREMIUM or full or final_day) else 48,
                    )
                if t["fertilizer_available"] and (not final_day or hour < 12):
                    add(pos, ["COLLECT_FERTILIZER"], 34 if fert_price >= 15 else 8)
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

        n_units = max(1, len(units))
        wheat_short = unfed - carried.get("WHEAT", 0)
        if wheat_short > 0 and shed.get("WHEAT", 0) > 0:
            per = min(shed["WHEAT"], max(1, math.ceil(wheat_short / n_units)))
            for st in SHED_TILES:
                add(
                    st, ["PICKUP", "WHEAT", per], 95, only_without="WHEAT", key=("PICKUP_WHEAT", st)
                )
        fert_short = fert_targets - carried.get("FERTILIZER", 0)
        if fert_short > 0 and shed.get("FERTILIZER", 0) > 0:
            per = min(shed["FERTILIZER"], max(1, math.ceil(fert_short / n_units)), 8)
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
                if final_day and hour + sd >= LAST_STEP_HOUR - 3:
                    dprio = 200
                elif hour >= 21:
                    dprio = 85
                elif premium_load > 0:
                    dprio = 84
                elif goods >= self.p["drop_threshold"]:
                    dprio = 50
                else:
                    dprio = None
                if dprio is not None and dprio - 4 * sd > best_score:
                    best = {
                        "pos": nearest_shed(pos),
                        "op": ["DROP"],
                        "key": ("DROP", i),
                        "seed": None,
                    }
                    best_score = 0
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
        print(f"[hextex_v3] step {obs.get('step')} error: {exc!r}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
