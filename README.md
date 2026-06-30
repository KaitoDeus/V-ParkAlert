# Hệ Thống Giám Sát Và Cảnh Báo Đỗ Xe Trái Phép V-ParkAlert (Web App)

Dự án **V-ParkAlert** là một hệ thống Web App Command Center (Trung tâm điều hành) quản lý giám sát, ghi nhận và tiếp nhận phản ánh vi phạm dừng đỗ phương tiện giao thông thông minh áp dụng Trí Tuệ Nhân Tạo (AI).

---

## 1. Cấu Trúc Thư Mục Dự Án

Dự án được tổ chức cấu trúc thư mục rõ ràng theo kiến trúc phân tầng:

```text
d:\.V-ParkAlert\
├── docs/                   # Tài liệu nghiệp vụ & kỹ thuật (PRD, Tech Stack, Memory...)
│   ├── business-requirement.md
│   ├── memory.md
│   ├── prd.md
│   └── tech-stack.md
├── media/                  # Thư mục lưu trữ tệp đa phương tiện & ảnh vi phạm
│   └── citizen_reports/    # Ảnh chụp phản ánh của người dân gửi lên
├── src/                    # Mã nguồn hệ thống (FastAPI Backend & Static Web)
│   ├── api/                # Các route API (v1) xử lý logic nghiệp vụ
│   │   ├── deps.py         # Dependencies cho DB session và Authenticate
│   │   └── v1/             # Các endpoint auth, camera, violations
│   ├── core/               # Cấu hình hệ thống (DB, config, JWT, Websocket)
│   │   ├── config.py       # Tải tệp cấu hình môi trường (.env)
│   │   ├── database.py     # Cấu hình kết nối CSDL và tự động tạo DB
│   │   ├── security.py     # Xử lý băm mật khẩu và JWT Token
│   │   └── websocket_manager.py # Quản lý kết nối thời gian thực qua WebSocket
│   ├── models/             # Định nghĩa cấu trúc bảng CSDL (SQLAlchemy ORM)
│   │   ├── base.py         # Khởi tạo Base class
│   │   ├── user.py         # Model tài khoản người dùng
│   │   └── violation.py    # Model thông tin vi phạm dừng đỗ
│   ├── repositories/       # Tầng tương tác CSDL trực tiếp (Repository Pattern)
│   │   ├── base.py         # Lớp Repository cơ bản
│   │   ├── user_repository.py
│   │   └── violation_repository.py
│   ├── schemas/            # Định nghĩa định dạng dữ liệu vào/ra API (Pydantic)
│   ├── services/           # Tầng xử lý nghiệp vụ chính & AI Pipeline
│   │   ├── ai_pipeline.py  # Xử lý quét nhận dạng xe cộ (YOLOv8) & biển số xe (ONNX/OpenCV)
│   │   ├── auth_service.py # Nghiệp vụ đăng nhập và phân quyền
│   │   ├── camera_service.py # Quản lý luồng và proxy camera (YouTube Live Stream)
│   │   └── violation_service.py # Nghiệp vụ quản lý & xuất báo cáo vi phạm Excel
│   ├── static/             # Giao diện Web tĩnh phục vụ trực tiếp từ FastAPI
│   │   ├── components/     # Các thành phần giao diện con (sidebar, report...)
│   │   ├── css/            # Các tệp CSS giao diện (base.css, light.css...)
│   │   ├── js/             # Các module Javascript logic tương tác UI
│   │   ├── index.html      # Trang chủ Dashboard hợp nhất
│   │   └── login.html      # Giao diện đăng nhập Glassmorphism
│   ├── init_db.py          # Script khởi tạo bảng CSDL & Seeding dữ liệu mẫu
│   ├── main.py             # Điểm khởi chạy FastAPI chính (cổng 8000)
│   ├── requirements.txt    # Các thư viện Python yêu cầu cho dự án
│   ├── start.bat           # File khởi chạy nhanh hệ thống trên Windows
│   └── start.sh            # Script khởi chạy nhanh hệ thống trên Linux/macOS
├── .env                    # Tệp cấu hình môi trường (SQL Server, AI paths)
└── .gitignore              # Cấu hình bỏ qua git
```

---

## 2. Chuẩn Bị Môi Trường & Cơ Sở Dữ Liệu

Hệ thống sử dụng **Microsoft SQL Server** làm hệ quản trị cơ sở dữ liệu chính. Bạn cần tạo tệp cấu hình `.env` ở thư mục gốc để thiết lập kết nối (hoặc hệ thống sẽ sử dụng các tham số mặc định dưới đây):

- **DB_USER**: `sa`
- **DB_PASSWORD**: `Password123`
- **DB_SERVER**: `localhost`
- **DB_PORT**: `1433`
- **DB_NAME**: `v_parkalert`

> [!NOTE]
> Hệ thống tích hợp khả năng tự tạo cơ sở dữ liệu. Khi bạn chạy script khởi tạo, nó sẽ kết nối vào server SQL qua DB Master, tự động tạo cơ sở dữ liệu `v_parkalert` nếu chưa tồn tại, sau đó khởi tạo toàn bộ cấu trúc bảng mà không cần phải thực hiện thủ công bằng SQL Server Management Studio (SSMS).

---

## 3. Các Bước Cài Đặt Và Khởi Chạy

Bạn có thể chạy hệ thống theo hai cách: chạy nhanh qua script tự động hoặc cài đặt thủ công.

### Cách 1: Khởi chạy nhanh (Khuyến khích)

Dự án đã tích hợp sẵn các file script tự động tạo môi trường ảo, cài đặt thư viện, khởi tạo database và khởi chạy ứng dụng:

