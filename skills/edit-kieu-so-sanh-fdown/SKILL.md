---
name: edit-kieu-so-sanh-fdown
description: Dựng video dọc 9:16 từ video quay người nói (DJI/điện thoại) theo PHONG CÁCH SO SÁNH "VIDEO GỐC vs AI ĐÃ EDIT" kiểu FDown — nền tối có lưới, thẻ nhỏ "VIDEO GỐC" bên trái, nhãn VS, thẻ lớn viền vàng "AI ĐÃ EDIT" bên phải (phóng gần, phụ đề, chữ nhấn pop-up), ảnh bìa kiểu snaptik (logo tròn + ô tiêu đề xanh đậm) ở 2,4 giây đầu, lời kêu gọi "BÌNH LUẬN BÊN DƯỚI" cuối video, cắt khoảng lặng/câu vấp, khử ồn, âm −14 LUFS. DÙNG KHI người dùng nói "kiểu FDown", "video gốc vs AI đã edit", "so sánh trước và sau", "thẻ viền vàng", "nhìn thấy cả video gốc", "demo AI edit cho khách xem". KHÔNG dùng khi muốn toàn khung sạch/chuyên nghiệp không viền, không thẻ so sánh → dùng skill edit-kieu-toan-khung-chuyen-nghiep (đồng bộ cùng ảnh bìa, cùng nguyên tắc cắt, khác bố cục).
---

# Skill: Edit kiểu SO SÁNH FDown (video gốc vs AI đã edit)

*Phong cách "Dạng 1" của anh Bùi Viết Cường. Mẫu tham chiếu: `FDown…mp4` (bố cục) + `snaptik…mp4` (ảnh bìa).*

## Chọn skill nào cho đồng bộ
| Người dùng muốn | Skill |
|---|---|
| Thấy cả video gốc cạnh video đã edit, thẻ viền vàng, nền lưới, nhãn VS — để CHỨNG MINH "AI edit thế nào" | **skill này** |
| Video sạch toàn khung, không viền/nền/nhãn, chữ khối vàng + minh họa động kiểu chuyên gia | `edit-kieu-toan-khung-chuyen-nghiep` |
Cả hai: cùng ảnh bìa snaptik 2,4s đầu, cùng cách cắt, cùng khử ồn, cùng −14 LUFS, cùng lời kêu gọi. Không trộn hai kiểu trong một video. Không rõ → hỏi "so sánh video gốc (Dạng 1) hay toàn khung chuyên nghiệp (Dạng 2)?". Mặc định khi anh nói "chuyên nghiệp / bỏ viền / bỏ video gốc" = Dạng 2.

## Bố cục (khung 1080×1920)
- Nền tối + lưới mờ (`layout.make_bg`).
- Thẻ trái "VIDEO GỐC": 324×576 tại (30,567), viền trắng mảnh, hiện khung gốc không phóng, cùng mốc thời gian với thẻ phải (tức cũng nhảy theo các chỗ cắt).
- Nhãn "VS" tròn viền vàng giữa hai thẻ.
- Thẻ phải "AI ĐÃ EDIT": 657×1170 tại (393,270), viền vàng 6px + glow, huy hiệu "✦ AI" góc trên trái, phóng xen kẽ 1.35 / 1.7 theo từng đoạn cắt, bám mặt (tâm mượt), phụ đề karaoke 2–3 từ (trắng, từ đang nói vàng) ở 80% chiều cao thẻ, chữ nhấn pop-up (kèm glow vàng) ở 58%.
- Lời kêu gọi: viên thuốc vàng "BÌNH LUẬN BÊN DƯỚI" + dòng nhỏ trắng, dưới thẻ phải, 4,5s cuối.
- Ảnh bìa (frame 0 = thumbnail): toàn khung người nói + dải navy dưới đáy + logo/ảnh giảng viên tròn viền vàng góc trên trái + ô tiêu đề xanh đậm bo góc (thẻ tên "#Bùi Viết Cường", 2–3 dòng: trắng, dòng cuối vàng, gạch vàng dưới ô). 2,4s rồi hòa vào bố cục chính 0,35s.
- Nhạc nền rất nhỏ (0.04) + SFX whoosh/pop nhẹ ở chỗ chuyển và chữ nhấn.

