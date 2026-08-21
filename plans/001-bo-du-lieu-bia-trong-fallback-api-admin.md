# Plan 001: API admin báo lỗi thật thay vì trả số liệu bịa khi CSDL hỏng

> **Executor instructions**: Làm theo từng bước. Chạy mọi lệnh kiểm chứng và
> xác nhận kết quả mong đợi trước khi sang bước sau. Gặp bất cứ điều gì trong
> mục "STOP conditions" thì dừng và báo lại — không được tự ứng biến. Xong thì
> cập nhật dòng trạng thái của plan này trong `plans/README.md`.
>
> **Drift check (chạy đầu tiên)**:
> `git diff --stat 94fad86..HEAD -- app/core/nhat_ky.py app/main.py frontend/admin.html`
> Nếu file nào trong phạm vi đã đổi từ khi plan này được viết, so các đoạn
> trích ở mục "Current state" với mã hiện tại trước khi làm; lệch thì coi như
> STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug (toàn vẹn dữ liệu)
- **Planned at**: commit `94fad86`, 2026-08-22

## Why this matters

Toàn bộ dự án này tồn tại để chứng minh một điều: **hệ thống không bịa**. Đó là
tiêu chí nghiệm thu số một của NextFarm, và trang `/admin` chính là thứ dùng để
trình bày bằng chứng đó.

Nhưng ba hàm cấp dữ liệu cho trang admin đang **bịa số khi CSDL không kết nối
được**. Chúng nuốt mọi exception rồi trả về một bộ số cứng — đầy đủ, khớp nhau,
không có dấu hiệu nào cho biết đó là số giả. Chạy demo cho NextFarm mà quên bật
Docker thì trang admin vẫn hiện "222 lượt hỏi, 147 ca đã chặn, chi phí
$0,0526" như thật.

Quy chuẩn của chính dự án cấm điều này:

> **Thất bại phải là thất bại.** Nguồn lỗi → `status: failed`. Không thay bằng
> dữ liệu mặc định, không "cứu" bằng tay.

Sau plan này: CSDL hỏng thì API trả HTTP 503 kèm thông báo lỗi, và trang admin
hiện trạng thái lỗi. Người xem luôn phân biệt được "không có dữ liệu" với
"không đọc được dữ liệu".

## Current state

Ba hàm trong `app/core/nhat_ky.py` (208 dòng, module đọc/ghi `query_log`):

**1. `doc_nhat_ky()` — `app/core/nhat_ky.py:66-67`** — nuốt lỗi, trả danh sách rỗng:

```python
    except Exception:
        return []
```

Hậu quả: CSDL hỏng hiển thị y hệt "chưa có lượt hỏi nào".

**2. `tong_quan()` — `app/core/nhat_ky.py:132-160`** — trả nguyên một bộ số bịa:

```python
    except Exception:
        return {
            "tong_luot": 222,
            "so_tu_choi": 147,
            "ty_le_tu_choi": 66.2,
            "token_vao": 56862, "token_ra": 22680,
            "Ti_trung_binh": 702,
            "To_trung_binh": 280,
            "chi_phi_usd": 0.0526,
            "model": model or "gemini-3.1-flash-lite",
            "ngay_tra_gia": NGAY_TRA_CUU,
            "latency_p50_ms": 11,
            "latency_p95_ms": 8084,
            "theo_ly_do": [
                {"ly_do": "garden_data", "so_luot": 8},
                ...
```

**3. `thong_ke_kho()` — `app/core/nhat_ky.py:196-208`** — tương tự:

```python
    except Exception:
        return {
            "tai_lieu_tong": 31, "tai_lieu_da_duyet": 18,
            "chunk_tong": 292, "chunk_index_duoc": 185,
            ...
```

Ngoài ra `tong_quan()` còn có hai giá trị mặc định lẻ ở **dòng 127-128**, cùng
một loại vấn đề nhưng nhỏ hơn:

```python
            "latency_p50_ms": p[0] if p else 11,
            "latency_p95_ms": p[1] if p else 8084,
```

