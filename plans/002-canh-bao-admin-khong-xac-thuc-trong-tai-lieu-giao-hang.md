# Plan 002: Đưa cảnh báo `/admin` không có xác thực vào tài liệu giao hàng

> **Executor instructions**: Làm theo từng bước, chạy mọi lệnh kiểm chứng. Gặp
> "STOP conditions" thì dừng và báo. Xong thì cập nhật `plans/README.md`.
>
> **Drift check**: `git diff --stat 94fad86..HEAD -- docs/GIAO_HANG_NEXTFARM.md app/main.py`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security (tài liệu)
- **Planned at**: commit `94fad86`, 2026-08-22

## Why this matters

`/admin` và ba endpoint `/api/admin/*` **không có xác thực**. Đó là lựa chọn
đúng cho PoC chạy cục bộ (`make serve` bind `127.0.0.1`, không phải `0.0.0.0`),
và `README.md` đã ghi rõ điều đó hai lần.

Nhưng NextFarm không đọc `README.md`. Họ đọc `docs/GIAO_HANG_NEXTFARM.md` — và
ở đó `/admin` được giới thiệu như một tính năng sẵn sàng dùng, **không kèm một
dòng cảnh báo nào**:

> `docs/GIAO_HANG_NEXTFARM.md:110`
> * Cấu hình dashboard giám sát token, chi phí và tỷ lệ từ chối theo thời gian
>   thực (đã có sẵn tại `/admin`).

Nếu NextFarm triển khai theo tài liệu này lên một máy chủ có địa chỉ công khai,
`/api/admin/nhat_ky` sẽ trả về **toàn bộ nhật ký truy vấn** — câu hỏi thật của
nông dân, câu trả lời, chi phí — cho bất kỳ ai gọi tới, không cần đăng nhập.

Đây là lỗ hổng do **tài liệu thiếu**, không phải do mã sai. Mã đang đúng với
mục đích PoC. Cái sai là tài liệu bàn giao không nói cho người nhận biết ranh
giới đó ở đâu.

## Current state

**Chỗ cần sửa — `docs/GIAO_HANG_NEXTFARM.md`, ba vị trí nhắc tới `/admin`:**

```
110:* Cấu hình dashboard giám sát token, chi phí và tỷ lệ từ chối theo thời gian thực (đã có sẵn tại `/admin`).
382:make serve       # http://localhost:8000  và  /admin
400:Trang `/admin` → bấm **"Chỉ xem ca đã chặn"** để thấy toàn bộ ca hệ thống đã chặn, kèm lý do.
```

**Câu cảnh báo đã có sẵn trong `README.md` — dùng lại nguyên văn, đừng viết mới:**

```
228: Trang admin **chưa có đăng nhập** vì chạy cục bộ. Deploy ra ngoài thì bắt buộc thêm khoá.
307: - **Trang admin chưa có đăng nhập** — chạy cục bộ. Deploy ra ngoài thì bắt buộc thêm khoá.
```

**Bằng chứng mã nguồn để trích dẫn trong tài liệu — `app/main.py:128-146`**, ba
endpoint không có tham số phụ thuộc xác thực nào:

```python
@app.get("/api/admin/tong_quan")
def admin_tong_quan():
    from app.core.nhat_ky import tong_quan
    return tong_quan()
```

**Ràng buộc đang bảo vệ hệ thống hôm nay — `Makefile:115`:**

