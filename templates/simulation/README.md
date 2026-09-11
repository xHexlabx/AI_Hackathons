# {{TITLE}}

> Kaggle simulation competition: <https://www.kaggle.com/competitions/{{SLUG}}> · env `{{ENV}}` · เริ่ม {{DATE}}

## 🎯 Game

_(สรุปกติกา, observation / action format, เงื่อนไขชนะ)_

## 🗂️ Layout

```
{{NAME}}/
├── main.py            # agent ที่จะ submit (ฟังก์ชัน `agent` ต้องเป็น callable สุดท้ายของไฟล์)
├── agents/            # baseline / variants สำหรับเทียบ
├── sim/run.py         # เล่น N เกม  A vs B  แล้วสรุป win-rate
├── notes/             # research & strategy notes
├── episodes/          # replay json (git-ignored)
└── submissions/       # tar.gz ที่ submit (git-ignored)
```

## 🚀 Run

```bash
cd {{GROUP}}/{{NAME}}
uv run python sim/run.py main.py random -n 4          # local matches
uv run kaggle competitions submit -c {{SLUG}} -f main.py -m "v1"
```
