# {{TITLE}}

> Kaggle: <https://www.kaggle.com/competitions/{{SLUG}}> · เริ่ม {{DATE}}

## 🎯 Task

_(อธิบายโจทย์ / metric / submission format สั้น ๆ)_

## 🗂️ Layout

```
{{NAME}}/
├── config.yaml        # paths, seed, CV, model params
├── src/               # pipeline (python-first)
│   ├── data.py        # load raw files (auto-download ผ่าน kaggle CLI)
│   ├── features.py    # feature engineering
│   ├── train.py       # CV training  ->  models/ + OOF score
│   └── predict.py     # inference    ->  submissions/
├── notebooks/         # EDA เท่านั้น
├── data/raw|processed # git-ignored
├── models/            # git-ignored
└── submissions/       # git-ignored
```

## 🚀 Run

```bash
# จาก repo root (ครั้งเดียว): uv sync
cd {{GROUP}}/{{NAME}}
uv run python -m src.train              # CV + fit
uv run python -m src.predict            # เขียน submissions/submission_*.csv
uv run kaggle competitions submit -c {{SLUG}} -f submissions/<file>.csv -m "v1"
```

## 📓 Log

| Date | Version | CV | LB | Note |
|------|---------|----|----|------|
| {{DATE}} | v0 | - | - | scaffold |
