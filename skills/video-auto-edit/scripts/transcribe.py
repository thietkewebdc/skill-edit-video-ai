#!/usr/bin/env python3
"""Transcribe video/audio -> transcript.json (word timestamps) + transcript.txt."""
import argparse, json, os

def fmt(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--lang", default="vi")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--out", default="work")
    ap.add_argument("--prompt", default="", help="Từ khoá/tên riêng giúp Whisper nhận đúng")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    try:
        model = WhisperModel(a.model, device="cpu", compute_type=os.environ.get("WHISPER_COMPUTE", "int8"))  # int8: máy 8GB; "auto" nạp float32 ~6GB gây swap, treo máy
    except Exception:
        model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, info = model.transcribe(a.input, language=a.lang, word_timestamps=True,
                                  vad_filter=True, initial_prompt=a.prompt or None)
    out = {"language": info.language, "duration": info.duration, "segments": []}
    lines = []
    for s in segs:
        words = [{"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                 for w in (s.words or []) if w.word.strip()]
        out["segments"].append({"start": round(s.start, 3), "end": round(s.end, 3),
                                "text": s.text.strip(), "words": words})
        lines.append(f"[{fmt(s.start)} -> {fmt(s.end)}] {s.text.strip()}")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "transcript.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"OK: {len(out['segments'])} câu, {info.duration:.1f}s -> {a.out}/transcript.json")

if __name__ == "__main__":
    main()
