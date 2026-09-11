# 🚜 Kaggle Competitions

| Competition | Type | Approach | Status |
|---|---|---|---|
| [Kaggriculture](Kaggriculture/) | 🎮 Simulation (2-player farming sim, shared market) | Rule-based planner + greedy scheduler (python) | 🔥 active — deadline Sep 2026 |
| [Titanic](Titanic/) | Tabular · binary classification | AutoGluon | ✅ |
| [Spaceship_Titanic](Spaceship_Titanic/) | Tabular · binary classification | AutoGluon | ✅ |

เริ่มงานใหม่:

```bash
uv run python scripts/new_project.py <Name> --slug <kaggle-slug>                       # tabular
uv run python scripts/new_project.py <Name> --slug <slug> --template simulation --env <env>
```
