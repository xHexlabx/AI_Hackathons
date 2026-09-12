"""จัดโครงโฟลเดอร์แบบที่ ultralytics ต้องการ จาก split ที่ make_split.py สร้างไว้

    uv run python scripts/prepare_yolo.py --fold 4

ultralytics หา label โดยแทน /images/ ด้วย /labels/ ในพาธของภาพ แต่ข้อมูลต้นทางวาง
.jpg กับ .txt ไว้โฟลเดอร์เดียวกัน จึงต้องกางโครงใหม่ ใช้ symlink ไม่ได้ก็อปไฟล์ 3.7 GB
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "datasets" / "TrafficHackathon" / "train"
SPLITS = ROOT / "splits"
PSEUDO = ROOT / "datasets" / "pseudo"
OUT = ROOT / "datasets" / "yolo"
NAME = re.compile(r"^(?P<session>.+)_(?P<frame>\d+)$")


def link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    dst.symlink_to(src)


def val_ranges(fold: int) -> dict[str, tuple[int, int]]:
    """ช่วงเฟรมของบล็อก val ในแต่ละเซสชัน ใช้กันไม่ให้ pseudo label รั่วเข้าไปฝั่ง val"""
    spans: dict[str, list[int]] = defaultdict(list)
    for stem in (SPLITS / f"fold{fold}_val.txt").read_text().split():
        m = NAME.match(stem)
        if m:
            spans[m["session"]].append(int(m["frame"]))
    return {k: (min(v), max(v)) for k, v in spans.items()}


def pseudo_stems(fold: int, buffer: int) -> list[str]:
    """เฟรมที่ลาก label มา เอาเฉพาะที่อยู่นอกบล็อก val ของโฟลด์นี้"""
    if not PSEUDO.is_dir():
        return []
    spans = val_ranges(fold)
    out = []
    for txt in sorted(PSEUDO.glob("*.txt")):
        m = NAME.match(txt.stem)
        if not m:
            continue
        span = spans.get(m["session"])
        frame = int(m["frame"])
        if span and span[0] - buffer <= frame <= span[1] + buffer:
            continue  # ติดกับบล็อก val เกินไป จะรั่ว
        if (SRC / f"{txt.stem}.jpg").exists():
            out.append(txt.stem)
    return out


def build(fold: int, with_pseudo: bool = False, buffer: int = 10) -> Path:
    classes = [c.strip() for c in (SRC / "classes.txt").read_text().splitlines() if c.strip()]
    base = OUT / (f"fold{fold}_pseudo" if with_pseudo else f"fold{fold}")
    counts = {}
    for part in ("train", "val"):
        stems = (SPLITS / f"fold{fold}_{part}.txt").read_text().split()
        for stem in stems:
            link(SRC / f"{stem}.jpg", base / "images" / part / f"{stem}.jpg")
            link(SRC / f"{stem}.txt", base / "labels" / part / f"{stem}.txt")
        counts[part] = len(stems)

    counts["pseudo"] = 0
    if with_pseudo:
        for stem in pseudo_stems(fold, buffer):
            link(SRC / f"{stem}.jpg", base / "images" / "train" / f"{stem}.jpg")
            link(PSEUDO / f"{stem}.txt", base / "labels" / "train" / f"{stem}.txt")
            counts["pseudo"] += 1

    names = "\n".join(f"  {i}: {n}" for i, n in enumerate(classes))
    (base / "data.yaml").write_text(
        f"# สร้างโดย scripts/prepare_yolo.py — fold {fold}\n"
        f"path: {base}\ntrain: images/train\nval: images/val\n\nnames:\n{names}\n",
        encoding="utf-8",
    )
    extra = f" (+{counts['pseudo']:,} pseudo)" if counts["pseudo"] else ""
    print(f"fold {fold}: train {counts['train']:,}{extra} · val {counts['val']:,} ภาพ")
    print(f"data.yaml -> {base / 'data.yaml'}")
    return base / "data.yaml"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fold", type=int, default=4, help="โฟลด์ที่จะกาง (4 = บล็อกท้าย ใกล้ test สุด)")
    ap.add_argument("--all", action="store_true", help="กางทุกโฟลด์")
    ap.add_argument("--with-pseudo", action="store_true", help="ใส่ label ที่ลากมาจากเฟรมข้างเคียงด้วย")
    ap.add_argument("--buffer", type=int, default=10, help="กัน pseudo ที่ติดบล็อก val กี่เฟรม")
    args = ap.parse_args()
    for fold in range(5) if args.all else [args.fold]:
        build(fold, with_pseudo=args.with_pseudo, buffer=args.buffer)


if __name__ == "__main__":
    main()
