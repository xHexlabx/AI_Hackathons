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

## 🧠 Strategy (v10 — "dairy & berries")

เงินในเกมนี้มาจาก **ร้านค้าในเมือง**: ทุกร้านดูดสินค้าที่ต้องการออกจากตลาด 6 หน่วย/วัน ทำให้ของ premium ที่ผลิตน้อยกว่าที่เมืองดูดราคาพุ่ง ($250–340) ส่วนของที่ล้นตลาดดิ่งลง $1

1. **Day 0** — วัว 3 + แกะ 1 ติดโรงเก็บ, melon 8 บน tile ไกล, wheat 8, จ้าง 6 คน (ใช้เงินเกือบหมด)
2. **Day 1–12** — ขายปุ๋ย/ข้าวสาลีทันทีเป็น cash flow, ซื้อวัว/แกะเพิ่มวันละ ≤2 ตัวควบคู่กับเมล็ดสตรอว์เบอร์รี่ (แบ่งเงินครึ่ง-ครึ่ง), เป้าหมายสัตว์/สตรอว์เบอร์รี่ปรับตามร้านที่เปิด (`SHOP_DEMAND`)
3. **Day 10** — เท melon wave แรก; ปลูก wave สองถ้าราคายัง ≥ $130
4. **Day 6–14** — สตรอว์เบอร์รี่ 24 + 6/ร้าน (สูงสุด 48 แปลง) ใส่ปุ๋ยจากวัวตอนอายุ 10 และ 14 (ผลผลิต ×2)
5. **ทุกเทิร์น** — ของ premium ขายเมื่อราคา ≥ reserve (ลดลงตาม supply รวมของเราและคู่แข่งที่มองเห็นได้), ของ staple ขายทันที, บังคับขายทุกอย่างตั้งแต่ 21:00 กัน shed ล้น
6. **Day 26–29** — reserve ลดเป็น 0 เชิงเส้น (liquidation) และขายให้หมดก่อน step 718

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
| 2026-09-12 | **v10** | **90k** (vs v6: 112k, vs rancher_rita: 88k) | 68k | parallel reinvestment, melon 2nd wave, wheat cap · beats v7 100% · still 0-8 vs broker_bea |
