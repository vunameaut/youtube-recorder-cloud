# 🚀 Hướng Dẫn Deploy YouTube Recorder Lên Cloud (Chạy 24/7 Không Cần Bật Máy Tính)

Hệ thống cho phép bạn **tắt máy tính ở nhà hoàn toàn**. Bất cứ khi nào bạn ở ngoài đường hay ở cơ quan:
1. Mở trang web trên điện thoại.
2. Dán link video/livestream YouTube và bấm **Bắt đầu tải**.
3. Cloud server tự động ghi luồng, ghép video qua FFmpeg chất lượng cao nhất, và **đẩy thẳng file vào Google Drive** của bạn.
4. Có thông báo Telegram kèm đường link Google Drive khi hoàn tất!

---

## 🌟 LỰA CHỌN 1: GOOGLE COLAB (Đơn giản nhất, không cần cài đặt gì)

Google Colab có sẵn kết nối trực tiếp với tài khoản Google Drive của bạn:
1. Vào trang [Google Colab](https://colab.research.google.com/).
2. Bấm **File** -> **Upload notebook** -> Chọn file `Colab_YouTube_Recorder.ipynb` trong thư mục này.
3. Bấm **Run** các ô từ trên xuống dưới:
   - Bước 1: Cho phép kết nối với Google Drive của bạn.
   - Bước 2: Tự cài đặt FFmpeg và thư viện cần thiết.
   - Bước 3: Màn hình sẽ xuất hiện 1 đường link dạng:
     `https://xxxxxxxx.trycloudflare.com`
4. Dùng điện thoại mở link đó lên -> Dán link và bấm tải!
5. Video tải xong sẽ nằm ngay trong thư mục: **`Google Drive của bạn > YT_Recordings > YYYY-MM-DD`**.

---

## 🌟 LỰA CHỌN 2: HUGGING FACE SPACES (Docker - Chạy 24/7 Hoàn Toàn Miễn Phí)

Hugging Face Spaces cung cấp máy chủ miễn phí (16GB RAM, 50GB ổ đĩa, 2 CPU), có link web cố định dạng `https://ten-ban-youtube-recorder.hf.space`.

### Các bước tạo Space:
1. Đăng nhập [Hugging Face](https://huggingface.co/) (nếu chưa có thì đăng ký tài khoản miễn phí).
2. Vào mục **Spaces** -> Bấm nút **Create new Space**.
3. Điền thông tin:
   - **Space name**: `youtube-recorder`
   - **License**: `mit` (hoặc để trống)
   - **Space SDK**: Chọn **Docker** (Blank)
   - **Space hardware**: Chọn **CPU basic • 2 vCPU • 16 GB • Free**
4. Bấm **Create Space**.
5. Trong Space vừa tạo, chuyển sang tab **Files** -> Bấm **Add file** -> **Upload files** và kéo toàn bộ các file trong thư mục `youtube-recorder-cloud` lên:
   - `Dockerfile`
   - `requirements.txt`
   - `server.py`
   - `recorder_service.py`
   - `gdrive_uploader.py`
   - `config_service.py`
   - `history_service.py`
   - `cookies.txt`
   - Thư mục `static/` (gồm `index.html`, `style.css`, `app.js`)
6. Bấm **Commit changes to main**.
7. Space sẽ tự động build Docker và hiển thị trạng thái **Running**!
8. Từ giờ bạn có thể lưu link Space vào Bookmark điện thoại, bất cứ lúc nào muốn tải chỉ cần mở ra dán link!

---

### Cách cấp quyền để Hugging Face tự đẩy video vào Google Drive:
Trong mục **Settings** của Space -> phần **Variables and secrets**:
- Tạo Secret tên: `GDRIVE_FOLDER_ID` = ID của thư mục Google Drive bạn muốn lưu video (chuỗi ký tự phía sau `folders/` trên link trình duyệt Google Drive).
- Tạo Secret tên: `GDRIVE_SERVICE_ACCOUNT_JSON` = Nội dung file Service Account Google Cloud (cho phép Cloud tải file không giới hạn vào Drive cá nhân).
