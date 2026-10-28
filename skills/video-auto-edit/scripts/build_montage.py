#!/usr/bin/env python3
"""Render plan.json -> montage cắt đúng beat, chỉnh màu, chống rung, tiêu đề, nhạc nền."""
import argparse, json, os, subprocess, tempfile

ASPECTS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "16:9": (1920, 1080)}
GRADES = {
    "none": "null",
    "warm": "eq=contrast=1.06:saturation=1.18:gamma=0.98,colorbalance=rs=0.05:bs=-0.05:rm=0.04:bm=-0.04:rh=0.03:bh=-0.03",
    "teal_orange": "eq=contrast=1.08:saturation=1.12,colorbalance=rs=-0.06:bs=0.08:rh=0.08:bh=-0.08",
    "film": "eq=contrast=1.04:saturation=0.9:gamma=1.02,colorbalance=bs=0.04:rh=0.03,noise=alls=6:allf=t",
    "vivid": "eq=contrast=1.1:saturation=1.35",
}

def has_audio(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return bool(r.stdout.strip())

def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

def vf_frame(W, H, fit, crop_x):
    if fit == "blur":
        return (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:6[bg];"
                f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")
    fx = 0.5 if crop_x in (None, "center") else float(crop_x)
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:(iw-{W})*{fx}:(ih-{H})/2"

def ts(t):
    return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--out", required=True)
    ap.add_argument("--font", default="Be Vietnam Pro")
    ap.add_argument("--preview", action="store_true", help="Render nhanh 540p để duyệt")
    a = ap.parse_args()
    P = json.load(open(a.plan, encoding="utf-8"))
    bt = json.load(open(P["beats"]))
    W, H = ASPECTS.get(P.get("aspect", "9:16"), (1080, 1920))
    if a.preview: W, H = W // 2, H // 2
    beats = [b for b in bt["beats"] if b >= P.get("music_start", 0)]
    grade = P.get("grade", "warm")
    gf = GRADES.get(grade) or (f"lut3d='{os.path.abspath(grade)}'" if os.path.exists(grade) else "null")
    tmp = tempfile.mkdtemp(prefix="montage_")
    parts, events, k, t_out = [], [], 0, 0.0
    preset = ["-preset", "veryfast", "-crf", "26"] if a.preview else ["-preset", "medium", "-crf", "19"]
    for i, s in enumerate(P["shots"]):
        n = s.get("beats", 4)
        if k + n >= len(beats): print(f"Hết nhạc ở shot {i}, dừng."); break
        L = beats[k + n] - beats[k]; k += n
        sp = float(s.get("speed", 1.0))
        src_len = L * sp
        cd = dur(s["clip"])
        start = max(0, min(float(s.get("in", 0)), cd - src_len - 0.05))
        vf = []
        if s.get("stabilize"): vf.append("deshake=rx=32:ry=32")
        vf.append(vf_frame(W, H, s.get("fit", P.get("fit", "crop")), s.get("crop_x")))
        vf.append(gf)
        if sp != 1: vf.append(f"setpts=PTS/{sp}")
        if s.get("zoom"):   # zoom chậm nhẹ tạo cảm giác điện ảnh
            vf.append(f"scale=iw*1.08:ih*1.08,crop={W}:{H}:(iw-{W})/2+(iw-{W})/2*sin(t/{max(L,1)}):(ih-{H})/2")
        vf += ["fps=30", "setsar=1", "format=yuv420p"]
        out = f"{tmp}/s{i:03d}.mp4"
        ha = has_audio(s["clip"])
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{src_len + 0.1:.3f}", "-i", s["clip"]]
        if not ha: cmd += ["-f", "lavfi", "-t", f"{L:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        af = "aresample=48000,aformat=channel_layouts=stereo"
        if sp != 1: af += f",atempo={min(2, max(0.5, sp))}"
        cmd += ["-filter_complex", f"[0:v]{','.join(vf)}[v];[{0 if ha else 1}:a]{af}[a]",
                "-map", "[v]", "-map", "[a]", "-t", f"{L:.3f}", "-c:v", "libx264", *preset,
                "-c:a", "aac", "-b:a", "192k", out]
        subprocess.run(cmd, check=True)
        if s.get("title"):
            events.append((t_out + 0.1, t_out + min(L, 2.8) - 0.05, s["title"]))
        t_out += L
        parts.append(out)
        print(f"  shot {i+1}/{len(P['shots'])}: #{s.get('id','?')} {L:.2f}s", flush=True)
    lst = f"{tmp}/list.txt"
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    body = f"{tmp}/body.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", body], check=True)
    total = t_out
    fs = int(W * 0.075)
    ass = f"{tmp}/titles.ass"
    open(ass, "w", encoding="utf-8").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: T,{a.font},{fs},&H0042C5F5,&H00FFFFFF,&H003A1F0B,&H803A1F0B,-1,0,0,0,100,100,4,0,1,{max(3,fs//10)},3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "".join(f"Dialogue: 0,{ts(s)},{ts(e)},T,,0,0,0,,{{\\fad(200,250)}}{t}\n" for s, e, t in events))
    ap_ = os.path.abspath(ass).replace("\\", "/").replace(":", "\\:")
    fo = P.get("fade_out", 1.5)
    ms = P.get("music_start", 0) + (beats[0] - P.get("music_start", 0))  # bắt đầu nhạc đúng beat đầu
    oa = P.get("orig_audio", 0.15)
    fc = (f"[0:v]ass='{ap_}',fade=t=out:st={max(0,total-fo):.2f}:d={fo}[v];"
          f"[1:a]atrim=start={ms:.3f}:duration={total:.3f},asetpts=PTS-STARTPTS,"
          f"afade=t=out:st={max(0,total-fo):.2f}:d={fo}[m];"
          f"[0:a]volume={oa}[o];[m][o]amix=inputs=2:duration=first:normalize=0,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", body, "-i", P["music"], "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", *preset, "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.3f}",
                    "-movflags", "+faststart", a.out], check=True)
    # Pass 2: bù loudness cho chuẩn -14 LUFS
    import re, shutil
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.out, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r'"input_i"\s*:\s*"(-?[\d.]+)"', r.stderr)
    if m and abs(-14 - float(m.group(1))) > 0.8:
        g = -14 - float(m.group(1)); fixed = f"{tmp}/fixed.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.out, "-c:v", "copy", "-af",
                        f"volume={g:.2f}dB,alimiter=limit=0.84", "-c:a", "aac", "-b:a", "192k", fixed], check=True)
        shutil.move(fixed, a.out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK: {len(parts)} shot, {total:.1f}s -> {a.out}")

if __name__ == "__main__":
    main()
