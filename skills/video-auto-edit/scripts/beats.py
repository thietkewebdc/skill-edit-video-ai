#!/usr/bin/env python3
"""Dò beat nhạc (không cần librosa): BPM, vị trí beat, năng lượng từng beat, drop."""
import argparse, json, subprocess
import numpy as np

SR, HOP, N = 22050, 512, 2048

def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("music")
    ap.add_argument("--out", default="work/beats.json")
    ap.add_argument("--bpm-min", type=float, default=70)
    ap.add_argument("--bpm-max", type=float, default=180)
    a = ap.parse_args()
    x = load(a.music)
    nfr = 1 + (len(x) - N) // HOP
    win = np.hanning(N).astype(np.float32)
    frames = np.lib.stride_tricks.as_strided(x, (nfr, N), (x.strides[0] * HOP, x.strides[0]))
    mag = np.log1p(np.abs(np.fft.rfft(frames * win, axis=1)))
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(1)
    flux = np.concatenate([[0], flux])
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    rms = np.sqrt((frames ** 2).mean(1))
    fps = SR / HOP
    # Tempo: autocorrelation của onset envelope
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(len(ac))
    lo, hi = int(fps * 60 / a.bpm_max), int(fps * 60 / a.bpm_min)
    bpm_w = np.exp(-0.5 * (np.log2((60 * fps / np.maximum(lags[lo:hi], 1)) / 120)) ** 2)  # ưu tiên quanh 120
    lag = lo + int(np.argmax(ac[lo:hi] * bpm_w))
    # Nội suy parabol để lấy chu kỳ chính xác dưới 1 frame
    if 1 <= lag < len(ac) - 1:
        y0, y1, y2 = ac[lag - 1], ac[lag], ac[lag + 1]
        den = y0 - 2 * y1 + y2
        flag = lag + (0.5 * (y0 - y2) / den if den != 0 else 0)
    else:
        flag = lag
    # Tinh chỉnh chu kỳ trên toàn bài: thử quanh flag, chọn lưới khớp onset nhất
    dur = len(x) / SR
    def grid_score(per, o):
        idx = (np.arange(o, len(flux), per)).astype(int)
        return flux[idx[idx < len(flux)]].sum()
    best = (-1e9, flag, 0.0)
    for per in np.linspace(flag * 0.985, flag * 1.015, 61):
        for o in np.arange(0, per, 0.5):
            sc = grid_score(per, o)
            if sc > best[0]: best = (sc, per, o)
    _, per, off = best
    period = per / fps
    beats, k = [], 0
    while True:
        tg = (off + k * per) / fps
        if tg >= dur: break
        i = int(round(tg * fps)); j0, j1 = max(0, i - 2), min(len(flux), i + 3)
        j = j0 + int(np.argmax(flux[j0:j1])) if j1 > j0 else i
        tb = j / fps if abs(j / fps - tg) < 0.04 else tg
        beats.append(round(tb + N / (2 * SR), 3)); k += 1   # bù độ trễ cửa sổ FFT
    en = [float(rms[int(b * fps):int((b + period) * fps)].mean()) if int(b * fps) < len(rms) else 0 for b in beats]
    en = np.array(en); en = (en / (en.max() + 1e-9)).round(3)
    # Drop: beat mà năng lượng 4 beat tới tăng mạnh so với 8 beat trước
    drops = []
    for k in range(8, len(beats) - 4):
        if en[k:k + 4].mean() > 1.6 * en[k - 8:k].mean() and en[k:k + 4].mean() > 0.5:
            if not drops or beats[k] - drops[-1] > 8: drops.append(beats[k])
    out = {"music": a.music, "duration": round(dur, 2), "bpm": round(60 / period, 1),
           "beats": beats, "energy": en.tolist(), "downbeats": beats[::4], "drops": drops}
    json.dump(out, open(a.out, "w"), indent=0)
    print(f"OK: {out['bpm']} BPM, {len(beats)} beat, drop tại {drops[:5]} -> {a.out}")

if __name__ == "__main__":
    main()
