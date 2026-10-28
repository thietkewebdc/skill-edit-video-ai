#!/usr/bin/env python3
"""TEMPLATE — natural captioned reel (edit CONFIG per video, then run).
Pipeline: cut/reorder → grade+vignette → burn ASS karaoke captions → drawtext hook/pills/CTA
→ voice denoise + ducked music bed → loudnorm -14 → 1080x1920 mp4.
Run in a venv that has ffmpeg on PATH (numpy not required here).
Two passes internally: (1) cut base, (2) style+audio. Adapt the CONFIG block.
"""
import subprocess, os
from pathlib import Path

# ─────────── CONFIG (edit these per video) ───────────
SKILL   = Path(__file__).resolve().parents[1]
FONT    = SKILL / "assets" / "Montserrat.ttf"
MUSIC   = SKILL / "assets" / "bgm-inspired.mp3"
SRC     = "/ABS/PATH/source.mp4"          # input talking-head
WORK    = "/ABS/PATH/scratch"             # scratch dir
OUT     = "/ABS/PATH/output.mp4"
# kept source segments in OUTPUT order (drop bland intro, remove stutters/dead, hook first).
# Set [] to keep whole clip unchanged.
CUTS    = [(7.20, 41.15), (41.98, 42.64), (43.94, 68.68), (71.62, 90.40)]
VOICE_GAIN_DB = 0                          # +28..31 if voice is very quiet (-40 LUFS)
FREEZE_OUT    = 1.5                         # seconds of end freeze for CTA (0 = none)
# captions on OUTPUT timeline: (start, end, "text", "W"|"Y", big?0/1)
CAPTIONS = [
  (0.10, 3.42, "Ví dụ câu mở đầu", "W", 0),
  (3.52, 6.20, "SỐ LIỆU HAY", "Y", 1),
]
# drawtext overlays: (text, t0, t1, boxcolor, fontcolor, x, y, fontsize)
HOOK = ("HOOK TO Ở ĐÂY?", 0.0, 4.2, "0xFFD400@0.96", "0x1E1746", "(w-tw)/2", 48, 52)
PILLS = [
  ("SỐ LIỆU 1", 10.8, 15.4, "0x1f5fbf@0.92", "white", "w-tw-50", 320, 40),
]
CTA  = ("BÌNH LUẬN: QUAN TÂM", None, None, "0x5946CE@0.96", "white", "(w-tw)/2", 1650, 58)  # t0/t1 filled below
WHOOSH_AT = []   # output-timeline seconds to place whoosh (optional; needs numpy variant)
# ─────────────────────────────────────────────────────

os.makedirs(WORK, exist_ok=True)
def run(c):
    p = subprocess.run(c, capture_output=True, text=True)
    if p.returncode: print("ERR", p.stderr[-1800:]); raise SystemExit(1)
def tt(s):
    cs = int(round(s*100)); return f"{cs//360000}:{(cs//6000)%60:02d}:{(cs//100)%60:02d}.{cs%100:02d}"

# ── Pass 1: cut base (or straight scale) ──
base = f"{WORK}/base.mp4"
if CUTS:
    vt = "".join(f"[0:v:0]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];" for i,(a,b) in enumerate(CUTS))
    at = "".join(f"[0:a:0]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}];" for i,(a,b) in enumerate(CUTS))
    vc = "".join(f"[v{i}]" for i in range(len(CUTS))) + f"concat=n={len(CUTS)}:v=1:a=0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30[v]"
    ac = "".join(f"[a{i}]" for i in range(len(CUTS))) + f"concat=n={len(CUTS)}:v=0:a=1[a]"
    run(["ffmpeg","-v","error","-y","-i",SRC,"-filter_complex",vt+at+vc+";"+ac,
         "-map","[v]","-map","[a]","-c:v","libx264","-crf","18","-preset","medium",
         "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k",base])
else:
    run(["ffmpeg","-v","error","-y","-i",SRC,"-map","0:v:0","-map","0:a:0",
         "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
         "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-r","30",
         "-c:a","aac","-b:a","192k",base])
dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",base]))
END = dur + FREEZE_OUT
cta = list(CTA); cta[1] = END-6 if cta[1] is None else cta[1]; cta[2] = END if cta[2] is None else cta[2]

# ── ASS captions ──
head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
"[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
"Style: W,Montserrat,74,&H00FFFFFF,&H000000FF,&H00101010,&HB4000000,-1,0,0,0,100,100,0,0,1,7,3,2,80,80,330,1\n"
"Style: Y,Montserrat,74,&H0000D4FF,&H000000FF,&H00101010,&HB4000000,-1,0,0,0,100,100,0,0,1,7,3,2,80,80,330,1\n\n"
"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
lines=[]
for s,e,txt,st,big in CAPTIONS:
    fx = "{\\fad(90,70)\\fscx90\\fscy90\\t(0,110,\\fscx100\\fscy100)}" if not big else "{\\fad(90,70)\\fs92\\fscx88\\fscy88\\t(0,120,\\fscx104\\fscy104)}"
    lines.append(f"Dialogue: 0,{tt(s)},{tt(e)},{st},,0,0,0,,{fx}{txt}")
ass=f"{WORK}/cap.ass"; Path(ass).write_text(head+"\n".join(lines)+"\n",encoding="utf-8")

def dtxt(txt,t0,t1,box,fg,x,y,fs):
    tf=f"{WORK}/dt_{abs(hash(txt))%99999}.txt"; Path(tf).write_text(txt,encoding="utf-8")
    a=f"if(lt(t,{t0}+0.2),(t-{t0})/0.2,if(gt(t,{t1}-0.3),({t1}-t)/0.3,1))"
    return (f"drawtext=fontfile='{FONT}':textfile='{tf}':x={x}:y={y}:fontsize={fs}:fontcolor={fg}:"
            f"box=1:boxcolor={box}:boxborderw=24:alpha='{a}':enable='between(t,{t0},{t1})'")
overlays=[dtxt(*HOOK)] + [dtxt(*p) for p in PILLS] + [dtxt(*cta)]

vf=(f"tpad=stop_mode=clone:stop_duration={FREEZE_OUT}," if FREEZE_OUT>0 else "") + \
   ("eq=contrast=1.06:saturation=1.10:gamma=0.98,colorbalance=rm=0.02:bm=-0.02,vignette=PI/5,"
    f"subtitles='{ass}':fontsdir='{SKILL/'assets'}',"+",".join(overlays))
vgain = f"volume={VOICE_GAIN_DB}dB," if VOICE_GAIN_DB else ""
af=(f"[0:a]highpass=f=80,afftdn=nr=10:nf=-32,{vgain}acompressor=threshold=-20dB:ratio=3:attack=8:release=180:makeup=3[vc];"
    "[vc]asplit=2[vk][vm];[1:a]volume=0.08,aloop=loop=-1:size=200000000[m0];"
    "[m0][vk]sidechaincompress=threshold=0.04:ratio=10:attack=12:release=320[md];"
    "[vm][md]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1:LRA=11,alimiter=limit=0.97[a]")
run(["ffmpeg","-v","error","-y","-i",base,"-i",str(MUSIC),"-filter_complex",vf+"[v];"+af,
     "-map","[v]","-map","[a]","-t",str(END),"-c:v","libx264","-preset","medium","-crf","20",
     "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-movflags","+faststart",OUT])
print("DONE", OUT)
