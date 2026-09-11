<div align="center">

# 🏆 AI Hackathons

**พื้นที่รวมงาน Kaggle competitions และ AI hackathons ของ HexTex**<br>
Python-first · reproducible · เริ่มโปรเจกต์ใหม่ได้ในคำสั่งเดียว

[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![uv](https://img.shields.io/badge/deps-uv-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=D7FF64)](https://docs.astral.sh/ruff/)
[![CI](https://github.com/xHexlabx/AI_Hackathons/actions/workflows/ci.yml/badge.svg)](https://github.com/xHexlabx/AI_Hackathons/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

Repository นี้รวบรวม code และเทคนิคจากการแข่ง Kaggle / hackathon ต่าง ๆ หวังว่าจะเป็นประโยชน์กับผู้เข้าชมไม่มากก็น้อย หากมีข้อผิดพลาดขออภัยมา ณ ที่นี้ด้วยนะครับ — HexTex 😸

> **ตั้งแต่ปี 2026** งานใหม่ทั้งหมดพัฒนาด้วย **Python package (`src/`) เป็นหลัก** — notebook ใช้สำหรับ EDA เท่านั้น
> งานเก่า (2024–2025) ยังเก็บ notebook ต้นฉบับไว้ครบใน `notebooks/` ของแต่ละโปรเจกต์

## ✨ Highlights

| | Event | Result |
|---|---|---|
| 🥇 | [Mahidol × SuperAI — Human Activity Recognition](Hackathons/Human_Activity_Recognition/) | **ชนะเลิศ** (on-site) |
| 🏅 | [PSU Phuket — Durian Hackathon](Hackathons/Durian_Hackathon/) | อันดับ 5 · Private score **#3** |
| 🚜 | [Kaggle × Google — Kaggriculture](Kaggles/Kaggriculture/) (2026) | 🔥 กำลังแข่ง — simulation agent |

## 🗂️ โครงสร้าง

```
AI_Hackathons/
├── Kaggles/            🚜 Kaggle competitions          (Kaggriculture, Titanic, Spaceship Titanic, ...)
├── Hackathons/         🏁 on-site / InClass hackathons  (HAR, Durian, Hotel Review, ...)
├── mini_projects/      🧪 ทดลองเล็ก ๆ                    (Thai handwritten digits, ...)
├── common/             🧰 shared python package          (seed, paths, kaggle CLI, submission, sim harness)
├── templates/          📐 โครงโปรเจกต์ต้นแบบ             (tabular · simulation)
├── scripts/            ⚙️  new_project.py  — scaffold โปรเจกต์ใหม่
├── tests/              ✅ pytest
└── pyproject.toml      📦 uv project + ruff config
```

### โครงสร้างภายในแต่ละโปรเจกต์

```
<Group>/<Project>/
├── README.md           โจทย์ · approach · log ผลลัพธ์
├── config.yaml         paths / seed / CV / model params        (tabular)
├── main.py             agent ที่ submit                          (simulation)
├── src/                pipeline: data → features → train → predict
├── notebooks/          EDA / notebook เก่า
├── data/ models/ submissions/ episodes/        ← git-ignored ทั้งหมด
└── notes/              research & strategy notes
```

## 🚀 เริ่มต้นใช้งาน

```bash
# 1) ติดตั้ง environment (Python 3.12 + deps หลัก + kaggle-environments)
uv sync                         # เพิ่ม --group dl สำหรับ torch/timm/transformers, --group nb สำหรับ JupyterLab

# 2) Kaggle CLI (ครั้งเดียว)
uv run kaggle auth login        # หรือวาง token ไว้ที่ ~/.kaggle/access_token

# 3) เริ่มโปรเจกต์ใหม่จาก template
uv run python scripts/new_project.py Spaceship_Titanic --slug spaceship-titanic              # tabular
uv run python scripts/new_project.py Kaggriculture --slug kaggriculture \
    --template simulation --env kaggriculture                                                  # simulation

# 4) รัน pipeline ของโปรเจกต์ (tabular)
cd Kaggles/<Project> && uv run python -m src.train && uv run python -m src.predict

# lint / test
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

## 📁 โปรเจกต์ทั้งหมด

### 🚜 Kaggle Competitions — [`Kaggles/`](Kaggles/)

| Competition | Type | Approach | Status |
|---|---|---|---|
| [Kaggriculture](Kaggles/Kaggriculture/) | 🎮 Simulation — 2-player farming sim, shared market | Rule-based planner + greedy task scheduler (pure python) | 🔥 active |
| [Titanic](Kaggles/Titanic/) | Tabular · binary classification | AutoGluon | ✅ |
| [Spaceship Titanic](Kaggles/Spaceship_Titanic/) | Tabular · binary classification | AutoGluon | ✅ |

### 🏁 Hackathons — [`Hackathons/`](Hackathons/)

| Project | Event | Task · Approach | Result |
|---|---|---|---|
| [Pre_Human_Activity_Recognition](Hackathons/Pre_Human_Activity_Recognition/) | Mahidol × SuperAI (warm-up) | accelerometer → 6 activities · features + AutoGluon | 📈 |
| [Human_Activity_Recognition](Hackathons/Human_Activity_Recognition/) | Mahidol × SuperAI (on-site) | acc + gyro → 9 activities · features + AutoGluon | 🥇 ชนะเลิศ |
| [Durian_Hackathon](Hackathons/Durian_Hackathon/) | PSU Phuket | image classification ×3 · MaxViT / YOLOv11x-cls / CLIP | 🏅 อันดับ 5 (Private #3) |
| [Hotel_Review_Sentiment_Analysis](Hackathons/Hotel_Review_Sentiment_Analysis/) | — | review text → rating · LLM | 🚧 WIP |

### 🧪 Mini Projects — [`mini_projects/`](mini_projects/)

| Project | Task · Model |
|---|---|
| [thai_number_handwritten_classification](mini_projects/thai_number_handwritten_classification/) | ตัวเลขไทยเขียนมือ ๐–๙ · YOLO11x-cls |

## 🧭 Conventions

- **Python-first** — logic อยู่ใน `src/` (หรือ `main.py` สำหรับ simulation) รันด้วย `uv run`; notebook มีไว้ดูข้อมูลเท่านั้น
- **Data ไม่ขึ้น git** — `data/`, `models/`, `submissions/`, `episodes/` ถูก ignore ทั้ง repo (เก็บโครงด้วย `.gitkeep`)
- **ไม่มี secret ใน code** — ใช้ env var (`HF_TOKEN`, Kaggle token ใน `~/.kaggle/`) เท่านั้น
- **Lint/format** ด้วย Ruff (line length 100) · ทดสอบด้วย pytest · CI รันทุก push
- **ชื่อโฟลเดอร์โปรเจกต์** ใช้ `Title_Case_With_Underscores` ตามเดิม

## 🙏 Special Thanks

- Tan 👾 — <https://github.com/tara-tan>
- N'PP 🦆 — <https://github.com/Makufff>
- Gun 🐰 — <https://github.com/Rufflogix>

## 📄 License

[MIT](LICENSE) © 2024–2026 HexTex
