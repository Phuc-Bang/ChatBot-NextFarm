# Kế hoạch cải thiện — ChatBot NextFarm (Bài toán A)

Rà soát ngày **2026-08-22**, tại commit `94fad86`.
Phạm vi theo yêu cầu: **bảo mật** (repo công khai, `/admin` không xác thực),
**lệch giữa mã và tài liệu**, **việc còn dở**. Bỏ qua chủ đề mở rộng kho tri
thức — đã biết và đã ghi trong `docs/reports/P13_phan_tich_tu_choi.md`.

Các plan trong thư mục này viết cho **một người thực thi không có ngữ cảnh gì
từ phiên rà soát**. Mỗi plan tự chứa đủ thông tin: đường dẫn, trích đoạn mã,
quy ước phải theo, lệnh kiểm chứng, và điều kiện dừng.

---

## Thứ tự thực hiện

| # | Plan | Ưu tiên | Công | Rủi ro | Phụ thuộc | Trạng thái |
|---|---|---|---|---|---|---|
| 001 | [API admin báo lỗi thật thay vì trả số liệu bịa](001-bo-du-lieu-bia-trong-fallback-api-admin.md) | **P1** | S | LOW | — | **XONG** — `49c1640` |
| 002 | [Cảnh báo `/admin` không xác thực trong tài liệu giao hàng](002-canh-bao-admin-khong-xac-thuc-trong-tai-lieu-giao-hang.md) | **P1** | S | LOW | — | **XONG** — `cf6c036`, rồi `248bf7d` vượt phạm vi |
| 003 | [Đồng bộ số test và chặn lệch số liệu tài liệu](003-dong-bo-so-test-va-chan-lech-so-lieu-tai-lieu.md) | P2 | S | LOW | — | **XONG** — `7982cad` |

Cả ba đã thực hiện ngày **2026-08-22**. Bộ kiểm thử: 323 → **339 xanh**.

### Đính chính và sai lệch so với lúc viết plan

**Plan 002 — tiền đề chưa đủ đúng.** Plan viết *"`docs/GIAO_HANG_NEXTFARM.md`
không kèm một dòng cảnh báo nào"*. Thực tế mục 6 phần *Giới hạn đã biết* đã có
một dòng từ commit `1aa655c`. Khoảng trống thật hẹp hơn: `/admin` được **giới
thiệu như tính năng sẵn sàng** ở mục Triển khai Production, cách dòng cảnh báo
hơn 200 dòng, và không chỗ nào nói **cái gì lộ ra**.

**Plan 003 — bước 2 đã xong trước.** Bảy chỗ ghi `310` được sửa ở commit
`0a922d6` (21/08), trước khi plan này được thực thi. Việc còn lại chỉ là hàng
rào ở bước 3 — và nó **bắt lỗi ngay lần chạy thật đầu tiên**: thêm 8 test cho
cửa `/admin` làm tài liệu lệch từ 331 sang 339.

**Vượt phạm vi có chủ đích — `248bf7d`.** Plan 002 cố tình để việc thêm xác
thực ra ngoài, lý do: *"cần quyết định về cơ chế và cần NextFarm nêu yêu cầu"*.
Đã làm khác: thêm một cửa kiểm **mặc định an toàn** (`ADMIN_TOKEN` để trống →
chỉ loopback; có đặt → bắt buộc token). Lý do làm khác: nó **không** chốt cơ
chế thay NextFarm — họ vẫn đặt OAuth/SSO ở reverse proxy được — nhưng nó biến
một deploy quên cấu hình từ *lặng lẽ phơi nhật ký* thành *từ chối*. Giới hạn
còn lại (khoá tĩnh không phải hệ thống danh tính) đã ghi vào tài liệu giao
hàng thay vì bỏ qua.

---

## Vì sao 001 đứng đầu

Dự án này tồn tại để chứng minh hệ thống **không bịa**. Trang `/admin` là nơi
trình bày bằng chứng đó cho NextFarm.

Ba hàm cấp dữ liệu cho trang ấy **đã** bịa số khi CSDL không kết nối được —
`app/core/nhat_ky.py:132` và `:196` trả về một bộ số cứng đầy đủ và khớp nhau,
không dấu hiệu nào cho biết là số giả. Demo mà quên bật Docker thì trang admin
vẫn hiện "222 lượt hỏi, 147 ca đã chặn, chi phí $0,0526" như thật.

Quy chuẩn của chính dự án cấm điều này: *"Thất bại phải là thất bại. Không thay
bằng dữ liệu mặc định."*

