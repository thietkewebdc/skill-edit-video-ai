"""Bố cục 'VIDEO GỐC vs AI ĐÃ EDIT' (kiểu FDown) + ảnh bìa kiểu snaptik. Khung 1080x1920."""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts") + os.sep   # Montserrat (OFL) đi kèm skill
F_BLACK, F_BOLD = FD + "Montserrat-Black.ttf", FD + "Montserrat-Bold.ttf"
GOLD = (255, 190, 40)
GOLD_L = (255, 214, 90)
NAVY = (10, 22, 66)

# vị trí thẻ (đo theo video mẫu FDown, nhân 3)
LC = dict(x=30, y=567, w=324, h=576)       # thẻ trái: video gốc
RC = dict(x=393, y=270, w=657, h=1170)     # thẻ phải: AI đã edit
RC2 = dict(x=120, y=210, w=840, h=1494)    # dạng 1 thẻ (chỉ video edit)


def font(path, size):
    return ImageFont.truetype(path, size)


def rr_mask(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], r * 2, fill=255)
    return np.asarray(m.resize((w, h), Image.LANCZOS), dtype=np.float32)[..., None] / 255.0


def make_bg():
    """nền tối có lưới mờ + vầng sáng ấm nhẹ sau thẻ phải"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32)
    base[:] = (14, 14, 16)
    # vầng sáng vàng rất nhẹ quanh thẻ phải
    d = np.sqrt(((xx - 720) / 700) ** 2 + ((yy - 860) / 1000) ** 2)
    glow = np.clip(1 - d, 0, 1) ** 2
    base += glow[..., None] * np.array([26, 18, 4], np.float32)
    # lưới
    step = 54
    grid = ((xx % step) < 1.6) | ((yy % step) < 1.6)
    base += grid[..., None] * 7
    # tối dần ở mép
    vig = np.clip(1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2), 0.55, 1)
    base *= vig[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)[..., ::-1].copy()   # BGR


def text_w(draw, s, f, spacing=0):
    return draw.textlength(s, font=f) + spacing * max(0, len(s) - 1)


def draw_glow_text(img, xy_center, s, f, fill, glow, blur=14, anchor="mm"):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy_center, s, font=f, fill=glow + (255,), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)
    d2 = ImageDraw.Draw(img)
    d2.text((xy_center[0] + 3, xy_center[1] + 4), s, font=f, fill=(0, 0, 0, 220), anchor=anchor)
    d2.text(xy_center, s, font=f, fill=fill + (255,), anchor=anchor)


def make_frame_layer(label_left="VIDEO GỐC", label_right="AI ĐÃ EDIT", badge="✦ AI"):
    """lớp RGBA tĩnh: viền thẻ, nhãn, VS, huy hiệu AI (đặt SAU khi dán video vào thẻ)"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # viền thẻ trái: trắng mảnh
    d.rounded_rectangle([LC["x"] - 2, LC["y"] - 2, LC["x"] + LC["w"] + 1, LC["y"] + LC["h"] + 1], 24, outline=(235, 235, 235, 255), width=4)
    # viền thẻ phải: vàng + glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle([RC["x"] - 4, RC["y"] - 4, RC["x"] + RC["w"] + 3, RC["y"] + RC["h"] + 3], 34, outline=GOLD + (255,), width=12)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([RC["x"] - 3, RC["y"] - 3, RC["x"] + RC["w"] + 2, RC["y"] + RC["h"] + 2], 32, outline=GOLD + (255,), width=6)
    # nhãn
    fl = font(F_BLACK, 40)
    d.text((LC["x"] + LC["w"] / 2 + 2, LC["y"] - 44 + 3), label_left, font=fl, fill=(0, 0, 0, 200), anchor="mm")
    d.text((LC["x"] + LC["w"] / 2, LC["y"] - 44), label_left, font=fl, fill=(255, 255, 255, 255), anchor="mm")
    fr = font(F_BLACK, 76)
    draw_glow_text(img, (RC["x"] + RC["w"] / 2, RC["y"] - 62), label_right, fr, GOLD_L, GOLD, blur=16)
    # VS
    cx, cy = LC["x"] + LC["w"] + 19, LC["y"] + LC["h"] // 2
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(20, 18, 12, 255), outline=GOLD + (255,), width=5)
    d.text((cx, cy + 1), "VS", font=font(F_BLACK, 26), fill=GOLD_L + (255,), anchor="mm")
    # huy hiệu AI (góc trên-trái thẻ phải)
    bx, by = RC["x"] + 18, RC["y"] + 18
    d.rounded_rectangle([bx, by, bx + 110, by + 50], 16, fill=GOLD + (255,))
    sx, sy = bx + 28, by + 25
    star = [(sx, sy - 15), (sx + 4, sy - 4), (sx + 15, sy), (sx + 4, sy + 4), (sx, sy + 15), (sx - 4, sy + 4), (sx - 15, sy), (sx - 4, sy - 4)]
    d.polygon(star, fill=(30, 20, 0, 255))
    d.text((bx + 72, by + 26), "AI", font=font(F_BLACK, 28), fill=(30, 20, 0, 255), anchor="mm")
    return np.asarray(img)


