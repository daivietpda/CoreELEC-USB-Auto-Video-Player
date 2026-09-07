# CoreELEC USB Auto Video Player Add-on (v1.0.0)

Kodi Service Add-on chuyên dụng cho CoreELEC (21.3 Omega) có khả năng tự động phát hiện USB cắm vào thiết bị, tự động phát video toàn màn hình theo các chế độ tùy chỉnh với vòng lặp vô hạn, và **hỗ trợ tự động phát hiện và phát luồng trực tuyến HLS (.m3u8)** với cơ chế kiểm tra kết nối thông minh (chống treo khi mất mạng) cùng chuyển đổi dự phòng (fallback) linh hoạt giữa HLS và USB.

---

## 1. Tính Năng Nổi Bật

- **Tự động nhận diện USB**: Hoạt động tức thì khi cắm USB mới vào thiết bị, hoặc tự động phát ngay khi khởi động CoreELEC nếu USB đã cắm sẵn từ trước.
- **Hỗ trợ Luồng Trực Tuyến HLS (.m3u8)**:
  - Cho phép nhập trực tiếp URL luồng HLS (ví dụ: `http://192.168.x.x:8080/hls/tv.m3u8`) trong cài đặt.
  - **Tiền kiểm tra an toàn (Pre-flight probe)**: Luôn kiểm tra trạng thái HTTP của luồng trước khi gọi Kodi Player.
  - **Nếu luồng ONLINE**: Tự động kết nối và phát toàn màn hình bằng hardware decoding.
  - **Nếu luồng OFFLINE hoặc mất mạng**: **Tuyệt đối không cố gắng play**, tránh hoàn toàn tình trạng đứng hình, treo Kodi hoặc spam thông báo lỗi.
  - **Chuyển đổi dự phòng thông minh (Fallback)**: Khi luồng HLS mất tín hiệu, tự động chuyển sang phát video trên USB (nếu có cắm); khi luồng HLS online trở lại, tự động phục hồi phát HLS.
- **3 Chế độ phát video USB**:
  1. **Tự động phát 1 video và lặp lại (Single Video Loop)**: Tự động chọn video duy nhất (hoặc video đầu tiên theo thứ tự sắp xếp) và lặp lại vô hạn.
  2. **Tự động phát tất cả video liên tiếp và lặp lại (Multiple Video Loop)**: Tự động lập playlist toàn bộ video trên USB và phát xoay vòng liên tục không gián đoạn.
  3. **Chọn video thủ công (Manual Selection)**: Cho phép người dùng duyệt và chọn 1 hoặc nhiều video cụ thể bằng hộp thoại checkbox. Lựa chọn được lưu bền vững qua các lần khởi động lại.
- **Đa ngôn ngữ tự động (i18n)**: Tự động chuyển đổi giao diện và thông báo theo ngôn ngữ hệ thống của Kodi (**Tiếng Việt** và **Tiếng Anh**).
- **Thứ tự phát đa dạng**: Hỗ trợ Tên file A → Z (áp dụng Natural Sorting: `1.mp4`, `2.mp4`, `10.mp4`), Tên file Z → A, và Phát ngẫu nhiên (Random).
- **Phát từ đầu không Resume Dialog**: Tự động đặt điểm phát về `00:00:00`, triệt tiêu hoàn toàn hộp thoại hỏi Resume của Kodi.
- **Phát toàn màn hình (Fullscreen)**: Tự động chuyển giao diện về toàn màn hình khi bắt đầu phát.
- **Cơ chế dừng thông minh**: Khi người dùng bấm STOP trên remote hoặc bàn phím, add-on dừng phát và kết thúc phiên autoplay hiện tại, tuyệt đối không tự động ép phát lại làm kẹt người dùng.
- **An toàn khi rút USB**: Tự động nhận diện khi USB bị rút trong lúc phát, dừng player sạch sẽ, giải phóng playlist và quay lại trạng thái chờ mà không gây treo hoặc crash Kodi.
- **Debounce chống trùng lặp**: Thiết lập độ trễ chờ filesystem mount ổn định (0s - 10s; mặc định 2s) nhằm loại trừ hoàn toàn các sự kiện kích hoạt trùng lặp.
- **Bảo vệ hệ thống**: Chỉ quét các thiết bị lưu trữ ngoài/USB removable, tuyệt đối không can thiệp vào các phân vùng hệ thống (`/storage`, `/flash`, `/`, eMMC).

