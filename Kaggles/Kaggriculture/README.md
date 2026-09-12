# 🚜 Kaggriculture — Kaggle × Google simulation competition

> <https://www.kaggle.com/competitions/kaggriculture> · prize $50k (top-10 × $5k) · **entry deadline 2026-09-23**
> 2-player farming sim on a shared market · 720 turns (30 days × 24 h) · score = money in the bank at the end

📖 Research, rules that matter, market economics and strategy: [`notes/research.md`](notes/research.md)

## 🗂️ Layout

```
Kaggriculture/
├── main.py              # agent ที่ submit (= agents/hextex_v6.py)  ← last callable in file = agent
├── agents/              # hextex_v1 … v10 (ประวัติการพัฒนา) + reference/ (Kaggle reference agents, MIT)
├── sim/
│   ├── run.py           # เล่น N เกม A vs B (parallel, สลับฝั่ง) + save replay
│   ├── sweep.py         # parameter sweep ผ่าน env HEXTEX_PARAMS
│   ├── econ.py          # ตาราง price curve / revenue pot ต่อสินค้า
│   ├── inspect_replay.py# สรุปรายวัน: เงิน, tiles, market orders, actions
│   ├── feed_report.py   # ตรวจการเลี้ยงสัตว์ / การเดิน / เงิน รายวัน
│   └── revenue_report.py# รายได้แยกตามสินค้า + timeline การลงทุน ของทั้งสองฝั่ง
├── notes/research.md    # research notes + strategy + results log
├── episodes/            # replay json (git-ignored)
└── submissions/         # tar.gz / main.py ที่เคย submit (git-ignored)
```

## 🚀 Run

```bash
cd Kaggles/Kaggriculture
uv run python sim/run.py main.py agents/reference/broker_bea.py -n 8  # vs ladder meta line (เป้าหมาย)
uv run python sim/run.py main.py starter -n 8                       # vs built-in baseline
uv run python sim/run.py main.py agents/hextex_v5.py -n 8 --seed 100 # vs previous version
uv run python sim/run.py main.py main.py -n 8 --replay episodes/mirror.json
uv run python sim/inspect_replay.py episodes/mirror.json             # day-by-day summary
uv run python sim/sweep.py main.py -n 4 --grid '{"geese_cap": [30, 36, 42]}'

# submit (ต้อง join competition บนเว็บก่อน + login CLI ครั้งเดียว: `uv run kaggle auth login`)
uv run kaggle competitions submit -c kaggriculture -f main.py -m "hextex v6"
uv run kaggle competitions submissions -c kaggriculture
```

## 🧠 Strategy (v21 — clone-line macro + route planner)

เงินในเกมนี้มาจาก **ร้านค้าในเมือง**: ทุกร้านดูดสินค้าที่ต้องการออกจากตลาด 6 หน่วย/วัน ทำให้ของ premium ที่ผลิตน้อยกว่าที่เมืองดูดราคาพุ่ง ($250–340) ส่วนของที่ล้นตลาดดิ่งลง $1

1. **Day 0** — ตาม clone line ของ ladder: จ้าง 5 คน, melon 12 บน tile ไกล, wheat 7, วัว 2 + แกะ 2 ติดโรงเก็บ (order list ตายตัว เรียงให้เงินพอ), เก็บข้าวสาลี 4 หน่วยไว้ feed วันที่ 1
2. **Day 1–12** — ขายปุ๋ย/ข้าวสาลีทันทีเป็น cash flow; **ฝูงขั้นต่ำตามตาราง clone**: วัว 3/4/6/8 (d3/4/7/8), แกะ 4 (d9) / 6 (d11), ห่าน 3 (d12) ซื้อเร็วสุดที่เงินและ feed safety ยอม (rush ≤8 ตัว/วันเมื่อ gap ≥ 4); เกินขั้นต่ำขยายตาม demand − supply คู่แข่งที่มองเห็น (นม/ขนแกะ/ไข่/มะเขือเทศ/แครอท ตามร้านที่เปิด)
3. **Day 10** — เท melon wave แรก; ปลูก wave สองถ้าราคายัง ≥ $130
4. **Day 5–13** — สตรอว์เบอร์รี่ 2 wave: 5 ต้น/วัน d5–8 (20) + 13 ต้นบน tile เมลอน d11 (33, สูงสุด 39) ใส่ปุ๋ยตอนอายุ **9 และ 13** (production tick เกิดตอนสิ้นวันอายุ 9/11/13/15 → ปุ๋ย 1 หน่วยคลุม 2 tick = 8 ผล/ต้น)
5. **ทุกเทิร์น** — คนงานแบ่งเป็น cluster ติดกัน (route planner) หยิบข้าวสาลี/ปุ๋ยครบตอนเกิดที่โรงเก็บ; ของ premium ขายเมื่อราคา ≥ reserve, staple ขายทันที; กลับมาขายก่อน shed ล้นตั้งแต่ 18:00
6. **Day 27–29** — สะสมนม/ขนแกะถึง cap แล้วเก็บรอบสุดท้าย, liquidation ramp, **จ้างคนงานเต็มวันที่ 29** และขายให้หมดก่อน step 718