def make_frame_layer_single():
    """lớp tĩnh cho dạng chỉ-video-edit: một thẻ lớn viền vàng + nhãn AI ĐÃ EDIT"""
    R = RC2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([R["x"] - 4, R["y"] - 4, R["x"] + R["w"] + 3, R["y"] + R["h"] + 3], 38, outline=GOLD + (255,), width=14)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([R["x"] - 3, R["y"] - 3, R["x"] + R["w"] + 2, R["y"] + R["h"] + 2], 36, outline=GOLD + (255,), width=7)
    draw_glow_text(img, (R["x"] + R["w"] / 2, R["y"] - 70), "AI ĐÃ EDIT", font(F_BLACK, 84), GOLD_L, GOLD, blur=18)
    return np.asarray(img)


def blend_rgba(dst_bgr, rgba, x=0, y=0):
    """dán lớp RGBA (RGB thứ tự R,G,B) lên ảnh BGR tại (x,y), cắt theo biên"""
    h, w = rgba.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst_bgr.shape[1]), min(y + h, dst_bgr.shape[0])
    if x0 >= x1 or y0 >= y1:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = src[..., 3:4].astype(np.float32) / 255.0
    rgb = src[..., :3][..., ::-1].astype(np.float32)
    roi = dst_bgr[y0:y1, x0:x1].astype(np.float32)
    dst_bgr[y0:y1, x0:x1] = (roi * (1 - a) + rgb * a).astype(np.uint8)


def render_text_rgba(lines, size=64, colors=None, stroke=0, shadow=6, pad=40, font_path=F_BLACK, line_gap=1.08, glow=None):
    """lines: list[str] (hoặc list[list[(từ, màu)]]) -> ảnh RGBA căn giữa, chữ khối + bóng đen đổ chéo"""
    f = font(font_path, size)
    rows = []
    for ln in lines:
        segs = ln if isinstance(ln, list) else [(ln, (255, 255, 255))]
        rows.append(segs)
    tmp = Image.new("RGBA", (10, 10))
    td = ImageDraw.Draw(tmp)
    widths = []
    for segs in rows:
        wsum = 0
        for i, (t, c) in enumerate(segs):
            wsum += td.textlength(t, font=f) + (td.textlength(" ", font=f) if i < len(segs) - 1 else 0)
        widths.append(wsum)
    lh = int(size * line_gap)
    Wt, Ht = int(max(widths)) + pad * 2 + shadow, lh * len(rows) + pad * 2 + shadow
    img = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0))
    if glow is not None:
        g = Image.new("RGBA", (Wt, Ht), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        for r, segs in enumerate(rows):
            x = (Wt - widths[r]) / 2
            for t, c in segs:
                gd.text((x, pad + r * lh), t, font=f, fill=glow + (255,))
                x += td.textlength(t + " ", font=f)
        g = g.filter(ImageFilter.GaussianBlur(14))
        img.alpha_composite(g)
    d = ImageDraw.Draw(img)
    for r, segs in enumerate(rows):
        x = (Wt - widths[r]) / 2
        for t, c in segs:
            if shadow:
                d.text((x + shadow, pad + r * lh + shadow), t, font=f, fill=(0, 0, 0, 230), stroke_width=stroke, stroke_fill=(0, 0, 0, 230))
            if stroke:
                d.text((x, pad + r * lh), t, font=f, fill=(0, 0, 0, 255), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
            d.text((x, pad + r * lh), t, font=f, fill=c + (255,))
            x += td.textlength(t + " ", font=f)
    return np.asarray(img)


# ---------- ẢNH BÌA kiểu snaptik ----------
def avatar_circle(path, d=190):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    s = min(w, h * 0.72)
    # lấy phần đầu-vai: bám phía trên
    box = (int((w - s) / 2), 0, int((w + s) / 2), int(s))
    im = im.crop(box).resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (d + 14, d + 14), (0, 0, 0, 0))
    ring = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, d + 13, d + 13], fill=GOLD + (255,))
    ImageDraw.Draw(ring).ellipse([6, 6, d + 7, d + 7], fill=NAVY + (255,))
    out.alpha_composite(ring)
    m = Image.new("L", (d, d), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=255)
    out.paste(im, (7, 7), m)
    return np.asarray(out)


