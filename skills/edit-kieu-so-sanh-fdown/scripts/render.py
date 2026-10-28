"""Dựng 1 video: cắt theo từ -> proxy 1080x1920 -> ghép bố cục FDown + bìa snaptik -> âm thanh -14 LUFS.
Dùng: python render.py cfg.json [--cut-only] [--preview N]"""
import json, sys, os, subprocess, math, time, shutil
import numpy as np, cv2
import layout as L

import shutil, sys
FF = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")
FFP = shutil.which("ffprobe") or os.path.expanduser("~/.local/bin/ffprobe")
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets") + os.sep   # SFX/nhạc nền tự tổng hợp; thay bằng file của bạn nếu muốn
FPS = 30
W, H = L.W, L.H
PW, PH = W, H   # kích thước proxy (có thể cao hơn cho dạng 1 thẻ)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stderr[-1500:])
        raise SystemExit("lỗi: " + " ".join(cmd[:3]))
    return r


# ------------------------------------------------------------------ cắt
def plan_segments(words, drop, tail=0.5, gap_cut=0.6, pad=0.10, min_seg=2.0, lead=0.0):
    """words: [{w,s,e}], drop: [[s,e]] khoảng nguồn bỏ (theo giây gốc). Trả (segments nguồn, words_đã_gắn_index)."""
    def dropped(w):
        mid = (w["s"] + w["e"]) / 2
        return any(a <= mid <= b for a, b in drop)
    ws = [w for w in words if not dropped(w)]
    runs, cur = [], [ws[0]]
    for w in ws[1:]:
        if w["s"] - cur[-1]["e"] > gap_cut:
            runs.append(cur); cur = [w]
        else:
            cur.append(w)
    runs.append(cur)
    # gộp run quá ngắn (<2s) vào run kề
    def dur(r): return r[-1]["e"] - r[0]["s"] + 2 * pad
    i = 0
    while i < len(runs):
        if len(runs) > 1 and dur(runs[i]) < min_seg:
            j = i + 1 if i + 1 < len(runs) else i - 1
            a, b = (i, j) if j > i else (j, i)
            runs[a] = runs[a] + runs[b]
            del runs[b]
            i = max(0, a - 1)
        else:
            i += 1
    segs = []
    for k, r in enumerate(runs):
        s = max(0, r[0]["s"] - pad - (lead if k == 0 else 0))
        e = r[-1]["e"] + (tail if k == len(runs) - 1 else pad)
        segs.append([round(s, 3), round(e, 3)])
    # bỏ chồng lấn
    for k in range(1, len(segs)):
        if segs[k][0] < segs[k - 1][1]:
            mid = (segs[k][0] + segs[k - 1][1]) / 2
            segs[k - 1][1] = segs[k][0] = round(mid, 3)
    return segs, runs


def remap_words(words, segs, drop):
    out, t0 = [], 0.0
    for s, e in segs:
        for w in words:
            mid = (w["s"] + w["e"]) / 2
            if s <= mid <= e and not any(a <= mid <= b for a, b in drop):
                out.append({"w": w["w"], "s": round(t0 + max(w["s"], s) - s, 3), "e": round(t0 + min(w["e"], e) - s, 3)})
        t0 += e - s
    return out


