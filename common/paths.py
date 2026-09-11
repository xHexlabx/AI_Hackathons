"""Resolve the standard folder layout of a competition project.

Every project (Kaggles/<Name>, Hackathons/<Name>, mini_projects/<Name>) follows:

    <project>/
      data/raw/         # downloaded competition files   (git-ignored)
      data/processed/   # cached features / folds        (git-ignored)
      models/           # trained weights                 (git-ignored)
      submissions/      # submission csv / tar.gz         (git-ignored)
      notebooks/        # EDA only
      src/              # the actual pipeline
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_MARKERS = ("config.yaml", "main.py", "README.md")


def find_project_root(start: Path | str | None = None) -> Path:
    """Walk upwards from `start` (default: cwd) until a project marker is found."""
    p = Path(start or Path.cwd()).resolve()
    for candidate in (p, *p.parents):
        if (candidate / "pyproject.toml").exists() and candidate.name == "AI_Hackathons":
            break  # reached the repo root without finding a project - stop here
        if any((candidate / m).exists() for m in _MARKERS) and (candidate / "src").exists():
            return candidate
        if (candidate / "main.py").exists():
            return candidate
    return p


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @classmethod
    def discover(cls, start: Path | str | None = None) -> ProjectPaths:
        return cls(find_project_root(start))

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def raw(self) -> Path:
        return self.data / "raw"

    @property
    def processed(self) -> Path:
        return self.data / "processed"

    @property
    def models(self) -> Path:
        return self.root / "models"

    @property
    def submissions(self) -> Path:
        return self.root / "submissions"

    def ensure(self) -> ProjectPaths:
        for d in (self.raw, self.processed, self.models, self.submissions):
            d.mkdir(parents=True, exist_ok=True)
        return self