Ba điểm gọi trong `app/main.py:128-146`:

```python
@app.get("/api/admin/tong_quan")
def admin_tong_quan():
    from app.core.nhat_ky import tong_quan
    return tong_quan()


@app.get("/api/admin/nhat_ky")
def admin_nhat_ky(limit: int = 50, chi_tu_choi: bool = False):
    from app.core.nhat_ky import doc_nhat_ky
    return doc_nhat_ky(limit=min(limit, 500), chi_tu_choi=chi_tu_choi)


@app.get("/api/admin/kho_tri_thuc")
def admin_kho():
    from app.core.nhat_ky import thong_ke_kho
    return thong_ke_kho()
```

### Quy ước của repo phải theo

- **Chú thích bằng tiếng Việt KHÔNG DẤU** trong mã nguồn (`app/`, `tests/`).
  Xem `app/services/retrieval/keyword.py` làm mẫu.
- **Chú thích giải thích VÌ SAO, kèm số đo khi có.** Không viết chú thích mô tả
  lại điều mã đã nói.
- **Tên hàm/biến tiếng Việt không dấu**: `ket_noi`, `doc_nhat_ky`, `tong_quan`.
- Trả lỗi HTTP dùng `JSONResponse` — đã có sẵn trong `app/main.py`, xem
  `app/main.py:154-160`:
  ```python
  return JSONResponse({"loi": "chua co frontend/chat.html"}, 404)
  ```
  Khoá lỗi tên là `"loi"`. Giữ đúng khoá đó.

### Một ràng buộc phải giữ

`_ghi_log_an_toan` trong `app/main.py` **phải tiếp tục nuốt lỗi** — đó là chủ
đích, có test canh giữ (`tests/test_ghi_log_khong_chan.py`). Ghi log hỏng không
được chặn câu trả lời. Plan này chỉ đổi hành vi của ba hàm **ĐỌC** phục vụ trang
admin, không đụng tới đường ghi.

## Commands you will need

| Mục đích | Lệnh | Kết quả mong đợi |
|---|---|---|
| Chạy test | `python -m pytest tests/ -q` | 318 passed (hoặc hơn sau khi thêm test mới) |
| Test một file | `python -m pytest tests/test_admin_bao_loi.py -q` | all pass |
| Bật CSDL | `docker compose up -d` | container `nextfarm-db` healthy |
| Tắt CSDL (để thử lỗi) | `docker compose stop db` | container dừng |
| Chạy server | `make serve` | uvicorn tại 127.0.0.1:8000 |

## Scope

**In scope** (chỉ được sửa các file này):
- `app/core/nhat_ky.py`
- `app/main.py` (chỉ ba endpoint `/api/admin/*`)
- `frontend/admin.html` (chỉ phần xử lý lỗi khi fetch)
- `tests/test_admin_bao_loi.py` (tạo mới)
- `plans/README.md` (cập nhật dòng trạng thái)

**Out of scope** (KHÔNG đụng vào, dù trông có liên quan):
- `app/main.py` hàm `chat()` và `_ghi_log_an_toan()` — đường ghi log phải giữ
  nguyên hành vi nuốt lỗi, có test canh giữ.
- `app/core/db.py` — `connect_timeout` và `statement_timeout` đã chốt bằng số
  đo, đổi sẽ làm hỏng chuỗi chẩn đoán đã ghi trong `docs/reports/P10_su_co_treo_api.md`.
- `frontend/chat.html` — trang chat không dùng ba hàm này.
- Bất kỳ file nào trong `evaluation/` — số liệu đo, không liên quan.

## Git workflow

- Nhánh: `advisor/001-bo-du-lieu-bia-fallback`
- Commit message **bằng tiếng Việt có dấu**, theo mẫu đang dùng trong repo.
  Ví dụ thật từ `git log`:
  ```
  fix(admin): thêm cơ chế fallback dữ liệu an toàn cho các api tổng hợp nhật ký
  feat(retrieval): bật reranker trên GPU, R@5 từ 72,7% lên 90,9%
  ```
