# CoreELEC USB Auto Video Player Add-on

Kodi Service Add-on chuyên dụng cho CoreELEC (21.3 Omega) có khả năng tự động phát hiện USB cắm vào thiết bị và tự động phát video toàn màn hình theo các chế độ tùy chỉnh với vòng lặp vô hạn, chống resume dialog, chống trigger nhiều lần và xử lý an toàn khi người dùng nhấn Stop hoặc rút USB.

---

## 1. Tính Năng Nổi Bật

- **Tự động nhận diện USB**: Hoạt động tức thì khi cắm USB mới vào thiết bị, hoặc tự động phát ngay khi khởi động CoreELEC nếu USB đã cắm sẵn từ trước.
- **3 Chế độ phát linh hoạt**:
  1. **Tự động phát 1 video và lặp lại (Single Video Loop)**: Tự động chọn video duy nhất (hoặc video đầu tiên theo thứ tự sắp xếp) và lặp lại vô hạn.
  2. **Tự động phát tất cả video liên tiếp và lặp lại (Multiple Video Loop)**: Tự động lập playlist toàn bộ video trên USB và phát xoay vòng liên tục không gián đoạn.
  3. **Chọn video thủ công (Manual Selection)**: Cho phép người dùng duyệt và chọn 1 hoặc nhiều video cụ thể bằng hộp thoại checkbox. Lựa chọn được lưu bền vững qua các lần khởi động lại.
- **Thứ tự phát đa dạng**: Hỗ trợ Tên file A → Z (áp dụng Natural Sorting: `1.mp4`, `2.mp4`, `10.mp4`), Tên file Z → A, và Phát ngẫu nhiên (Random).
- **Phát từ đầu không Resume Dialog**: Tự động đặt điểm phát về `00:00:00`, triệt tiêu hoàn toàn hộp thoại hỏi Resume của Kodi.
- **Phát toàn màn hình (Fullscreen)**: Tự động chuyển giao diện về toàn màn hình khi bắt đầu phát.
- **Cơ chế dừng thông minh**: Khi người dùng bấm STOP trên remote hoặc bàn phím, add-on dừng phát và kết thúc phiên autoplay hiện tại, tuyệt đối không tự động ép phát lại làm kẹt người dùng.
- **An toàn khi rút USB**: Tự động nhận diện khi USB bị rút trong lúc phát, dừng player sạch sẽ, giải phóng playlist và quay lại trạng thái chờ mà không gây treo hoặc crash Kodi.
- **Debounce chống trùng lặp**: Thiết lập độ trễ chờ filesystem mount ổn định (0s, 1s, 2s, 3s, 5s, 10s; mặc định 2s) nhằm loại trừ hoàn toàn các sự kiện kích hoạt trùng lặp.
- **Bảo vệ hệ thống**: Chỉ quét các thiết bị lưu trữ ngoài/USB removable, tuyệt đối không quét hay can thiệp vào các phân vùng hệ thống (`/storage`, `/flash`, `/`, eMMC).

---

## 2. Định Dạng Video Hỗ Trợ

- **Bắt buộc**: `.mp4`, `.mpg`
- **Mở rộng**: `.mpeg`, `.mkv`, `.avi`, `.ts`, `.m2ts`, `.mov`
- **Không phân biệt chữ hoa/chữ thường**: `.mp4`, `.MP4`, `.mpg`, `.MPG` đều được nhận diện chính xác.

---

## 3. Cách Chuẩn Bị USB

1. Định dạng USB với filesystem FAT32, exFAT, NTFS hoặc ext4.
2. Sao chép các file video vào thư mục gốc USB hoặc bất kỳ thư mục con nào (ví dụ `USB:/video/` hoặc `USB:/advertising/`).
3. Nếu muốn kiểm soát thứ tự phát theo danh số, hãy đặt tên file dạng `1.mp4`, `2.mp4`, `10.mp4` hoặc `video01.mp4`, `video02.mp4`.

---

## 4. Hướng Dẫn Cài Đặt

### Cách 1: Cài từ file ZIP qua giao diện Kodi (Khuyên dùng)
1. Tải file `service.usb.autovideoplayer-1.0.0.zip` chép vào USB hoặc chia sẻ mạng Samba của CoreELEC.
2. Trên màn hình Kodi, vào **Settings (Biểu tượng bánh răng)** → **Add-ons**.
3. Chọn **Install from zip file** (Nếu có thông báo bảo mật nguồn ngoài, chọn *Settings* → bật *Unknown sources*).
4. Tìm và chọn file `service.usb.autovideoplayer-1.0.0.zip`.
5. Đợi vài giây, Kodi sẽ hiển thị thông báo góc phải thông báo add-on đã được cài đặt thành công.

