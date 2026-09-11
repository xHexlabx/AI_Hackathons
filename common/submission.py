"""Submission file helpers for tabular competitions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def write_submission(
    df: pd.DataFrame,
    out_dir: Path,
    *,
    name: str = "submission",
    sample: pd.DataFrame | None = None,
    timestamp: bool = True,
) -> Path:
    """Write `df` to `out_dir/<name>[_YYYYmmdd-HHMM].csv`, validating against a sample."""
    if sample is not None:
        missing = set(sample.columns) - set(df.columns)
        if missing:
            raise ValueError(f"submission is missing columns: {sorted(missing)}")
        if len(df) != len(sample):
            raise ValueError(f"submission has {len(df)} rows, expected {len(sample)}")
        df = df[list(sample.columns)]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{name}_{datetime.now():%Y%m%d-%H%M}" if timestamp else name
    path = out_dir / f"{stem}.csv"
    df.to_csv(path, index=False)
    return path
