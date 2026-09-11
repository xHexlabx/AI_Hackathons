"""Average fold models on the test set and write a submission.

uv run python -m src.predict
"""

from __future__ import annotations

import joblib
import numpy as np

from common.submission import write_submission

from .config import Config
from .data import load_raw
from .features import build_features
from .train import predict


def main() -> None:
    cfg = Config.load()
    _, test, sample = load_raw(cfg)
    x = build_features(test, cfg)
    models = sorted(cfg.paths.models.glob("fold*.joblib"))
    if not models:
        raise SystemExit("no models found - run `python -m src.train` first")
    preds = np.mean([predict(joblib.load(m), x, cfg) for m in models], axis=0)
    sub = sample.copy()
    sub[sub.columns[-1]] = preds
    path = write_submission(sub, cfg.paths.submissions, sample=sample)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