---

## 2. Định Dạng Hỗ Trợ

- **Luồng trực tuyến**: Luồng HLS (`.m3u8`), HTTP Live Streams.
- **File video USB bắt buộc**: `.mp4`, `.mpg`.
- **File video USB mở rộng**: `.mpeg`, `.mkv`, `.avi`, `.ts`, `.m2ts`, `.mov` (không phân biệt chữ hoa/thường).

---

## 3. Cài Đặt và Cấu Hình

### A. Cài từ file ZIP qua giao diện Kodi
1. Tải file `service.usb.autovideoplayer-1.0.0.zip` chép vào USB hoặc bộ nhớ CoreELEC.
2. Trên màn hình Kodi, vào **Settings (Cài đặt)** → **Add-ons**.
3. Chọn **Install from zip file** (Cài đặt từ tệp zip) và chọn file zip của add-on.

### B. Cấu hình Cài đặt (Settings)
Vào **Settings** → **Add-ons** → **My add-ons** → **Services** → **USB Auto Video Player** → **Configure**:

#### 1. Cài đặt chung (General)
- **Bật USB Auto Video Player**: Bật/tắt add-on.
- **Tự động phát khi cắm USB**: Tự động kích hoạt khi có thiết bị USB.
- **Chế độ phát**: Lặp 1 video / Lặp tất cả video / Chọn video thủ công.
- **Thứ tự video**: A → Z / Z → A / Ngẫu nhiên.
- **Tìm video trong thư mục con**: Quét đệ quy các thư mục trên USB.
- **Phát video toàn màn hình**: Tự động chuyển về fullscreen.
- **Lặp lại video/playlist**: Bật vòng lặp vô hạn.
- **Thời gian chờ sau khi cắm USB**: Trì hoãn 2s (chống trigger trùng lặp).

#### 2. Luồng trực tuyến HLS (HLS Stream)
- **Bật luồng trực tuyến HLS**: Kích hoạt chế độ kiểm tra và phát luồng HLS.
- **Địa chỉ luồng HLS (.m3u8)**: Nhập URL (ví dụ: `http://192.168.x.x:8080/hls/tv.m3u8`).
- **Chế độ ưu tiên nguồn phát**:
  - *Ưu tiên HLS (Chuyển sang USB khi offline)*: Luôn ưu tiên phát HLS khi online; nếu mất tín hiệu hoặc mất mạng thì chuyển sang video USB; khi HLS online lại thì tự động phát tiếp HLS.
  - *Ưu tiên USB (Chuyển sang HLS khi không có USB)*: Phát USB khi có cắm; nếu không có USB thì phát HLS.
  - *Chỉ phát luồng HLS*: Chỉ phát HLS, nếu offline thì ở trạng thái chờ an toàn, không phát USB.
- **Thời gian thăm dò lại khi luồng offline**: 10s, 15s, 30s, 60s (chu kỳ kiểm tra ngầm khi luồng mất kết nối).
- **Thời gian chờ kết nối tối đa (Timeout)**: 2s, 3s, 5s (ngắt kiểm tra nhanh nếu mạng đứt, tránh treo).

---

## 4. Menu Chức Năng Nhanh

Khi mở add-on từ menu **Add-ons** → **Programs** (hoặc **Chương trình**):
1. **1. Chọn video cho Chế độ Thủ công (Mode 3)**: Mở danh sách checkbox chọn video trên USB.
2. **2. Phát video ngay từ USB (Bắt đầu phát)**: Kích hoạt phát video USB ngay lập tức.
3. **3. Phát ngay luồng HLS**: Tiền kiểm tra tín hiệu luồng HLS và phát ngay lập tức (nếu offline sẽ thông báo lý do cụ thể và không mở player).
4. **4. Mở Cài đặt Add-on**: Mở nhanh bảng cấu hình add-on.

---

## 5. Vị Trí Log & Debugging

File log của Kodi được lưu tại:
```text
/storage/.kodi/temp/kodi.log
```

Theo dõi log hoạt động theo thời gian thực:
```bash
tail -f /storage/.kodi/temp/kodi.log | grep "USB-AutoVideo"
```