def cover_overlay(hook_lines, tag="#Bùi Viết Cường", avatar_path=None, name_under="BÙI VIẾT CƯỜNG"):
    """lớp phủ ảnh bìa: dải tối navy dưới đáy + avatar tròn trái-trên + ô tiêu đề (thẻ tên + 2-3 dòng chữ) — RGBA 1080x1920"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # dải tối dưới đáy
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a = np.clip((yy - 0.52) / 0.30, 0, 1) ** 1.3
    grad = np.zeros((H, W, 4), np.uint8)
    grad[..., 0], grad[..., 1], grad[..., 2] = 6, 14, 42
    grad[..., 3] = (a * 245).astype(np.uint8)[:, 0][:, None].repeat(W, 1)
    img.alpha_composite(Image.fromarray(grad, "RGBA"))
    d = ImageDraw.Draw(img)
    # avatar
    if avatar_path:
        av = Image.fromarray(avatar_circle(avatar_path), "RGBA")
        img.alpha_composite(av, (80, 150))
    # ô tiêu đề
    n = len(hook_lines)
    f_tag = font(F_BOLD, 34)
    cw = 840
    size = 66
    while size > 40 and max(d.textlength(t, font=font(F_BLACK, size)) for t in hook_lines) > cw - 70:
        size -= 2
    f_big = font(F_BLACK, size)
    lh = 84
    ch = 70 + lh * n
    cx0 = (W - cw) // 2
    cy0 = 1130
    # thẻ tên
    tw = int(d.textlength(tag, font=f_tag)) + 56
    d.rounded_rectangle([cx0, cy0 - 56, cx0 + tw, cy0 + 12], 14, fill=(8, 18, 56, 255))
    d.text((cx0 + 28, cy0 - 22), tag, font=f_tag, fill=(240, 240, 255, 255), anchor="lm")
    d.line([cx0 + 28, cy0 - 2, cx0 + tw - 28, cy0 - 2], fill=GOLD + (255,), width=3)
    # thân ô
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([cx0 + 6, cy0 + 10, cx0 + cw + 6, cy0 + ch + 10], 26, fill=(0, 0, 0, 160))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], 26, fill=(10, 30, 100, 255), outline=(40, 90, 200, 255), width=3)
    # đường vàng đáy ô
    d.rounded_rectangle([cx0 + 120, cy0 + ch - 8, cx0 + cw - 120, cy0 + ch + 2], 5, fill=GOLD + (255,))
    for i, ln in enumerate(hook_lines):
        col = (255, 255, 255) if i < n - 1 or n == 1 else (255, 214, 40)
        d.text((cx0 + cw / 2, cy0 + 36 + lh * i + lh / 2), ln, font=f_big, fill=col + (255,), anchor="mm")
    return np.asarray(img)


def cover_overlay_v2(hook_lines, tag="#Bùi Viết Cường", avatar_path=None, name_under=None, mode="A", icon="auto"):
    """Bìa kiểu TikTok chuẩn v2 (ảnh mẫu 26/10/2026): xem cover_v2.py. Cùng chữ ký với cover_overlay."""
    import cover_v2
    return cover_v2.cover_overlay_v2(hook_lines, tag=tag, avatar_path=avatar_path, mode=mode, icon=icon)

def cover_overlay_auto(cfg, hook_lines, tag, avatar_path):
    """cfg["cover_style"]: "v2" (mặc định) hoặc "v1" (bìa Snaptik cũ). cfg["cover_mode"]: "A" | "B"; cfg["cover_icon"]."""
    if cfg.get("cover_style", "v2") == "v1": return cover_overlay(hook_lines, tag=tag, avatar_path=avatar_path)
    return cover_overlay_v2(hook_lines, tag=tag, avatar_path=avatar_path, mode=cfg.get("cover_mode", "A"), icon=cfg.get("cover_icon", "auto"))
