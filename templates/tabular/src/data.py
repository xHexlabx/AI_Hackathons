"""Load raw competition files (downloads them on first use)."""

from __future__ import annotations

import pandas as pd

from common.kaggle import download_competition

from .config import Config


def load_raw(cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = download_competition(cfg.competition, cfg.paths.raw)
    train = pd.read_csv(raw / "train.csv")
    test = pd.read_csv(raw / "test.csv")
    sample = pd.read_csv(raw / "sample_submission.csv")
    return train, test, sample
