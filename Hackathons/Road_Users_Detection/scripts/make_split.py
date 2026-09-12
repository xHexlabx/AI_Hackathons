"""สร้าง time-block cross-validation ที่เลียนแบบวิธีที่ผู้จัดตัด test ออกมา

    uv run python scripts/make_split.py              # 5 folds
    uv run python scripts/make_split.py --folds 1    # split เดียว เอาบล็อกท้ายเป็น val

test คือ *ช่วงท้าย* ของแต่ละเซสชัน (19 จาก 24 เซสชันอยู่หลังเฟรม train ตัวสุดท้ายทั้งหมด)
จึงแบ่ง validation เป็นบล็อกเวลาต่อเนื่อง ไม่ใช่สุ่มรายภาพ เพราะเฟรมห่างกันแค่ 1-4 เฟรม
และไม่ใช่แบ่งตามกล้อง เพราะ test ใช้กล้องชุดเดียวกับ train ทั้ง 24 ตัว

ใช้หลายโฟลด์เพราะคลาสหายากกระจุกเป็นช่วง ๆ — `emergency_car` มีแค่ 10 เหตุการณ์ทั้ง dataset
ถ้าใช้ split เดียว คะแนนของคลาสพวกนี้จะขึ้นกับดวงว่าเหตุการณ์ตกไปฝั่งไหน
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "datasets" / "TrafficHackathon" / "train"
SPLITS = ROOT / "splits"
NAME = re.compile(r"^(?P<session>.+)_(?P<frame>\d+)$")


def labelled_frames() -> dict[str, list[int]]:
    out: dict[str, list[int]] = defaultdict(list)
    for txt in TRAIN.glob("*.txt"):
        if txt.stem == "classes":
            continue
        m = NAME.match(txt.stem)
        if m and (TRAIN / f"{txt.stem}.jpg").exists():
            out[m["session"]].append(int(m["frame"]))
    return {k: sorted(v) for k, v in out.items()}


def class_counts(stems: list[str]) -> Counter:
    c: Counter = Counter()
    for stem in stems:
        for line in (TRAIN / f"{stem}.txt").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 5:
                c[int(float(parts[0]))] += 1
    return c


def blocks(frames: list[int], n: int) -> list[list[int]]:
    """ซอยเฟรมที่เรียงแล้วออกเป็น n บล็อกต่อเนื่อง ขนาดใกล้เคียงกัน"""
    size, extra = divmod(len(frames), n)
    out, i = [], 0
    for k in range(n):
        take = size + (1 if k < extra else 0)
        out.append(frames[i : i + take])
        i += take
    return out


def build_fold(sessions: dict[str, list[int]], fold: int, n_folds: int, buffer: int):
    train_stems, val_stems, dropped = [], [], 0
    for session, frames in sorted(sessions.items()):
        parts = blocks(frames, n_folds)
        held = parts[fold]
        if not held:
            train_stems.extend(f"{session}_{f}" for f in frames)
            continue
        lo, hi = held[0], held[-1]
        val_stems.extend(f"{session}_{f}" for f in held)
        for f in frames:
            if lo <= f <= hi:
                continue
            if lo - buffer <= f <= hi + buffer:  # เฟรมติดขอบ เกือบเป็นภาพเดียวกับ val
                dropped += 1
                continue
            train_stems.append(f"{session}_{f}")
    return sorted(train_stems), sorted(val_stems), dropped


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--folds", type=int, default=5, help="จำนวนโฟลด์ (1 = split เดียว)")
    ap.add_argument("--buffer", type=int, default=10, help="เว้นกี่เฟรมรอบบล็อก val")
    args = ap.parse_args()

    classes = [c.strip() for c in (TRAIN / "classes.txt").read_text().splitlines() if c.strip()]
    sessions = labelled_frames()
    n_folds = max(args.folds, 1)
    SPLITS.mkdir(exist_ok=True)

    print("=" * 74)
    print(f"เซสชัน {len(sessions)} · เฟรมที่มี label {sum(len(v) for v in sessions.values()):,}")
    print(f"แบ่งเป็น {n_folds} บล็อกเวลาต่อเนื่องต่อเซสชัน · buffer {args.buffer} เฟรมรอบบล็อก val\n")

    ids = list(range(len(classes)))
    header = "".join(f"{classes[c][:9]:>10}" for c in ids)
    print(f"  {'fold':<6}{'train':>7}{'val':>6}{'drop':>6}   กล่องใน val ต่อคลาส")
    print(f"  {'':<6}{'':>7}{'':>6}{'':>6}   {header}")

    for k in range(n_folds):
        tr, va, dropped = build_fold(sessions, k, n_folds, args.buffer)
        (SPLITS / f"fold{k}_train.txt").write_text("\n".join(tr) + "\n", encoding="utf-8")
        (SPLITS / f"fold{k}_val.txt").write_text("\n".join(va) + "\n", encoding="utf-8")
        vc = class_counts(va)
        row = "".join(f"{vc.get(c, 0):>10,}" for c in ids)
        print(f"  {k:<6}{len(tr):>7,}{len(va):>6,}{dropped:>6}   {row}")

    print(f"\nเขียนไฟล์ลง {SPLITS.relative_to(ROOT)}/ แล้ว (fold<k>_train.txt · fold<k>_val.txt)")
    print("fold สุดท้ายคือบล็อกท้ายของทุกเซสชัน ใกล้เคียงกับวิธีที่ test ถูกตัดออกมามากที่สุด")
    print("\nคลาสที่ val บางโฟลด์มีไม่ถึง 10 กล่อง ให้ดูค่าเฉลี่ยข้ามโฟลด์เท่านั้น")
    print("อย่าตัดสินใจจากโฟลด์เดียว โดยเฉพาะ emergency_car ที่มีแค่ 10 เหตุการณ์ทั้ง dataset")
    print("=" * 74)


if __name__ == "__main__":
    main()
