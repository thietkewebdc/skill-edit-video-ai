#!/usr/bin/env python3
"""Tạo plan montage tự động từ index.json + beats.json (+ tags.json do Claude gắn).
Claude nên xem lại và chỉnh plan.json trước khi render."""
import argparse, json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="work/index.json")
    ap.add_argument("--beats", default="work/beats.json")
    ap.add_argument("--tags", default=None, help="work/tags.json: {id: {day, place, tag, keep, best, hero}}")
    ap.add_argument("--target", type=float, default=60, help="Thời lượng mục tiêu (giây)")
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--grade", default="warm")
    ap.add_argument("--min-score", type=int, default=35)
    ap.add_argument("--music-start", type=float, default=0)
    ap.add_argument("--day-titles", action="store_true")
    ap.add_argument("--out", default="work/plan.json")
    a = ap.parse_args()
    idx = json.load(open(a.index, encoding="utf-8"))
    bt = json.load(open(a.beats))
    tags = {int(k): v for k, v in json.load(open(a.tags, encoding="utf-8")).items()} if a.tags else {}
    clips = []
    for c in idx["clips"]:
        t = tags.get(c["id"], {})
        if t.get("keep") is False: continue
        if c["score"] < a.min_score and not t.get("keep") and not t.get("hero"): continue
        clips.append({**c, **{"tag": t}})
    beats = [b for b in bt["beats"] if b >= a.music_start]
    en = bt["energy"][len(bt["beats"]) - len(beats):]
    fast = bt["bpm"] > 140
    # Lên lịch độ dài shot theo năng lượng nhạc
    slots, k, t0 = [], 0, beats[0] if beats else 0
    while k < len(beats) - 1 and beats[k] - t0 < a.target:
        n = 2 if en[k] > 0.7 else 4
        if fast: n *= 2
        if k == 0: n = max(n, 4)                       # shot mở đầu dài hơn chút
        n = min(n, len(beats) - 1 - k)
        slots.append(n); k += n
    need = len(slots)
    # Chọn clip: hero trước, sau đó rải đều theo dòng thời gian, ưu tiên điểm cao
    hero = [c for c in clips if c["tag"].get("hero")]
    rest = [c for c in clips if not c["tag"].get("hero")]
    pick = list(hero)
    if len(rest) > need - len(hero) > 0:
        buckets = need - len(hero); size = len(rest) / buckets
        for b in range(buckets):
            grp = rest[int(b * size):int((b + 1) * size)] or rest[-1:]
            pick.append(max(grp, key=lambda c: c["score"]))
    else:
        pick += rest
    order = {c["id"]: i for i, c in enumerate(idx["clips"])}
    opener = hero[0] if hero else None
    body = sorted([c for c in pick if c is not opener], key=lambda c: order[c["id"]])
    seq = ([opener] if opener else []) + body
    pool = sorted(clips, key=lambda c: (-c["score"], -c["duration"]))
    r = 0
    while len(seq) < need and pool:   # thiếu clip: xoay vòng các clip tốt, lấy đoạn khác
        seq.append(pool[r % len(pool)]); r += 1
    shots, used, last_day = [], {}, None
    for n, c in zip(slots, seq):
        spb = 60 / bt["bpm"]
        length = n * spb
        best = c["tag"].get("best")
        u = used.get(c["id"], 0)
        start = best if best is not None and u == 0 else c["duration"] * (0.3 + 0.25 * u) - length / 2
        start = max(0.2, min(start, c["duration"] - length - 0.1))
        used[c["id"]] = u + 1
        s = {"clip": c["file"], "id": c["id"], "in": round(max(0, start), 2), "beats": n}
        if length > c["duration"] - 0.2:
            s["speed"] = round(max(0.5, (c["duration"] - 0.3) / length), 2)  # clip ngắn: slow-mo cho đủ
            s["in"] = 0.1
        day = c["tag"].get("day")
        if a.day_titles and day and day != last_day:
            s["title"] = f"NGÀY {day}" + (f" · {c['tag']['place'].upper()}" if c["tag"].get("place") else "")
            last_day = day
        if c["motion"] > 20: s["stabilize"] = True
        shots.append(s)
    plan = {"music": bt["music"], "beats": a.beats, "music_start": a.music_start, "aspect": a.aspect,
            "grade": a.grade, "fit": "crop", "orig_audio": 0.15, "fade_out": 1.5, "shots": shots}
    json.dump(plan, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dur = beats[min(sum(slots), len(beats) - 1)] - beats[0] if beats else 0
    print(f"OK: {len(shots)} shot, ~{dur:.0f}s, {bt['bpm']} BPM -> {a.out}")

if __name__ == "__main__":
    main()
