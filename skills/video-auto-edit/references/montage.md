# Luồng Montage (du lịch / sự kiện / team building)

Pipeline: **Index footage → Claude xem & gắn tag → Dò beat → Plan → Preview → Render → QA**.

## 1. Index footage
```bash
python scripts/index_footage.py FOOTAGE_FOLDER --work work --jobs 4
```
Ra `work/index.json` (mỗi clip: thời lượng, ngày giờ quay, độ sáng, độ mờ, chuyển động, âm lượng, `score` 0-100)
và `work/sheets/sheet_XX.jpg` (mỗi sheet 8 clip, mỗi clip 1 hàng 4 frame, đánh số `#id`).
Clip xếp theo thời gian quay (creation_time). 500 clip ≈ 63 sheet: xem hết được, không cần mở từng video.

## 2. Claude xem sheet và gắn tag (bước quan trọng nhất)
Xem **từng** sheet bằng công cụ xem ảnh, rồi ghi `work/tags.json`:
```json
{
  "12": {"day": 1, "place": "Bangkok", "tag": "street_food", "hero": true, "best": 4.5},
  "13": {"day": 1, "tag": "group_selfie"},
  "27": {"keep": false},
  "40": {"day": 2, "place": "Pattaya", "tag": "beach", "hero": true}
}
```
- `hero`: cảnh đẹp nhất/đắt nhất. Hero đầu tiên = shot mở màn. Nên có 5-10 hero mỗi 60s.
- `best`: giây đẹp nhất trong clip (ước lượng từ frame nào đẹp: frame 1-4 ứng với 12%, 37%, 62%, 87% thời lượng).
- `keep: false`: rung, quay nhầm, che ống kính, trùng lặp.
- `day`/`place`: suy từ ngày quay trong index.json + nội dung hình (biển hiệu, cảnh). Không chắc thì hỏi người dùng.
- Ưu tiên đa dạng: cảnh rộng (landscape) → cận (đồ ăn, chi tiết) → người (mặt cười, nhóm) xen kẽ.

## 3. Dò beat
```bash
python scripts/beats.py MUSIC.mp3 --out work/beats.json
```
Ra BPM, danh sách beat, năng lượng từng beat, các điểm `drops`. Nhạc do người dùng cung cấp (không tự lấy nhạc bản quyền).
Mẹo: đặt `--music-start` ở đoạn điệp khúc/drop nếu muốn clip ngắn vào thẳng đoạn sung.

## 4. Plan
```bash
python scripts/auto_plan.py --tags work/tags.json --target 60 --aspect 9:16 --grade warm --day-titles
```
Tự: chọn clip rải đều dòng thời gian, hero lên trước, đoạn nhạc mạnh cắt 2 beat/shot, đoạn nhẹ 4 beat/shot,
clip rung → bật chống rung, clip quá ngắn → slow-mo cho đủ.

**Sau đó Claude đọc và chỉnh `work/plan.json`**:
- Shot đầu: hero mạnh nhất, 4-8 beat.
- Ngay tại `drops`: đặt cảnh nhiều năng lượng (nhảy, té nước, pháo hoa, cả nhóm hét).
- Shot cuối: cảnh cả nhóm/hoàng hôn, 8 beat, `fade_out` lo phần kết.
- Có tiếng cười/câu nói hay (audio_db cao): tăng `orig_audio` hoặc để shot đó dài hơn.

Các trường mỗi shot: `clip`, `in` (giây bắt đầu), `beats`, `speed` (0.5 = slow-mo), `stabilize`, `fit` (`crop`|`blur`),
`crop_x` (0..1), `zoom` (true = zoom chậm điện ảnh), `title`.
Mức plan: `grade` = `warm` (nắng ấm, hợp Thái Lan) | `teal_orange` | `film` | `vivid` | `none` | đường dẫn file `.cube` LUT.

## 5. Preview rồi mới render thật
```bash
python scripts/build_montage.py work/plan.json --out work/preview.mp4 --preview   # 540p, nhanh
python scripts/build_montage.py work/plan.json --out FINAL.mp4
python scripts/qa_check.py FINAL.mp4 --expect-aspect 9:16
```
Xem frame QA; kiểm tra tiêu đề không che mặt, crop không mất người.

## Gợi ý bộ sản phẩm từ 1 chuyến đi
| Bản | Cấu hình |
|---|---|
| Recap hype | `--target 45-60`, nhạc 120-130 BPM, `grade warm`, hero dày |
| Mỗi ngày 1 clip | lọc tags theo `day`, chạy plan riêng từng ngày, `--target 30` |
| Bản cảm xúc | nhạc chậm 70-90 BPM (auto 4 beat/shot), `zoom: true`, `grade film` |
| YouTube dài | Luồng Nói cho các đoạn có thoại + montage làm intro/chuyển cảnh |

## So với repo có sẵn
CutClaw (github.com/treesan/cutclaw) làm cùng bài toán với footage hàng giờ, dùng multi-agent + LLM caption.
Nặng hơn, cần API/GPU. Skill này nhẹ, chạy local, Claude chỉ cần xem contact sheet. Footage quá lớn (>5 giờ) có thể cân nhắc CutClaw.
