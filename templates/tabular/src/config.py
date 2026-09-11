"""Typed access to config.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from common.paths import ProjectPaths


@dataclass
class Config:
    competition: str
    seed: int = 42
    target: str = "target"
    id_col: str = "id"
    task: str = "classification"
    metric: str = "auc"
    n_folds: int = 5
    model: dict[str, Any] = field(default_factory=dict)
    paths: ProjectPaths = field(default_factory=ProjectPaths.discover)

    @classmethod
    def load(cls, path: Path | str | None = None) -> Config:
        paths = ProjectPaths.discover()
        cfg_path = Path(path) if path else paths.root / "config.yaml"
        raw = yaml.safe_load(cfg_path.read_text()) or {}
        return cls(paths=paths, **raw)
