#!/usr/bin/env python3
"""Lập chỉ mục thư mục footage: metadata, độ sáng, độ nét, độ rung, contact sheet để Claude xem.
Ra: work/index.json + work/sheets/sheet_XX.jpg (mỗi sheet 8 clip, mỗi clip 1 hàng 4 frame, có số thứ tự)."""
import argparse, json, os, re, subprocess, statistics as st
from concurrent.futures import ThreadPoolExecutor

EXT = (".mp4", ".mov", ".mkv", ".m4v", ".avi", ".mts", ".insv")

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration:format_tags=creation_time:stream=codec_type,width,height,r_frame_rate:stream_tags=rotate,creation_time",
        "-show_entries", "stream_side_data=rotation", "-of", "json", p], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    rot = abs(int(float(v.get("tags", {}).get("rotate", 0) or 0)))
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd: rot = abs(int(sd["rotation"]))
    w, h = v.get("width", 0), v.get("height", 0)
    if rot in (90, 270): w, h = h, w
    ct = j.get("format", {}).get("tags", {}).get("creation_time") or v.get("tags", {}).get("creation_time", "")
    return {"duration": float(j.get("format", {}).get("duration", 0) or 0), "width": w, "height": h,
            "has_audio": any(s.get("codec_type") == "audio" for s in j.get("streams", [])),
            "created": ct}

def analyze(p, dur):
    """fps thấp, ảnh nhỏ: YAVG = sáng, YDIF = chuyển động/rung, blur = độ mờ."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-an", "-vf",
        "fps=3,scale=320:-2,signalstats,blurdetect,metadata=print:file=-", "-f", "null", "-"],
        capture_output=True, text=True)
    y, d, b = [], [], []
    for line in r.stdout.splitlines():
        m = re.search(r"lavfi\.(signalstats\.YAVG|signalstats\.YDIF|blur)=([\d.]+)", line)
        if m:
            k, val = m.group(1), float(m.group(2))
            (y if k.endswith("YAVG") else d if k.endswith("YDIF") else b).append(val)
    f = lambda a: round(st.median(a), 2) if a else 0
    return {"brightness": f(y), "motion": f(d), "motion_peak": round(max(d), 1) if d else 0, "blur": f(b)}

def loud(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"mean_volume: (-?[\d.]+)", r.stderr)
    return float(m.group(1)) if m else -99

def score(c):
    s = 50
    if c["duration"] < 1.5: s -= 40
    if c["brightness"] < 40: s -= 20          # quá tối
    if c["brightness"] > 220: s -= 15         # cháy sáng
    if c["blur"] > 8: s -= 20                 # mờ
    if c["motion"] > 25: s -= 15              # rung/lia nhanh
    if 3 < c["motion"] < 15: s += 10          # có chuyển động vừa phải = sống động
    if c["has_audio"] and c["audio_db"] > -30: s += 5   # có tiếng nói/cười
    return max(0, min(100, s))

def frames(p, dur, out, n=4):
    os.makedirs(out, exist_ok=True)
    paths = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        fp = f"{out}/{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1",
                        "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2", fp])
        paths.append(fp)
    return paths

def sheets(clips, work, per=8):
    from PIL import Image, ImageDraw, ImageFont
    try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except Exception:
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        except Exception: font = ImageFont.load_default()
    os.makedirs(f"{work}/sheets", exist_ok=True)
    out = []
    for k in range(0, len(clips), per):
        grp = clips[k:k + per]
        W, rowh = 90 + 4 * 324, 184
        img = Image.new("RGB", (W, rowh * len(grp)), (11, 31, 58))
        dr = ImageDraw.Draw(img)
        for r, c in enumerate(grp):
            dr.text((8, r * rowh + 70), f"#{c['id']}", fill=(245, 197, 66), font=font)
            dr.text((8, r * rowh + 100), f"{c['duration']:.0f}s", fill=(255, 255, 255), font=font)
            for i, fp in enumerate(c["_frames"]):
                if os.path.exists(fp):
                    img.paste(Image.open(fp), (90 + i * 324, r * rowh + 2))
        p = f"{work}/sheets/sheet_{k // per + 1:02d}.jpg"
        img.save(p, quality=80); out.append(p)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--work", default="work")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    files = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(a.folder) for f in fs if f.lower().endswith(EXT))
    def one(p):
        c = {"file": os.path.abspath(p), "name": os.path.basename(p), **probe(p)}
        if c["duration"] <= 0: return None
        c.update(analyze(p, c["duration"]))
        c["audio_db"] = loud(p) if c["has_audio"] else -99
        c["score"] = score(c)
        return c
    with ThreadPoolExecutor(a.jobs) as ex:
        clips = [c for c in ex.map(one, files) if c]
    clips.sort(key=lambda c: (c["created"] or "9999", c["name"]))  # theo thời gian quay
    for i, c in enumerate(clips, 1):
        c["id"] = i
        c["_frames"] = frames(c["file"], c["duration"], f"{a.work}/frames/{i:03d}")
    sh = sheets(clips, a.work)
    for c in clips: c.pop("_frames")
    json.dump({"clips": clips, "sheets": sh}, open(f"{a.work}/index.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    tot = sum(c["duration"] for c in clips)
    print(f"OK: {len(clips)} clip, tổng {tot/60:.1f} phút, {len(sh)} contact sheet -> {a.work}/index.json")
    bad = [c["id"] for c in clips if c["score"] < 35]
    if bad: print(f"Clip điểm thấp (tối/mờ/rung/quá ngắn): {bad}")

if __name__ == "__main__":
    main()
