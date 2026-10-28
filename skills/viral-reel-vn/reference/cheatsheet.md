# Cheatsheet — exact parameters (copy/paste)

FONT = the skill's `assets/Montserrat.ttf`. Colors below are proven-good.

## Framing / crop to 1080×1920
```
scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920
```
Removing browser/dock/Zoom chrome (screen recordings): `crop=W:H:X:Y` first, then scale+pad.

## Warm grade + vignette (natural polish)
```
eq=contrast=1.06:saturation=1.10:gamma=0.98,colorbalance=rm=0.02:bm=-0.02,vignette=PI/5
```

## ASS caption styles (the signature)
```
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: W,Montserrat,74,&H00FFFFFF,&H000000FF,&H00101010,&HB4000000,-1,0,0,0,100,100,0,0,1,7,3,2,80,80,330,1
Style: Y,Montserrat,74,&H0000D4FF,&H000000FF,&H00101010,&HB4000000,-1,0,0,0,100,100,0,0,1,7,3,2,80,80,330,1
```
- `&H0000D4FF` = yellow (ASS is AABBGGRR). White = `&H00FFFFFF`.
- Per-line effect: normal `{\fad(90,70)\fscx90\fscy90\t(0,110,\fscx100\fscy100)}`,
  big `{\fad(90,70)\fs92\fscx88\fscy88\t(0,120,\fscx104\fscy104)}`.
- MarginV ≈ 330 (natural, lower third). Framed layout uses ≈ 600 (higher).
- Keep lines short; `WrapStyle:0` wraps long lines to 2 (else they clip with WrapStyle:2).
- Burn: `subtitles='/abs/cap.ass':fontsdir='/abs/dir'`.

## Pop-up pill / hook / CTA (drawtext)
Fade alpha helper (t0..t1): `if(lt(t,{t0}+0.2),(t-{t0})/0.2,if(gt(t,{t1}-0.3),({t1}-t)/0.3,1))`
```
drawtext=fontfile='{FONT}':textfile='{tf}':x=(w-tw)/2:y=Y:fontsize=FS:fontcolor=FG:
 box=1:boxcolor=COLOR@0.9:boxborderw=24:alpha='ALPHA':enable='between(t,T0,T1)'
```
- Pills: red `0x8A1B1B` (cost/bad), green `0x137a2e` (saving/good), blue `0x1f5fbf` (fact).
- Hook ribbon: `boxcolor=0xFFD400@0.96 fontcolor=0x1E1746` at `y=48` (top), 0–4s.
- CTA: `boxcolor=0x5946CE@0.96 fontcolor=white` "BÌNH LUẬN: QUAN TÂM" at bottom; +`tpad=stop_mode=clone:stop_duration=1.5` freeze so it lingers (apply tpad BEFORE subtitles/drawtext so padded frames get them).
- Vietnamese/emoji: Montserrat has no emoji → convey ❌/✅ with red/green color, not glyphs.

## Cut + reorder (remove stutters, hook first)
```
[0:v:0]trim=A1:A2,setpts=PTS-STARTPTS[va]; ... concat=n=N:v=1:a=0, scale/crop [v]
[0:a:0]atrim=A1:A2,asetpts=PTS-STARTPTS[aa]; ... concat=n=N:v=0:a=1 [a]
```
Then remap word time → output time: `out = sum(prior kept-seg durations) + (t - seg_start)`.

## Audio (voice + ducked music + normalize)
```
[0:a]highpass=f=80,afftdn=nr=10:nf=-32,acompressor=threshold=-20dB:ratio=3:makeup=3[vc];
[vc]asplit=2[vk][vm];
[1:a]volume=0.08,aloop=loop=-1:size=200000000[m0];
[m0][vk]sidechaincompress=threshold=0.04:ratio=10:attack=12:release=320[md];
[vm][md]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1:LRA=11[a]
```
Very quiet voice (−40 LUFS): add `volume=+28..31dB` before loudnorm, then `alimiter=limit=0.95`.
Two-pass loudnorm for accuracy (measure JSON → pass `measured_*`). NOTE zsh eats `:l` in
`$VAR:l...` — use `${VAR}` or literals.

## Bokeh background (rembg per frame) — see scripts/bokeh.py
`u2net_human_seg`, `only_mask=True`, EMA smooth mask across frames (0.55 new / 0.45 prev) to
stop edge flicker, GaussianBlur(3) feather, bg = GaussianBlur(30)+darken 0.86, composite.
~0.5–0.6s/frame → ~10 min per 1000 frames (run in background). Skip for "tự nhiên" look.

## Framed card + person-shrink panel — see scripts/build_framed.py
Dark navy bg + radial glow + dot grid. Person in rounded card (r=44) with 3-stroke orange
glow border (16@70,10@140,5@255). At reveal beats, ease card width 940→520 & move to top
(smoothstep over 0.4s), fade in a graphic PANEL (rounded dark card + glow) in lower area.
Whoosh on each shrink. This is the "y chang mẫu" look.
