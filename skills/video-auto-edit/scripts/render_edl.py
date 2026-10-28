#!/usr/bin/env python3
"""Render EDL -> video: cắt, nối, fade audio, reframe tỉ lệ."""
import argparse, json, subprocess

ASPECTS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "16:9": (1920, 1080)}

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height", "-of", "json", path], capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    ha = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                         "stream=index", "-of", "csv=p=0", path], capture_output=True, text=True)
    return s["width"], s["height"], bool(ha.stdout.strip())

def reframe(aspect, crop_x, w, h):
    if aspect not in ASPECTS:
        return "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    W, H = ASPECTS[aspect]
    if crop_x == "blur":  # nền mờ, giữ nguyên khung gốc ở giữa
        return (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"boxblur=20:5[bg];[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2")
    # crop_x: "center" | số 0..1 (vị trí ngang của chủ thể)
    fx = 0.5 if crop_x in (None, "center") else float(crop_x)
    return (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H}:(iw-{W})*{fx}:(ih-{H})/2")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("--out", default="work/cut.mp4")
    ap.add_argument("--fps", default="30")
    a = ap.parse_args()
    e = json.load(open(a.edl, encoding="utf-8"))
    src, segs = e["source"], e["segments"]
    w, h, has_audio = probe(src)
    parts, labels = [], []
    for i, s in enumerate(segs):
        st, en = s["start"], s["end"]
        d = en - st
        parts.append(f"[0:v]trim={st}:{en},setpts=PTS-STARTPTS,fps={a.fps}[v{i}]")
        if has_audio:
            fo = max(0, d - 0.02)
            parts.append(f"[0:a]atrim={st}:{en},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d=0.02,afade=t=out:st={fo:.3f}:d=0.02[a{i}]")
            labels.append(f"[v{i}][a{i}]")
        else:
            labels.append(f"[v{i}]")
    n = len(segs)
    concat = "".join(labels) + f"concat=n={n}:v=1:a={1 if has_audio else 0}[vc]" + ("[ac]" if has_audio else "")
    parts.append(concat)
    parts.append(f"[vc]{reframe(e.get('aspect','source'), e.get('crop_x','center'), w, h)},setsar=1[vout]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex", ";".join(parts),
           "-map", "[vout]"] + (["-map", "[ac]", "-c:a", "aac", "-b:a", "192k"] if has_audio else []) + \
          ["-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    total = sum(s["end"] - s["start"] for s in segs)
    print(f"OK: {n} đoạn, {total:.1f}s -> {a.out}")

if __name__ == "__main__":
    main()
