"""ตอบคำถามเดียว: การซอยภาพแบบ SAHI คุ้มไหมกับ dataset นี้ และควรใช้ tile ขนาดเท่าไร

    uv run python scripts/slice_check.py

เทียบ 3 ทาง: ย่อทั้งภาพเข้าโมเดล (baseline), ย่อทั้งภาพที่ความละเอียดสูง, และซอยเป็น tile
วัดสองอย่างที่ตัดสินใจได้จริง — วัตถุเหลือกี่พิกเซลหลังเข้าโมเดล และมีกี่กล่องที่ทุก tile ตัดขาด
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "datasets" / "TrafficHackathon" / "train"

# (ขนาด tile, overlap ratio)
SLICINGS = [(512, 0.2), (640, 0.2), (800, 0.2), (960, 0.25)]
# ความละเอียดที่ป้อนโมเดลแบบไม่ซอยภาพ
FULL_INPUTS = [640, 800, 1280]
# ต่ำกว่านี้ถือว่าโมเดลแทบมองไม่เห็น (stride 32 ของ backbone ทั่วไป)
TINY_PX = 16


def load_classes() -> list[str]:
    return [c.strip() for c in (TRAIN / "classes.txt").read_text().splitlines() if c.strip()]


def tiles(width: int, height: int, size: int, overlap: float) -> list[tuple[int, int, int, int]]:
    stride = int(size * (1 - overlap))
    out = []
    ys = list(range(0, max(height - size, 0) + 1, stride))
    xs = list(range(0, max(width - size, 0) + 1, stride))
    if ys[-1] + size < height:
        ys.append(height - size)
    if xs[-1] + size < width:
        xs.append(width - size)
    for y in ys:
        for x in xs:
            out.append((x, y, x + size, y + size))
    return out


def collect() -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """คืน (boxes_xyxy พิกเซล, class ids, ขนาดภาพที่พบบ่อยที่สุด)"""
    boxes, labels, sizes = [], [], Counter()
    for txt in sorted(TRAIN.glob("*.txt")):
        if txt.stem == "classes":
            continue
        img = TRAIN / f"{txt.stem}.jpg"
        if not img.exists():
            continue
        w, h = Image.open(img).size
        sizes[(w, h)] += 1
        for line in txt.read_text().splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            cls, cx, cy, bw, bh = (float(p) for p in parts[:5])
            boxes.append(
                [(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h]
            )
            labels.append(int(cls))
    return np.array(boxes), np.array(labels), sizes.most_common(1)[0][0]


def main() -> None:
    classes = load_classes()
    boxes, labels, (width, height) = collect()
    bw = boxes[:, 2] - boxes[:, 0]
    bh = boxes[:, 3] - boxes[:, 1]
    long_side = np.maximum(bw, bh)
    print("=" * 78)
    print(f"ภาพส่วนใหญ่ {width} x {height} · กล่องทั้งหมด {len(boxes):,}")
    q25, q50, q75 = np.percentile(long_side, [25, 50, 75])
    print(f"ด้านยาวของกล่อง (px): median {q50:.0f}  p25 {q25:.0f}  p75 {q75:.0f}")

    print(f"\n— ย่อทั้งภาพเข้าโมเดล: วัตถุเหลือกี่ px และกี่ % ที่เล็กกว่า {TINY_PX} px —")
    for inp in FULL_INPUTS:
        scale = inp / width
        scaled = long_side * scale
        tiny = 100 * (scaled < TINY_PX).mean()
        print(
            f"  input {inp:>4} px (scale {scale:.2f})  median {np.median(scaled):5.1f} px"
            f"   เล็กกว่า {TINY_PX} px: {tiny:5.1f}%"
        )

    print("\n— ซอยเป็น tile แล้วรันที่สเกลจริง (SAHI) —")
    for size, overlap in SLICINGS:
        grid = tiles(width, height, size, overlap)
        inside = np.zeros(len(boxes), dtype=bool)
        for x1, y1, x2, y2 in grid:
            inside |= (
                (boxes[:, 0] >= x1)
                & (boxes[:, 1] >= y1)
                & (boxes[:, 2] <= x2)
                & (boxes[:, 3] <= y2)
            )
        cut = 100 * (~inside).mean()
        tiny = 100 * (long_side < TINY_PX).mean()
        print(
            f"  tile {size:>3} overlap {overlap:.0%}  ->  {len(grid):>2} tiles/ภาพ"
            f"   กล่องที่ไม่มี tile ไหนครอบได้ทั้งใบ: {cut:5.2f}%"
            f"   เล็กกว่า {TINY_PX} px: {tiny:.1f}%"
        )

    size, overlap = 640, 0.2
    grid = tiles(width, height, size, overlap)
    inside = np.zeros(len(boxes), dtype=bool)
    for x1, y1, x2, y2 in grid:
        inside |= (
            (boxes[:, 0] >= x1) & (boxes[:, 1] >= y1) & (boxes[:, 2] <= x2) & (boxes[:, 3] <= y2)
        )

    print(f"\n— รายคลาส: ใครได้ประโยชน์จาก tile {size} px และใครโดนตัด —")
    print(f"  {'class':<15}{'n':>7}{'median px':>11}{'<16px @640':>12}{'tile ตัดขาด':>14}")
    for cid in range(len(classes)):
        m = labels == cid
        if not m.any():
            continue
        ls = long_side[m]
        tiny640 = 100 * ((ls * 640 / width) < TINY_PX).mean()
        print(
            f"  {classes[cid]:<15}{m.sum():>7,}{np.median(ls):>11.0f}"
            f"{tiny640:>11.1f}%{100 * (~inside[m]).mean():>13.1f}%"
        )
    print("=" * 78)


if __name__ == "__main__":
    main()
