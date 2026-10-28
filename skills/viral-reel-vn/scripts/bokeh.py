#!/usr/bin/env python3
"""Bokeh background for a folder of frames (rembg human segmentation).
Usage: python bokeh.py <frames_in_dir> <frames_out_dir>
Run inside the rembg venv. ~0.5-0.6s/frame; run in background for long clips.
First frame extract:  ffmpeg -i SRC -map 0:v:0 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -q:v 3 frames_in/%05d.jpg
Encode after:         ffmpeg -framerate 30 -i frames_out/%05d.jpg ... (see build scripts)
"""
import glob, sys, time
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session

IN, OUT = sys.argv[1], sys.argv[2]
frames = sorted(glob.glob(f"{IN}/*.jpg"))
sess = new_session("u2net_human_seg")   # ~176MB model auto-downloads first run
prev = None
t0 = time.time()
for i, fp in enumerate(frames):
    img = Image.open(fp).convert("RGB")
    m = np.asarray(remove(img, session=sess, only_mask=True)).astype(np.float32) / 255.0
    if prev is not None:
        m = 0.55 * m + 0.45 * prev          # temporal smoothing → less edge flicker
    prev = m
    mask = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
    bg = img.filter(ImageFilter.GaussianBlur(30))
    bg = Image.eval(bg, lambda p: int(p * 0.86))   # darken bg so subject pops
    Image.composite(img, bg, mask).save(f"{OUT}/{i+1:05d}.jpg", quality=92)
    if i % 200 == 0:
        print(i, len(frames), round(time.time() - t0), "s", flush=True)
print("BOKEH DONE", len(frames), round(time.time() - t0), "s")
