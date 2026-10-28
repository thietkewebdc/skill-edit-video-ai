# Bộ Skill Edit Video bằng AI — Thiết Kế Web DC

Phát triển bởi **Bùi Viết Cường** (Thiết Kế Web DC). Các skill chạy trong **Claude Code**, xử lý video **ngay trên máy bạn** (ffmpeg + Whisper), không tải video lên đâu cả.

## Gồm những skill nào
| Skill | Làm gì | Gọi bằng |
|---|---|---|
| `edit-kieu-so-sanh-fdown` | Video dọc 9:16 từ video người nói: thẻ **VIDEO GỐC** cạnh thẻ **AI ĐÃ EDIT** viền vàng, bìa kiểu TikTok, phụ đề karaoke, chữ nhấn, khử ồn, −14 LUFS | `/edit-kieu-so-sanh-fdown` |
| `video-auto-edit` | Cắt khoảng lặng/từ đệm, chọn đoạn hay làm Shorts/Reels/TikTok, phụ đề karaoke tiếng Việt, montage theo nhạc | `/video-auto-edit` |
| `video-huong-dan-man-hinh-voice` | Video hướng dẫn: quay màn hình + giọng đọc clone + sub thanh xanh + vòng tròn mặt vàng | `/video-huong-dan-man-hinh-voice` |
| `viral-reel-vn` | Reel viral kiểu FDown: hook, phụ đề karaoke, nhãn ❌✅, bokeh | `/viral-reel-vn` |

## Cài đặt (macOS, 2 phút)
```bash
git clone https://github.com/thietkewebdc/skill-edit-video-ai.git
cd skill-edit-video-ai
./install.sh              # cài tất cả; hoặc ./install.sh video-auto-edit
```
Cần có: **Claude Code**, **ffmpeg**, **Python 3.10+** và `pip install numpy opencv-python pillow faster-whisper`.
Windows/Linux: chưa kiểm tra kỹ; script chủ yếu là Python + ffmpeg nên nhiều khả năng chạy được, bạn thử và báo lỗi qua mục Issues.

## Cách dùng nhanh
Mở Claude Code trong thư mục có video, rồi nói, ví dụ:
- "Dùng `/edit-kieu-so-sanh-fdown` dựng video `quay.mp4` thành bản 9:16, độ dài khoảng 60 giây."
- "Dùng `/video-auto-edit` cắt 3 short hay nhất từ `podcast.mp4`."

## Giọng nói clone (lồng tiếng)
Skill `video-huong-dan-man-hinh-voice` đọc lời bằng giọng clone qua **[VieNeu-TTS](https://github.com/thietkewebdc/VieNeu-TTS)** (chạy trên máy, nhanh) hoặc OmniVoice (hay hơn, chậm hơn).
Bạn tự chuẩn bị mẫu giọng của chính mình (`mau.wav` 5–30 giây + `mau.txt` lời đọc) và đặt vào `skills/video-huong-dan-man-hinh-voice/assets/giong/`. Chỉ clone giọng của chính bạn hoặc giọng đã được đồng ý.

## Lưu ý
- **Video phải có lời nói rõ.** Video chỉ có nhạc/tiếng nhỏ khiến Whisper "bịa" câu kiểu "Hãy subscribe cho kênh…"; skill sẽ báo thay vì dựng bừa.
- Quay **dọc, từ 1080p trở lên** cho hình đẹp. Video quay ngang chuyển sang khung dọc sẽ nhỏ và mờ hơn.
- Máy 8GB: dùng Whisper `int8` (đã mặc định), mỗi lần chạy một video.
- Chưa có trong bộ này: kiểu "Toàn khung chuyên nghiệp" (Dạng 2) và các skill dựa trên bộ chuyên gia của bên thứ ba, vì chưa được phép phát hành lại.

## Giấy phép
Xem [LICENSE.txt](LICENSE.txt): dùng miễn phí cho video cá nhân/thương mại, không bán lại.