- **Trên Windows:** Click đúp hoặc chạy file `src/start.bat` từ Command Prompt.
- **Trên Linux/macOS:** Mở terminal tại thư mục gốc dự án và chạy:
  ```bash
  chmod +x src/start.sh
  ./src/start.sh
  ```

---

### Cách 2: Khởi chạy thủ công từng bước

#### Bước 1: Thiết lập môi trường ảo Python và cài đặt thư viện

1. Mở Terminal/PowerShell tại thư mục `d:\.V-ParkAlert\src`.
2. Tạo và kích hoạt môi trường ảo:
   - **Trên Windows (PowerShell/CMD):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **Trên Git Bash/Linux/macOS:**
     ```bash
     python -m venv .venv
     source .venv/Scripts/activate
     ```
3. Cài đặt các thư viện yêu cầu:
   ```bash
   pip install -r requirements.txt
   ```

#### Bước 2: Khởi tạo cơ sở dữ liệu và nạp dữ liệu mẫu

Chạy lệnh sau để hệ thống tự động tạo các bảng và nạp sẵn tài khoản/bản ghi vi phạm mẫu ban đầu:

```bash
python -m src.init_db
```

#### Bước 3: Khởi chạy ứng dụng FastAPI

Chạy lệnh sau để khởi động máy chủ phát triển:

```bash
python -m src.main
```

Ứng dụng sẽ hoạt động tại địa chỉ: [http://localhost:8000](http://localhost:8000)

Bạn chỉ cần truy cập vào trình duyệt web theo địa chỉ trên để trải nghiệm hệ thống.

---

## 4. Tài Khoản Đăng Nhập Kiểm Thử

Hệ thống hỗ trợ phân quyền vai trò (Role-Based Access Control) chặt chẽ. Đăng nhập bằng các tài khoản mẫu sau để kiểm thử (tất cả mật khẩu đều là `password123`):

1.  **Giao diện Người Dân (Citizen):**
    - **Tài khoản:** `citizen`
    - **Tính năng:**
      - Tải lên hình ảnh bằng chứng vi phạm bằng cách click hoặc kéo thả.
      - Xem hiệu ứng AI quét ảnh (`Scanning Line`) và nhận diện tự động điền form.
      - Tương tác ghim vị trí chính xác của phương tiện vi phạm trên bản đồ số Leaflet.
      - Xem lịch sử và trạng thái phản ánh cá nhân.
2.  **Giao diện Lực Lượng Chức Năng (Authority):**
    - **Tài khoản:** `authority`
    - **Tính năng:**
      - Theo dõi bảng thống kê KPI vi phạm thời gian thực (Tổng số, Chờ duyệt, Đã duyệt, Bác bỏ).
      - Bản đồ điểm nóng (Heatmap) Leaflet tối màu hiển thị các điểm vi phạm đã duyệt (nhấp nháy đỏ) và vị trí camera AI giám sát.
      - Giám sát luồng camera trực tuyến (YouTube Live Stream) và bật/tắt hiển thị HUD vẽ bounding box AI trực quan.
      - Bảng điều khiển giả lập sự cố vi phạm đỗ xe để thử nghiệm gửi tín hiệu tức thời.
      - Xem chi tiết, chỉnh sửa thông tin do AI gợi ý và phê duyệt/bác bỏ báo cáo.
      - Trích xuất báo cáo xử lý vi phạm ra định dạng Excel (`.xlsx`).
3.  **Giao diện Hệ Thống AI (AI System):**
    - **Tài khoản:** `ai_system`
    - **Tính năng:**
      - Quản lý danh sách, xem trạng thái hoạt động (FPS, độ trễ) và bật/tắt từng luồng camera AI giám sát.
      - Theo dõi biểu đồ thời gian thực về tiêu thụ tài nguyên phần cứng (CPU, RAM) và độ trễ suy luận AI.
      - Xem nhật ký quét tự động thời gian thực của camera AI (bao gồm ảnh cắt vi phạm, biển số xe, loại vi phạm, độ tin cậy AI).

---

## 5. Quy Trình Phân Tích Hình Ảnh (AI Detection Pipeline)

Khi nhận hình ảnh camera hoặc ảnh người dân gửi lên, hệ thống sẽ kích hoạt một quy trình xử lý hình ảnh 10 bước nghiêm ngặt:

1.  **Vehicle Detection (YOLOv8):** Định vị phương tiện giao thông (ô tô, xe tải, xe máy, xe buýt).
2.  **Crop Vehicle ROI:** Cắt vùng ảnh chứa phương tiện để tối ưu hóa vùng xử lý tiếp theo.
3.  **Plate Detection inside ROI:** Phát hiện vị trí biển số xe bên trong vùng xe đã cắt.
4.  **Crop Plate ROI:** Cắt vùng chứa biển số xe.
5.  **Image Enhancement:** Tiền xử lý cải thiện chất lượng ảnh biển số bằng thuật toán nâng cao (CLAHE, Bilateral Filter, Adaptive Threshold, Sharpen).
6.  **PaddleOCR / Character Recognition:** Nhận diện các ký tự trên biển số.
7.  **Regex Validation:** Đối chiếu với định dạng biển số xe tiêu chuẩn của Việt Nam.
8.  **Temporal Voting:** Cơ chế bỏ phiếu theo thời gian giữa các khung hình liên tục để khử nhiễu.
9.  **Confidence Threshold Check:** Chỉ chấp nhận kết quả nếu độ tin cậy của mô hình AI lớn hơn hoặc bằng 75%.
10. **Debug Visualization Overlay:** Vẽ bounding box màu xanh lục quanh phương tiện, màu vàng quanh biển số và ghi chú thông số độ tin cậy lên ảnh trước khi xuất kết quả.
