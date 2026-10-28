---
name: viral-reel-vn
description: Edit a Vietnamese talking-head video into a viral vertical reel (TikTok/Reels/Shorts) in the "FDown competitor" style — hook-first, karaoke captions (white emphasis + yellow flow), pop-up ❌✅ label callouts, optional framed card + person-shrink panel reveals, silence/stutter cutting, bokeh background, whoosh SFX, comment-bait CTA, warm grade, normalized to -14 LUFS at 1080×1920. Use whenever the user hands over a talking-head clip (DJI/phone/webcam) and asks to edit it "đẹp / nổi bật / theo style đối thủ / cho TikTok", or references this reference style. Runs fully local with ffmpeg + mlx-whisper + rembg + libass.
---

# Viral Reel VN — edit talking-head into competitor-style vertical reel

Reproduces the editing style of the reference video
`FDown.vn_Tai_video_Facebook_720p (HD)_94c0.mp4` (Vietnamese AI/business creator reel).
Read `reference/style-spec.md` for the full look breakdown and
`reference/cheatsheet.md` for exact ASS styles, drawtext recipes, crop/grade/loudnorm numbers.

## When to use
User gives a talking-head video (họ nói vào camera) and wants it turned into a punchy
vertical reel. Also for re-editing footage already discussed. NOT for faceless
auto-generated videos from a topic/URL (that is the `auto-video-gen` repo instead).

## Output contract (always)
- 1080×1920, H.264 yuv420p, 30fps, AAC 192k, `+faststart`.
- Integrated loudness **−14 LUFS**, true peak ≤ −1 dBTP (verify with loudnorm print).
- Vietnamese renders with full diacritics (font = `assets/Montserrat.ttf`).
- Deliver to the user's project folder, then QC a 5–6 frame contact sheet before sending.

## Environment (this machine)
- ffmpeg/ffprobe: `~/.local/bin` — `export PATH="$HOME/.local/bin:$PATH"`.
- ASR: mlx-whisper venv at `~/Documents/Video Mới/.video-review/asr-env` (Apple Silicon).
  `source .../asr-env/bin/activate` then run `scripts/transcribe.py`.
- Matting (bokeh): rembg venv — create once with
  `uv venv --python 3.11 rembg-env && source rembg-env/bin/activate && uv pip install "rembg[cpu]" onnxruntime pillow numpy`.
  Model `u2net_human_seg` (~176MB) auto-downloads on first use (ask before downloading).
- Assets in this skill: `assets/Montserrat.ttf`, `assets/bgm-inspired.mp3`, `assets/whoosh.mp3`, `assets/pop.mp3`.
- Work in a scratchpad dir, not the project folder.

## The pipeline (follow in order)

### 1. Probe + understand the footage
- `ffprobe` duration/res/fps; `volumedetect` for level (voice is usually very quiet, −25 to −45 dB).
- Contact sheet: `ffmpeg -i F -map 0:v:0 -vf "fps=1/6,scale=240:-1,tile=5x3" sheet.jpg` → read it.
- NOTE the video stream index: DJI/phone files often have `0:a:0` audio first + an mjpeg
  thumbnail stream — always map `0:v:0` explicitly.

### 2. Transcribe (word-level) — needed for captions, cut points, hook
```
source ~/Documents/Video\ Mới/.video-review/asr-env/bin/activate
python scripts/transcribe.py <audio_or_video> <out.json> "domain prompt with likely terms"
```
Fix ASR errors by hand (e.g. "khương dấn"→"hướng dẫn", "hotend"→"hosting", "tiết biển"→"tên miền").

### 3. Editorial decisions (the human-taste part)
- **Hook to front (~4s):** pick the punchiest line/number and either (a) drop a bland intro so
  a strong line opens, or (b) cold-open a teaser clip. Add a big yellow HOOK ribbon text.
- **Cut stutters / dead air / repeats:** from word timestamps find repeated phrases and >0.6s
  gaps. Talking is often continuous — do NOT over-cut (clips words). Trim trailing silence.
- **Style choice:**
  - *Natural* (default for "tự nhiên"): keep real background + warm grade + vignette + captions
    + a few money/keyword pills. Reliable, fast (no matting). See `scripts/build_captioned.py`.
  - *Premium framed* (for "sang/đẹp như mẫu"): bokeh background + rounded glow card + person
    shrinks to top while a graphic PANEL reveals below at key beats. See `scripts/build_framed.py`
    (+ `scripts/bokeh.py` first). This is the exact "kéo người thu nhỏ + panel" look.

### 4. Build the cut (if cutting/reordering)
Use ffmpeg `trim/atrim + concat` to assemble kept segments in output order, scaled+cropped to
1080×1920. Record the kept source-segments so you can remap word times → output timeline for captions.
Template in `scripts/build_captioned.py` (`CUTS` list) and `reference/cheatsheet.md`.

### 5. Captions (ASS karaoke) — the signature look
- Two styles: **W** = white bold (emphasis/punch), **Y** = yellow `&H0000D4FF` (numbers / flow).
- Short phrases (2–6 words), one at a time, synced to speech; `\fad` + slight scale-pop.
- Big money/keyword phrases get larger font. Heavy black outline (7–8) so it reads on any bg.
- Generate the `.ass` with the helper in `scripts/build_captioned.py`; burn with
  `subtitles=cap.ass:fontsdir=<dir>`.

### 6. Pop-ups, hook, CTA (drawtext)
- Money/keyword **pills**: `drawtext ... box=1:boxcolor=<c>@0.9:boxborderw=24` with a fade alpha.
  Red `0x8A1B1B` = cost/bad, green `0x137a2e` = saving/good, blue `0x1f5fbf` = neutral fact.
- **Hook ribbon** top, yellow `0xFFD400`, dark text, 0–4s.
- **CTA** end: purple `0x5946CE` pill "BÌNH LUẬN: QUAN TÂM" + optional 1.5s freeze (`tpad`).

### 7. Audio
- Voice: `highpass=80, afftdn=nr=10, acompressor, [+volume if very quiet]`.
- Music bed: `assets/bgm-inspired.mp3` low (`volume=0.08`), ** duck** under voice
  (`sidechaincompress`). Whoosh (`assets/whoosh.mp3`) on reveal/cut beats.
- Final: `loudnorm=I=-14:TP=-1:LRA=11` (verify with a print pass).

### 8. Export + QC + deliver
- Encode 1080×1920 per output contract.
- Extract 5–6 frames across the video → hstack → read the sheet; check diacritics, no clipped
  captions, panels/pills correct, cut seams clean.
- Copy to `~/Documents/Video Mới/` with a descriptive name and send with a short caption.

## Guardrails
- Never fabricate spoken words — captions must match what the person actually said (may tidy wording).
- Real people / brands / data on screen → ask before publishing publicly; offer to blur.
- Downloading the rembg model is a file download → confirm with the user first.
- Keep the source file untouched; write outputs to new paths.