### Cách 2: Cài đặt trực tiếp qua SSH / SFTP
Sao chép thư mục add-on vào thư mục addons của Kodi trên thiết bị:
```bash
scp -r service.usb.autovideoplayer root@192.168.x.x:/storage/.kodi/addons/
ssh root@192.168.x.x "systemctl restart kodi"
```

---

## 5. Cấu Hình Add-on (Settings)

Vào **Settings** → **Add-ons** → **My add-ons** → **Services** → **USB Auto Video Player** → **Configure**:

| Tùy chọn | Giá trị khả dụng | Mặc định | Ý nghĩa |
| :--- | :--- | :--- | :--- |
| **Enable USB Auto Video Player** | Bật / Tắt | **Bật** | Bật hoặc tắt toàn bộ dịch vụ add-on |
| **Tự động phát khi cắm USB** | Bật / Tắt | **Bật** | Tự kích hoạt phát khi cắm USB hoặc khởi động |
| **Chế độ phát (Playback mode)** | 1. Tự động phát 1 video và lặp lại<br>2. Tự động phát tất cả video và lặp lại<br>3. Chọn video thủ công | **1 video** | Quyết định cách thức phát video trên USB |
| **Thứ tự video (Video ordering)** | A → Z, Z → A, Ngẫu nhiên | **A → Z** | Thứ tự sắp xếp danh sách phát |
| **Tìm video trong thư mục con** | Bật / Tắt | **Bật** | Quét đệ quy tìm video ở mọi thư mục |
| **Phát video toàn màn hình** | Bật / Tắt | **Bật** | Tự chuyển về fullscreen khi bắt đầu phát |
| **Lặp lại video/playlist** | Bật / Tắt | **Bật** | Tự động lặp lại vô hạn khi kết thúc |
| **Delay sau khi cắm USB** | 0s, 1s, 2s, 3s, 5s, 10s | **2 giây** | Chờ filesystem mount ổn định trước khi quét |
| **Hiển thị thông báo (Notifications)** | Bật / Tắt | **Bật** | Hiện thông báo nhỏ góc màn hình khi cắm/rút USB |
| **Ghi log chi tiết (Debug logging)** | Bật / Tắt | **Tắt** | Bật ghi log debug để phân tích lỗi |

---

## 6. Hướng Dẫn Sử Dụng Chế Độ Thủ Công (Mode 3)

1. Cắm USB có chứa video vào box CoreELEC.
2. Mở add-on từ menu **Add-ons** → **Programs** → chọn **USB Auto Video Player**.
3. Chọn **1. Chọn video cho Chế độ Thủ công (Mode 3)**.
4. Một danh sách chứa toàn bộ video trên USB sẽ hiện ra với các ô checkbox.
5. Dùng remote hoặc chuột chọn các video muốn phát, sau đó nhấn **OK**.
6. Vào Cài đặt add-on chuyển **Chế độ phát** thành **Chọn video thủ công**.
7. Khi cắm USB vào (hoặc chọn menu *Phát video ngay từ USB*), add-on sẽ chỉ phát và lặp lại các video đã được chọn.

---

## 7. Vị Trí Log & Debugging

File log của Kodi được lưu tại:
```text
/storage/.kodi/temp/kodi.log
```

Để theo dõi log hoạt động của add-on theo thời gian thực qua SSH:
```bash
tail -f /storage/.kodi/temp/kodi.log | grep "USB-AutoVideo"
```

Các dòng log tiêu chuẩn của add-on:
```text
[USB-AutoVideo] Service started.
[USB-AutoVideo] Detected USB insertion: 'USB-64G' (/var/media/USB-64G).
[USB-AutoVideo] Found 4 video(s) on /var/media/USB-64G.
[USB-AutoVideo] Starting playlist with 4 video(s)
[USB-AutoVideo] User stopped playback. Autoplay session suspended.
[USB-AutoVideo] USB storage unmounted/removed: /var/media/USB-64G
```

---

## 8. Cách Gỡ Cài Đặt (Uninstall)

1. Vào **Settings** → **Add-ons** → **My add-ons** → **Services** → **USB Auto Video Player**.
2. Chọn **Uninstall**.
3. Khởi động lại Kodi nếu cần.
