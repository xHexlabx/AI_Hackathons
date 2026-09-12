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

## 7. What the ladder taught us (2026-09-12, after the first public game)

Our first ladder game (episode 107962160): **$45.5k vs $94k** (opponent: 7 cows + 66 strawberries).
The community dataset (`georgymamarin/kaggriculture-episodes`) shows the whole field plays a ~$85-95k
line; top-rated seats average $100-120k; the record is ~$215k. The geese economy of v6 is simply the
wrong economy.

**The money is in the town.** Each shop instance drains 6/day of every product it wants (12 for a
single-product shop). Strawberry is wanted by 4 of the 8 shop types, milk by 3, wool by 1 (x2).
Undersupplied premium goods climb to **$250-340** (milk $334, strawberry $264, wool $246 in real games);
oversupplied ones crash to $1 within days (glut side is linear/quadratic).

**Meta field plan** (the `broker_bea` reference agent replays a fixed 712-turn trace shared by 100+ teams):
day 0: 3 cows + 1 sheep + 7 melons + 10 wheat, every coin spent; cows 8 / sheep 6 by day 12;
strawberries 2 (day 5) -> 40 (day 15); land on days 8 and 11 (3 quadrants only); 12 hands from day 9;
melons replanted through day 21; sells fertiliser/wheat immediately, premium goods with a reserve price.
Result: ~$95-107k in a mirror, $110-130k against weaker farms.

**Reference agents** (MIT, `agents/reference/`, dataset `raykkretzschmar/kaggriculture-reference-agents`)
are now our sparring ladder: fallow_finn ($3k) ... rancher_rita ($46k) ... broker_bea ($164k expected).

### Our versions against that ladder (8 games, seats swapped, mean $)

| version | vs starter | vs v6 | vs v7 | mirror | vs broker_bea | notes |
|---|---|---|---|---|---|---|
| v6 (geese) | 53k | – | – | 30k | – | ladder game: 45k vs 94k |
| v7 | 102k | 79k (100% win) | – | 89k | 66k vs 114k (0-8) | cows + strawberries + reserve pricing |
| v8 | – | – | 78k (62%) | 74k | 66k vs 114k | all-in opening, demand-sized herds |
| v9 | – | – | 77k (12%) | 70k | 67k vs 113k | opponent-aware reserve, evening dump |
| **v10 = main.py** | see README | see README | **79k vs 67k (100%)** | 68k | 62k vs 89k (0-8) | parallel reinvestment, melon 2nd wave, wheat cap |

### Why Bea still wins (revenue_report.py on v9 vs Bea, same market)

| | v9 | Bea |
|---|---|---|
| units harvested: melon / strawberry / wool / milk | 36 / 87 / 85 / 173 | 120 / 268 / 168 / 230 |
| production online | cows 6 by day 6 then stalled (cash reserve), straw 18 by day 14 | cows 8 + sheep 6 by day 10-12, straw 40 by day 15 |
| labour | 40 wheat tiles (520 wheat, ~$13k) eat 5 hands | ~10 wheat tiles, everything else premium |
| market | holds milk at reserve | sells continuously; **buys ~1400 wheat and re-sells it** as the town drains the market (wheat arbitrage) |

Take-aways for the next iteration:
1. Spend every coin on production assets in days 0-12 (cows/sheep/strawberries interleaved); no cash reserve beyond one day of feed.
2. Replant melons after the day-10 dump while the price is >= ~$130 (second wave ~$6k).
3. Consider the wheat arbitrage (buy when cheap, sell as the town drains) and buying feed instead of growing it.
4. Tune against `broker_bea`, not against `starter`; the objective is win-rate, not bank.

## 8. Round 2 (2026-09-12): ladder-meta benchmark loop

Method: every change is benchmarked with `sim/run.py <agent> agents/reference/broker_bea.py -n 24 --seed 1000`
(same seeds for every version; SE of the mean ~3k, so differences < 5k are noise) plus `sim/sweep.py` one-at-a-time.