def build_cut(cfg, segs, work):
    """cắt các đoạn từ nguồn 4K -> proxy 1080x1920 30fps + wav tiếng (một lệnh ffmpeg, concat)."""
    n = len(segs)
    parts, labels_v, labels_a = [], [], []
    for i, (s, e) in enumerate(segs):
        parts.append(f"[0:v:0]trim=start={s}:end={e},setpts=PTS-STARTPTS,fps={FPS},scale={PW}:{PH}:flags=lanczos[v{i}]")
        parts.append(f"[0:a:0]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,aresample=48000[a{i}]")
        labels_v.append(f"[v{i}]"); labels_a.append(f"[a{i}]")
    fc = ";".join(parts) + ";" + "".join(f"{v}{a}" for v, a in zip(labels_v, labels_a)) + f"concat=n={n}:v=1:a=1[v][a]"
    script = os.path.join(work, "cut_filter.txt")
    open(script, "w").write(fc)
    out_v = os.path.join(work, "cut_proxy.mp4")
    run([FF, "-y", "-v", "error", "-hwaccel", "videotoolbox", "-i", cfg["src"], "-filter_complex_script", script,
         "-map", "[v]", "-map", "[a]", "-c:v", "h264_videotoolbox", "-b:v", "16M", "-pix_fmt", "yuv420p",
         "-c:a", "pcm_s16le", "-ar", "48000", out_v.replace(".mp4", ".mov")])
    return out_v.replace(".mp4", ".mov")