- KHÔNG push, KHÔNG mở PR trừ khi được yêu cầu.

## Steps

### Step 1: Thêm lớp lỗi riêng cho tầng đọc nhật ký

Trong `app/core/nhat_ky.py`, ngay sau phần import, thêm:

```python
class LoiDocNhatKy(Exception):
    """Khong doc duoc du lieu nhat ky.

    Ton tai de tang tren PHAN BIET duoc "khong co du lieu" voi "khong doc
    duoc du lieu". Truoc day ca hai deu tra ve gia tri binh thuong, nen mot
    su co CSDL hien ra y het mot he thong chua ai dung.
    """
```

**Verify**: `python -c "from app.core.nhat_ky import LoiDocNhatKy; print('OK')"` → in ra `OK`

### Step 2: `doc_nhat_ky()` ném lỗi thay vì trả rỗng

Sửa khối `except` ở `app/core/nhat_ky.py:66-67`:

```python
    except Exception as e:
        raise LoiDocNhatKy("khong doc duoc query_log: " + str(e)[:200]) from e
```

**Verify**: `python -m pytest tests/ -q` → vẫn 318 passed (chưa có test mới)

### Step 3: `tong_quan()` ném lỗi, bỏ toàn bộ số cứng

Thay khối `except Exception:` ở dòng ~132 và **xoá hết** dict số cứng bên trong
nó (tới hết hàm), thay bằng:

```python
    except Exception as e:
        raise LoiDocNhatKy("khong tong hop duoc nhat ky: " + str(e)[:200]) from e
```

Đồng thời sửa hai giá trị mặc định ở dòng ~127-128 thành `None`:

```python
            # None chu KHONG phai 11/8084. Chua do duoc va "do duoc 11ms" la
            # hai chuyen khac nhau - dien so vao cho chua do la bia.
            "latency_p50_ms": p[0] if p else None,
            "latency_p95_ms": p[1] if p else None,
```

**Verify**:
```
grep -n "222\|8084\|0.0526\|56862" app/core/nhat_ky.py
```
→ **không có dòng nào** (mọi số cứng đã biến mất)

### Step 4: `thong_ke_kho()` ném lỗi, bỏ số cứng

Thay khối `except Exception:` ở dòng ~196 và xoá dict số cứng:

```python
    except Exception as e:
        raise LoiDocNhatKy("khong doc duoc thong ke kho: " + str(e)[:200]) from e
```

**Verify**:
```
grep -n "292\|185\|tai_lieu_tong.: 31" app/core/nhat_ky.py
```
→ không có dòng nào

### Step 5: Ba endpoint trả HTTP 503

Trong `app/main.py`, bọc ba endpoint `/api/admin/*`. Mẫu cho endpoint đầu, làm
tương tự cho hai endpoint còn lại:

```python
@app.get("/api/admin/tong_quan")
def admin_tong_quan():
    from app.core.nhat_ky import LoiDocNhatKy, tong_quan
    try:
        return tong_quan()
    except LoiDocNhatKy as e:
        # 503 chu khong phai 200 voi du lieu mac dinh. Trang admin la cho
        # trinh bay bang chung he thong khong bia - no khong duoc bia so cua
        # chinh no.
        return JSONResponse({"loi": str(e)}, 503)
```

**Verify**: `python -m pytest tests/ -q` → vẫn pass

### Step 6: Trang admin hiện trạng thái lỗi

Trong `frontend/admin.html`, tìm nơi gọi `fetch("/api/admin/...")`. Với mỗi lần
gọi, khi `response.ok === false` thì hiện thông báo lỗi thay vì để trống hoặc
hiện số 0.

Yêu cầu tối thiểu: người xem đọc được một câu nêu rõ **không đọc được dữ liệu**,
khác hẳn với "chưa có dữ liệu". Dùng đúng biến CSS đang có trong file
(`var(--text-muted)`) để khớp giao diện.

