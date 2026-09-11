# 🚜 Kaggriculture — Kaggle × Google simulation competition

> <https://www.kaggle.com/competitions/kaggriculture> · prize $50k (top-10 × $5k) · **entry deadline 2026-09-23**
> 2-player farming sim on a shared market · 720 turns (30 days × 24 h) · score = money in the bank at the end

📖 Research, rules that matter, market economics and strategy: [`notes/research.md`](notes/research.md)

## 🗂️ Layout

```
Kaggriculture/
├── main.py              # agent ที่ submit (= agents/hextex_v6.py)  ← last callable in file = agent
├── agents/              # hextex_v1 … v6 (ประวัติการพัฒนา, ใช้เป็นคู่ซ้อม)
├── sim/
│   ├── run.py           # เล่น N เกม A vs B (parallel, สลับฝั่ง) + save replay
│   ├── sweep.py         # parameter sweep ผ่าน env HEXTEX_PARAMS
│   ├── econ.py          # ตาราง price curve / revenue pot ต่อสินค้า
│   ├── inspect_replay.py# สรุปรายวัน: เงิน, tiles, market orders, actions
│   └── feed_report.py   # ตรวจการเลี้ยงสัตว์ / การเดิน / เงิน รายวัน
├── notes/research.md    # research notes + strategy + results log
├── episodes/            # replay json (git-ignored)
└── submissions/         # tar.gz / main.py ที่เคย submit (git-ignored)
```

## 🚀 Run

```bash
cd Kaggles/Kaggriculture
uv run python sim/run.py main.py starter -n 8                       # vs built-in baseline
uv run python sim/run.py main.py agents/hextex_v5.py -n 8 --seed 100 # vs previous version
uv run python sim/run.py main.py main.py -n 8 --replay episodes/mirror.json
uv run python sim/inspect_replay.py episodes/mirror.json             # day-by-day summary
uv run python sim/sweep.py main.py -n 4 --grid '{"geese_cap": [30, 36, 42]}'

# submit (ต้อง join competition บนเว็บก่อน + login CLI ครั้งเดียว: `uv run kaggle auth login`)
uv run kaggle competitions submit -c kaggriculture -f main.py -m "hextex v6"
uv run kaggle competitions submissions -c kaggriculture
```

## 🧠 Strategy (v6)

1. **Day 0** — 3 geese ติดโรงเก็บ, ~22 melon บน tile ไกล, จ้างคนงาน 7 คน
2. **Day 1–9** — รดน้ำ melon, เลี้ยง+ดูแลห่าน (2 ไข่/วัน), **ขายปุ๋ยทุกวัน ($100/หน่วย)** เป็น cash flow
3. **Day 10** — เก็บ melon ~130 ลูก ขายทีเดียว (~$15–26k; first seller wins the pot)
4. **Day 10–18** — ซื้อที่ดินครบ, ห่านถึง ~36 ตัว (จำกัดด้วยแรงงาน), wheat/carrot บน tile ที่เหลือตาม labour budget
5. **ทุกเทิร์น** — ขายทุกอย่างยกเว้นข้าวสาลีสำรอง 1 วัน; แบ่งคนงานเป็นโซน, หยิบข้าวสาลีตามจำนวนห่านในโซน
6. **Day 29** — เก็บทุกอย่าง เดินกลับโรงเก็บ ขายให้หมดก่อน step 718

## 📓 Log (8 games, seats swapped)

| Date | Version | vs starter (mean $) | mirror (mean $) | Note |
|---|---|---|---|---|
| 2026-09-11 | v1 | 7.8k | – | greedy scheduler baseline |
| 2026-09-11 | v2 | 25.4k | 20.5k | cash discipline, cows/sheep |
| 2026-09-12 | v3 | 22.0k | – | ❌ melon fertiliser (harvest blocked by first_yield_day) |
| 2026-09-12 | v4 | 28.3k | – | sell fertiliser; geese starved (wheat mis-distributed) |
| 2026-09-12 | v5 | 38.8k | 23.8k | carrier builds coop, wheat gating |
| 2026-09-12 | v6 | **~52k** | ~30k | zone-based feeding, labour-capped crops, sweep-tuned |
