# Style phụ đề

Mặc định theo nhận diện navy-gold:
- Chữ: trắng `#FFFFFF`
- Highlight karaoke: gold `#F5C542`
- Viền: navy `#0B1F3A`

Tuỳ chỉnh qua tham số `make_subs.py`: `--hl`, `--text`, `--outline`, `--font`, `--words`, `--upper`.

| Kiểu video | Lệnh gợi ý |
|---|---|
| Shorts năng lượng cao | `--style shorts --words 2 --upper` |
| Shorts giáo dục, nhiều chữ | `--style shorts --words 4` |
| YouTube ngang dài | `--style classic` |
| Theo brand khách | `--hl "#MÃ_MÀU_BRAND" --outline "#000000" --font "Tên font"` |

Font chưa cài vào máy → tải .ttf vào thư mục `fonts/`, chạy `finish.py --fontsdir fonts`.
Font phải hỗ trợ tiếng Việt: Be Vietnam Pro, Montserrat, Inter, Roboto, Nunito.