| version | vs Bea (mean / Bea mean / win) | change | verdict |
|---|---|---|---|
| v10 | 63k / 99k / 0% | baseline | |
| v11 | 62k / 87k / 6% | strawberry fert logistics (wrong ages), continuous melons, 3 quads | no gain |
| v12 | 69k / 93k / 6% | herds = town drain − opponent supply, crew schedule (12 hands by day 10) | +6k |
| v13 | 69k / 82k / 12% | **fertiliser at ages 9 & 13** (ticks fire at END of ages 9/11/13/15) | yield 7.4/plant (Bea 6.8) |
| v14 | 81k / 97k / 12% | demand-aware strawberry tiles, geese for egg demand, strict 3 quadrants | +12k, mirror 97k |
| **v15** | **81k / 96k / 21%** | tomatoes for pizza / farmers-market demand | best; promoted to main.py |
| v16 | 60k / 92k / 0% | plan on EXPECTED end-of-season demand | ❌ over-invests day 0, starves, concedes |
| v17 | 76k / 93k / 12% | v15 + hedged herd (5 sheep, 4 cows), land after day 6 | ❌ no gain |

Per-seed analysis (v15, 24 seeds): we win games with 2-3 pet cafés (carrots 200-335 units) and lose big
(−45k) in games with yarn store(s) + 2-3 milk shops where Bea's fixed 8 cows / 6 sheep meet strong demand
(Bea 146-150k). Yarn stores that unlock late (day 18-24) still pay Bea ~$25k because its sheep already exist;
our demand-driven herd arrives too late. Milk/wool/strawberry all crash to $1 by day 18-24 when both flood.

Remaining gap (6-seed aggregate, $/game): strawberry +18k, milk +12k, wool +6k for Bea; eggs +7k, melons +3k,
carrots +2k for us. Walking is still 54-57% of actions for both.

Ideas not yet tried: daily route planning (cut walking), melon dump timing on day 10 (sell before Bea),
marginal-revenue planner instead of "fill the gap" targets, wheat buy-low/sell-high like Bea.

### Follow-ups (same day)
* v18 = v15 + ripe melons harvested/carried/sold first (prio 180/150): 48 games vs Bea 79.5k / 93.1k / 23% vs
  v15 79.0k / 93.9k / 15% on the same seeds -> within noise; kept as the newest candidate, not submitted.
* Strawberry sizing (`straw_base` 16/24/30) and the demand factor made no measurable difference over 48 games.
* Bea's "wheat trading" is not an arbitrage: it buys ~590 wheat at ~$43 and sells ~370 at ~$45 (shed-delta
  estimate) - essentially feed purchases. Nothing to copy.
* Day-10 melon dump: both players sell late in the day (hour 15-23) because the far melon tiles are reached
  last; the price only moves from $272 to $227 for ~100 melons, so the race is worth ~$3k at most.

**Where the next +15k has to come from:** labour. Both sides spend 54-57% of unit actions walking. A per-day
route plan (contiguous tile sets per unit, sweep order, one shed trip) should cut that to ~40% and free
~60 actions/day = 15-20 more tended tiles. That is a structural change (new scheduler), not a parameter.

### Ladder game 108038668 (v15 vs aiexpert1120, 88k vs 100k) - reaction speed
Shops: yarn store on day 3 and day 9, two pet cafes. The opponent opened with 16 melons + 1 sheep (kept ~$1000),
bought **9 sheep on day 10** with the melon money and finished with 14 sheep -> 309 wool at ~$243 = $75k.
We reached 7 sheep only by day 13 (2 purchases/day, cash split with strawberry seeds) -> 132 wool.
=> v18b: when the demand gap (target - owned animals) >= 4, buy up to 8 animals/day and give seeds only 20%
of the cash. vs Bea unchanged (81k / 98k), but **69% vs v15 head-to-head** and 100% vs v10: it matters against
adaptive opponents, which Bea is not. Benchmarks should use a POOL of opponents: `sim/pool.py`.

