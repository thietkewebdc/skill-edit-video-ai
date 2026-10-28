#!/usr/bin/env python3
"""transcript.json + edl.json -> phụ đề .ass (karaoke) khớp timeline đã cắt."""
import argparse, json

ASPECTS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "16:9": (1920, 1080)}

def col(hexrgb, alpha="00"):  # #RRGGBB -> &HAABBGGRR
    h = hexrgb.lstrip("#")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}".upper()

def ts(t):
    t = max(0, t)
    return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript"); ap.add_argument("edl")
    ap.add_argument("--style", choices=["shorts", "classic"], default="shorts")
    ap.add_argument("--font", default="Be Vietnam Pro")
    ap.add_argument("--hl", default="#F5C542", help="Màu highlight (gold)")
    ap.add_argument("--text", default="#FFFFFF")
    ap.add_argument("--outline", default="#0B1F3A", help="Màu viền (navy)")
    ap.add_argument("--words", type=int, default=3, help="Số từ tối đa mỗi dòng (shorts)")
    ap.add_argument("--upper", action="store_true")
    ap.add_argument("--out", default="work/subs.ass")
    a = ap.parse_args()
    t = json.load(open(a.transcript, encoding="utf-8"))
    e = json.load(open(a.edl, encoding="utf-8"))
    W, H = ASPECTS.get(e.get("aspect"), (1920, 1080))
    # Map thời gian gốc -> thời gian output
    words, off = [], 0.0
    allw = [w for s in t["segments"] for w in s["words"]]
    for seg in e["segments"]:
        for w in allw:
            if w["start"] >= seg["start"] - 0.01 and w["end"] <= seg["end"] + 0.05:
                words.append({"w": w["w"], "s": off + w["start"] - seg["start"],
                              "e": off + min(w["end"], seg["end"]) - seg["start"]})
        off += seg["end"] - seg["start"]
    shorts = a.style == "shorts"
    size = int(W * (0.085 if shorts else 0.045))
    maxw = a.words if shorts else 8
    marginv = int(H * (0.30 if shorts else 0.06))
    # PrimaryColour = màu sau khi karaoke chạy qua (highlight), Secondary = chưa tới
    primary = col(a.hl) if shorts else col(a.text)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{a.font},{size},{primary},{col(a.text)},{col(a.outline)},{col(a.outline,'80')},-1,0,0,0,100,100,0,0,1,{max(3,size//12)},{2 if shorts else 1},2,60,60,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines, chunk = [], []
    def flush():
        if not chunk: return
        st, en = chunk[0]["s"], chunk[-1]["e"]
        txt = ""
        for i, w in enumerate(chunk):
            nxt = chunk[i+1]["s"] if i + 1 < len(chunk) else w["e"]
            k = max(1, round((nxt - w["s"]) * 100))
            word = w["w"].upper() if a.upper else w["w"]
            txt += (f"{{\\k{k}}}{word} " if shorts else f"{word} ")
        lines.append(f"Dialogue: 0,{ts(st)},{ts(en + 0.05)},Main,,0,0,0,,{txt.strip()}")
        chunk.clear()
    for w in words:
        if chunk and (len(chunk) >= maxw or w["s"] - chunk[-1]["e"] > 0.6 or
                      chunk[-1]["w"].rstrip().endswith((".", "?", "!", ","))):
            flush()
        chunk.append(w)
    flush()
    open(a.out, "w", encoding="utf-8").write(head + "\n".join(lines) + "\n")
    print(f"OK: {len(lines)} dòng sub, {W}x{H} -> {a.out}")

if __name__ == "__main__":
    main()
