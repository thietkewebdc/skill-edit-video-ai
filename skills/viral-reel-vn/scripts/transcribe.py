#!/usr/bin/env python3
"""Word-level Vietnamese transcription with mlx-whisper.
Usage: python transcribe.py <video_or_audio> <out.json> ["domain prompt with likely terms"]
Run inside the asr-env venv (~/Documents/Video Mới/.video-review/asr-env).
Prints segment lines; writes full word-level JSON. Fix ASR errors by hand afterwards.
"""
import json, subprocess, sys, tempfile, os
import mlx_whisper

src = sys.argv[1]
out = sys.argv[2]
prompt = sys.argv[3] if len(sys.argv) > 3 else "Video ngắn tiếng Việt về AI, kinh doanh, làm video, thiết kế website."

# extract 16k mono wav (works for both video and audio inputs)
wav = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:a:0",
                "-ar", "16000", "-ac", "1", wav], check=True)

r = mlx_whisper.transcribe(
    wav,
    path_or_hf_repo="mlx-community/whisper-medium-mlx",   # medium = good VN accuracy
    language="vi", word_timestamps=True, verbose=False,
    initial_prompt=prompt,
)
with open(out, "w") as f:
    json.dump(r, f, ensure_ascii=False, indent=2)
for s in r["segments"]:
    print(f"{s['start']:.2f}-{s['end']:.2f}: {s['text'].strip()}")
os.remove(wav)
print(f"\nWords: {sum(len(s.get('words', [])) for s in r['segments'])} · saved {out}")