## 9. Round 3 (2026-09-12): four parallel agents

* **A – route planner (`agents/hextex_v19.py`)**: row-snake clusters balanced by workload, one PICKUP per item at
  spawn, sticky targets, idle units help other clusters from hour 8. Walking 57% -> 50%. vs Bea 88.8k/95.0k/35%
  (v18 79.5k/23%), 16-0 vs v18. Midday replans and k-medoid clustering were worse.
* **B – market layer (`agents/hextex_v19m.py`)**: nothing in the sell layer moves the needle (all within noise);
  realised prices already match Bea's. Found the end-of-day **shed overflow** leak (~$620/game, up to $5.9k):
  units carry 80-115 items at hour 23 -> fixed in v20 (return to shed from hour 18 when shed+carried+12 >= 100).
* **C – optimizer (`sim/optimize.py`, `sim/space_v18.json`)**: successive-halving random search; see its report.
* **D – top-team replays (`notes/top_agents.md`)**: the ladder's real meta line is a byte-identical "clone line"
  (Terry Luo 2919, cha7ura, tomo0608, KongKongDe): 2 cows + 2 sheep + 12 melons + 7 wheat + 5 hires on d0,
  8 cows / 6 sheep by d8-11, 3 geese d12, strawberries 20 (d5-8) + 13 (d11), land d6 + d11, 11 hands, 42% walking,
  digs strawberries at 16, 29 carrots d25-27, +$14k on d29. Top seats (3000+) keep that skeleton and scale the ONE
  herd the shops want (22 sheep with 4 yarn stores, 11-13 cows with 5-7 milk shops), cash < $1k on d1-9, sell
  continuously. Fill-ratio rule: milk/strawberry <= 0.9 x season drain -> ~$200; wool tolerates 1.1.
  Sparring partner built from the trace: `episodes/kaggle/top/clone_terry.py` (git-ignored) - beats Bea 100%.

**v20 = v19 + rush buying + full crew on day 29 + overflow return**: vs Bea 87.8k/91.5k/38% (48 games),
62% vs v19, 0-16 vs the clone (87k vs 129k). A first attempt to bolt the clone skeleton on (v20 draft) collapsed
(day-0 over-buying from the fill-ratio extension, unfed animals, 40k) -> to be done incrementally as v21.

### Round 3 results (agents C and E)

