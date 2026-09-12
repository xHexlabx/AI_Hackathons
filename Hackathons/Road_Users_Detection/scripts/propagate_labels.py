"""ลาก label จากเฟรมที่มี ไปยังเฟรมข้างเคียงที่ยังไม่มี ด้วย optical flow

    uv run python scripts/propagate_labels.py --max-gap 3

ทำไมถึงทำได้: ภาพเป็นเฟรมวิดีโอที่ห่างกันแค่ 1-4 เฟรม และ 89.4% ของเฟรมที่ยังไม่มี label
อยู่ห่างเฟรมที่มี label ไม่เกิน 10 เฟรม ระยะแค่นี้วัตถุแทบไม่ขยับ

ทำไมถึงคุ้ม: คลาสหายากกระจุกเป็นเหตุการณ์ เช่น emergency_car มีแค่ 10 เหตุการณ์ทั้ง dataset
แต่มีเฟรมข้างเคียงที่ยังไม่มี label อีก 49 เฟรม การลาก label จึงเพิ่มตัวอย่างคลาสหายากโดยตรง
ซึ่งเป็นสิ่งเดียวที่ mAP เฉลี่ยรายคลาสให้รางวัล

ผลลัพธ์เขียนแยกไว้ที่ datasets/pseudo/ ไม่แตะ ground truth เดิม
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "datasets" / "TrafficHackathon" / "train"
NAME = re.compile(r"^(?P<session>.+)_(?P<frame>\d+)$")

LK = dict(winSize=(21, 21), maxLevel=3, criteria=(3, 30, 0.01))  # 3 = COUNT|EPS
GRID = 5  # จุดที่สุ่มในกล่อง GRID x GRID
MIN_TRACKED = 4  # ต่ำกว่านี้ถือว่าติดตามไม่ได้ ทิ้งกล่องนั้น


def read_boxes(stem: str, w: int, h: int) -> list[tuple[int, np.ndarray]]:
    out = []
    for line in (SRC / f"{stem}.txt").read_text().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        cls, cx, cy, bw, bh = (float(v) for v in parts[:5])
        out.append(
            (
                int(cls),
                np.array(
                    [(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h]
                ),
            )
        )
    return out


def grid_points(box: np.ndarray) -> np.ndarray:
    xs = np.linspace(box[0], box[2], GRID + 2)[1:-1]
    ys = np.linspace(box[1], box[3], GRID + 2)[1:-1]
    return np.array([[x, y] for y in ys for x in xs], dtype=np.float32)


def shift_boxes(prev_gray, next_gray, boxes, shape):
    """ขยับกล่องตามการไหลของภาพ คืนเฉพาะกล่องที่ติดตามได้"""
    import cv2

    if not boxes:
        return []
    counts = [len(grid_points(b)) for _, b in boxes]
    pts = np.concatenate([grid_points(b) for _, b in boxes]).reshape(-1, 1, 2)
    nxt, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, next_gray, pts, None, **LK)
    status = status.reshape(-1).astype(bool)
    nxt = nxt.reshape(-1, 2)
    pts = pts.reshape(-1, 2)

    h, w = shape
    out, start = [], 0
    for (cls, box), n in zip(boxes, counts, strict=True):
        sl = slice(start, start + n)
        start += n
        ok = status[sl]
        if ok.sum() < MIN_TRACKED:
            continue
        before, after = pts[sl][ok], nxt[sl][ok]
        dx, dy = np.median(after - before, axis=0)
        # สเกลจากการกระจายตัวของจุด กันกรณีรถวิ่งเข้าหากล้อง
        spread_before = np.std(before, axis=0).mean()
        spread_after = np.std(after, axis=0).mean()
        scale = spread_after / spread_before if spread_before > 1e-3 else 1.0
        scale = float(np.clip(scale, 0.8, 1.25))
        cx, cy = (box[0] + box[2]) / 2 + dx, (box[1] + box[3]) / 2 + dy
        bw, bh = (box[2] - box[0]) * scale, (box[3] - box[1]) * scale
        new = np.array([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2])
        clipped = np.array([max(new[0], 0), max(new[1], 0), min(new[2], w), min(new[3], h)])
        if clipped[2] - clipped[0] < 2 or clipped[3] - clipped[1] < 2:
            continue
        area_new = (new[2] - new[0]) * (new[3] - new[1])
        area_clip = (clipped[2] - clipped[0]) * (clipped[3] - clipped[1])
        if area_clip < 0.5 * area_new:  # ออกนอกเฟรมไปเกินครึ่ง
            continue
        out.append((cls, clipped))
    return out


def run_session(frames, labelled, session, max_gap, out_dir, stats):
    import cv2

    best: dict[int, tuple[int, list]] = {}
    for direction in (1, -1):
        order = frames if direction == 1 else frames[::-1]
        carry, steps, prev_gray = None, 0, None
        for f in order:
            stem = f"{session}_{f}"
            img = cv2.imread(str(SRC / f"{stem}.jpg"), cv2.IMREAD_GRAYSCALE)
            if img is None:
                carry, prev_gray = None, None
                continue
            if stem in labelled:
                h, w = img.shape
                carry, steps = read_boxes(stem, w, h), 0
            elif carry is not None and steps < max_gap and prev_gray is not None:
                carry = shift_boxes(prev_gray, img, carry, img.shape)
                steps += 1
                if carry and (f not in best or steps < best[f][0]):
                    best[f] = (steps, [(c, b.copy()) for c, b in carry])
            else:
                carry, steps = None, 0
            prev_gray = img

    for f, (steps, boxes) in best.items():
        stem = f"{session}_{f}"
        h, w = 1080, 1920
        lines = []
        for cls, b in boxes:
            cx, cy = (b[0] + b[2]) / 2 / w, (b[1] + b[3]) / 2 / h
            bw, bh = (b[2] - b[0]) / w, (b[3] - b[1]) / h
            lines.append(f"{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
        (out_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        stats["frames"] += 1
        stats["boxes"] += len(boxes)
        stats["by_step"][steps] += 1
        for cls, _ in boxes:
            stats["by_class"][cls] += 1


def match(pred, truth, iou_thr=0.5):
    """จับคู่กล่องที่ลากมากับ ground truth แบบ greedy เทียบเฉพาะคลาสเดียวกัน"""
    used, hits, ious = set(), 0, []
    for cls_p, bp in pred:
        best, best_iou = None, iou_thr
        for j, (cls_t, bt) in enumerate(truth):
            if j in used or cls_t != cls_p:
                continue
            x1, y1 = max(bp[0], bt[0]), max(bp[1], bt[1])
            x2, y2 = min(bp[2], bt[2]), min(bp[3], bt[3])
            inter = max(x2 - x1, 0) * max(y2 - y1, 0)
            ap = (bp[2] - bp[0]) * (bp[3] - bp[1])
            at = (bt[2] - bt[0]) * (bt[3] - bt[1])
            iou = inter / max(ap + at - inter, 1e-9)
            if iou >= best_iou:
                best, best_iou = j, iou
        if best is not None:
            used.add(best)
            hits += 1
            ious.append(best_iou)
    return hits, ious


def validate(max_gap: int) -> None:
    """วัดคุณภาพ: แกล้งลบ label ของเฟรมที่มีอยู่แล้ว ลากมาจากเฟรมข้างเคียง แล้วเทียบกับของจริง"""
    import cv2

    labelled = {p.stem for p in SRC.glob("*.txt") if p.stem != "classes"}
    sessions = defaultdict(list)
    for stem in labelled:
        m = NAME.match(stem)
        if m:
            sessions[m["session"]].append(int(m["frame"]))

    per_gap = defaultdict(lambda: {"pred": 0, "truth": 0, "hit": 0, "iou": []})
    for session, frames in sorted(sessions.items()):
        frames = sorted(frames)
        for a, b in zip(frames, frames[1:], strict=False):
            gap = b - a
            if gap > max_gap:
                continue
            img_a = cv2.imread(str(SRC / f"{session}_{a}.jpg"), cv2.IMREAD_GRAYSCALE)
            img_b = cv2.imread(str(SRC / f"{session}_{b}.jpg"), cv2.IMREAD_GRAYSCALE)
            if img_a is None or img_b is None:
                continue
            h, w = img_a.shape
            moved = shift_boxes(img_a, img_b, read_boxes(f"{session}_{a}", w, h), img_a.shape)
            truth = read_boxes(f"{session}_{b}", w, h)
            hits, ious = match(moved, truth)
            d = per_gap[gap]
            d["pred"] += len(moved)
            d["truth"] += len(truth)
            d["hit"] += hits
            d["iou"].extend(ious)

    print("=" * 68)
    print("คุณภาพของ label ที่ลากมา (เทียบกับ ground truth ของเฟรมปลายทาง, IoU >= 0.5)")
    print(f"  {'ระยะ':<8}{'คู่กล่อง':>10}{'precision':>12}{'recall':>10}{'mean IoU':>11}")
    for gap in sorted(per_gap):
        d = per_gap[gap]
        prec = d["hit"] / d["pred"] if d["pred"] else 0
        rec = d["hit"] / d["truth"] if d["truth"] else 0
        miou = float(np.mean(d["iou"])) if d["iou"] else 0
        print(f"  {str(gap) + ' เฟรม':<8}{d['pred']:>10,}{prec:>11.1%}{rec:>10.1%}{miou:>11.3f}")
    print("=" * 68)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-gap", type=int, default=3, help="ลากได้ไกลสุดกี่เฟรมจากต้นทาง")
    ap.add_argument("--out", default="datasets/pseudo")
    ap.add_argument("--validate", action="store_true", help="วัดความแม่นแทนการเขียนไฟล์")
    args = ap.parse_args()

    if args.validate:
        validate(args.max_gap)
        return

    classes = [c.strip() for c in (SRC / "classes.txt").read_text().splitlines() if c.strip()]
    labelled = {p.stem for p in SRC.glob("*.txt") if p.stem != "classes"}
    sessions = defaultdict(list)
    for p in SRC.glob("*.jpg"):
        m = NAME.match(p.stem)
        if m:
            sessions[m["session"]].append(int(m["frame"]))

    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.txt"):
        old.unlink()

    stats = {"frames": 0, "boxes": 0, "by_step": defaultdict(int), "by_class": defaultdict(int)}
    for i, (session, frames) in enumerate(sorted(sessions.items()), 1):
        run_session(sorted(frames), labelled, session, args.max_gap, out_dir, stats)
        print(
            f"  [{i:>2}/{len(sessions)}] {session:<45} รวม {stats['frames']:>5,} เฟรม", flush=True
        )

    unlabelled = sum(len(v) for v in sessions.values()) - len(labelled)
    print("\n" + "=" * 68)
    print(
        f"ลาก label ได้ {stats['frames']:,} เฟรม จาก {unlabelled:,} เฟรมที่ยังไม่มี label"
        f" ({100 * stats['frames'] / unlabelled:.0f}%)"
    )
    print(f"กล่องที่ได้เพิ่ม {stats['boxes']:,}")
    print(
        "  แยกตามระยะที่ลาก : "
        + "  ".join(f"{k} เฟรม: {v:,}" for k, v in sorted(stats["by_step"].items()))
    )
    print("\n  กล่องที่ได้เพิ่มรายคลาส (เทียบกับของเดิม)")
    orig = defaultdict(int)
    for stem in labelled:
        for line in (SRC / f"{stem}.txt").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 5:
                orig[int(float(parts[0]))] += 1
    for cid, name in enumerate(classes):
        new = stats["by_class"].get(cid, 0)
        base = orig.get(cid, 0)
        gain = f"+{100 * new / base:.0f}%" if base else "-"
        print(f"    {name:<16}{base:>8,} -> {base + new:>8,}   {gain:>7}")
    print("=" * 68)


if __name__ == "__main__":
    main()