```
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`127.0.0.1` chứ không phải `0.0.0.0` — đây là thứ duy nhất đang chặn truy cập từ
máy khác. Đổi một chữ là mất.

### Quy ước của repo phải theo

- Tài liệu trong `docs/` viết **tiếng Việt CÓ DẤU**.
- Cảnh báo dùng blockquote `>` kèm **in đậm** ở câu đầu. Xem mẫu thật ở
  `docs/GIAO_HANG_NEXTFARM.md:123`:
  ```markdown
  > **Một điều trong mục này là CAM KẾT, chưa phải hiện trạng:**
  ```
- Không hứa hẹn thứ chưa đo. Nếu nêu cách khắc phục thì nêu là **việc cần làm**,
  không nêu như đã có.

## Commands you will need

| Mục đích | Lệnh | Kết quả mong đợi |
|---|---|---|
| Kiểm nội dung | `grep -n "admin" docs/GIAO_HANG_NEXTFARM.md` | thấy các dòng đã sửa |
| Chạy test | `python -m pytest tests/ -q` | 318 passed (tài liệu không ảnh hưởng) |

## Scope

**In scope**:
- `docs/GIAO_HANG_NEXTFARM.md`
- `plans/README.md` (cập nhật trạng thái)

**Out of scope**:
- `app/main.py` — **KHÔNG thêm xác thực trong plan này.** Thêm auth là thay đổi
  hành vi, cần quyết định về cơ chế (khoá tĩnh? OAuth? chỉ chặn ở reverse
  proxy?) và cần NextFarm nêu yêu cầu. Plan này chỉ làm cho tài liệu nói đúng
  sự thật hiện tại.
- `README.md` — đã đúng rồi.
- `Makefile` — `127.0.0.1` giữ nguyên.

## Git workflow

- Nhánh: `advisor/002-canh-bao-admin-khong-auth`
- Commit tiếng Việt có dấu, ví dụ thật từ `git log`:
  ```
  docs(giao-hang): sổ giả định và bảng ánh xạ tiêu chí nghiệm thu
  ```

## Steps

### Step 1: Thêm cảnh báo ngay tại chỗ giới thiệu `/admin`

Ở `docs/GIAO_HANG_NEXTFARM.md`, ngay sau dòng 110, chèn một blockquote. Nội dung
phải nêu đủ bốn ý:

1. `/admin` và `/api/admin/*` hiện **không có xác thực**;
2. hôm nay an toàn **chỉ vì** `make serve` bind `127.0.0.1`;
3. cái gì lộ ra nếu triển khai công khai — toàn bộ nhật ký truy vấn, gồm câu hỏi
   thật của người dùng;
4. đây là **việc bắt buộc phải làm trước khi triển khai**, không phải tuỳ chọn.

Nêu rõ đây là ranh giới có chủ đích của PoC, không phải sơ suất.

**Verify**: `grep -n -A6 "đã có sẵn tại" docs/GIAO_HANG_NEXTFARM.md` → thấy
blockquote mới, có chứa chuỗi `127.0.0.1`

### Step 2: Thêm nhắc lại ở mục hướng dẫn chạy

Ở dòng ~382 (`make serve`), thêm một dòng ngắn ngay dưới khối lệnh, trỏ về cảnh
báo ở Step 1. Một câu là đủ — mục đích là người đọc nhảy thẳng vào phần hướng
dẫn chạy vẫn gặp cảnh báo.

**Verify**: `grep -n -A3 "make serve" docs/GIAO_HANG_NEXTFARM.md` → thấy dòng nhắc

### Step 3: Đưa vào danh sách việc NextFarm cần làm khi triển khai

Tìm trong `docs/GIAO_HANG_NEXTFARM.md` mục liệt kê giới hạn đã biết hoặc việc
cần chuẩn bị (tìm bằng `grep -n "Giới hạn\|giới hạn đã biết\|cần chuẩn bị"`).
Thêm một mục: thêm xác thực cho `/admin` và `/api/admin/*` là **điều kiện tiên
quyết để triển khai ra ngoài máy cục bộ**.

Nếu không tìm thấy mục nào phù hợp → đây là STOP condition, báo lại.

**Verify**: `grep -c "xác thực" docs/GIAO_HANG_NEXTFARM.md` → ≥ 3

## Test plan

Không có test tự động cho thay đổi tài liệu. Thay vào đó, kiểm bằng mắt:

- Đọc lại toàn bộ ba chỗ đã sửa, xác nhận không mâu thuẫn với `README.md:228,307`.
- Xác nhận không có chỗ nào trong `docs/GIAO_HANG_NEXTFARM.md` còn mô tả `/admin`
  như đã sẵn sàng triển khai công khai:
  `grep -n "admin" docs/GIAO_HANG_NEXTFARM.md` — đọc từng dòng kết quả.

## Done criteria

- [ ] `grep -c "xác thực" docs/GIAO_HANG_NEXTFARM.md` → ≥ 3
- [ ] `grep -c "127.0.0.1" docs/GIAO_HANG_NEXTFARM.md` → ≥ 1
- [ ] `python -m pytest tests/ -q` → exit 0, 318 passed (không đổi)
- [ ] `git status` → chỉ `docs/GIAO_HANG_NEXTFARM.md` và `plans/README.md` bị sửa
- [ ] Dòng trạng thái plan 002 trong `plans/README.md` đã cập nhật

## STOP conditions

- Không tìm thấy mục "giới hạn đã biết" hoặc tương đương ở Step 3.
- Phát hiện `/admin` **đã** có xác thực trong mã (grep `Depends\|HTTPBasic\|api_key`
  trong `app/main.py` ra kết quả) — lúc đó tài liệu không sai, phải báo lại.
- `Makefile` đã đổi sang `0.0.0.0` — đó là vấn đề nghiêm trọng hơn tài liệu, báo
  ngay thay vì tiếp tục.

## Maintenance note

Khi nào thêm xác thực thật cho `/admin`, cảnh báo này phải được sửa lại chứ
không xoá — đổi thành mô tả cơ chế đang dùng. Một cảnh báo bị xoá mà không thay
bằng gì sẽ khiến người đọc sau tưởng vấn đề chưa từng tồn tại.

Liên quan: `plans/001-*` sửa việc API admin bịa số. Hai plan độc lập nhau, làm
theo thứ tự nào cũng được.
