"""ชื่อไฟล์บอกว่าภาพมาจากวิดีโอ — ตรวจว่าเฟรมต่อเนื่องกันแค่ไหน และ train/test มาจากคลิปเดียวกันไหม

    uv run python scripts/sequence_check.py

รูปแบบชื่อ: <กล้อง/เซสชัน>_<เลขเฟรม>.jpg  เช่น TF4-DS-09-01-28032023_630.jpg
คำถามที่ต้องตอบ:
  1. เฟรมถูกสุ่มมาทุก ๆ กี่เฟรม
  2. train กับ test ใช้เซสชันเดียวกันหรือไม่ — ถ้าใช่ การสุ่มแบ่ง validation จะรั่วหนัก
  3. เฟรม test แทรกอยู่ระหว่างเฟรม train ห่างแค่ไหน
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "datasets" / "TrafficHackathon" / "train"
TEST = ROOT / "datasets" / "TrafficHackathon" / "test"

NAME = re.compile(r"^(?P<session>.+)_(?P<frame>\d+)$")


def parse(folder: Path) -> dict[str, list[int]]:
    out: dict[str, list[int]] = defaultdict(list)
    for p in folder.glob("*.jpg"):
        m = NAME.match(p.stem)
        if m:
            out[m["session"]].append(int(m["frame"]))
    return {k: sorted(v) for k, v in out.items()}


def strides(seqs: dict[str, list[int]]) -> Counter:
    c: Counter = Counter()
    for frames in seqs.values():
        c.update(np.diff(frames).tolist())
    return c


def main() -> None:
    train, test = parse(TRAIN), parse(TEST)
    labelled = {p.stem for p in TRAIN.glob("*.txt") if p.stem != "classes"}

    print("=" * 78)
    print(f"train : {sum(len(v) for v in train.values()):,} ภาพ จาก {len(train)} เซสชัน")
    print(f"test  : {sum(len(v) for v in test.values()):,} ภาพ จาก {len(test)} เซสชัน")

    print("\n— ระยะห่างระหว่างเฟรมที่ติดกัน (บอกว่าสุ่มมาทุกกี่เฟรม) —")
    for name, seqs in (("train", train), ("test", test)):
        top = strides(seqs).most_common(4)
        print(f"  {name:<6} {', '.join(f'ห่าง {d} เฟรม x{n:,}' for d, n in top)}")

    shared = sorted(set(train) & set(test))
    print(
        f"\n— เซสชันที่ใช้ร่วมกันระหว่าง train กับ test: {len(shared)} จาก {len(set(train) | set(test))} —"
    )
    if shared:
        tr_in = sum(len(train[s]) for s in shared)
        te_in = sum(len(test[s]) for s in shared)
        print(f"  ภาพ train ที่อยู่ในเซสชันร่วม : {tr_in:,}")
        print(f"  ภาพ test ที่อยู่ในเซสชันร่วม  : {te_in:,}")

        gaps = []
        gaps_lab = []
        for s in shared:
            tr = np.array(train[s])
            lab = np.array([f for f in train[s] if f"{s}_{f}" in labelled])
            for f in test[s]:
                gaps.append(int(np.min(np.abs(tr - f))))
                if len(lab):
                    gaps_lab.append(int(np.min(np.abs(lab - f))))
        g = np.array(gaps)
        print("\n— ระยะจากเฟรม test ไปเฟรม train ที่ใกล้ที่สุด (หน่วย: เฟรมของวิดีโอ) —")
        p10, p50, p90 = np.percentile(g, [10, 50, 90])
        print(f"  median {p50:.0f}   p10 {p10:.0f}   p90 {p90:.0f}")
        for k in (5, 10, 25):
            print(f"  test ที่มีเฟรม train ห่างไม่เกิน {k:>2} เฟรม : {100 * (g <= k).mean():5.1f}%")
        if gaps_lab:
            gl = np.array(gaps_lab)
            print(
                f"  เทียบเฉพาะเฟรม train ที่ *มี label* : median {np.median(gl):.0f}"
                f" · ห่างไม่เกิน 25 เฟรม {100 * (gl <= 25).mean():.1f}%"
            )

    print("\n— label กระจายตัวยังไงในแต่ละเซสชัน —")
    lab_sessions = Counter()
    for stem in labelled:
        m = NAME.match(stem)
        if m:
            lab_sessions[m["session"]] += 1
    covered = [s for s in train if lab_sessions.get(s)]
    print(f"  เซสชันที่มี label อย่างน้อย 1 เฟรม : {len(covered)} จาก {len(train)}")
    ratios = [lab_sessions.get(s, 0) / len(train[s]) for s in train]
    print(
        f"  สัดส่วนเฟรมที่มี label ต่อเซสชัน : median {100 * np.median(ratios):.0f}%"
        f"  min {100 * min(ratios):.0f}%  max {100 * max(ratios):.0f}%"
    )
    print("\n  5 เซสชันที่ label เยอะสุด")
    for s, n in lab_sessions.most_common(5):
        print(f"    {s:<45} {n:>4} / {len(train.get(s, [])):>4} เฟรม")
    print("\n— เฟรม train ที่ยังไม่มี label อยู่ห่างเฟรมที่มี label ใกล้สุดเท่าไร —")
    print("  (ยิ่งใกล้ ยิ่ง propagate label ด้วย tracking ได้แม่น)")
    near = []
    for session, frames in train.items():
        lab = np.array([f for f in frames if f"{session}_{f}" in labelled])
        if not len(lab):
            continue
        for f in frames:
            if f"{session}_{f}" not in labelled:
                near.append(int(np.min(np.abs(lab - f))))
    n = np.array(near)
    print(f"  เฟรมที่ยังไม่มี label : {len(n):,}")
    for k in (1, 2, 3, 5, 10):
        print(f"    ห่างเฟรมที่มี label ไม่เกิน {k:>2} เฟรม : {100 * (n <= k).mean():5.1f}%")
    print("=" * 78)


if __name__ == "__main__":
    main()
