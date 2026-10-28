# EDL format (edl.json)

```json
{
  "source": "D:/video/podcast_ep12.mp4",
  "aspect": "9:16",
  "crop_x": "center",
  "title": "3 lỗi SEO khiến web mất top",
  "segments": [
    {"start": 754.20, "end": 761.85, "note": "hook: câu hỏi gây tò mò"},
    {"start": 790.10, "end": 832.40, "note": "nội dung chính"}
  ]
}
```

| Trường | Giá trị |
|---|---|
| `source` | Đường dẫn video gốc (bắt buộc) |
| `aspect` | `9:16` (Shorts/Reels/TikTok), `1:1`, `4:5` (feed FB/IG), `16:9` (YouTube), `source` (giữ nguyên) |
| `crop_x` | `center`; số `0..1` = vị trí ngang của người nói (0 = sát trái, 1 = sát phải); `blur` = giữ nguyên khung, nền mờ (dùng cho quay màn hình, slide) |
| `segments` | Theo thứ tự phát. Được phép đảo thứ tự (đưa câu hook lên đầu) |

## Mẹo chọn đoạn
- Hook có thể lấy từ cuối clip đưa lên đầu (cold open), rồi mới vào nội dung.
- Mỗi đoạn nên bắt đầu ở từ đầu câu, kết thúc sau từ cuối + 0.1-0.2s.
- Tìm crop_x: trích 1 frame (`ffmpeg -ss 10 -i IN -frames:v 1 f.jpg`), xem người nói nằm đâu.
- Quay màn hình/tutorial → `blur` thay vì crop, tránh mất chữ.