คู่ซ้อมมาตรฐาน: `agents/reference/broker_bea.py` (meta line ของ ladder, MIT) — เป้าหมายถัดไปคือชนะ Bea ให้ได้

## 📓 Log (8 games, seats swapped)

| Date | Version | vs starter (mean $) | mirror (mean $) | Note |
|---|---|---|---|---|
| 2026-09-11 | v1 | 7.8k | – | greedy scheduler baseline |
| 2026-09-11 | v2 | 25.4k | 20.5k | cash discipline, cows/sheep |
| 2026-09-12 | v3 | 22.0k | – | ❌ melon fertiliser (harvest blocked by first_yield_day) |
| 2026-09-12 | v4 | 28.3k | – | sell fertiliser; geese starved (wheat mis-distributed) |
| 2026-09-12 | v5 | 38.8k | 23.8k | carrier builds coop, wheat gating |
| 2026-09-12 | v6 | ~52k | ~30k | zone-based feeding, labour-capped crops, sweep-tuned · ladder game: 45k vs 94k ❌ |
| 2026-09-12 | v7 | 102k | 89k | 🔄 new economy: cows + strawberries sized by town shops, reserve-price selling |
| 2026-09-12 | v8–v9 | – | 70–74k | all-in opening, demand-sized herds, opponent-aware reserve (no gain vs Bea) |
| 2026-09-12 | v10 | 90k (vs v6: 112k, vs rancher_rita: 88k) | 68k | parallel reinvestment, melon 2nd wave, wheat cap · beats v7 100% · 0-8 vs broker_bea |
| 2026-09-12 | v11–v13 | – | – | strawberry fertiliser timing fixed (ticks fire at END of ages 9/11/13/15 → fertilise at 9 & 13), continuous melons, 3 quadrants |
| 2026-09-12 | v14 | – | 97k | demand-aware strawberries (town drain − opponent tiles), geese when bakeries/brunch spots exist · 100% vs v12 |
| 2026-09-12 | **v15** | **124k** (vs v10: 91k, 100% win) | – | + tomatoes for pizza/farmers-market demand · **vs broker_bea 81k vs 96k, 21% win (24 games)** |
| 2026-09-12 | v16–v17 | – | – | ❌ expected-demand planning (over-invests day 0, concedes markets) / herd hedge — no gain, not promoted |
| 2026-09-12 | v18 | – | – | melon rush on day 10 · 48 games vs Bea: 79.5k vs 93.1k (23%) ≈ v15 — plateau of parameter tuning |
| 2026-09-12 | v18b | – | – | rush-buy animals when a demand gap opens (≤8/day) · pool win 60% (v15: 56%), **69% vs v15**, vs Bea unchanged · submitted |
| 2026-09-12 | v19 | – | 100k | 🤖 **route planner** (agent A): row-snake clusters per hand, one shed trip at spawn · walking 57%→50% · vs Bea 88.8k/95.0k **35%** · **16-0 vs v18** |
| 2026-09-12 | v20 | – | – | v19 + rush buying + full crew on day 29 + shed-overflow return · vs Bea **87.8k vs 91.5k, 38%** · 62% vs v19 · vs ladder clone 87k vs 129k (0%) · submitted |
| 2026-09-12 | v23 | – | – | ❌ anti-meta test: geese-first + melon rush → 68k vs clone 125k (v21: 83k vs 120k); denial does not work, gap is labour (notes §11) |
| 2026-09-12 | v22 (WIP) | – | – | 🤖 planner pass 2, agent stopped mid-way: walking 48% but 38% vs v21, 0-8 vs clone — not promoted, resume here |
| 2026-09-12 | **v21 = main.py** | – | – | 🤖 agent E: clone opening (2 cows + 2 sheep + 12 melons + 7 wheat, 5 hires), herd floors 8 cows/6 sheep/3 geese by d8–12, strawberry 2nd wave d11, feed safety + optimizer params · **58–69% vs v20**, vs Bea 38%, pool 60% · submitted |
