"""K-fold training. Saves fold models to models/ and prints the OOF score.

uv run python -m src.train
"""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold

from common.seed import seed_everything

from .config import Config
from .data import load_raw
from .features import build_features

METRICS = {
    "auc": roc_auc_score,
    "accuracy": lambda y, p: accuracy_score(y, (p > 0.5).astype(int)),
    "rmse": lambda y, p: float(np.sqrt(mean_squared_error(y, p))),
    "mae": mean_absolute_error,
}


def make_model(cfg: Config):
    import lightgbm as lgb

    params = {"random_state": cfg.seed, **cfg.model.get("params", {})}
    return (
        lgb.LGBMClassifier(**params)
        if cfg.task == "classification"
        else lgb.LGBMRegressor(**params)
    )


def predict(model, x: pd.DataFrame, cfg: Config) -> np.ndarray:
    return model.predict_proba(x)[:, 1] if cfg.task == "classification" else model.predict(x)


def main() -> None:
    cfg = Config.load()
    seed_everything(cfg.seed)
    cfg.paths.ensure()
    train, _, _ = load_raw(cfg)
    x, y = build_features(train, cfg), train[cfg.target].to_numpy()

    splitter = (StratifiedKFold if cfg.task == "classification" else KFold)(
        cfg.n_folds, shuffle=True, random_state=cfg.seed
    )
    oof = np.zeros(len(x), dtype=float)
    for fold, (tr, va) in enumerate(splitter.split(x, y)):
        model = make_model(cfg)
        model.fit(x.iloc[tr], y[tr], eval_set=[(x.iloc[va], y[va])])
        oof[va] = predict(model, x.iloc[va], cfg)
        joblib.dump(model, cfg.paths.models / f"fold{fold}.joblib")
        print(f"fold {fold}: {cfg.metric}={METRICS[cfg.metric](y[va], oof[va]):.5f}")
    print(f"OOF {cfg.metric}={METRICS[cfg.metric](y, oof):.5f}")


if __name__ == "__main__":
    main()
