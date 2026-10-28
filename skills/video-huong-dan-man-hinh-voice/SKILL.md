---
name: video-huong-dan-man-hinh-voice
description: Làm VIDEO HƯỚNG DẪN CÔNG NGHỆ/AI bán tự động cho kênh Bùi Viết Cường (Thiết Kế Web DC) — quay màn hình + lời đọc giọng CLONE Bùi Viết Cường (VieNeu/OmniVoice/VoiceStudio) tự canh khớp với thao tác, sub thanh xanh gọn ở đáy, vòng tròn mặt viền vàng góc dưới (chạy song song), 20s đầu người thật cắt gọn, màn nhắc lời (teleprompter) cho các đoạn người thật, quảng cáo khóa E-Learning ở giữa. Dùng khi người dùng nói "video hướng dẫn AI", "quay màn hình rồi lồng voice clone", "ghép voice vào màn hình", "vòng tròn mặt viền vàng", "màn hình nhắc lời", "kịch bản lên video hướng dẫn kiểu Higgsfield", "cắt 20s đầu", hoặc gọi /video-huong-dan-man-hinh-voice. Muốn phủ chữ khối vàng/xanh, SFX → thêm skill chuyen-gia-edit-HMT-video-chia-se. Cắt short dọc → chuyen-gia-edit-HMT-tu-a-z (shorts.py).
---

# Video hướng dẫn: màn hình + voice clone + mặt vòng tròn vàng

*Quy trình chốt với anh Cường ngày 23/10/2026, rút từ video mẫu "Master Higgsfield AI in 20 Minutes" (Metics Media).*

Mục tiêu kênh: video hướng dẫn tiếng Việt về AI và công nghệ, chi tiết từng bước, kéo người xem về **khóa E-Learning**. Anh chỉ quay người thật 3 đoạn ngắn; phần thân là màn hình + giọng clone, vẫn có mặt anh trong vòng tròn để đỡ "AI".

## Khuôn video (10 phút)
| Phần | Giờ | Ai nói | Hình |
|---|---|---|---|
| Hook + hứa kết quả (20s) | 0:00 | **Anh thật** | Người thật, cắt gọn bằng `cut_opening.py` |
| Giới thiệu 3 ý chính | 0:20 | Giọng clone | Màn hình / thành phẩm |
| Mục 1, 2 | ~1:00–5:00 | Clone | Màn hình + sub + vòng tròn mặt |
| **Quảng cáo khóa E-Learning (15–20s)** | ~5:00 | **Anh thật** | Người thật |
| Mục 3 + dự án tổng hợp | 5:15–9:30 | Clone | Màn hình + sub + vòng tròn |
| Chốt + kêu gọi đăng ký (15s) | cuối | **Anh thật** | Người thật |

**Công thức mỗi mục** (rút từ video mẫu): một câu nói đích → thẻ chương → thao tác từng bước (đọc đúng theo hành động, trái sang phải) → chỗ AI chờ thì tua nhanh → xem kết quả, tải về → câu nối sang mục sau. Link/CTA nhắc 2 lần (đầu, cuối). Chi tiết phân tích mẫu: [references/phan-tich-video-mau.md](references/phan-tich-video-mau.md).

## Quy trình thân bài (màn hình + voice)
Thư mục làm việc `<tên>__edit/`. `S` = `~/.claude/skills/video-huong-dan-man-hinh-voice/scripts`.

1. **Quay màn hình** (anh quay không nói, OBS/Openscreen, 1080p60). **Chừa trống ~100px đáy khung** vì thanh sub nằm đó và sẽ che thanh điều khiển sát đáy của giao diện. Tốt nhất quay mặt cùng lúc (xem mục vòng tròn).
2. **Chia cảnh** theo từng thao tác, viết `scenes.json`:
   `[{"id":1,"t0":197.9,"t1":215.5,"text":"Bắt đầu nào. Trên thanh menu, bạn rê chuột vào Image..."}]` (`t0,t1` = đoạn màn hình nguồn, giây).
   **Luật viết lời: ~3 chữ/giây của đoạn màn hình** (cảnh 17s → ~50 chữ). Viết ngắn thì màn hình bị tua nhanh nghe vội. Tên nút/menu giữ nguyên tiếng Anh. Xưng "mình"/"các bạn".
3. **Tạo giọng** (mỗi cảnh một wav): `scripts/tts_batch.py` — VieNeu nhanh (~75s cho 9 câu), OmniVoice hay hơn nhưng chậm ~3x; hoặc VoiceStudio xuất `wav/s<id>.wav` cùng tên. Lệnh gọi ghi ở đầu file.
4. **Canh khớp**: `python3 $S/fit_voice.py --src man_hinh.mp4 --out ghep.mp4` → tự tua (≤1.3x) hoặc làm chậm (≥0.85x) rồi đứng hình; in `work/bao_cao.txt`: cảnh nào "thừa N giây im lặng → viết thêm ~M chữ". **Viết thêm lời cho các cảnh đó rồi chạy lại** (`tts_batch.py --only 8`).
5. **Sub**: `python3 $S/make_sub.py --in ghep.mp4 --out co_sub.mp4` — thanh xanh `#0B4C73` rộng 80% khung, cao 92px, viền xanh sáng mép trên, chữ trắng Be Vietnam Pro 44, video giữ nguyên toàn khung (KHÔNG làm nền xanh phủ kín — anh đã bác).
6. **Vòng tròn mặt** (mục dưới) rồi phủ chữ khối/SFX nếu muốn (skill `chuyen-gia-edit-HMT-video-chia-se`), chuẩn âm −14 LUFS.

