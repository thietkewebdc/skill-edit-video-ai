#!/usr/bin/env bash
set -e
command -v ffmpeg >/dev/null || { echo "Cần cài ffmpeg: brew install ffmpeg | sudo apt install ffmpeg | winget install ffmpeg"; exit 1; }
pip install -q faster-whisper numpy pillow || pip install -q --break-system-packages faster-whisper numpy pillow
echo "OK. Nên cài font 'Be Vietnam Pro' (Google Fonts) để phụ đề tiếng Việt đẹp."
