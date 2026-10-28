#!/usr/bin/env python3
"""Burn phụ đề + nhạc nền ducking + chuẩn hoá loudness -14 LUFS."""
import argparse, subprocess, os

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--subs")
    ap.add_argument("--music")
    ap.add_argument("--music-vol", type=float, default=0.18)
    ap.add_argument("--lufs", type=float, default=-14)
    ap.add_argument("--fontsdir", default=None, help="Thư mục chứa font .ttf nếu font chưa cài vào máy")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.video]
    if a.music:
        cmd += ["-stream_loop", "-1", "-i", a.music]
    fc = []
    if a.subs:
        p = os.path.abspath(a.subs).replace("\\", "/").replace(":", "\\:")
        fd = f":fontsdir={os.path.abspath(a.fontsdir)}" if a.fontsdir else ""
        fc.append(f"[0:v]ass='{p}'{fd}[v]")
    else:
        fc.append("[0:v]null[v]")
    ln = f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11"
    if a.music:
        fc.append("[0:a]asplit=2[vo][sc]")
        fc.append(f"[1:a]volume={a.music_vol}[m]")
        fc.append("[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]")
        fc.append(f"[vo][duck]amix=inputs=2:duration=first:normalize=0,{ln}[a]")
    else:
        fc.append(f"[0:a]{ln}[a]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(f"OK -> {a.out}")

if __name__ == "__main__":
    main()
