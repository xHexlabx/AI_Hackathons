# What the top-rated teams do (replay study, 2026-09-12)

> Question: what do ladder-top teams (teams.csv `ladder_score` >= 2900: SpaTaro, Otter Vibe, feel the agi,
> Unknown Mother-Goose, ymg_aq, binghua, keiz, kanno, Terry Luo) do differently from the meta line
> (`agents/reference/broker_bea.py`) and from our `main.py` (= `agents/hextex_v15.py`)?
>
> Data: community dataset `georgymamarin/kaggriculture-episodes` (episodes/teams/episode_features, up to
> 2026-09-11 22:50 UTC) + 9 public replays downloaded to `episodes/kaggle/top/` (git-ignored).
> Tool: `episodes/kaggle/top/analyze_top.py` — re-simulates the market lockstep of every step with both
> players' orders, so revenue/spend per product reconcile with the money delta exactly (residual 0 in all
> 24 seats). `sim/revenue_report.py` is *wrong* on these replays: it charges failed `BUY_PRODUCT` orders and
> puts the difference into the `?` bucket (SpaTaro's "buy:STRAWBERRY 59k" is an artefact).
>
> Note on ratings: `episodes.csv` `rating_X` is the per-submission rating at game time (new submissions start
> ~1800, max seen 2790); the "top" filter therefore uses `teams.ladder_score`.

## 1. Games analysed

| episode | top seat (ladder) | bank | opponent (ladder) | bank | shop mix (unlock d3..d24) | winner |
|---|---|---|---|---|---|---|
| 107812593 | SpaTaro (3126) | 115.6k | yotsutose (1886) | 108.9k | smoothie x5, pet café, farmers mkt, pizza | top |
| 105713321 | SpaTaro (3126) | 135.7k | Maksim Borisov (2465) | 132.3k | smoothie x2, brunch, ice cream x2, bakery, pizza, yarn | top |
| 106996162 | Otter Vibe (3026) | 102.6k | KongKongDe (2650) | 119.7k | bakery, farmers mkt, yarn, smoothie, ice cream, pizza x2, brunch | **opp** |
| 107022468 | feel the agi (3018) | 142.3k | tomo0608 (1945) | 126.9k | ice cream, pizza, brunch x2, smoothie x3, bakery | top |
| 107323449 | Unknown Mother-Goose (3017) | 138.2k | Juan Leiva (2318) | 119.7k | yarn x4, brunch x2, smoothie, pizza | top |
| 107299734 | ymg_aq (3015) | 95.4k | cha7ura (2386) | 89.4k | pet café x3, ice cream, farmers mkt x3, bakery | top |
| 107270780 | binghua (2967) | 119.2k | ¡olé! (1814) | 109.5k | pizza x5, ice cream x2, pet café | top |
| 107275012 | keiz (2919) | 117.1k | kanno (2936) | 96.0k | yarn x2, pet café, smoothie x2, brunch, pizza, bakery | keiz |
| 107272485 | keiz (2919) | 116.2k | Terry Luo (2919) | 120.6k | pizza, farmers mkt, smoothie x2, yarn, ice cream x2, bakery | Terry Luo |

Reference points from our own replays (same tool): `episodes/v15_vs_bea.json` v15 81.5k vs broker_bea 89.1k;
ladder game 108038668 HexTex (v15) 88.0k vs aiexpert1120 99.6k.

Per-seat summary (peak assets, revenue by product) is in the scratch CSV produced by the tool; the numbers
used below are quoted inline.

## 2. The ladder's real meta line ("clone line") — it is not `broker_bea.py`

cha7ura, tomo0608, Terry Luo (ladder 2919!) and KongKongDe play a byte-identical 712-turn trace (harvest
totals wheat 517 / wool 161 / milk 245 / melon 72 / eggs 74-78 / strawberry 249 / carrot 82-83; 6643 actions,
2782 moves). Maksim Borisov, ¡olé!, kanno, yotsutose are small variants (9 sheep / 9 cows / 11 sheep / 38
strawberries). This line is what we meet most often, and a pure clone (Terry Luo) sits at ladder ~2920.

| day | clone line (Kaggle, 1.32.x) | `broker_bea.py` in our sim |
|---|---|---|
| 0 | 5 hires, 2 cows + 2 sheep, 12 melon + 7 wheat seeds, 31 wheat bought (feed), all cash spent | 4 hires, 3 cows + 1 sheep, 7 melons, 10 wheat |
| 1-5 | 3-5 hands; cows 3 (d3), 4 (d4); sells fertiliser + surplus wheat daily | similar |
| 6 | land NE; 7 hands; 4 strawberries; first wool (10 @ $209) | land d7 |
| 7-9 | cows 6 (d7), 8 (d8); strawberries 12/16/20; sheep 4 (d9); first milk d8 (12 @ $201) | 5 cows d8, 6 sheep d9 |
| 10 | 11 hands; melon dump 60 (h6-17) + 12 on d11 @ $200-247 = $14.4k; buys 40 wheat | similar |
| 11-12 | land SW (d11); sheep 6, geese 3; strawberries 33 (13 planted d11); wheat tiles 20-25 | 40 strawberries by d15 |
| 12-21 | 9-11 hands (hires total $3.6k for the game); 8 cows / 6 sheep / 3 geese / 33 straw / 24 wheat; fertiliser on strawberries at ages 9 and 13 (61 units) | 12 hands ($7.8k); buys 931 wheat ($40k) |
| 22-27 | digs strawberries at age 16 (d21, d27), wheat 30-38 tiles, plants 29-31 carrots d25-27 | 40 straw kept to d24 |
| 28-29 | harvests everything (65 carrots, 51 wheat, 27 milk, 17 straw, 12 eggs, 11 wool) and sells by h22: **+$14k on day 29** | +$11k |
| labour | 42 % moves, 6 % PASS, 11 hands max | 56 % moves, 12 hands |
| result | $89-133k depending on shops | $89-107k |

`broker_bea.py` walks as much as we do (56 %) and hires 12; the ladder clone is leaner. Our benchmark
opponent is therefore slightly *weaker* than the ladder median, and our sim results overstate us.

## 3. What the top seats do differently (same skeleton, different sizing)

Every top seat except Otter Vibe and Mother-Goose opens exactly like the clone (5 hires, 2 cows + 2 sheep,
12 melons, 7 wheat on d0, land d6 + d10/11, melon dump d10, 12 hands from d10). The gains come from five
things, in order of size:

### 3.1 They scale the ONE premium herd the shops want, early, and hard

| game | shops for the good | top seat | clone / opponent | top revenue | opp revenue |
|---|---|---|---|---|---|
| 107323449 | yarn x4 (drain 930 wool) | Mother-Goose **22 sheep** (15 by d12, 21 by d16) | Juan Leiva 12 sheep | wool $108.2k (441 @ $245) | $71.5k (292 @ $245) |
| 107275012 | yarn x2 (606) | keiz **16 sheep** by d12 | kanno 11 sheep | wool $83.2k (381 @ $218) | $58.9k (273 @ $216) |
| 107270780 | milk x7 (732) | binghua **11 cows** by d12 | ¡olé! 9 cows | milk $73.2k (304 @ $241) | $62.6k (261 @ $240) |
| 107022468 | milk x5 (570) | feel the agi **11 cows** by d9 | tomo0608 8 cows | milk $62.6k (306 @ $205) | $49.9k (239 @ $209) |
| 105713321 | milk x5 (552) | SpaTaro **12 cows** (8 by d10) | Maksim 8 cows | milk $57.1k (293 @ $195) | $47.0k (239 @ $197) |
| 107812593 | milk x6 but late (588) | SpaTaro **13 cows by d9** | yotsutose 9 cows | milk $41.7k (352 @ $118) | $33.0k (270 @ $122) |
| 107299734 | pet café x3 (drain 966 carrots) | ymg_aq **30 carrot tiles** from d16 | cha7ura 29 tiles from d25 | carrot $31.4k (172 @ $182) | $18.6k (83 @ $224) |

Marginal value observed: ~$4k per extra cow and ~$4-5k per extra sheep as long as the combined supply stays
under the town drain (section 4), against a cost of $400-500 + ~30 wheat ($1k) + ~2 actions/day.

How they finance it: **every coin is reinvested before the melon dump** (money at h0 stays < $1k on days
1-9 for all top seats). SpaTaro d8: $21 at h0 -> sells 12 milk @ $216 -> buys 5 cows the same day (7 -> 12
cows). Mother-Goose d0: 7 hires + 5 cows + 1 sheep + 1 melon + 18 wheat seeds = $2,960, then 3-4 sheep
every 2-3 days from d6 to d22 paid from wool.

They decide by day 8-12 using the shops unlocked on d3/d6/d9 (3 of the 8), and never go *below* the clone's
8 cows / 6 sheep baseline unless the shops are clearly elsewhere (keiz: 4 cows / 16 sheep; Mother-Goose 5 / 22).

### 3.2 Strawberries: 33-39 plants, planted in two waves, replaced by carrots when they die

Mechanic (env source): strawberry produces at the END of ages 9/11/13/15 (+1, or +2 if fertilised and
watered), `max_yield` 4 is a per-plant *holding cap*, and after the 4th tick the plant decays into a weed
(age 17-18). So a plant = 8 units over ages 10-16 if fertilised at 9 and 13 and harvested every 2 days.
Clone harvest per age: 65/66/60/58 units at ages 10/12/14/16 — exactly this.

* Clone: 20 planted d5-8 + 13 on d11 (melon tiles) = 33; 249 units; first sale d15; DIGs them at age 16.
* SpaTaro: 24 by d9 + 7 on d12 + 5 on d15 = 36 (267 units); game 2: 39 planted d3-13 (295 units @ $207 = $61k).
* Mother-Goose: 29 planted d5-14 in small batches (172 units — wool was the priority).
* A plant put in on **d11-13** still gives all 8 units by d29 — the last profitable planting window.

### 3.3 Wheat: grow it, fertilise it at age 1-2, sell the surplus

* Clone: 7 wheat tiles d0, 20-25 tiles d12-21, 30-38 tiles d22-27; buys only 155 wheat ($5.5k) for 8 cows +
  6 sheep + 3 geese; sells 305 surplus wheat ($12.9k).
* feel the agi: 39-41 wheat tiles from d24, **0 wheat bought after d11**, sells 578 wheat ($21.8k).
* Fertiliser on wheat at age 1-2 (window is ages 2-4, doubled bonus, cap 6): Otter Vibe 108x -> 5.61 wheat
  per harvest, Mother-Goose 98x -> 4.51, keiz 46-50x, binghua 43x; the clone never does it (3.19/harvest).
  One fertiliser (sells for $36-50) adds 2-3 wheat ($35-45 each) -> +$40-90 per unit, ~100 units/game = +$4-8k.
* keiz's "wheat trading" (buys 830-910, sells 885-942 wheat) nets only +$2.1-2.3k. Not worth copying.

### 3.4 Labour: 11-12 hands, 38-45 % walking, and spare capacity

| seat | actions | moves | PASS | max hands | hires $ |
|---|---|---|---|---|---|
| clone (Terry Luo) | 6643 | 42 % | 6 % | 11 | 3,630 |
| SpaTaro | 7047-7186 | 39-41 % | 12-16 % | 12 | 4,316-5,099 |
| feel the agi | 7125 | 45 % | 8 % | 12 | 5,688 |
| Mother-Goose | 7730 | 42 % | 13 % | 13 | 7,565 |
| Otter Vibe (lost) | 7063 | 38 % | 9 % | **15** | **9,616** |
| **hextex v15** | 7284 | **56 %** | 6 % | 12 | 7,572 |

The 13th-15th hand costs $609-1596/day (fib); Otter Vibe paid $9.6k for hands and still lost by 17k.
SpaTaro runs 9-12 hands with 12-16 % idle actions — labour is not its constraint. We spend 1,300 more
actions walking than the clone (4,092 vs 2,782) with the same crew.

### 3.5 Selling: continuously, no reserve price; the price is set by drain vs supply, not by timing

All top seats sell milk/wool/strawberries every day from the first unit (milk from d8, wool d6, straw d13-16).
Hour-of-day makes no measurable difference (feel the agi sells milk at h0-5, tomo0608 at h18-23, same game:
$205 vs $209 avg). What matters is the season-long fill ratio (section 4). Fertiliser is sold the day it is
collected (all seats, $36-66 avg); nobody hoards anything, and the shed sits at 90-100 in the last week
regardless (Mother-Goose and binghua each lost ~11-17 units to the 100 cap).

### 3.6 Last two days

Clone d29: +$14.1k (harvests 65 carrots planted d25-27, 51 wheat, 27 milk left to accumulate, 17 straw, 12
eggs, 11 wool; sells at h0-1 and h13-22; leftover 0). ymg_aq +$17.1k, Mother-Goose +$15.3k (sells 112 wheat +
46 wool), KongKongDe +$14.6k, SpaTaro +$6-7k, feel the agi +$5.9k (everything at h21-22).
**Ours: +$0.9k (v15 vs Bea) and +$2.8k (ladder)** — 0 hands hired on d29, 33 / 25 weed tiles, nothing left to
harvest (7 eggs + 2 tomatoes). Our farm is effectively dead from d25.

## 4. Fill ratio -> price (the sizing rule), all 11 games

fill = units sold by BOTH players over the season / town drain over the season, where drain per shop
instance = 6/day x (29 - unlock day) (12/day for yarn store and pet café) + 29 from the town centre.

| product (glut curve) | fill and realised average price |
|---|---|
| MILK (linear) | 0.77 -> $241 · 0.96-0.97 -> $188-209 · 1.01-1.06 -> $118-132 · 1.13 -> $88 · 1.23 -> $42-62 · 1.5-2.8 -> $32-87 |
| WOOL (square) | 0.72-0.79 -> $245 · 1.08 -> $216 · 1.17 -> $150-167 · 1.42 -> $65-72 · >= 2.6 -> $35-117 |
| STRAWBERRY (linear) | 0.63 -> $248 · 0.82-0.89 -> $199-214 · 0.93-0.97 -> $147-160 · 1.07 -> $137-144 · 1.33-1.50 -> $50-102 |
| CARROT (hinge T=450) | 0.26 -> $182-224 · 0.37 -> $57 · 0.57-1.10 -> $36-46 |
| TOMATO (hinge T=200) | 0.02 -> $228 · 0.28-0.41 -> $66-85 |
| EGG (hinge T=332) | 0.23 -> $61 · 0.54 -> $55 · >= 1.6 -> $41-46 |
| MELON | 30 drain vs 120-240 sold: $196-247 on d10 h6-17, $100-150 for a second wave, $1 by d24 |

Rule of thumb: for milk and strawberries keep (our + opponent's visible) season supply <= ~0.9 x drain
(price ~$200); for wool up to ~1.1 x drain still pays $216. Drain is observable: the shop list is public
and `market.inventory` is the running deficit (10000 - inventory = drain - sales so far).

Production per asset: cow 1.5 milk/day (3 per 2 days, cap 6 -> harvest every 2-4 days), sheep 1.33 wool/day
(4 per 3 days), goose 2 eggs/day, strawberry 8 per plant over ages 10-16, carrot 3 (4 fertilised) per 3
days, wheat 4 (6 fertilised) per 4 days.

## 5. Where our agent loses money (v15 vs Bea replay and the ladder game)

| gap | evidence | estimated cost per game |
|---|---|---|
| herd too small / too late | v15: 3 cows 3 sheep 4 geese; ladder: 4 cows 7 sheep vs aiexpert1120's 14 sheep (wool $75.6k vs our $31.5k at $245, fill 0.72 — room for 7 more sheep) | 15-45k when yarn/milk shops exist |
| no second strawberry wave, plants left to decay | 32 planted d5-9 only; 17-33 weed tiles from d25; clone plants 13 more on d11 (+~100 units) | 10-20k |
| farm dead on d25-29, no hires on d29 | d29: +0.9k / +2.8k vs clone +14k | 8-12k |
| walking | 56 % moves vs 42 %; 1,300 actions/game | 5-10k (as tended tiles) or 3k in hands |
| carrots sold into the flat part of the hinge | ladder: 211 carrots @ $58 (deficit 380 < T 450); ymg_aq holds until deficit > 450 -> $182-244 | 0-15k depending on pet cafés |
| second melon wave | 60 melons d21-26 @ $101 -> $1 = $3k for 13 seeds + ~150 actions | ~0 (labour better on strawberries) |
| 12 hands from d10 every day | $376/day vs clone $232 (11) | ~3k |
| reserve-price holding | v15 milk held then sold d19-26 @ $2-32 (fill 1.71: holding cannot fix oversupply) | 1-3k + shed-cap risk |

## 6. Recommendations (ranked by expected gain per game)

1. **Adopt the clone skeleton and size the premium herd by fill ratio, committing by d8-12** (+15-30k).
   d0: 5 hires, 2 cows + 2 sheep, 12 melons, 7 wheat, buy ~30 wheat, spend everything. Baseline 8 cows /
   6 sheep by d9-11 (this alone matches the clone). From d6 on, each day compute season drain per product
   from the shop list (6/day x days left per instance, x2 for yarn/pet café) and the opponent's visible
   animals; add cows while (ours + theirs) x 1.5/day x days-left <= 0.9 x remaining milk drain, sheep while
   <= 1.1 x wool drain. Never hold cash: buy the next animal the hour the milk/wool/fertiliser money is in.
   Targets seen: 11-13 cows with 5-7 milk shops, 16-22 sheep with 2-4 yarn stores.
2. **Second strawberry wave on d11-13 (melon tiles) and keep 33-39 plants alive to age 16** (+10-20k).
   Fertilise at ages 9 and 13 (we do), harvest every 2 days after each tick, DIG at age 16-17 and re-use the
   tile (carrots for a d28-29 harvest, or wheat).
3. **Play the last 5 days like the clone** (+8-12k): plant 25-30 carrots on d24-26 (3 units each, $43+),
   keep watering everything that still produces, let milk/wool accumulate to the cap (6) for one final
   harvest on d28-29, hire the full crew on d29 (currently 0), and sell every unit by h22 (clone leftover 0).
4. **Cut walking from 56 % to <= 45 %** (+5-10k): contiguous tile sets per hand, one shed trip per day,
   feed/care/collect/harvest a pasture in one visit, cows harvested every 2-4 days (cap 6) instead of daily.
   The freed ~55 actions/day = 15-20 more tended tiles, or drop to 11 hands ($144/day).
5. **Wheat self-supply + fertiliser at age 1-2** (+4-8k): 20-25 wheat tiles from d12, 30-40 from d22 on
   freed strawberry tiles; put fertiliser on wheat when its price < ~$60 (it yields 6 instead of 4); stop
   buying wheat after ~d12 (feel the agi: 0 bought after d11, 578 wheat sold for $21.8k).
6. **Hinge goods (carrot/tomato/egg): sell only past the knee, otherwise skip** (0-15k): carrot pays only
   when `10000 - inventory > 450` (tomato 200, egg 332); with >= 2 pet cafés by d9 plant 25-30 carrots from
   ~d15 and hold sales until the knee (shed cap 100 permitting, e.g. ymg_aq: 172 carrots @ $182 = $31k);
   with 1 pet café or none, carrots are a $43 crop — only as the d25-27 finisher.
7. **Sell continuously, drop reserve prices** (+1-3k, less risk): reserve logic cannot raise a price the
   drain does not support; it only piles units against the 100-item shed cap and into a d29 dump.
8. **Skip the second melon wave** unless the opponent has no melons and the price is >= $150 (~0).
9. **Rebuild the sparring partner**: extract Terry Luo's action trace (episode 107272485 seat 0) into a
   replay-agent; it is the real ladder median ($110k avg here) and walks 42 %, not `broker_bea.py`'s 56 %.

## 7. Mechanics we had missed or mis-modelled

* **Strawberry lifecycle**: 4 production ticks (end of ages 9/11/13/15), per-plant holding cap 4, then
  decay to a weed at age 17-18. A plant is a 16-day asset; the last useful planting day is 13. Our agent
  neither replants after d9 nor digs the dead plants (33 weeds at d29).
* **Carrot/tomato/egg "hinge"**: price is flat (`base x (1 + deficit/T)`) until the cumulative deficit
  exceeds T (450 / 200 / 332 units), then quadratic (carrot $176 at deficit 700, $385 at 900). Demand-sized
  selling into the flat part (our ladder game: 211 carrots @ $58) wastes the tiles.
* **Animal `max_held`** (cow 6, sheep 6, goose 4): milk/wool can accumulate for 4 / 4.5 days before a
  harvest is needed — the cheap way to cut animal actions, and the reason the clone can leave the last
  harvest to d29.
* **`BUY_PRODUCT` executes only for WHEAT and FERTILIZER** (env line 598); a buy is quoted at the post-buy
  inventory so buy+sell in one turn nets exactly $0. SpaTaro's per-turn `BUY_PRODUCT CARROT/MILK/...` orders
  and feel the agi / ymg_aq / kanno's day-0 "buy 30 wheat, sell 30 wheat" loops are no-ops (verified on the
  money trace) — ignore them.
* **Sales at $1 do not add to market inventory**, so dumping at the floor never deepens the glut.
* Shops are drawn with replacement every 3 days (d3..d24, 8 instances); by d9 only 3 are known. Expected
  season drain per product from the 8 draws is 744 x P(type wants it): strawberry/wheat 372, milk/carrot
  279, egg/tomato/wool 186 — a prior for the herd decision when few shops are visible.