## Quy trình
1. **Thăm dò**: `ffprobe`; DJI thường là HEVC 4K dọc 25fps. Nghe âm: video quay quán cà phê → bắt buộc khử ồn.
2. **Nhận giọng** (BẮT BUỘC dùng script này, đừng dùng mlx-whisper turbo — nó bịa "Hãy subscribe…", "bài hát…" trên tiếng ồn):
   `ffmpeg -i video -map 0:a:0 -ac 1 -ar 16000 a.wav` rồi `python3.12 scripts/asr3.py a.wav words.json` (faster-whisper large-v3 int8, chuẩn hóa âm, khối ≤12s ở chỗ ngừng, KHÔNG initial_prompt; chạy ~1× thời gian thực; mỗi lần chỉ 1 tiến trình ASR, máy 8GB sẽ swap).
3. **Đọc bản chữ** + đo khoảng lặng thật (năng lượng âm, ngưỡng ~30% giữa p10 và p90 dB): mốc từ của whisper lệch tới ~1s → cắt phải bám khoảng lặng, không bám mốc từ.
4. **Quyết định cắt** (`segs` = các khoảng giây NGUỒN): bỏ câu lặp/vấp/lan man/đoạn máy nghe không ra; chỗ ngừng >0.6s cắt (mối nối còn ~0.2s); đoạn ≥2s; đuôi video +0.5s; không đổi thứ tự. Mục tiêu 2–3 phút cho video dài; chốt bằng một câu kêu gọi.
5. **Sửa chữ phụ đề** theo chỉ số từ: `prep.apply(src_json, dst_json, drop=[...], sub={idx: "chữ đúng"})` (xem `mau/`). Chỉ sửa chỗ chắc chắn theo ngữ cảnh; chỗ đoán âm (tên công cụ…) phải báo anh duyệt; chỗ không nghe ra → bỏ chữ, đừng bịa. KHÔNG tự thêm con số/cam kết ngoài lời nói.
6. **Viết cfg** (`mau/cfg-mau.json`): `src`, `words`, `segs`, `hook` (3 dòng, rút từ chính lời anh nói), `cta`, `pops_src` (chữ nhấn: giây NGUỒN, `lines` 1–3 dòng, `size`, `dur`; không để hai pop chồng nhau; chữ dài tự co vừa thẻ).
7. **Dựng**: `PYTHONPATH=scripts python3.12 scripts/render.py cfg.json` → cắt (VideoToolbox) → proxy 1080×1920 → ghép → khử ồn RNNoise 0.85 + gate + nén → −14 LUFS → `.mp4` + `_anh-bia.jpg`. Sửa chỉ âm thanh: `scripts/remux.py cfg.json`.
8. **QA**: xem sheet khung hình (0s, các pop, cuối); `ebur128` ≈ −14 LUFS; chữ không tràn thẻ; không còn từ ảo; hỏi lại số liệu anh đã nói.
9. **Đăng**: nén <50MB (`-b:v` tính theo độ dài) rồi lên lịch qua DC Post (xem skill/ghi chú Postiz); tiêu đề/caption theo công thức hook (nỗi đau, so sánh lựa chọn, con số thật), bám đúng lời trong video.

## Bìa v2 chuẩn TikTok (cập nhật 26–28/10/2026, theo ảnh mẫu của anh Cường)
Bìa 2,4s đầu giờ dùng `scripts/cover_v2.py` (cùng thiết kế với giai đoạn C của skill `edit-video-bvc-tu-a-z`): logo tròn viền vàng góc trên trái, thẻ tên dạng tab, ô tiêu đề navy bo góc ở 55–74% chiều cao với **viền vàng phát sáng cạnh dưới + cạnh phải**, hook 3 dòng (2 trắng + dòng cuối VÀNG to hơn), hoa văn mờ theo chủ đề (`$`, đồng hồ, biểu đồ), dải navy đậm dần từ ~64% xuống đáy. Vùng an toàn TikTok: 0–10% trên cùng, cột icon bên phải, 20% dưới cùng để trống.
- cfg: `"cover_style": "v2"` (mặc định) hoặc `"v1"` (bìa Snaptik cũ); `"cover_mode": "A"|"B"` (B = chữ số vàng); `"cover_icon": "auto"|"dollar"|"clock"|"chart"|"none"`; `"cover_zoom"` phóng khung mặt (video ngang tự đặt 1.55).
- Hook theo công thức **con số thật + nghịch lý + câu hỏi**, mỗi dòng ≤ 22 ký tự; chỉ dùng con số CÓ trong lời nói.
- Muốn thumbnail riêng (đăng kèm, YouTube 16:9, Facebook 1:1) → `edit-video-bvc-tu-a-z/scripts/thumb.py` (giai đoạn C).

