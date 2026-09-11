"""Thin wrappers around the Kaggle CLI (auth is handled by the CLI itself).

Set up once:  `uv run kaggle auth login`  (or put a token in ~/.kaggle/access_token)
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path


def _kaggle(*args: str) -> subprocess.CompletedProcess[str]:
    exe = shutil.which("kaggle")
    if exe is None:
        raise RuntimeError("kaggle CLI not found - run `uv sync` first")
    return subprocess.run([exe, *args], check=True, text=True, capture_output=True)


def download_competition(slug: str, dest: Path, *, unzip: bool = True) -> Path:
    """Download all competition files into `dest` (skips if already present)."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if any(dest.iterdir()):
        return dest
    _kaggle("competitions", "download", "-c", slug, "-p", str(dest))
    if unzip:
        for z in dest.glob("*.zip"):
            with zipfile.ZipFile(z) as zf:
                zf.extractall(dest)
            z.unlink()
    return dest


def submit(slug: str, file: Path, message: str) -> str:
    """Submit a file (csv, main.py or tar.gz) and return the CLI output."""
    return _kaggle("competitions", "submit", "-c", slug, "-f", str(file), "-m", message).stdout
