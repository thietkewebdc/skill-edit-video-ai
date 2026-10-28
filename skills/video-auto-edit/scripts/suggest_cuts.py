#!/usr/bin/env python3
"""Tự tạo EDL jump-cut: bỏ khoảng lặng dài và từ đệm."""
import argparse, json, re

FILLERS = {"ờ", "ừ", "ừm", "ưm", "à", "ạ", "ơ", "uh", "um", "uhm", "hmm", "ầy", "ờm"}

def clean(w):
    return re.sub(r"[^\wÀ-ỹ]", "", w.lower())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("--source", default=None, help="Mặc định lấy từ tên transcript không có")
    ap.add_argument("--max-gap", type=float, default=0.45)
    ap.add_argument("--pad", type=float, default=0.08)
    ap.add_argument("--min-seg", type=float, default=0.4)
    ap.add_argument("--aspect", default="source")
    ap.add_argument("--out", default="work/edl.json")
    a = ap.parse_args()
    t = json.load(open(a.transcript, encoding="utf-8"))
    words = [w for s in t["segments"] for w in s["words"] if clean(w["w"]) not in FILLERS]
    segs = []
    for w in words:
        if segs and w["start"] - segs[-1]["end"] <= a.max_gap:
            segs[-1]["end"] = w["end"]
        else:
            segs.append({"start": w["start"], "end": w["end"]})
    dur = t.get("duration", 1e9)
    out = []
    for s in segs:
        st, en = max(0, s["start"] - a.pad), min(dur, s["end"] + a.pad)
        if en - st < a.min_seg:
            continue
        if out and st <= out[-1]["end"]:
            out[-1]["end"] = round(en, 3)
        else:
            out.append({"start": round(st, 3), "end": round(en, 3)})
    kept = sum(s["end"] - s["start"] for s in out)
    edl = {"source": a.source or "INPUT.mp4", "aspect": a.aspect, "crop_x": "center", "segments": out}
    json.dump(edl, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK: {len(out)} đoạn, giữ {kept:.1f}s / {dur:.1f}s ({100*kept/max(dur,1):.0f}%) -> {a.out}")
    if edl["source"] == "INPUT.mp4":
        print("LƯU Ý: sửa trường 'source' trong EDL thành đường dẫn video gốc (hoặc dùng --source).")

if __name__ == "__main__":
    main()
