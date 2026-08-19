# P1 — Kết quả crawl thực tế

> Số liệu trong tài liệu này là kết quả chạy thật, không phải ước lượng.
> Nguồn lỗi được để nguyên là lỗi (quy chuẩn v2.0 §23.1 nguyên tắc 3).

Ngày chạy: 19/08/2026 · `crawler/data/manifest.json`

---

## 1. Chạy `crawl.py` trên 7 nguồn kế thừa từ CRAWLER_GUIDE

| Trạng thái | Số nguồn |
|---|---|
| `ok` | **4** |
| `failed` | 1 |
| `robots_disallowed` | 2 |
| **Tổng** | 7 |

Chi tiết:

| Nguồn | Cây | Kết quả | Ghi chú |
|---|---|---|---|
| `ninhbinh_dua_chuot_dong` | dưa chuột | ✅ ok | 6.847 ký tự |
| `ninhbinh_dua_chuot_quytrinh` | dưa chuột | ✅ ok | 5.639 ký tự |
| `hatinh_dua_chuot_vietgap` | dưa chuột | ✅ ok | 12.731 ký tự |
| `laichau_dua_chuot_xuanhe` | dưa chuột | ✅ ok | 4.013 ký tự |
| `lamdong_ca_chua` | cà chua | ❌ failed | HTTP 404 — liên kết đã chết |
| `hanoi_ca_chua` | cà chua | ⛔ robots_disallowed | `robots.txt` trả 503 |
| `gso_lua_dong_xuan_2024` | lúa | ⛔ robots_disallowed | `robots.txt` ConnectTimeout |

Hai trường hợp `robots_disallowed` đã được kiểm chứng độc lập bằng `curl`:

```
https://sonnptnt.hanoi.gov.vn/robots.txt   HTTP 000 sau 0,56 s  (lỗi kết nối)
https://www.gso.gov.vn/robots.txt          HTTP 000 sau 20,01 s (timeout)
```

Đây không phải lỗi của crawler. Hai tên miền này thực sự không truy cập được
từ môi trường hiện tại. Crawler áp dụng quy tắc thận trọng của DEC-028a
(`robots.txt` không đọc được → không tải) nên xếp vào `robots_disallowed`.

---

## 2. Phát hiện quan trọng — kho tri thức đang lệch hoàn toàn

> **Cả 4 nguồn tải được đều là dưa chuột. Hiện có 0 nguồn cho lúa và 0 nguồn
> cho cà chua.**

Hệ quả nếu dừng ở đây:

- Bot chỉ trả lời được về dưa chuột. Mọi câu hỏi về lúa và cà chua đều phải
  abstain vì không có evidence — đúng hành vi, nhưng vô dụng
- Không đo được Recall@K có ý nghĩa: 4 tài liệu là quá ít để việc xếp hạng
  có tác dụng
- Không xây được nhóm `known_answer` cho 2 trong 3 cây của eval set (P3)

`ASM-07` đặt mục tiêu 50–80 tài liệu, mỗi cây ≥ 3 vùng miền. **Hiện đạt
4 tài liệu, 1 cây, 3 vùng.** Đây là khoảng cách phải xử lý trước khi sang P3.

---

## 3. Chạy `discover.py` để tìm thêm nguồn

Thay vì gõ tay 50–80 URL (đoán URL là một dạng bịa đặt — phần lớn sẽ 404),
`discover.py` xuất phát từ các trang chuyên mục **đã chứng minh là tải được**
rồi thu thập liên kết bài viết.

Ba seed trong `crawler/seeds.yaml`:

| Seed | Liên kết thu được |
|---|---|
| `ninhbinh_kht` (Khuyến nông Ninh Bình) | 10 |
| `hatinh_khcn` (NTM Hà Tĩnh) | 18 |
| `laichau_tailieu` (Sở NN&MT Lai Châu) | 0 |
| **Tổng đề xuất** | **28** |

Phân loại theo cây: `lua` 3 · chưa rõ 25 · `ca_chua` 0 · `dua_chuot` 0.

### Kết luận từ lần chạy này

**Ba trang chuyên mục trên là cổng tin tức, không phải thư viện tài liệu
kỹ thuật.** Nội dung thu được chủ yếu là tin hoạt động — tập huấn, mô hình
thử nghiệm, chỉ đạo sản xuất — chứ không phải quy trình canh tác. Ví dụ các
tiêu đề thu được: *"Kiểm tra tiến độ thực hiện dự án khuyến nông"*,
*"Hướng dẫn phòng chống bệnh dại trên vật nuôi"*, *"Kiểm soát tốt môi trường
trong nuôi tôm"*.

Ba seed hiện tại **không đủ** để đạt `ASM-07`.

---

## 4. Một lỗi đã sửa trong lần chạy đầu

`guess_crop` ban đầu so khớp chuỗi thường, nên `"mạ"` khớp bên trong `"mạnh"`
và gán nhãn `lua` cho bài *"Bước chuyển mạnh mẽ trong xây dựng NTM ở Hà Tĩnh"*.
Đã sửa bằng khớp theo biên từ, và thêm test hồi quy trong
`tests/test_discover.py`.

Nhãn sai ở bước đề xuất không nguy hiểm bằng nhãn sai ở bước trả lời, nhưng
vẫn phải sửa: người duyệt sẽ tin vào nhãn nếu nó thường đúng.

---

## 5. Việc cần làm tiếp để đạt ASM-07

Theo thứ tự ưu tiên:

1. **Bổ sung seed từ các tên miền khác** — cần tên miền có thật, đã kiểm tra
   truy cập được. Không được đoán tên miền của các tỉnh khác.
2. **Đi sâu vào trang lưu trữ / phân trang** thay vì chỉ trang chuyên mục
   đầu tiên. Trang đầu chỉ hiện tin mới nhất.
3. **Dùng chức năng tìm kiếm của chính website** nếu có, với từ khoá tên cây.
4. Nếu sau tất cả vẫn không đủ 50–80 tài liệu → **thu hẹp phạm vi cây trồng
   của PoC và ghi rõ giới hạn**, thay vì hạ chuẩn nguồn xuống Tier 3.

Phương án 4 là phương án trung thực nhất nếu ba phương án đầu không đủ:
kích thước thật của kho tri thức quyết định phạm vi câu hỏi bot được phép
trả lời, chứ không phải ngược lại.