* **C – optimizer** (`sim/optimize.py`, 2,160 games): random configs are almost all worse than the defaults; the only
  consistent mild positives are `tomato_min_drain 13`, `max_carrots 32`, `liq_start_step 660` (paired margin +4.7k ± 2.2k
  vs Bea, mostly by depressing Bea's income). Round-1 "signals" (`open_cows 2`, `dist_penalty 9`, `spec_cows 5`) did not
  survive isolation. Stage-1 (16-game) rankings are noise; 48 games minimum.
* **E – clone-skeleton macro (`agents/hextex_v21.py`)**, one step at a time vs the clone:
  kept = clone opening as a fixed order list (5 HIRE, 12 melon, 7 wheat, 2 cows + 2 sheep, 4 feed wheat; placement-day
  ration saved for day 1), herd schedule floors (cows 3/4/6/8 on d3/4/7/8, sheep 4 d9 / 6 d11, geese 3 d12) with
  cash-only feed safety, strawberry pacing 5/day d5-8 + second wave of 13 on d11 (33, cap 39), `animal_actions` 5.0 so
  animal clusters are smaller (unfed animals 2-4/day -> 0-2, no escapes), second melon wave off.
  dropped = crops far / animals near (-8k), 25-40 wheat tiles (-8k: more labour than it earns in our planner), land on
  d6/d11 (-9.5k), 11 hands (-5k); neutral = wheat fertiliser at age 1-2, carrot finisher, reserve prices 0.
  v21 vs v20: **69% head-to-head** (16 games); vs Bea 84.4k/86.0k/38%; vs clone 82.7k/120.4k (margin -37.7k vs -39.1k).
  Pool (12 games x 6 opponents): v21 60%, v20 62% - equal within noise.

**Remaining gap to the clone (~38k) is labour, not the plan**: the clone walks 42% with 11 hands (6643 actions,
2782 moves), we walk 49-51% with 12 hands (~800 more moves); it harvests 517 own wheat while we buy $8.6k of feed;
its fertiliser revenue is 2x ours (more animals earlier, every unit sold); 2-3 of our animals still go unfed on some
late days (cluster logistics).

## 10. Where to resume (paused 2026-09-12)

State: `main.py` = v21 (submitted; ladder ratings ~800 for v15/v20/v21 and climbing). Partial `agents/hextex_v22.py`
(planner pass 2, agent stopped mid-way): runs clean, walking 48% (v21 50%), but 38% vs v21 head-to-head and 0-8 vs the
clone -> not promoted. The ~38k/game gap to the ladder clone is labour efficiency, not the plan.

Next steps, in order:
1. Planner pass 2 done properly: walking <= 45% (clone 42%), zero unfed animals, then spend the freed actions on
   wheat self-supply (clone: 517 wheat from ~25 tiles, we buy ~$8.6k of feed) or drop to 11 hands.
   Consider the clone's model: one fixed sweep per hand per day, no replanning, no mid-day shed trips.
2. Re-check ladder ratings after ~1 day; keep the best two submissions (v20/v21) as the final candidates unless v22 wins
   head-to-head AND on the pool (`sim/pool.py`, includes the clone).
3. Fill-ratio herd extension (agent D recs 1, 3) is implemented but conservative; once labour allows, raise caps.
Benchmarks: clone `sim/run.py <agent> episodes/kaggle/top/clone_terry.py -n 16 --seed 3000`, Bea 48 games seed 1000,
head-to-head vs main 24 games seed 1200, pool 12 games/opponent. Deadlines: entry 2026-09-23, final 2026-09-30.

## 11. Anti-meta experiment (2026-09-12, v23) - negative result

Hypothesis: the only shared state is the market, so beat the clone line by (a) earning on products it cannot crash
(eggs: log curve; fertiliser pot taken early with cheap geese) and (b) spoiling its premium pots / front-running the
melon dump. `agents/hextex_v23.py` = v21 with a geese-first opening (6 geese + 10 melons + 7 wheat, geese 12 by d6),
lighter cow/sheep floors, and a "melon rush" morning on day 10 (all units harvest and carry melons before hour 7).

Result (24 games vs the clone, seed 3000): **67.9k vs 124.8k** - worse than v21 (82.7k vs 120.4k). 479 eggs sold for
$19.5k ($41/egg, the log floor); fertiliser $12.5k vs the clone's $18k even with more animals early; giving up milk cost
~$24k in a 4-milk-shop seed (the clone's milk pot got bigger, not smaller). Strawberries did not crash either: with 4
strawberry shops the season drain absorbs 450+ units at $190-235.

Why denial does not work here: the pots that matter (milk/strawberry) are shop-driven and large; to crash them we must
match the clone's supply, which costs the same as it costs them. Eggs are safe but capped at ~$40. The clone's edge is
**efficiency, not the plan**: same seed, revenue gap only ~8-10k but **spend gap ~20k** (hires 7.5k vs 3.6k, bought
feed ~8k vs ~0, more seeds), because it walks 42% and grows 517 wheat with 11 hands. In our planner growing wheat
(`wheat_tiles_cap` 16-20) scores -6k and 13 hands +-0 (sweep, 16 games). => The lever is still the route planner.

What remains true and cheap: melon front-running on day 10 (clone sells h6-17; worth ~$3-5k), selling fertiliser the
day it is collected, and detecting the clone from its day-0 purchases (2 cows + 2 sheep + 12 melons + 7 wheat) if a
mode switch is ever useful.
