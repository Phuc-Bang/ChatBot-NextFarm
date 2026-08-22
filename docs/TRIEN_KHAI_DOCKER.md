# Hướng Dẫn Triển Khai Nextfarm AI Bằng Docker (Production Deployment)

Tài liệu này hướng dẫn chi tiết quy trình đóng gói và triển khai hệ thống **Nextfarm AI** trên máy chủ (On-Premise hoặc Cloud: AWS, GCP, Azure, DigitalOcean) bằng Docker và Docker Compose.

---

## 1. Yêu cầu Hệ thống Tối thiểu

* **Hệ điều hành:** Linux (Ubuntu 22.04 LTS khuyến nghị) hoặc Docker Desktop (Windows/macOS).
* **Docker Engine:** Phiên bản 24.0+
* **Docker Compose:** Phiên bản v2.20+
* **Cấu hình phần cứng:**
  * CPU: 2 vCPU
  * RAM: 4 GB (khuyến nghị 8 GB để tải model embedding cục bộ mượt mà)
  * Ổ đĩa: 20 GB dung lượng trống

---

## 2. Chuẩn bị Môi trường & Cấu hình Biến

Tạo tệp `.env` từ tệp mẫu `.env.example`:

```bash
cp .env.example .env
```

Cập nhật các giá trị bí mật trong `.env`:

```ini
# Cấu hình CSDL PostgreSQL
POSTGRES_USER=nextfarm
POSTGRES_PASSWORD=your_super_secret_db_password_here
POSTGRES_DB=nextfarm

# Mã bí mật quản trị (bảo vệ các endpoint /admin và /api/admin/*)
ADMIN_TOKEN=your_secure_admin_token_here

# Khóa API LLM (Google Gemini)
GEMINI_API_KEY=AIzaSy...your_gemini_api_key

# Cổng truy cập ứng dụng
PORT=8000
```

---

## 3. Khởi chạy Ứng dụng Production

Chỉ với 1 lệnh duy nhất để build container và khởi động cả hệ thống:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Các bước tự động diễn ra:
1. Container `nextfarm-prod-db` khởi động PostgreSQL 16 tích hợp sẵn pgvector, nạp 3 extension `vector`, `unaccent`, `pg_trgm`.
2. Container `nextfarm-prod-app` biên dịch image Python 3.11-slim, tải trước weights mô hình embedding tiếng Việt, khởi chạy FastAPI.
3. Healthcheck tự động giám sát trạng thái kết nối giữa ứng dụng và CSDL.

---

## 4. Nạp Dữ liệu Kho Tri Thức Lần Đầu (Ingestion)

Sau khi container khởi chạy, thực thi nạp dữ liệu kho tri thức chuẩn hóa từ Git:

```bash
docker compose -f docker-compose.prod.yml exec app python knowledge/ingestion/load.py
```

Lệnh này sẽ nạp 185 chunk đã được kiểm duyệt và 141 fact nông học đã xác thực vào CSDL pgvector.

---

## 5. Kiểm tra & Giám sát

* **Trang Người Dùng (Nông dân Chat):** `http://<IP_SERVER>:8000/`
* **Trang Báo Cáo Đo Lường Kỹ Thuật:** `http://<IP_SERVER>:8000/report`
* **Trang Đánh Giá Chuyên Gia:** `http://<IP_SERVER>:8000/expert`
* **Trang Quản Trị Hệ Thống:** `http://<IP_SERVER>:8000/admin?token=<ADMIN_TOKEN>`

### Xem nhật ký thời gian thực (Logs):
```bash
docker compose -f docker-compose.prod.yml logs -f app
```

### Dừng hệ thống:
```bash
docker compose -f docker-compose.prod.yml down
```
