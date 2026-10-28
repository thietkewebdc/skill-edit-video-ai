#!/usr/bin/env python3
"""QA output: thời lượng, độ phân giải, audio, loudness, frame mẫu."""
import argparse, json, subprocess, os, re

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--expect-aspect", default=None)
    ap.add_argument("--frames", default="work/qa_frames")
    a = ap.parse_args()
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height", "-of", "json", a.video],
        capture_output=True, text=True).stdout)
    dur = float(p["format"]["duration"])
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    has_a = any(s["codec_type"] == "audio" for s in p["streams"])
    ok, notes = True, []
    print(f"Thời lượng: {dur:.1f}s | {v['width']}x{v['height']} | audio: {has_a}")
    if a.expect_aspect:
        x, y = map(int, a.expect_aspect.split(":"))
        if abs(v["width"] / v["height"] - x / y) > 0.01:
            ok = False; notes.append(f"Sai tỉ lệ, cần {a.expect_aspect}")
        if a.expect_aspect == "9:16" and dur > 60:
            notes.append("Short dài hơn 60s")
    if has_a:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-af",
                            "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
        m = re.search(r'"input_i"\s*:\s*"(-?[\d.]+|-inf)"', r.stderr)
        if m and m.group(1) != "-inf":
            li = float(m.group(1)); print(f"Loudness: {li:.1f} LUFS")
            if not -16 <= li <= -12: notes.append("Loudness ngoài khoảng -16..-12 LUFS")
    else:
        ok = False; notes.append("Không có audio")
    os.makedirs(a.frames, exist_ok=True)
    for i, f in enumerate([0.15, 0.5, 0.85]):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur*f:.2f}", "-i", a.video,
                        "-frames:v", "1", "-vf", "scale=540:-2", f"{a.frames}/frame{i+1}.jpg"])
    print(f"Frame mẫu: {a.frames}/frame1-3.jpg  -> hãy XEM để kiểm tra sub và crop")
    print("PASS" if ok and not notes else "CẦN XEM: " + "; ".join(notes))

if __name__ == "__main__":
    main()
