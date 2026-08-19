# P1 — Kết quả crawl thực tế

> Số liệu trong tài liệu này là kết quả chạy thật, không phải ước lượng.
> Nguồn lỗi được để nguyên là lỗi (quy chuẩn v2.0 §23.1 nguyên tắc 3).

Ngày chạy: 19/08/2026 · dữ liệu gốc: `crawler/data/manifest.json`

---

## Tóm tắt

| | Đợt 1 | Đợt 2 |
|---|---|---|
| Số nguồn khai báo | 7 | 15 |
| Tải được (`ok`) | 4 | **8** |
| Lúa / Cà chua / Dưa chuột | 0 / 0 / 4 | **1 / 3 / 4** |
| Số vùng miền phủ được | 3 | 5 |

Mục tiêu `ASM-07` là 50–80 tài liệu, mỗi cây ≥ 3 vùng. **Hiện đạt 8 tài liệu.**
Khoảng cách còn lớn — xem §5.

---

## 1. Đợt 1 — 7 nguồn kế thừa từ CRAWLER_GUIDE

| Trạng thái | Số nguồn |
|---|---|
| `ok` | 4 |
| `failed` | 1 |
| `robots_disallowed` | 2 |

| Nguồn | Cây | Kết quả |
|---|---|---|
| `ninhbinh_dua_chuot_dong` | dưa chuột | ✅ 6.847 ký tự |
| `ninhbinh_dua_chuot_quytrinh` | dưa chuột | ✅ 5.639 ký tự |
| `hatinh_dua_chuot_vietgap` | dưa chuột | ✅ 12.691 ký tự |
| `laichau_dua_chuot_xuanhe` | dưa chuột | ✅ 4.013 ký tự |
| `lamdong_ca_chua` | cà chua | ❌ HTTP 404 |
| `hanoi_ca_chua` | cà chua | ⛔ `robots.txt` trả 503 |
| `gso_lua_dong_xuan_2024` | lúa | ⛔ `robots.txt` ConnectTimeout |

Hai ca `robots_disallowed` đã kiểm chứng độc lập bằng `curl`:

```
https://sonnptnt.hanoi.gov.vn/robots.txt   HTTP 000 sau 0,56 s  (lỗi kết nối)
https://www.gso.gov.vn/robots.txt          HTTP 000 sau 20,01 s (timeout)
```

Không phải lỗi crawler — hai tên miền này thực sự không truy cập được từ môi
trường hiện tại. Crawler áp dụng quy tắc thận trọng của DEC-028a.

**Phát hiện của đợt 1:** cả 4 nguồn tải được đều là dưa chuột. Không có nguồn
nào cho lúa và cà chua.

---

## 2. Đợt 2 — bổ sung 8 nguồn tìm qua công cụ tìm kiếm

| Trạng thái | Số nguồn |
|---|---|
| `ok` | **8** |
| `failed` | 4 |
| `robots_disallowed` | 3 |
| **Tổng** | 15 |

Nguồn mới tải được:

| Nguồn | Cây | Vùng | Kết quả |
|---|---|---|---|
| `ninhbinh_gntt_ca_chua` | cà chua | ĐB sông Hồng | ✅ 7.657 ký tự |
| `hcm_dost_ca_chua_bi` | cà chua | Đông Nam Bộ | ✅ 1.992 ký tự |
| `phanbonquocgia_ca_chua` | cà chua | toàn quốc | ✅ 8.673 ký tự |
| `quangtri_lua_ngap_kho_xen_ke` | lúa | Bắc Trung Bộ | ✅ 5.931 ký tự |

Nguồn mới thất bại:

| Nguồn | Lỗi | Đã kiểm chứng độc lập |
|---|---|---|
| `lamdong_ca_chua_ghep` | HTTP 404 | ✅ vẫn 404 với https + UA trình duyệt |
| `lamdong_ca_chua_cherry_pdf` | HTTP 404 | ✅ cùng tên miền, đường dẫn đã đổi |
| `lamdong_ttbvtv_ca_chua` | HTTP 404 | ✅ trang chuyên mục lặp chuyển hướng vô hạn |
| `bacgiang_ntm_ca_chua_bi` | SSLError khi đọc `robots.txt` | ✅ `curl` cũng trả HTTP 000 |

Toàn bộ đường dẫn của `khuyennong.lamdong.gov.vn` và `ttbvtv.lamdong.gov.vn`
lấy từ chỉ mục tìm kiếm đều đã chết. Tên miền còn sống (chuyển hướng
`http → https` hoạt động) nhưng cấu trúc đường dẫn đã thay đổi. Đây là mất mát
đáng tiếc: Lâm Đồng là nguồn Tier 1 mạnh cho cà chua, và có sẵn một tài liệu
PDF ban hành chính thức — vốn định dùng để kiểm chứng DEC-027 trên dữ liệu thật.

> **Chưa có nguồn PDF nào tải được.** Khả năng đọc PDF của crawler mới chỉ được
> kiểm chứng bằng PDF tự sinh trong `tests/test_crawl.py`, chưa kiểm chứng trên
> tài liệu thật.

---