## Nguồn quay NGANG (bẫy 28/10/2026)
Skill thiết kế cho video **quay dọc** (DJI 4K dọc). Video quay ngang (VD 848×464) cắt thẳng sang 9:16 rồi phóng 1.3–1.65× sẽ **mất đỉnh đầu, mặt lệch, rất mờ, minh họa đè người** (anh Cường bắt lỗi trên IMG_6294.MP4).
- Studio tự xử lý: nguồn rộng hơn cao ≥ 10% → dựng **khung dọc 1080×1920, video ngang đặt giữa, nền là chính video đó làm mờ** (`boxblur`), `zoom` hạ còn `[1.0, 1.1]`, minh họa động đặt `y: 0.2` (dải mờ phía trên), phụ đề ở dải dưới, bìa `cover_zoom: 1.55`. Đánh đổi: video chỉ chiếm ~1/3 chiều cao khung; chữ nhấn 2 dòng có thể chạm mép dưới video.
- Chạy tay: tự dựng canvas bằng ffmpeg (`split` → nền `scale=1080:1920:force_original_aspect_ratio=increase,crop,boxblur=28:4,eq=brightness=-0.14` + `scale=1080:-2` overlay giữa) rồi đưa file đó vào `cfg.src`.
- Muốn lấp đầy khung (cắt ngang vừa phải): chưa có chế độ này; ưu tiên **quay dọc ≥ 1080p**.
- Nguồn < 720p: luôn báo anh trước, ảnh sẽ mờ.

## Kiểm tra lời nói TRƯỚC khi dựng (bẫy 26/10/2026)
Video không có lời (mic không thu, tiếng quá nhỏ, nhạc nền, ngôn ngữ khác) → Whisper **bịa** câu "Hãy subscribe cho kênh…/La La School/Ghiền Mì Gõ/để không bỏ lỡ…". Studio chặn khi: có câu ảo, hoặc < 25 từ thật, hoặc < 0.4 từ/giây, hoặc AI chỉ giữ < 8s. Chạy tay: đọc `words.json`; thấy câu kêu gọi đăng ký kênh ở đoạn không ai nói → **không dựng**, báo anh kiểm tra mic. Không bao giờ lấy câu ảo làm hook.
- Clip quá ngắn (< ~15s nói) không qua được ngưỡng; dùng video có nhiều lời hơn để thử.
- Máy M1 8GB: Whisper phải `compute_type="int8"` (`float32` ~6GB làm treo máy, swap đầy). `video-auto-edit/scripts/transcribe.py` đã vá. Mỗi lần chỉ 1 tiến trình ASR; ổ chỉ còn ~4GB nên dọn thư mục làm việc sau mỗi video.

## Bẫy đã gặp
- Ổ đĩa đầy → ffmpeg "No space left", file cụt: dọn thư mục làm việc sau mỗi video (proxy+thẻ thô ~1GB/video).
- `pkill -f` theo chuỗi có trong lệnh Monitor sẽ giết luôn Monitor.
- Log cũ báo "xong" nhầm: kiểm bằng giờ file.
- Lia khung/nhấp nháy phóng gây chóng mặt (anh đã chê ở Dạng 2): ở Dạng 1 khung phóng bám mặt đã làm mượt; nếu video có người nhích nhiều, hạ độ nhạy hoặc dùng tâm cố định như Dạng 2.
- Máy: chạy được trên macOS (đã thử M1 8GB). Cần Python 3.10+ (cv2, numpy, PIL, faster-whisper), ffmpeg trên PATH. **Đã đóng gói đủ**: font Montserrat (OFL) trong `fonts/`, SFX + nhạc nền tự tổng hợp trong `assets/` (thay bằng file của bạn nếu muốn). Khử ồn: dùng RNNoise nếu máy có skill `edit-video-bvc-tu-a-z`/`chuyen-gia-edit-HMT-tu-a-z`, không có thì tự dùng ffmpeg `afftdn` (yếu hơn).