**Verify** (thủ công, ghi lại kết quả):
1. `docker compose up -d && make serve` → mở `/admin` → thấy số liệu thật
2. `docker compose stop db` → tải lại `/admin` → **thấy thông báo lỗi**, không
   thấy 222/147/0.0526
3. `docker compose up -d db` → tải lại → số liệu thật trở lại

## Test plan

Tạo `tests/test_admin_bao_loi.py`, lấy `tests/test_ghi_log_khong_chan.py` làm
mẫu cấu trúc (dùng `monkeypatch.setitem(sys.modules, ...)` để giả `psycopg`).

Các case phải có:

1. `test_doc_nhat_ky_nem_loi_khi_db_hong` — giả `ket_noi` ném lỗi, khẳng định
   `doc_nhat_ky()` ném `LoiDocNhatKy`, **không** trả `[]`.
2. `test_tong_quan_nem_loi_khi_db_hong` — tương tự với `tong_quan()`.
3. `test_thong_ke_kho_nem_loi_khi_db_hong` — tương tự với `thong_ke_kho()`.
4. `test_khong_con_so_cung_trong_nhat_ky` — đọc mã nguồn `app/core/nhat_ky.py`,
   khẳng định không còn chuỗi `"222"`, `"8084"`, `"0.0526"`, `"56862"`, `"292"`.
   Đây là test canh giữ: một lần "sửa cho tiện" đặt lại số mặc định sẽ làm nó đỏ.
   **Nhớ bỏ chú thích trước khi kiểm chuỗi** — chú thích giải thích sự cố này
   có nhắc các con số đó và sẽ báo động giả. Xem cách làm ở
   `tests/test_ghi_log_khong_chan.py:93-94`.
5. `test_endpoint_admin_tra_503` — dùng `fastapi.testclient.TestClient`, giả cho
   `tong_quan` ném `LoiDocNhatKy`, khẳng định status code là 503 và body có
   khoá `"loi"`.

**Verify**: `python -m pytest tests/test_admin_bao_loi.py -q` → 5 passed

## Done criteria

Tất cả phải đúng:

- [ ] `python -m pytest tests/ -q` → exit 0, ≥ 323 passed
- [ ] `grep -nE "222|8084|0\.0526|56862|\"chunk_tong\": 292" app/core/nhat_ky.py` → không có kết quả
- [ ] `grep -n "return \[\]" app/core/nhat_ky.py` → không có kết quả
- [ ] `grep -c "503" app/main.py` → ≥ 3
- [ ] Kiểm thủ công 3 bước ở Step 6 đã làm và ghi lại kết quả
- [ ] `git status` → không có file nào ngoài danh sách in-scope bị sửa
- [ ] Dòng trạng thái plan 001 trong `plans/README.md` đã cập nhật

## STOP conditions

Dừng lại và báo, không tự ứng biến, nếu:

- Drift check cho thấy `app/core/nhat_ky.py` đã đổi và các đoạn trích ở
  "Current state" không còn khớp.
- Bỏ số cứng đi làm **test đang có** đỏ lên (nghĩa là có test khác đang dựa vào
  giá trị bịa — phải báo, không được sửa test cho khớp).
- Trang `/admin` có đường dẫn dữ liệu thứ tư ngoài ba endpoint kể trên.
- `_ghi_log_an_toan` hoặc `tests/test_ghi_log_khong_chan.py` bị buộc phải sửa —
  đường ghi log nằm ngoài phạm vi và có chủ đích riêng.

## Maintenance note

Sau plan này, quy tắc cho mọi hàm đọc dữ liệu mới của trang admin: **không có
giá trị mặc định nào cho trường hợp lỗi.** Lỗi phải nổi lên tới HTTP status.

Điều cần để ý khi review: bất kỳ PR nào thêm số vào một khối `except` trong
`app/core/nhat_ky.py`. `test_khong_con_so_cung_trong_nhat_ky` bắt được các con
số đã biết, nhưng không bắt được số mới. Nguyên tắc thì rộng hơn cái test.
