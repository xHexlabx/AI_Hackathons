"""เทรน detector สาย DETR (NMS-free) จาก COCO weights ด้วย ultralytics

    uv run python scripts/train.py --fold 4 --imgsz 1280 --epochs 60

ทำไมเป็น RT-DETR ไม่ใช่ YOLO: โจทย์มีรถบังกันจน NMS ตัดกล่องที่ถูกทิ้ง (4.3% ของกล่อง
ทับกล่องคลาสเดียวกันที่ IoU > 0.5) DETR ทำนายเป็นเซ็ตผ่าน bipartite matching จึงไม่ต้องมี NMS
ทำไม imgsz สูง: ที่ 640 วัตถุ 30.6% เหลือต่ำกว่า 16 px ที่ 1280 เหลือแค่ 6.4%
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fold", type=int, default=4)
    ap.add_argument("--data", default=None, help="พาธ data.yaml ถ้าไม่ใช่ของโฟลด์ปกติ")
    ap.add_argument("--model", default="rtdetr-l.pt", help="COCO-pretrained checkpoint")
    ap.add_argument("--imgsz", type=int, default=1280)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--name", default=None)
    ap.add_argument("--patience", type=int, default=20)
    args = ap.parse_args()

    from ultralytics import RTDETR, YOLO

    data = (
        Path(args.data)
        if args.data
        else ROOT / "datasets" / "yolo" / f"fold{args.fold}" / "data.yaml"
    )
    if not data.exists():
        raise SystemExit(f"ไม่พบ {data} — รัน scripts/prepare_yolo.py --fold {args.fold} ก่อน")

    loader = RTDETR if "rtdetr" in args.model else YOLO
    model = loader(args.model)
    name = args.name or f"{Path(args.model).stem}_f{args.fold}_{args.imgsz}"
    model.train(
        data=str(data),
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        project=str(ROOT / "runs"),
        name=name,
        patience=args.patience,
        amp=True,
        cache=False,
        workers=4,
        seed=42,
        # ภาพเป็นกล้องนิ่งจับถนน — พลิกซ้ายขวาได้ แต่ห้ามพลิกบนล่างหรือหมุนแรง
        fliplr=0.5,
        flipud=0.0,
        degrees=0.0,
        # default 0.5 ย่อภาพได้ถึงครึ่ง ซึ่งดันวัตถุที่เล็กอยู่แล้วให้ต่ำกว่าเกณฑ์ที่โมเดลมองเห็น
        scale=0.3,
        mosaic=1.0,
        close_mosaic=10,
        plots=True,
    )


if __name__ == "__main__":
    main()
