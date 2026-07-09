# 🎙️ AI YouTube Dubber

Một ứng dụng hoàn chỉnh bằng Python giúp lồng tiếng các video YouTube từ tiếng Anh sang tiếng Việt tự động bằng AI, đồng thời giữ lại nhạc nền và hiệu ứng âm thanh gốc của video. Ứng dụng cung cấp giao diện đồ họa (GUI) thân thiện được xây dựng bằng Gradio.

## ✨ Tính năng chính

- **📥 Tải video tự động:** Hỗ trợ tải video chất lượng cao (lên đến 1080p) từ YouTube thông qua `yt-dlp`. Có thể sử dụng cookies để vượt qua các giới hạn của YouTube đối với các video bị giới hạn độ tuổi hoặc chặn bot.
- **🌿 Giữ lại nhạc nền nguyên bản:** Sử dụng mô hình học sâu `Demucs` để tách riêng biệt giọng nói (vocals) và nhạc nền (background music/effects) từ video gốc.
- **📝 Nhận diện giọng nói siêu chuẩn (STT):** Sử dụng `OpenAI Whisper` để bóc băng (transcribe) giọng nói tiếng Anh. Tự động chia nhỏ (chunking) đối với các video dài trên 10 phút để tránh quá tải bộ nhớ.
- **🌐 Dịch thuật mượt mà:** Dịch trực tiếp từ tiếng Anh sang tiếng Việt bằng `deep-translator`. Có cơ chế nhận diện từ mượn và thông minh trong việc giữ nguyên các từ chuyên ngành/khoa học.
- **🔊 Lồng tiếng Việt tự nhiên (TTS):** Sử dụng `Microsoft Edge TTS` để tạo ra giọng đọc tiếng Việt truyền cảm (hỗ trợ giọng Nam/Nữ). Tích hợp cơ chế *Retry with Exponential Backoff* để chống lại tình trạng rớt mạng hoặc rate-limit từ server.
- **⏱ Căn chỉnh thời gian thông minh:** Tự động co giãn tốc độ (speed-up/slow-down) giọng lồng tiếng Việt bằng FFmpeg (`atempo`) để khớp hoàn hảo với khẩu hình và độ dài của từng câu nói tiếng Anh trong video gốc.
- **🎨 Giao diện web trực quan:** Giao diện người dùng dễ thao tác bằng `Gradio`, cho phép theo dõi log hệ thống trực tiếp, điều chỉnh âm lượng tiếng gốc/lồng tiếng, và xem bảng đối chiếu transcript Anh-Việt.

## 🛠 Yêu cầu hệ thống

- Python 3.8+ (Khuyên dùng Python 3.10+)
- **FFmpeg**: Cần được cài đặt sẵn trên máy tính và thêm vào biến môi trường `PATH`.
- (Tùy chọn) GPU NVIDIA: Nếu có card đồ họa NVIDIA + CUDA, các quá trình chạy Whisper và Demucs sẽ nhanh hơn gấp nhiều lần so với chạy trên CPU.

## 📦 Hướng dẫn cài đặt

**1. Clone dự án và truy cập vào thư mục**
```bash
git clone https://github.com/your-username/youtube_dubbing_app.git
cd youtube_dubbing_app
```

**2. Cài đặt các thư viện Python cần thiết**
```bash
pip install -r requirements.txt
```
*(Lưu ý: Đảm bảo bạn đã cài `torch` phiên bản tương thích với CUDA nếu muốn dùng GPU).*

**3. Cài đặt FFmpeg (Dành cho Windows)**
- Tải bản build của FFmpeg từ [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) hoặc dùng `winget install ffmpeg`.
- Giải nén và thêm thư mục `bin` vào biến môi trường `PATH` của Windows.