## 3. Phủ sóng hiện tại

| Cây | Số tài liệu | Vùng miền |
|---|---|---|
| Dưa chuột | 4 | ĐB sông Hồng ×2, Bắc Trung Bộ, Trung du miền núi |
| Cà chua | 3 | ĐB sông Hồng, Đông Nam Bộ, toàn quốc |
| **Lúa** | **1** | Bắc Trung Bộ |

Lúa là cây yếu nhất — và cũng là cây quan trọng nhất với nông dân Việt Nam.
Tài liệu lúa duy nhất hiện có lại là **tin về một mô hình thí điểm tưới ngập
khô xen kẽ**, không phải quy trình canh tác đầy đủ.

---

## 4. `discover.py` — tìm nguồn thay vì đoán URL

Thay vì gõ tay 50–80 URL (đoán URL là một dạng bịa đặt — phần lớn sẽ 404),
`discover.py` xuất phát từ trang chuyên mục **đã chứng minh tải được** rồi thu
thập liên kết bài viết. Đầu ra là **đề xuất**, người duyệt quyết định.

| Seed | Kết quả |
|---|---|
| `ninhbinh_kht` | 10 liên kết |
| `hatinh_khcn` | 18 liên kết |
| `quangtri_khkt` | 22 liên kết |
| `laichau_tailieu` | 0 |
| `lamdong_ki_thuat_trong_rau` | ❌ HTTP 404 |
| `lamdong_ttbvtv_quy_trinh` | ❌ TooManyRedirects |
| `ninhbinh_gntt_khuyennong` | ❌ HTTP 404 |
| **Tổng đề xuất** | **50** (lúa 5 · chưa rõ 45) |

### Vấn đề chất lượng

**Các trang chuyên mục này là cổng tin tức, không phải thư viện tài liệu kỹ
thuật.** Phần lớn liên kết thu được là tin hoạt động: tập huấn, mô hình thử
nghiệm, chỉ đạo sản xuất, thông báo hành chính. Ví dụ tiêu đề thật thu được:
*"Kiểm tra tiến độ thực hiện dự án khuyến nông"*, *"Hướng dẫn xây dựng dự toán
ngân sách nhà nước năm 2027"*, *"Phiên chợ khuyến nông"*.

Trong 22 liên kết của Quảng Trị chỉ có **1 tài liệu kỹ thuật thật sự về lúa**
(*"Hướng dẫn phòng trừ dịch hại lúa giai đoạn trước, trong và sau trổ"* — đồng
thời là nội dung high-risk, sẽ phải duyệt lẻ theo §24.4).

Một trường hợp nhãn sai còn lại: *"Hướng dẫn quy trình kỹ thuật trồng ngô sinh
khối trên đất lúa chuyển đổi"* bị gán nhãn `lua` vì cụm "đất lúa". Đây là bài
về ngô. Người duyệt phải loại — đúng vai trò của bước duyệt.

---

## 5. Việc phải làm để đạt ASM-07

Theo thứ tự ưu tiên:

1. **Đi sâu vào trang lưu trữ / phân trang.** Trang chuyên mục chỉ hiện tin mới
   nhất; tài liệu kỹ thuật nằm ở các trang sau. Cần thêm hỗ trợ phân trang cho
   `discover.py`.
2. **Dùng chức năng tìm kiếm của chính website** với từ khoá tên cây, thay vì
   duyệt chuyên mục theo thời gian.
3. **Bổ sung tên miền mới đã kiểm tra truy cập được.** Không đoán tên miền của
   các tỉnh khác — mọi tên miền phải đến từ nguồn có thật rồi được crawler xác
   nhận.
4. **Ưu tiên tuyệt đối cho lúa** — hiện chỉ 1 tài liệu, và không phải quy trình
   canh tác.

Nếu sau tất cả vẫn không đủ 50–80 tài liệu, phương án trung thực là **thu hẹp
phạm vi cây trồng của PoC và ghi rõ giới hạn**, thay vì hạ chuẩn nguồn xuống
Tier 3. Kích thước thật của kho tri thức quyết định phạm vi câu hỏi bot được
phép trả lời, chứ không phải ngược lại.

---

## 6. Một lỗi đã sửa

`guess_crop` ban đầu so khớp chuỗi thường nên `"mạ"` khớp bên trong `"mạnh"`,
gán nhãn `lua` cho bài *"Bước chuyển mạnh mẽ trong xây dựng NTM ở Hà Tĩnh"*.
Đã sửa bằng khớp theo biên từ, kèm test hồi quy trong `tests/test_discover.py`.

Nhãn sai ở bước đề xuất không nguy hiểm bằng nhãn sai ở bước trả lời, nhưng vẫn
phải sửa: người duyệt sẽ tin vào nhãn nếu nó thường đúng.

---

## 7. Ghi chú vận hành

`CRAWLER_CONTACT_EMAIL` hiện **chưa được đặt**, nên User-Agent thiếu địa chỉ
liên hệ. DEC-028b yêu cầu có liên hệ thật trước khi crawl diện rộng. Cần điền
vào `.env` (không commit) trước đợt crawl lớn tiếp theo.
