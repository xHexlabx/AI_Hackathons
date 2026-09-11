"""Feature engineering. Keep it pure: DataFrame in, DataFrame out."""

from __future__ import annotations

import pandas as pd

from .config import Config


def build_features(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = df.drop(columns=[c for c in (cfg.target, cfg.id_col) if c in df.columns])
    for col in out.select_dtypes(include=["object", "category"]).columns:
        out[col] = out[col].astype("category").cat.codes
    return out