**4. Xác thực YouTube (Rất quan trọng để không bị lỗi)**
Do YouTube thường xuyên chặn bot và giới hạn độ tuổi, bạn CẦN sử dụng file `cookies.txt`.
**Cách lấy file cookies an toàn:**
- Bước 1: Khuyên bạn nên tạo một tài khoản Google phụ (không dùng tài khoản chính) và đăng nhập vào YouTube trên trình duyệt (Chrome/Edge/Firefox).
- Bước 2: Cài đặt tiện ích mở rộng có tên **"Get cookies.txt LOCALLY"** vào trình duyệt.
- Bước 3: Đang ở trang chủ YouTube, bấm vào biểu tượng tiện ích đó và chọn **Export**.
- Bước 4: Đổi tên file vừa tải về thành `cookies.txt` và đặt thẳng vào thư mục gốc của dự án này (`youtube_dubbing_app`).
*(Lưu ý: File này đã được thêm vào `.gitignore` nên sẽ không bao giờ bị lộ khi bạn tải code lên mạng).*

## 🚀 Hướng dẫn sử dụng

Chạy file giao diện chính của ứng dụng bằng lệnh:

```bash
python app_ui.py
```

1. Mở trình duyệt và truy cập vào địa chỉ mạng cục bộ (thường là `http://127.0.0.1:7860`).
2. Dán đường link video YouTube bạn muốn lồng tiếng vào ô **Link YouTube**.
3. (Tùy chọn) Chọn Giọng đọc (Nam/Nữ), tinh chỉnh âm lượng tiếng gốc, và chọn model Whisper.
4. Bấm **Bắt đầu Lồng Tiếng** và theo dõi tiến trình thông qua bảng Log.
5. Sau khi quá trình hoàn tất, xem và tải xuống video thành phẩm trực tiếp trên giao diện.

## 📂 Cấu trúc thư mục

```text
youtube_dubbing_app/
│
├── app_ui.py                 # File khởi chạy giao diện chính (Gradio)
├── main.py                   # Luồng điều phối (pipeline) chính của ứng dụng
├── requirements.txt          # Danh sách thư viện phụ thuộc
├── cookies.txt               # (Người dùng tự thêm) File chứa cookies của YouTube
│
├── modules/
│   ├── downloader.py         # Tải video/âm thanh bằng yt-dlp
│   ├── voice_separator.py    # Tách giọng nói và nhạc nền bằng Demucs
│   ├── stt_engine.py         # Nhận diện giọng nói bằng Whisper
│   ├── translator.py         # Dịch text bằng Google Translate API
│   ├── tts_engine.py         # Tổng hợp giọng nói TTS bằng Edge-TTS & FFmpeg concat
│   ├── audio_chunker.py      # Tiện ích cắt file âm thanh lớn
│   ├── text_normalizer.py    # Chuẩn hóa văn bản, xử lý các từ viết tắt/Toán học
│   └── media_merger.py       # Trộn ghép âm thanh lồng tiếng vào video gốc (MoviePy)
│
└── temp/                     # (Tự động sinh ra) Thư mục chứa các file tạm thời trong quá trình xử lý
```

## 📝 Cơ chế xử lý nổi bật
1. **File-based Concat FFmpeg**: Việc trộn hàng trăm câu thoại MP3 được hệ thống thực hiện thông qua ghi danh sách ra file `.txt` rồi dùng FFmpeg ghép lại. Kỹ thuật này triệt tiêu hoàn toàn lỗi tràn bộ nhớ (Out of Memory - OOM) khi xử lý các video dài hàng chục phút.
2. **Auto-Retry TTS**: Ứng dụng tự động điều tiết tần suất gửi request cho Microsoft Edge TTS và tự động thử lại khi kết nối bị từ chối, giúp tránh bị mất âm thanh do server ban IP.
3. **Smart Pause**: Hệ thống tính toán chính xác khoảng thời gian ngưng nghỉ của người nói gốc để chèn đoạn im lặng (silence) vào bản lồng tiếng, đảm bảo video sau lồng tiếng khớp hoàn hảo với nhịp điệu của bản gốc.

---
**Disclaimer**: Dự án phục vụ mục đích nghiên cứu, học tập và cá nhân. Vui lòng tuân thủ điều khoản dịch vụ của YouTube và tôn trọng bản quyền của các nhà sáng tạo nội dung gốc.