## Vòng tròn mặt viền vàng
Ý anh: "video dưới" là cảnh **anh đang làm đúng việc đang hướng dẫn** — ngồi ngay ngắn gõ phím, rê chuột, nhìn màn hình; **không** dùng đoạn vung tay múa chân. Viền tròn vàng `#F4C80F` (không dùng khung vuông viền đỏ của đối thủ), góc dưới phải trên thanh sub.
1. `python3 $S/facecam_pip.py sheet mat.mp4 sheet.png` → mở ảnh (mốc giờ mỗi 4s), ghi các đoạn "ngồi làm việc", loại đoạn vung tay/với tay bấm máy. (`suggest` chỉ là gợi ý, không đáng tin hoàn toàn — luôn kiểm bằng sheet.)
2. `python3 $S/facecam_pip.py render --main co_sub.mp4 --face mat.mp4 --windows "4-26,38-62,76-84" --out ra.mp4` → các đoạn nối chuyển mờ 0.4s, tự lặp nếu thiếu, tiếng mặt tắt.
3. Chỉnh khung mặt bằng `--crop W:H:X:Y` (mặt nằm ở ⅓ trên của vòng), `--size`, `--x/--y`.
Lưu ý quay: camera ngang tầm mắt, mặt giữa khung, chừa khoảng trên đầu, **1080p trở lên** (3 file thử chỉ 848×464 nên mặt hơi mờ), quay mặt và màn hình cùng lúc, vỗ tay một cái lúc bắt đầu để đồng bộ.

## 3 đoạn người thật
- **Màn nhắc lời**: mở `assets/nhac-loi.html` (Chrome/Safari, toàn màn hình, đặt sát ống kính). Truyền lời/thời lượng qua đường dẫn: `nhac-loi.html?d=20&t=<lời đã mã hóa URL>`, hoặc bấm **E** sửa lời. Space chạy (đếm 3-2-1), R về đầu, M lật gương, +/− cỡ chữ, ±1s thời lượng; từ đang đọc vàng, nhịp báo chữ/giây (vừa 2.2–3.2). Bấm quay camera trước rồi mới Space; vỗ tay một cái.
- **20s đầu (mẫu đã dùng)**: *"Bạn chưa từng dùng AI để tạo ảnh hay video? Không sao cả. Chỉ sau video này, bạn sẽ tự làm được những thứ như đang thấy trên màn hình, từ ảnh sản phẩm, video quảng cáo cho đến giọng đọc. Mình là Cường, và mình sẽ chỉ từng bước một, để ai xem cũng làm theo được."* (58 chữ, 2.9 chữ/giây). Cấu trúc hook: câu hỏi chạm nỗi lo → gỡ rào cản → hứa kết quả cụ thể → tên → cam kết. Quảng cáo giữa và chốt cuối viết cùng kiểu; quảng cáo = khóa E-Learning Mastery.
- **Cắt gọn** bỏ im lặng/vấp/lan man: `python3 $S/cut_opening.py words mo-dau.mp4 work` (in chữ@mốc) → chọn đoạn giữ, ghi `ranges.json` `[[5.96,9.98],[10.62,13.57],...]` → `python3 $S/cut_opening.py render mo-dau.mp4 work ranges.json -o mo-dau-20s.mp4`. Mép tự dời vào khoảng lặng, zoom xen kẽ 100%/115%, chuẩn âm ≈ −14 LUFS. **Bắt buộc nghe lại** (`words` trên file ra): chữ kế dính ở mép (lần thử có "trên", "view", "được" lọt) → lùi mép 0.05–0.15s, đặt mép vào chỗ im lặng; mối nối KHÔNG có im lặng thì giữ nguyên, đừng cắt giữa tiếng. Lời nói vấp nhưng cần giữ đuôi 0.5s sau chữ cuối.

## Bẫy đã gặp
- VieNeu/OmniVoice chạy trong venv riêng (đường dẫn đầu `tts_batch.py`); ASR dùng `~/.claude/hmt-asr/venv` (mlx-whisper). Whisper chạy trên đoạn không tiếng hay ra chữ ảo ("Hãy subscribe cho kênh…") — video chỉ có cảnh ngồi làm việc thì đừng tin transcript.
- `ffmpeg concat` báo lỗi SAR khác nhau khi crop: đã thêm `setsar=1`.
- `loudnorm` một lượt ra ≈ −15.4 LUFS; script bù +1.3 dB + limiter (đỉnh ≈ −0.8 dB).
- Nguồn có dấu cách cuối tên thư mục (`Video Gốc `) và ký tự tổ hợp: dùng glob `Video*` thay vì gõ tên.
- Giọng clone ngắn hơn lời ước → luôn đọc `bao_cao.txt` sau bước 4.

## Tham chiếu
- [references/phan-tich-video-mau.md](references/phan-tich-video-mau.md) — phân tích video mẫu.
- Bản chạy thử đủ bước: `~/Documents/code/thu-nghiem-voice-man-hinh/` (scenes.json, wav, sub, demo) và `~/Documents/code/video-mo-dau-20s/`.
