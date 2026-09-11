"""Scaffold a new competition folder from templates/.

    uv run python scripts/new_project.py Titanic --slug titanic
    uv run python scripts/new_project.py Kaggriculture --slug kaggriculture \
        --template simulation --env kaggriculture
    uv run python scripts/new_project.py Some_Hackathon --group Hackathons --slug some-hack

Placeholders {{NAME}} {{TITLE}} {{SLUG}} {{GROUP}} {{DATE}} {{ENV}} are filled in text files.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".toml", ".txt", ".sh", ".json"}


def render(path: Path, mapping: dict[str, str]) -> None:
    if path.suffix not in TEXT_SUFFIXES:
        return
    text = path.read_text(encoding="utf-8")
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", value)
    path.write_text(text, encoding="utf-8")


def scaffold(
    name: str,
    *,
    group: str,
    template: str,
    slug: str,
    title: str | None = None,
    env: str = "",
    root: Path = REPO,
) -> Path:
    src = root / "templates" / template
    if not src.is_dir():
        raise SystemExit(
            f"unknown template: {template} (have: {[p.name for p in (root / 'templates').iterdir()]})"
        )
    dest = root / group / name
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    shutil.copytree(src, dest)
    mapping = {
        "NAME": name,
        "TITLE": title or name.replace("_", " "),
        "SLUG": slug,
        "GROUP": group,
        "DATE": date.today().isoformat(),
        "ENV": env or slug,
    }
    for p in dest.rglob("*"):
        if p.is_file():
            render(p, mapping)
    return dest


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("name", help="folder name, e.g. Spaceship_Titanic")
    ap.add_argument("--slug", required=True, help="kaggle competition slug (URL tail)")
    ap.add_argument(
        "--group", default="Kaggles", choices=["Kaggles", "Hackathons", "mini_projects"]
    )
    ap.add_argument("--template", default="tabular", help="folder under templates/")
    ap.add_argument("--title", default=None)
    ap.add_argument("--env", default="", help="kaggle-environments name (simulation template)")
    args = ap.parse_args()
    dest = scaffold(
        args.name,
        group=args.group,
        template=args.template,
        slug=args.slug,
        title=args.title,
        env=args.env,
    )
    print(f"created {dest.relative_to(REPO)}")
    print(f"next:   cd {dest.relative_to(REPO)} && $EDITOR README.md")


if __name__ == "__main__":
    main()
