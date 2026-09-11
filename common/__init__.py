"""Shared helpers for every competition in this repo.

Keep this small and dependency-light: seeding, paths, Kaggle CLI wrappers,
submission writing and a tiny harness for kaggle-environments simulations.
"""

from common.paths import ProjectPaths, find_project_root
from common.seed import seed_everything

__all__ = ["ProjectPaths", "find_project_root", "seed_everything"]
