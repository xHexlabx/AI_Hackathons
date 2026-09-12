"""สำรวจ dataset ก่อนเลือกสถาปัตยกรรม — เน้นคำถามเดียว: กล่องซ้อนกันแค่ไหนจน NMS จะพัง?

uv run python scripts/eda.py
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "datasets" / "TrafficHackathon" / "train"
TEST = ROOT / "datasets" / "TrafficHackathon" / "test"


def load_classes() -> list[str]:
    return [c.strip() for c in (TRAIN / "classes.txt").read_text().splitlines() if c.strip()]


def read_label(path: Path) -> np.ndarray:
    """YOLO txt -> (n, 5) array of [cls, cx, cy, w, h] in normalised coords."""
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 5:
            rows.append([float(p) for p in parts[:5]])
    return np.array(rows, dtype=float).reshape(-1, 5)


def to_xyxy(boxes: np.ndarray) -> np.ndarray:
    cx, cy, w, h = boxes[:, 1], boxes[:, 2], boxes[:, 3], boxes[:, 4]
    return np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)


def pairwise_iou(boxes: np.ndarray) -> np.ndarray:
    if len(boxes) < 2:
        return np.zeros((len(boxes), len(boxes)))
    x1 = np.maximum(boxes[:, None, 0], boxes[None, :, 0])
    y1 = np.maximum(boxes[:, None, 1], boxes[None, :, 1])
    x2 = np.minimum(boxes[:, None, 2], boxes[None, :, 2])
    y2 = np.minimum(boxes[:, None, 3], boxes[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union = area[:, None] + area[None, :] - inter
    iou = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
    np.fill_diagonal(iou, 0.0)
    return iou


def pct(part: int, whole: int) -> str:
    return f"{part:,} ({100 * part / whole:.1f}%)" if whole else "0"


def main() -> None:
    classes = load_classes()
    images = sorted(TRAIN.glob("*.jpg"))
    labels = {p.stem for p in TRAIN.glob("*.txt") if p.stem != "classes"}
    test_images = sorted(TEST.glob("*.jpg"))

    print("=" * 70)
    print(f"classes ({len(classes)}): {', '.join(classes)}")
    print(f"train images : {len(images):,}")
    missing = pct(len(images) - len(labels), len(images))
    print(f"train labels : {len(labels):,}   -> ไม่มี label: {missing}")
    print(f"test images  : {len(test_images):,}")

    sizes = Counter(Image.open(p).size for p in images[:400])
    print(f"\nimage sizes (จาก 400 ภาพแรก): {sizes.most_common(5)}")

    per_image, cls_counter, areas, empty_labels = [], Counter(), [], 0
    max_ious, crowded_same, crowded_any, total_boxes = [], 0, 0, 0
    for p in images:
        if p.stem not in labels:
            continue
        arr = read_label(TRAIN / f"{p.stem}.txt")
        per_image.append(len(arr))
        if len(arr) == 0:
            empty_labels += 1
            continue
        cls_counter.update(int(c) for c in arr[:, 0])
        areas.extend((arr[:, 3] * arr[:, 4]).tolist())
        total_boxes += len(arr)
        xyxy = to_xyxy(arr)
        iou = pairwise_iou(xyxy)
        if len(arr) > 1:
            max_ious.append(float(iou.max()))
            same = arr[:, 0][:, None] == arr[:, 0][None, :]
            crowded_same += int(((iou > 0.5) & same).any(axis=1).sum())
            crowded_any += int((iou > 0.5).any(axis=1).sum())

    n = np.array(per_image)
    print(f"\nไฟล์ label ที่ว่างเปล่า (ไม่มีวัตถุ) : {empty_labels:,}")
    print(
        f"วัตถุต่อภาพ : mean {n.mean():.1f}  median {np.median(n):.0f}  "
        f"max {n.max()}  total {total_boxes:,}"
    )

    print("\nกระจายคลาส")
    for cid, count in cls_counter.most_common():
        name = classes[cid] if cid < len(classes) else f"?{cid}"
        print(f"  {cid:>2} {name:<15} {count:>7,}  ({100 * count / total_boxes:5.2f}%)")

    a = np.array(areas)
    print("\nขนาดกล่อง (สัดส่วนพื้นที่ภาพ)")
    for q in (50, 75, 90, 99):
        print(f"  p{q:<3} {np.percentile(a, q) * 100:8.4f}%")
    print(f"  วัตถุที่เล็กกว่า 0.1% ของภาพ : {pct(int((a < 0.001).sum()), len(a))}")

    m = np.array(max_ious)
    print("\nความซ้อนทับของกล่อง ground truth (ตัวชี้วัดว่า NMS จะพังไหม)")
    print(f"  ภาพที่มีคู่กล่อง IoU > 0.5 : {pct(int((m > 0.5).sum()), len(m))}")
    print(f"  ภาพที่มีคู่กล่อง IoU > 0.7 : {pct(int((m > 0.7).sum()), len(m))}")
    print(f"  กล่องที่ทับกล่องอื่น IoU>0.5 (คลาสใดก็ได้) : {pct(crowded_any, total_boxes)}")
    same = pct(crowded_same, total_boxes)
    print(f"  กล่องที่ทับกล่อง *คลาสเดียวกัน* IoU>0.5     : {same}  <- NMS ตัดทิ้งตรงนี้")
    print("=" * 70)


if __name__ == "__main__":
    main()