Đã sửa ở `49c1640`: ba hàm ném `LoiDocNhatKy`, ba endpoint trả HTTP 503, trang
admin hiện bảng báo lỗi và **xoá sạch ô số liệu** thay vì để số cũ nằm lại.
Một chi tiết suýt lọt: HTTP 503 vẫn có body JSON hợp lệ nên
`.then(r => r.json())` **không** ném lỗi — thiếu kiểm `r.ok` thì 503 được vẽ
lên biểu đồ y như dữ liệu thật.

---

## Đã xem xét và KHÔNG đưa vào plan

Ghi lại để lần rà soát sau không mất công kiểm lại.

| Nghi vấn | Kết luận |
|---|---|
| XSS qua Markdown trong `frontend/chat.html` | **Không phải lỗi.** `chat.html:1303` escape **trước** khi thêm markup — đúng thứ tự. `chunkId` giới hạn charset `[a-zA-Z0-9_\-#]`, không parse cú pháp link nên không có `href` do dữ liệu điều khiển. |
| XSS lưu trữ qua nhật ký truy vấn ở `/admin` | **Không phải lỗi.** `admin.html:687` bọc `r.cau_hoi` bằng `escapeHtml`. Mọi trường dữ liệu trong bảng đều escape. |
| SQL injection ở `app/core/nhat_ky.py:53` | **Không phải lỗi.** Chuỗi `dk` ghép vào SQL là hằng literal (`" WHERE abstained"`), không đến từ dữ liệu vào. `limit` truyền qua tham số `%s` và đã chặn trên bằng `min(limit, 500)`. |
| Bí mật lọt vào git | **Không có.** `.env` nằm trong `.gitignore:9`, không được theo dõi. `git grep` mẫu khoá API trên toàn cây làm việc: rỗng. `.env.example` chỉ có khoá trống. |
| Server mở ra mạng ngoài | **Không.** `Makefile:115` bind `127.0.0.1`, không phải `0.0.0.0`. Đây là thứ đang bảo vệ `/admin` hôm nay — xem plan 002. |
| Không có CORS middleware | **Đúng chủ đích.** Không có CORS nghĩa là chỉ cùng gốc gọi được — mặc định an toàn hơn là cấu hình sai. |
| Phiên bản dependency không ghim | **Đã ghim.** `requirements.txt` ghim chính xác từng gói (`fastapi==0.115.6`...). |
| `_ghi_log_an_toan` nuốt lỗi | **Đúng chủ đích, có test canh giữ.** Ghi log hỏng không được chặn câu trả lời — xem `tests/test_ghi_log_khong_chan.py` và `docs/reports/P10_su_co_treo_api.md`. |
| `try/except ImportError` quanh `sentence_transformers` ở `tests/conftest.py:7` | **Không phải lỗi.** Môi trường không cài thư viện thì cũng không test nào chạm được segfault. 318/318 test vẫn thu thập và chạy đủ. |

---

## Không đưa vào plan, nhưng nên biết

**Chưa có CI.** Không có `.github/workflows/`. 339 test tồn tại nhưng không có
gì chạy chúng tự động khi push. Cả hai tài liệu bàn giao đều nêu "tích hợp
CI/CD" như việc của giai đoạn sau, nên đây **đúng với kế hoạch đã công bố**,
không phải sai lệch. Với repo công khai và một người làm, thêm một workflow chạy
`pytest` là việc nhỏ đáng làm — nhưng nó là mở rộng phạm vi, không phải sửa lỗi.

**Một `[TODO]` còn lại trong mã.** `knowledge/chunking/chunker.py:52` — kích
thước chunk chưa chốt sau khi đo Recall@K ở P6. Đã ghi rõ là chưa chốt và vì
sao, nên nó đang làm đúng việc của một `[TODO]`: đánh dấu chỗ chưa có số đo,
không phải chỗ bị bỏ quên.

---

## Cái gì KHÔNG được rà soát lần này

- `evaluation/` — mã chấm điểm và runner. Đọc lướt, không rà kỹ.
- `crawler/` — không đụng tới.
- `frontend/report.html` (27 KB) — chỉ kiểm các điểm chèn HTML, không đọc hết.
- Hiệu năng — không rà. Đường truy xuất vừa đo lại ngày 21/08, xem
  `docs/reports/P6_reranker.md`.
- Chất lượng nội dung nông học của kho tri thức — ngoài phạm vi và cần chuyên
  gia, xem `DEC-029`.
