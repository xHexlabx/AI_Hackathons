# Reference agents (third-party)

From the Kaggle dataset [raykkretzschmar/kaggriculture-reference-agents](https://www.kaggle.com/datasets/raykkretzschmar/kaggriculture-reference-agents)
by Rayk Kretzschmar. Code is MIT (see `LICENSE`, `NOTICE`); `broker_bea` and the other tier 6-9 agents replay a
base85-encoded "meta line" field plan reconstructed from public replays, which the author explicitly does not license.
We use these files **only as local sparring partners** (`sim/run.py`, `sim/sweep.py`); nothing from them is shipped in `main.py`.
