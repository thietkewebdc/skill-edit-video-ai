---
name: video-auto-edit
description: Tự động edit video bằng ffmpeg + Whisper - montage du lịch/sự kiện/team building cắt theo beat nhạc từ cả thư mục footage, cắt khoảng lặng/từ đệm (jump cut), chọn đoạn hay làm Shorts/Reels/TikTok 9:16, phụ đề karaoke tiếng Việt, nhạc nền tự hạ khi có giọng nói, chuẩn hoá âm lượng, xuất nhiều tỉ lệ. Dùng skill này bất cứ khi nào người dùng muốn edit, cắt, dựng, làm short, thêm sub/phụ đề, cắt podcast/livestream thành clip, hoặc xử lý file video (.mp4 .mov .mkv) - kể cả khi họ chỉ nói "làm video này gọn lại", "cắt cho anh mấy clip", "làm video chuyến đi", "recap", "montage", "highlight", "auto edit", "edit video", "make shorts", "add subtitles".
---

# Video Auto Edit

Có 2 luồng:
- **Luồng Nói** (tutorial, podcast, talking head, phỏng vấn): các bước 1-7 bên dưới.
- **Luồng Montage** (du lịch, sự kiện, team building, nhiều clip ngắn, ít lời thoại): đọc `references/montage.md`.
Nếu người dùng đưa cả một thư mục nhiều clip → gần như chắc chắn là Luồng Montage.

Pipeline: **Probe → Transcribe → Lập EDL → Render → Phụ đề → Hoàn thiện → QA**.
Claude là người "đạo diễn": đọc transcript, quyết định giữ đoạn nào; các script lo phần cơ khí.

Mọi file làm việc để trong thư mục `work/` cạnh video gốc. Không bao giờ ghi đè file gốc.

## 0. Setup (lần đầu)
```bash
bash scripts/setup.sh
```
Cần: ffmpeg, Python 3.10+, `faster-whisper`. Font: Be Vietnam Pro (fallback Arial).

## 1. Probe
```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of json INPUT
```
Ghi nhớ: thời lượng, độ phân giải, có audio không. Không có audio → bỏ bước 2, dựng theo cảnh.

## 2. Transcribe
```bash
python scripts/transcribe.py INPUT --lang vi --model large-v3 --out work/
```
Ra `work/transcript.json` (có timestamp từng từ) và `work/transcript.txt` (dạng `[mm:ss.s] câu`) để đọc nhanh.
Máy yếu/không GPU: dùng `--model medium` hoặc `small`.

## 3. Lập EDL (bước quan trọng nhất - Claude tự làm)
EDL = danh sách đoạn cần giữ. Format chi tiết: `references/edl-format.md`.

Chọn chế độ theo yêu cầu:

**A. Jump cut (video nói, tutorial, talking head)** - tự động:
```bash
python scripts/suggest_cuts.py work/transcript.json --max-gap 0.45 --pad 0.08 --out work/edl.json
```
Script bỏ khoảng lặng dài và từ đệm (ờ, ừm, à, uh, um...). Sau đó Claude đọc lại transcript,
xoá thêm các câu nói lặp/nói hỏng (người nói nói lại cùng một ý → giữ lần cuối).

**B. Highlight / Shorts (podcast, livestream, video dài)** - Claude chọn:
1. Đọc `transcript.txt`, tìm 3-5 đoạn 20-60s đứng độc lập được, mỗi đoạn có:
   - **Hook** trong 3s đầu: câu gây tò mò, số liệu, phản biện, câu hỏi.
   - Một ý trọn vẹn, kết thúc gọn (không cắt giữa câu).
2. Cắt đúng ranh giới từ (lấy `start` từ đầu tiên, `end` từ cuối cùng + 0.15s).
3. Mỗi short một file EDL: `work/edl_short1.json`...
4. Trình bày danh sách đoạn chọn (tiêu đề đề xuất + hook + thời lượng) cho người dùng trước khi render nếu họ đang theo dõi; nếu họ bảo "làm hết đi" thì render luôn.

**C. Rough cut theo kịch bản** - người dùng đưa script/outline: khớp từng ý với transcript, giữ take tốt nhất.

## 4. Render EDL
```bash
python scripts/render_edl.py work/edl.json --out work/cut.mp4
```
Tự xử lý: cắt, nối, fade audio 20ms chống tiếng "bụp", reframe theo `aspect` trong EDL (9:16, 1:1, 16:9), crop theo `crop_x`.

## 5. Phụ đề
```bash
python scripts/make_subs.py work/transcript.json work/edl.json --style shorts --out work/subs.ass
```
- `--style shorts`: chữ to giữa màn hình, 2-3 từ/lần, highlight karaoke vàng gold, viền navy.
- `--style classic`: sub 1 dòng dưới đáy, cho video ngang dài.
- Sửa lỗi chính tả tiếng Việt trong transcript.json **trước** bước này (tên riêng, thương hiệu, thuật ngữ). Whisper hay sai tên riêng - hỏi người dùng danh sách từ khoá nếu có.
Chi tiết style: `references/styles.md`.

## 6. Hoàn thiện
```bash
python scripts/finish.py work/cut.mp4 --subs work/subs.ass --music nhac.mp3 --out OUTPUT.mp4
```
- Burn phụ đề, nhạc nền tự loop + tự hạ (ducking) khi có giọng nói.
- Chuẩn hoá loudness -14 LUFS (chuẩn YouTube/TikTok).
- Không có nhạc thì bỏ `--music`.

## 7. QA (bắt buộc trước khi báo xong)
```bash
python scripts/qa_check.py OUTPUT.mp4 --expect-aspect 9:16
```
Kiểm tra: thời lượng, độ phân giải, có audio, loudness trong khoảng -16..-12 LUFS, xuất 3 frame mẫu vào `work/qa_frames/`.
**Xem các frame mẫu** (view ảnh) để chắc phụ đề không tràn, không che mặt, crop không mất chủ thể. Lỗi → sửa → render lại.

## Báo cáo cho người dùng
Ngắn gọn: file output, thời lượng trước → sau, các đoạn đã cắt/chọn, những gì cần họ kiểm tra tay (tên riêng trong sub, đoạn crop mặt).

## Nguyên tắc
- Không cắt giữa từ. Luôn bám timestamp từ trong transcript.
- Short: dưới 60s, hook trong 3s đầu, đoạn đầu không có khoảng lặng.
- Ưu tiên re-encode `libx264 -crf 20 -preset medium`, audio AAC 192k, 30fps nếu nguồn lạ.
- Video > 30 phút: transcribe 1 lần, tái sử dụng transcript.json cho mọi EDL.
- Không tự thêm nhạc có bản quyền. Chỉ dùng file nhạc người dùng cung cấp.
