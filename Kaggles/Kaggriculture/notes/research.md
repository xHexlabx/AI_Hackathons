# Kaggriculture — research notes

> Sources: environment source `kaggle_environments/envs/kaggriculture/{kaggriculture.py,README.md,AGENTS.md}`
> (kaggle-environments 1.32.7), competition page, own simulations (`sim/econ.py`, `sim/run.py`).
> Last updated 2026-09-12.

## 1. Competition facts

| | |
|---|---|
| Host | Kaggle × Google — simulation competition (agent vs agent) |
| Prize | $50,000 · top 10 × $5,000 (equal) |
| Entry deadline | **2026-09-23** (join + accept rules on the site) |
| Evaluation | Ladder games between submissions; after the final deadline submissions keep playing for **2 weeks**, then a single **Bradley-Terry tournament** ranks the final leaderboard |
| Submission | `main.py` (last callable in the file is the agent) or `tar.gz` with `main.py` at the root; `actTimeout` 1 s / step, 60 s overage |
| Episode | 2 players · 720 turns = 30 days × 24 hours · seeded, shops random |
| Score | money in the bank at step 718 — unsold inventory is worth **nothing** |

## 2. Rules that matter (verified in source)

* **HARVEST is a no-op before `first_yield_day`** → melon can never be cut before age 10, whatever the
  yield. Fertiliser on melons is useless (the README's "reaches cap at age 8" is a trap).
* One-time crops: yield = 1 + (watered days in the bonus window), window starts at `ceil(max_yield_day/2)`.
  Wheat: days 2-4 → 4 at day 4. Carrot: days 2-3 → 3 at day 3. Melon: days 6-10 → 6 at day 10.
  Fertiliser doubles the daily bonus for 3 days → wheat 5 at day 3 / 6 at day 4, carrot 4 at day 3.
* A fresh plant has `consecutive_unwatered = 1` → **must be watered on planting day**; a PLANT at hour 23
  becomes a weed. Missing two end-of-days = weed / animal escapes (unrecoverable).
* Animals: goose 1 egg/day from day 4, cow 1 milk / 2 days from day 8, sheep 1 wool / 3 days from day 6.
  `CARE` (fed + cared) banks +1 per day, paid on the next production → **goose = 2 eggs/day**.
  Every surviving animal offers 1 fertiliser/day (`COLLECT_FERTILIZER`), whether fed or not.
* Shed cap **100** non-seed items; overflow at end-of-day drop is **discarded**. Farmer inventories have no cap.
* Turn order: unit actions → market (per-unit lockstep between both players) → town consumption →
  decay → end-of-day. So `DROP` and `SELL` of the same items can happen **in the same turn**.
* Hire cost = fib(n) per extra hand that day: 10 hands = $143/day, 13 = $609, 14 = $986, 16 = $2583.
* Land: NE $1k → SW $2k → SE $4k (fixed order). Locked tiles are passable.
* Last processed action: **step 718 = day 29 hour 22**. No end-of-day on day 29.

## 3. Market economics (`sim/econ.py`)

Price = `base ± amp·f(|inv − 10000|)`, floor $1. Revenue from selling into a fresh market:

| product | base | shape (glut) | units before price < $38 | revenue | units to $1 floor | total pot |
|---|---|---|---|---|---|---|
| WHEAT | 25 | log | — | — | ∞ (~$19) | unlimited |
| EGG | 50 | log | ~1400 | $56k | ∞ (~$37) | unlimited |
| FERTILIZER | 100 | linear | 313 | **$21.5k** | 493 | $25k |
| MELON | 250 | sq | 146 | **$26.2k** | 158 | $26.5k |
| CARROT | 35 | sqrt | — | — | 842 | $10.7k |
| TOMATO | 60 | sqrt | 79 | $3.6k | 529 | $11k |
| MILK | 160 | linear | 59 | $5.9k | 76 | $6.2k |
| WOOL | 200 | sq | 53 | $7.8k | 59 | $7.9k |
| STRAWBERRY | 120 | linear | 43 | $3.4k | 62 | $3.8k |

Scarcity side: town shops drain inventory and push prices up (carrot/tomato/egg use a *hinge* → price
explodes past `T`). Three pet cafés drain 72 carrots/day → carrot went to $80-120 in our sims.

**Both players share every market** → the finite pots (melon, fertiliser, wool, milk) are races;
the unlimited sinks (egg, wheat) are limited only by land, labour and cash.

## 4. Unit economics

| asset | cost | output | value/day (early → late) | actions/day |
|---|---|---|---|---|
| Goose (fed+cared) | 300 + coop | 2 eggs + 1 fert | ~$180 → ~$110 | ~3.5 (feed, care, harvest/2d, collect) |
| Wheat tile | 10/4 days | 1 wheat/day (1.5 fert.) | ~$20 | ~2.5 |
| Carrot tile | 20/3 days | 1 carrot/day | $35 → $80+ with pet cafés | ~2.3 |
| Melon tile (one wave) | 80 | 6 melons on day 10 | ~$1000 once (uncontested) | ~1.3 |
| Cow | 400 + pasture | 1.5 milk/day | $160 → $1 fast unless milk shops | ~3.5 |
| Sheep | 500 + pasture | 1.3 wool/day | $200 → $1 fast unless yarn store | ~3.5 |
| Hand | fib(n)/day | 24 actions | — | — |

Walking is the binding constraint: 13 units × 24 = 312 actions/day; in our v4 replays ~60 % of
actions were moves. → cluster geese at the shed, route by zones, finish every task on a tile before
leaving, carry enough wheat per trip.

## 5. Strategy (current agent: `main.py` = `agents/hextex_v6.py`)

1. **Day 0**: 2-4 geese on the shed-adjacent tiles, ~22 melons on the far tiles, 7 hands.
2. **Days 1-9**: water melons, feed/care geese, **sell fertiliser at ~$100** (cash flow), eggs from day 4.
3. **Day 10**: harvest + dump ~130 melons in one turn (~$15-26k depending on the opponent).
4. **Days 10-18**: buy all land, geese up to ~32 (labour-limited), wheat/carrot only on as many tiles as
   the remaining labour can water (`crop_budget`), carrots if pet cafés unlock, a few cows/sheep only
   when milk/yarn shops exist. Units are split into contiguous zones; each fetches the wheat ration
   of the unfed animals in its zone (zone-aware pickup) and finishes every task on a tile before leaving.
5. **Every turn**: sell everything except a 1-day wheat ration; keep fertiliser only when it is worth
   < $25 (then use it on wheat/carrot).
6. **Day 29**: harvest, walk to the shed, drop + sell everything by hour 22.

### Results so far (8 games, seats swapped, `sim/run.py`)

| agent | vs starter (mean $) | mirror | notes |
|---|---|---|---|
| v1 | 7.8k | — | greedy scheduler, wheat + geese |
| v2 | 25.4k | 20.5k | + cash discipline, premium animals |
| v3 | 22.0k | — | melon fertiliser (useless — see rules) |
| v4 | 28.3k | — | sell fertiliser, cash reserve; geese starved (feeding bug) |
| v5 | 38.8k | 23.8k | carrier builds coops, wheat gating (zones were computed but not applied) |
| v6 | ~52-56k | ~30k | zone-aware feeding, labour-capped crops, sweep-tuned (`main.py`) |

### What the sweeps said (v6, 4-8 games each)
* `geese_cap` 30-36 > 42-48: beyond ~35 geese the 12-13 units cannot feed them and cash starves.
* `max_hands` 11-12 > 13-14: the 13th/14th hand ($233/$377 a day) does not pay for itself yet.
* `zone_bonus` 50 ≫ 0, `dist_penalty` 7 ≥ 4, `sticky_bonus` 40 > 20 > 0: locality is everything.
* `stay_bonus` 90 is too high (units over-stay); 40-60 fine.
* opening: 3 geese + 22 melons + 7 hands is a stable optimum among the tested openings.

## 6. Ideas / TODO

- [ ] Opponent-aware melon dump: if the opponent's melons are visible (`farms[1-p].tiles`), harvest at
      hour 0 of day 10 and sell the same turn (we already do) — consider fewer melons if they also plant ~25.
- [ ] Wheat self-sufficiency vs buying: buying 50 wheat/day pushes the price to ~$50; plant wheat on far tiles.
- [ ] Route planning per day (TSP-ish) instead of per-turn greedy assignment.
- [ ] Late-game: stop buying geese after day 18; stop COLLECT when fertiliser < $15.
- [ ] Sweep: `open_geese`, `open_melons`, `geese_cap`, `max_hands`, `dist_penalty`, `zone_bonus`.
- [ ] Download top replays from the Kaggle episode API and inspect what the leaders do.