# ------------------------------------------------------------------ mặt
def track_faces(path, work):
    cache = os.path.join(work, "face.json")
    if os.path.exists(cache):
        return json.load(open(cache))
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    pts = []
    step = 6
    for i in range(0, n, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if not ok: break
        sm = cv2.resize(fr, (PW // 3, PH // 3), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY)
        fs = cas.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
        if len(fs):
            x, y, w, h = max(fs, key=lambda r: r[2])
            pts.append((int(i), float((x + w / 2) * 3), float((y + h / 2) * 3), float(w * 3)))
    cap.release()
    if not pts:
        raise SystemExit("không dò được mặt")
    json.dump({"n": n, "pts": pts}, open(cache, "w"))
    return {"n": n, "pts": pts}


def face_curve(fd):
    n = fd["n"]; pts = fd["pts"]
    fx = np.interp(np.arange(n), [p[0] for p in pts], [p[1] for p in pts])
    fy = np.interp(np.arange(n), [p[0] for p in pts], [p[2] for p in pts])
    # làm mượt mạnh (camera cố định, người ít di chuyển)
    k = 31
    ker = np.ones(k) / k
    fx = np.convolve(np.pad(fx, (k // 2, k // 2), mode="edge"), ker, mode="valid")
    fy = np.convolve(np.pad(fy, (k // 2, k // 2), mode="edge"), ker, mode="valid")
    return fx, fy


# ------------------------------------------------------------------ vẽ
def crop_zoom(img, cx, cy, zoom, ow, oh, face_y=0.36):
    sh, sw = img.shape[:2]
    cw = sw / zoom; ch = cw * oh / ow
    x0 = min(max(cx - cw / 2, 0), sw - cw)
    y0 = min(max(cy - ch * face_y, 0), sh - ch)
    M = np.array([[ow / cw, 0, -x0 * ow / cw], [0, oh / ch, -y0 * oh / ch]], np.float32)
    return cv2.warpAffine(img, M, (ow, oh), flags=cv2.INTER_AREA if zoom < 1.4 else cv2.INTER_LINEAR)


def paste(dst, img, m, x, y):
    h, w = img.shape[:2]
    roi = dst[y:y + h, x:x + w]
    roi[:] = (roi * (1 - m) + img * m).astype(np.uint8)


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    t = min(max(t, 0), 1)
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def smooth(t):
    t = min(max(t, 0), 1)
    return t * t * (3 - 2 * t)


def scale_rgba(img, s):
    if abs(s - 1) < 0.01:
        return img
    h, w = img.shape[:2]
    return cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)


def fit_w(img, maxw):
    h, w = img.shape[:2]
    # đo bề rộng nội dung thật (bỏ đệm trong suốt)
    cols = np.where(img[..., 3].max(0) > 20)[0]
    cw = (cols[-1] - cols[0] + 1) if len(cols) else w
    if cw > maxw:
        return scale_rgba(img, maxw / cw)
    return img


def group_captions(words, max_chars=17, max_words=3, gap=0.45):
    groups, cur = [], []
    for w in words:
        txt = w["w"].upper()
        if not txt:
            continue
        if cur:
            cur_len = len(" ".join(x["w"] for x in cur)) + 1 + len(txt)
            if len(cur) >= max_words or cur_len > max_chars or w["s"] - cur[-1]["e"] > gap:
                groups.append(cur); cur = []
        cur.append(w)
    if cur: groups.append(cur)
    return groups


def render(cfg, preview=None):
    global PW, PH
    single = cfg.get("layout") == "single"
    if single:
        L.RC = L.RC2
        PW, PH = cfg.get("proxy", [1440, 2560])
    name = cfg["name"]
    work = os.path.join(cfg["work"], name)
    os.makedirs(work, exist_ok=True)
    words = json.load(open(cfg["words"]))
    words = words["words"] if isinstance(words, dict) else words
    # sửa chính tả theo cfg["fix"]: {"chữ sai": "chữ đúng"} (theo thứ tự), hoặc thay cả cụm bằng cfg["text_override"]
    if "words_fixed" in cfg:
        words = json.load(open(cfg["words_fixed"]))
    drop = cfg.get("drop", [])
    segs = cfg.get("segs") or plan_segments(words, drop, tail=cfg.get("tail", 0.5))[0]
    json.dump(segs, open(os.path.join(work, "segs.json"), "w"))
    import re as _re
    words = [dict(w, w=_re.sub(r"[.,?!;:…]+$", "", w["w"]).strip()) for w in words]
    words = [w for w in words if w["w"]]
    ow = remap_words(words, segs, drop)
    json.dump(ow, open(os.path.join(work, "words_out.json"), "w"), ensure_ascii=False)
    total = sum(e - s for s, e in segs)
    print(f"[{name}] {len(segs)} đoạn, {total:.1f}s (nguồn {segs[0][0]:.1f}-{segs[-1][1]:.1f})", flush=True)
    if cfg.get("cut_only"):
        return
    proxy = os.path.join(work, "cut_proxy.mov")
    if not os.path.exists(proxy):
        t = time.time(); build_cut(cfg, segs, work); print(f"  cắt xong {time.time()-t:.0f}s", flush=True)
    fd = track_faces(proxy, work)
    fx, fy = face_curve(fd)

    cap = cv2.VideoCapture(proxy)
    nfr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if preview:
        nfr = min(nfr, preview)
    # mốc đổi đoạn (output frames) để đổi mức zoom
    bounds, t0 = [0], 0.0
    for s, e in segs:
        t0 += e - s
        bounds.append(int(round(t0 * FPS)))
    zl = cfg.get("zoom", [1.35, 1.7])

    # tài nguyên tĩnh
    bg = L.make_bg()
    fl = L.make_frame_layer_single() if single else L.make_frame_layer()
    base = bg.copy()
    L.blend_rgba(base, fl)
    mR = L.rr_mask(L.RC["w"], L.RC["h"], 34 if single else 30); mL = L.rr_mask(L.LC["w"], L.LC["h"], 22)
    avatar_path = cfg["avatar"]
    cover_ov = L.cover_overlay_auto(cfg, cfg["hook"], cfg.get("tag", "#Bùi Viết Cường"), avatar_path)
    cover_len = cfg.get("cover_len", 2.3)
    cap_groups = group_captions(ow)
    cap_cache = {}
    pops = list(cfg.get("pops", []))
    def src2out(ts):
        acc = 0.0
        for a, b in segs:
            if a - 0.01 <= ts <= b:
                return acc + ts - a
            acc += b - a
        return None
    for p in cfg.get("pops_src", []):
        o = src2out(p["src"])
        if o is not None:
            q = dict(p); q["t0"] = o; q["t1"] = o + p.get("dur", 2.0); pops.append(q)
    pop_imgs = [fit_w(L.render_text_rgba(p["lines"], size=p.get("size", 84), glow=L.GOLD, shadow=7), L.RC['w'] - 70) for p in pops]
    cta = cfg.get("cta", {})
    cta_img = None
    if cta:
        from PIL import Image, ImageDraw
        f1 = L.font(L.F_BLACK, 44); f2 = L.font(L.F_BOLD, 28)
        tw = int(ImageDraw.Draw(Image.new("RGBA", (5, 5))).textlength(cta["main"], font=f1)) + 90
        img = Image.new("RGBA", (max(tw, 620), 190), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, img.size[0] - 1, 84], 42, fill=L.GOLD + (255,))
        d.text((img.size[0] / 2, 43), cta["main"], font=f1, fill=(30, 20, 0, 255), anchor="mm")
        d.text((img.size[0] / 2, 134), cta["sub"], font=f2, fill=(255, 255, 255, 255), anchor="mm")
        cta_img = np.asarray(img)

    out_mp4 = os.path.join(work, "video_noaudio.mp4")
    enc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out_mp4], stdin=subprocess.PIPE)
    first = None
    seg_i = 0
    t_start = time.time()
    ZBASE = 0.0
    for fi in range(nfr):
        ok, src = cap.read()
        if not ok: break
        t = fi / FPS
        while seg_i + 1 < len(bounds) - 1 and fi >= bounds[seg_i + 1]:
            seg_i += 1
        z = zl[seg_i % 2]
        # nhịp phóng nhẹ đầu mỗi đoạn
        since = (fi - bounds[seg_i]) / FPS
        z = z * (1 + 0.10 * (1 - smooth(since / 0.35)))
        cx = float(fx[min(fi, len(fx) - 1)]); cy = float(fy[min(fi, len(fy) - 1)])
        # ---- cảnh thân: bố cục chia đôi
        frame = base.copy()
        right = crop_zoom(src, cx, cy, z, L.RC["w"], L.RC["h"])
        if not single:
            left = cv2.resize(src, (L.LC["w"], L.LC["h"]), interpolation=cv2.INTER_AREA)
            roiL = frame[L.LC["y"]:L.LC["y"] + L.LC["h"], L.LC["x"]:L.LC["x"] + L.LC["w"]]
            roiL[:] = (roiL * (1 - mL) + left * mL).astype(np.uint8)
        roiR = frame[L.RC["y"]:L.RC["y"] + L.RC["h"], L.RC["x"]:L.RC["x"] + L.RC["w"]]
        roiR[:] = (roiR * (1 - mR) + right * mR).astype(np.uint8)
        # huy hiệu AI trên thẻ phải
        L.blend_rgba(frame, BADGE, L.RC["x"] + 18, L.RC["y"] + 18)
        # phụ đề karaoke
        cur = None
        for gi, g in enumerate(cap_groups):
            if g[0]["s"] - 0.05 <= t <= g[-1]["e"] + 0.25:
                cur = (gi, g)
                if t <= g[-1]["e"] + 0.05: break
        if cur and t > cover_len - 0.1:
            gi, g = cur
            active = max(i for i, w in enumerate(g) if w["s"] - 0.03 <= t) if g[0]["s"] - 0.03 <= t else 0
            key = (gi, active)
            if key not in cap_cache:
                line = [(w["w"].upper(), L.GOLD_L if i == active else (255, 255, 255)) for i, w in enumerate(g)]
                cap_cache[key] = L.render_text_rgba([line], size=cfg.get("cap_size", 64), shadow=6, stroke=0, pad=30)
            ci = cap_cache[key]
            pop = ease_out_back((t - g[0]["s"]) / 0.16)
            ci2 = scale_rgba(fit_w(ci, L.RC['w'] - 56), 0.88 + 0.12 * pop)
            ch, cw = ci2.shape[:2]
            L.blend_rgba(frame, ci2, L.RC["x"] + L.RC["w"] // 2 - cw // 2, L.RC["y"] + int(L.RC["h"] * cfg.get("cap_y", 0.80)) - ch // 2)
        # chữ nhấn lớn
        for p, pi in zip(pops, pop_imgs):
            if p["t0"] <= t <= p["t1"]:
                a = ease_out_back((t - p["t0"]) / 0.28)
                fade = 1.0 if t < p["t1"] - 0.2 else (p["t1"] - t) / 0.2
                im = scale_rgba(pi, (0.6 + 0.4 * a) * (0.9 + 0.1 * fade))
                ch, cw = im.shape[:2]
                if fade < 1:
                    im = im.copy(); im[..., 3] = (im[..., 3] * fade).astype(np.uint8)
                L.blend_rgba(frame, im, L.RC["x"] + L.RC["w"] // 2 - cw // 2, L.RC["y"] + int(L.RC["h"] * p.get("y", 0.58)) - ch // 2)
        # CTA cuối video
        if cta_img is not None and t >= total - cta.get("dur", 4.5):
            a = ease_out_back((t - (total - cta.get("dur", 4.5))) / 0.35)
            im = scale_rgba(cta_img, 0.7 + 0.3 * a)
            ch, cw = im.shape[:2]
            L.blend_rgba(frame, im, W // 2 - cw // 2 + (0 if single else 170), L.RC["y"] + L.RC["h"] + (14 if single else 60))
        # ---- bìa kiểu snaptik ở đầu video, rồi chuyển vào bố cục chia đôi
        if t < cover_len + 0.35:
            cov = crop_zoom(src, cx, cy, cfg.get("cover_zoom", 1.25), W, H, face_y=0.30)
            L.blend_rgba(cov, cover_ov)
            if t <= cover_len:
                frame = cov
            else:
                a = smooth((t - cover_len) / 0.35)
                frame = cv2.addWeighted(cov, 1 - a, frame, a, 0)
        if first is None:
            first = frame.copy()
        enc.stdin.write(frame.tobytes())
        if fi % 300 == 0:
            print(f"  khung {fi}/{nfr} ({fi/FPS:.0f}s) {time.time()-t_start:.0f}s", flush=True)
    enc.stdin.close(); enc.wait()
    cap.release()
    cv2.imwrite(os.path.join(work, "thumb.jpg"), first, [cv2.IMWRITE_JPEG_QUALITY, 95])
    json.dump({"total": total, "cover_len": cover_len, "pops": pops}, open(os.path.join(work, "meta.json"), "w"))
    print(f"  dựng hình xong {time.time()-t_start:.0f}s", flush=True)


BADGE = None


def init_badge():
    global BADGE
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (110, 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 109, 49], 16, fill=L.GOLD + (255,))
    sx, sy = 28, 25
    star = [(sx, sy - 15), (sx + 4, sy - 4), (sx + 15, sy), (sx + 4, sy + 4), (sx, sy + 15), (sx - 4, sy + 4), (sx - 15, sy), (sx - 4, sy - 4)]
    d.polygon(star, fill=(30, 20, 0, 255))
    d.text((72, 26), "AI", font=L.font(L.F_BLACK, 28), fill=(30, 20, 0, 255), anchor="mm")
    BADGE = np.asarray(img)


# ------------------------------------------------------------------ âm thanh
def build_audio(cfg, work, total):
    voice = os.path.join(work, "voice.wav")
    proxy = os.path.join(work, "cut_proxy.mov")
    run([FF, "-y", "-v", "error", "-i", proxy, "-vn", "-ac", "1", "-ar", "48000", voice])
    # khử ồn RNNoise (mix 0.85) TRƯỚC khi nén và chuẩn âm
    dn = os.path.join(work, "voice_dn.wav")
    _den = os.path.expanduser("~/.claude/skills/edit-video-bvc-tu-a-z/scripts/denoise.py")
    if not os.path.exists(_den): _den = os.path.expanduser("~/.claude/skills/chuyen-gia-edit-HMT-tu-a-z/scripts/denoise.py")
    if os.path.exists(_den): run([sys.executable, _den, voice, "-o", dn, "--mix", "0.85"])   # RNNoise 0.85 (nếu máy có skill khử ồn)
    else: run([FF, "-y", "-v", "error", "-i", voice, "-af", "highpass=f=80,afftdn=nr=14:nf=-35", dn])  # dự phòng: ffmpeg afftdn (yếu hơn)
    voice = dn
    meta = json.load(open(os.path.join(work, "meta.json")))
    cl = meta["cover_len"]
    # SFX: whoosh lúc chuyển bìa -> bố cục, pop ở mỗi chữ nhấn, whoosh nhẹ ở CTA
    inputs = ["-i", voice, "-stream_loop", "-1", "-i", ASSETS + "bgm-inspired.mp3", "-i", ASSETS + "whoosh.mp3", "-i", ASSETS + "pop.mp3"]
    fcs = ["[0:a]highpass=f=80,agate=threshold=0.012:ratio=2.2:attack=8:release=220:range=0.35,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,alimiter=limit=0.9,asplit=2[v1][v2]",
           f"[1:a]atrim=0:{total + 1},volume=0.04[bgm0]",
           "[bgm0][v1]sidechaincompress=threshold=0.015:ratio=14:attack=15:release=500[bgm]"]
    labels = ["[v2]", "[bgm]"]
    k = 0
    sfx = [(cl - 0.05, 2, 0.55)] + [(p["t0"], 3, 0.5) for p in meta["pops"]]
    cta = cfg.get("cta")
    if cta:
        sfx.append((total - cta.get("dur", 4.5), 2, 0.4))
    for (ts, idx, vol) in sfx:
        ms = int(max(0, ts) * 1000)
        fcs.append(f"[{idx}:a]volume={vol},adelay={ms}|{ms}[s{k}]"); labels.append(f"[s{k}]"); k += 1
    fcs.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,atrim=0:{total}[mix]")
    mix = os.path.join(work, "mix.wav")
    run([FF, "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(fcs), "-map", "[mix]", "-ar", "48000", mix])
    # chuẩn âm 2 lượt -14 LUFS
    r = subprocess.run([FF, "-v", "info", "-i", mix, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    j = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    final = os.path.join(work, "final.wav")
    run([FF, "-y", "-v", "error", "-i", mix, "-af",
         f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true",
         "-ar", "48000", final])
    # đo lại và bù độ chênh về đúng -14 LUFS (đỉnh <= -1.5 dBTP)
    for _ in range(2):
        m = subprocess.run([FF, "-v", "info", "-i", final, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
        import re as _re
        li = float(_re.findall(r"I:\s+(-?[\d.]+) LUFS", m)[-1])
        if abs(li + 14) < 0.4:
            break
        adj = os.path.join(work, "final_adj.wav")
        run([FF, "-y", "-v", "error", "-i", final, "-af", f"volume={-14 - li:.2f}dB,alimiter=limit=0.84:level=false", "-ar", "48000", adj])
        os.replace(adj, final)
    return final


def mux(cfg, work):
    meta = json.load(open(os.path.join(work, "meta.json")))
    final = build_audio(cfg, work, meta["total"])
    out = cfg["out"]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run([FF, "-y", "-v", "error", "-i", os.path.join(work, "video_noaudio.mp4"), "-i", final, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", out])
    shutil.copy(os.path.join(work, "thumb.jpg"), os.path.splitext(out)[0] + "_anh-bia.jpg")
    print("  xong:", out, flush=True)


def _expand(o):
    if isinstance(o, str): return os.path.expanduser(o) if o.startswith("~") else o
    if isinstance(o, dict): return {k: _expand(v) for k, v in o.items()}
    if isinstance(o, list): return [_expand(v) for v in o]
    return o


if __name__ == "__main__":
    cfg = _expand(json.load(open(sys.argv[1])))
    init_badge()
    if "--cut-only" in sys.argv:
        cfg["cut_only"] = True
    prev = None
    if "--preview" in sys.argv:
        prev = int(sys.argv[sys.argv.index("--preview") + 1])
    render(cfg, preview=prev)
    if not cfg.get("cut_only") and not prev:
        mux(cfg, os.path.join(cfg["work"], cfg["name"]))
