"""สร้างไฟล์ submission จากโมเดลที่เทรนแล้ว

    uv run python scripts/predict.py --weights runs/<name>/weights/best.pt

รูปแบบที่ผู้จัดต้องการ: 1 แถวต่อ 1 ภาพ คอลัมน์ id,boxes,labels,scores
โดย boxes เป็นพิกเซล [x1, y1, x2, y2] และปล่อยว่างได้ถ้าไม่เจออะไร

ใช้ conf ต่ำมากโดยตั้งใจ เพราะ mAP ให้รางวัลกับ recall ที่ precision ต่ำ
การตัดกล่องความมั่นใจน้อยทิ้งคือการโยนคะแนนทิ้งเปล่า ๆ
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "datasets" / "TrafficHackathon" / "test"
SAMPLE = ROOT / "datasets" / "sample_submission.csv"


def tiles(width: int, height: int, size: int, overlap: float):
    stride = max(int(size * (1 - overlap)), 1)
    xs = list(range(0, max(width - size, 0) + 1, stride))
    ys = list(range(0, max(height - size, 0) + 1, stride))
    if xs[-1] + size < width:
        xs.append(width - size)
    if ys[-1] + size < height:
        ys.append(height - size)
    return [(x, y) for y in ys for x in xs]


def nms(boxes: np.ndarray, scores: np.ndarray, labels: np.ndarray, iou_thr: float):
    """NMS แยกรายคลาส ใช้รวมกล่องซ้ำของวัตถุเดียวกันที่โผล่หลาย tile

    หมายเหตุ: ขั้นนี้คือจุดที่ SAHI ดึง NMS กลับเข้ามาในไปป์ไลน์ที่ตั้งใจให้ NMS-free
    แต่เป็น NMS ที่ทำงานกับกล่องซ้ำของวัตถุตัวเดียวกัน ไม่ใช่รถคนละคันที่บังกัน
    """
    keep = []
    for cls in np.unique(labels):
        idx = np.where(labels == cls)[0]
        order = idx[np.argsort(-scores[idx])]
        while len(order):
            i = order[0]
            keep.append(i)
            if len(order) == 1:
                break
            rest = order[1:]
            x1 = np.maximum(boxes[i, 0], boxes[rest, 0])
            y1 = np.maximum(boxes[i, 1], boxes[rest, 1])
            x2 = np.minimum(boxes[i, 2], boxes[rest, 2])
            y2 = np.minimum(boxes[i, 3], boxes[rest, 3])
            inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
            area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
            area_r = (boxes[rest, 2] - boxes[rest, 0]) * (boxes[rest, 3] - boxes[rest, 1])
            iou = inter / np.maximum(area_i + area_r - inter, 1e-9)
            order = rest[iou < iou_thr]
    return np.array(sorted(keep), dtype=int)


def detect_sliced(model, path: str, args):
    """รันทั้งบน tile และบนภาพเต็ม แล้วรวมผล — ของเล็กมาจาก tile ของใหญ่มาจากภาพเต็ม"""
    import cv2

    img = cv2.imread(path)
    h, w = img.shape[:2]
    crops, offsets = [], []
    for x, y in tiles(w, h, args.tile, args.overlap):
        crops.append(img[y : y + args.tile, x : x + args.tile])
        offsets.append((x, y))

    all_boxes, all_scores, all_labels = [], [], []
    for start in range(0, len(crops), 4):
        chunk = crops[start : start + 4]
        results = model.predict(
            chunk, imgsz=args.tile, conf=args.conf, max_det=args.max_det, verbose=False
        )
        for (ox, oy), res in zip(offsets[start : start + 4], results, strict=True):
            b = res.boxes
            if b is None or len(b) == 0:
                continue
            xyxy = b.xyxy.cpu().numpy() + np.array([ox, oy, ox, oy])
            all_boxes.append(xyxy)
            all_scores.append(b.conf.cpu().numpy())
            all_labels.append(b.cls.cpu().numpy())

    res = model.predict(
        [img], imgsz=args.imgsz, conf=args.conf, max_det=args.max_det, verbose=False
    )[0]
    if res.boxes is not None and len(res.boxes):
        all_boxes.append(res.boxes.xyxy.cpu().numpy())
        all_scores.append(res.boxes.conf.cpu().numpy())
        all_labels.append(res.boxes.cls.cpu().numpy())

    if not all_boxes:
        return np.zeros((0, 4)), np.zeros(0), np.zeros(0)
    boxes = np.concatenate(all_boxes)
    scores = np.concatenate(all_scores)
    labels = np.concatenate(all_labels)
    keep = nms(boxes, scores, labels, args.merge_iou)
    keep = keep[np.argsort(-scores[keep])][: args.max_det]
    return boxes[keep], scores[keep], labels[keep]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--imgsz", type=int, default=1280)
    ap.add_argument("--conf", type=float, default=0.001)
    ap.add_argument("--max-det", type=int, default=300)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--out", default=None)
    ap.add_argument("--sahi", action="store_true", help="ซอยภาพเป็น tile แล้วรวมกับผลจากภาพเต็ม")
    ap.add_argument(
        "--tile", type=int, default=960, help="ขนาด tile (960 = โดนตัดกล่องน้อยสุดจากที่วัดไว้)"
    )
    ap.add_argument("--overlap", type=float, default=0.25)
    ap.add_argument("--merge-iou", type=float, default=0.6, help="IoU ที่ถือว่าเป็นกล่องซ้ำข้าม tile")
    args = ap.parse_args()

    from ultralytics import RTDETR, YOLO

    weights = Path(args.weights)
    if not weights.is_absolute():
        weights = ROOT / weights
    loader = RTDETR if "rtdetr" in weights.name or "rtdetr" in str(weights) else YOLO
    model = loader(str(weights))

    ids = [r["id"] for r in csv.DictReader(SAMPLE.open(encoding="utf-8"))]
    paths = [str(TEST / i) for i in ids]
    missing = [i for i, p in zip(ids, paths, strict=True) if not Path(p).exists()]
    if missing:
        raise SystemExit(f"ไม่พบภาพ {len(missing)} ไฟล์ เช่น {missing[:3]}")

    tag = "_sahi" if args.sahi else ""
    default = ROOT / "submissions" / f"{weights.parent.parent.name}{tag}.csv"
    out = Path(args.out) if args.out else default
    out.parent.mkdir(parents=True, exist_ok=True)

    rows, n_boxes, n_empty = [], 0, 0
    step = 1 if args.sahi else args.batch
    for start in range(0, len(paths), step):
        chunk = paths[start : start + step]
        if args.sahi:
            xyxy, conf, cls = detect_sliced(model, chunk[0], args)
            detections = [(xyxy, conf, cls)]
        else:
            results = model.predict(
                chunk, imgsz=args.imgsz, conf=args.conf, max_det=args.max_det, verbose=False
            )
            detections = [
                (r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy(), r.boxes.cls.cpu().numpy())
                if r.boxes is not None and len(r.boxes)
                else (np.zeros((0, 4)), np.zeros(0), np.zeros(0))
                for r in results
            ]
        for image_id, (xyxy, conf, cls) in zip(ids[start : start + step], detections, strict=True):
            if len(xyxy) == 0:
                # sample_submission มีแถวว่างเป็นตัวอย่าง แต่ scorer จริงขึ้น ERROR ถ้าเจอแถวว่าง
                # (ทดสอบแล้ว 2026-09-13) จึงต้องมีอย่างน้อย 1 กล่องเสมอ ใส่กล่องจิ๋วความมั่นใจ 0
                rows.append(
                    {"id": image_id, "boxes": "[[0, 0, 1, 1]]", "labels": "[0]", "scores": "[0.0]"}
                )
                n_empty += 1
                continue
            boxes = [[int(round(v)) for v in row] for row in xyxy.tolist()]
            labels = [int(c) for c in cls.tolist()]
            scores = [float(v) for v in conf.tolist()]
            n_boxes += len(boxes)
            rows.append(
                {
                    "id": image_id,
                    "boxes": str(boxes),
                    "labels": str(labels),
                    "scores": str(scores),
                }
            )
        if start % (step * 40) == 0:
            print(f"  {start + len(chunk):>5,} / {len(paths):,}", flush=True)

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "boxes", "labels", "scores"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nเขียน {out}")
    print(f"  {len(rows):,} แถว · {n_boxes:,} กล่อง · เฉลี่ย {n_boxes / len(rows):.1f} กล่อง/ภาพ")
    print(f"  ภาพที่ไม่เจออะไรเลย {n_empty:,}")


if __name__ == "__main__":
    main()
