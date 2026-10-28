# Cài skill sang máy khác

1. Giải nén, chép thư mục `video-huong-dan-man-hinh-voice` vào `~/.claude/skills/` (Mac/Linux) hoặc `C:\Users\<tên>\.claude\skills\` (Windows).
2. Cần có: `ffmpeg` + `ffprobe` (có libass) trên PATH, Python 3.9+, `pip install numpy`.
3. Giọng clone (chọn một, hoặc xuất wav từ VoiceStudio rồi bỏ qua bước này):
   - VieNeu-TTS: tạo venv riêng cài `vieneu`, chạy `tts_batch.py` bằng python của venv đó.
   - OmniVoice: venv riêng cài `omnivoice torch soundfile`, thêm `--engine omni`.
   - Mẫu giọng Bùi Viết Cường đã nằm sẵn trong `assets/giong/` (mau.wav, mau.txt, omnivoice.prompt). Đổi chỗ: đặt biến môi trường `HMT_VOICE_DIR`.
4. Nhận giọng (chỉ cần cho `cut_opening.py words`): python có `mlx-whisper` (chỉ chạy được trên Mac Apple Silicon); đặt `HMT_ASR_PY=<đường dẫn python>`. Máy Windows/Linux: dùng `faster-whisper` rồi tự ghi `ranges.json`.
5. Font Be Vietnam Pro cho sub (cài font vào máy, hoặc đổi `--font Arial`).
6. Gọi skill: gõ `/video-huong-dan-man-hinh-voice` trong Claude Code.
