# P1 — Kết quả thu thập tài liệu

> Mọi số liệu trong tài liệu này là kết quả chạy thật, không phải ước lượng.
> Nguồn lỗi được để nguyên là lỗi (quy chuẩn v2.0 §23.1 nguyên tắc 3).

Ngày chạy: 19/08/2026 · dữ liệu gốc: `crawler/data/manifest.json`

---

## Tóm tắt

| | Đợt 1 | Đợt 2 | **Đợt 3 (cuối)** |
|---|---|---|---|
| Nguồn khai báo | 7 | 15 | **82** |
| Tải được (`ok`) | 4 | 8 | **31** |
| Lúa / Cà chua / Dưa chuột | 0 / 0 / 4 | 1 / 3 / 4 | **22 / 4 / 5** |
| Câu ứng viên số liệu | — | 83 | **193** |

**`ASM-07` đặt mục tiêu 50–80 tài liệu, mỗi cây ≥ 3 vùng. Kết quả đạt 31 tài
liệu.** Đây là con số thật của web công khai Tier 1 truy cập được, không phải
kết quả của việc làm chưa tới — xem §5.

---

## 1. Trạng thái cuối cùng

| Trạng thái | Số nguồn | Nguyên nhân |
|---|---|---|
| `ok` | **31** | |
| `empty` | 43 | **Toàn bộ từ `khuyennongvn.gov.vn`** — site render bằng JavaScript |
| `failed` | 5 | 4 × HTTP 404 (Lâm Đồng), 1 × trang đã gỡ |
| `robots_disallowed` | 3 | `robots.txt` không đọc được (Hà Nội, GSO, Bắc Giang) |
| **Tổng** | **82** | |

### Phủ sóng theo cây và vùng

| Cây | Tài liệu | Vùng miền (theo khai báo, **chưa qua duyệt**) |
|---|---|---|
| Lúa | 22 | Bắc Trung Bộ 17 · ĐB sông Hồng 3 · toàn quốc 2 |
| Dưa chuột | 5 | ĐB sông Hồng 2 · Bắc Trung Bộ 2 · Trung du miền núi 1 |
| Cà chua | 4 | ĐB sông Hồng · Đông Nam Bộ · Bắc Trung Bộ · toàn quốc |

> ⚠️ **Cột vùng miền chưa đáng tin.** `region` hiện lấy từ gợi ý của seed, tức
> là vùng của *trang đăng bài*, không phải vùng của *nội dung*. Ví dụ nhiều bài
> lúa gắn nhãn Bắc Trung Bộ thực chất nói về Long An, Hải Phòng, Huế vì được
> đăng lại trên cổng Hà Tĩnh. Câu hỏi 5a trong checklist duyệt tài liệu (§27.2)
> tồn tại để sửa đúng chỗ này.

### Nguồn theo cơ quan

| Cơ quan | Tài liệu |
|---|---|
| NTM Hà Tĩnh | 16 |
| Khuyến nông Ninh Bình | 6 |
| Trung tâm Khuyến nông Quảng Trị | 4 |
| Trung tâm Khảo kiểm nghiệm Phân bón Quốc gia | 3 |
| Sở NN&MT Lai Châu | 1 |
| Sở KH&CN TP.HCM | 1 |

---

## 2. Bốn hướng mở rộng đã thử — kết quả thật

Báo cáo trước đề ra bốn hướng để đạt `ASM-07`. Cả bốn đều đã thực hiện:

### 2.1. Phân trang kho lưu trữ ✅ làm được, hiệu quả có hạn

Ba site dùng ba mẫu phân trang khác nhau, xác minh bằng cách so tập liên kết
giữa trang 1 và trang 2 (không suy đoán từ hình dạng URL):

| Site | Mẫu | Sâu nhất |
|---|---|---|
| NTM Hà Tĩnh | `/page-{n}/` | 153 trang |
| Khuyến nông Quảng Trị | `/page/{n}` | — |
| Khuyến nông Ninh Bình | `/page-{n}/` | — |

Quét sâu 40 trang của Hà Tĩnh: trang 40 vẫn có 12 bài mới so với trang 1, tức
là phân trang hoạt động thật. Nhưng tổng số bài về **ba cây trong phạm vi**
gần như không tăng — kho lưu trữ lớn nhưng nội dung chủ yếu về cây khác, chăn
nuôi, thuỷ sản và tin hoạt động.

### 2.2. Sitemap ✅ làm được, nhưng nội dung không lấy được

`khuyennongvn.gov.vn` (Trung tâm Khuyến nông Quốc gia) công bố sitemap chia
theo ngày, khoảng 100 URL mỗi ngày, 182 ngày. Đọc hết cho **43 URL** khớp tên
ba cây.

**Cả 43 đều `empty`:** HTML tải về gần như rỗng, nội dung được render bằng
JavaScript. Đây đúng là giới hạn đã ghi sẵn ở `CRAWLER_GUIDE §8`, không phải
lỗi phát sinh. Sitemap vẫn hữu ích để biết có những bài nào; chỉ là không lấy
được nội dung bằng `requests`.

### 2.3. Tìm kiếm trên chính website ❌ gần như không site nào hỗ trợ

Dò các mẫu endpoint tìm kiếm phổ biến trên 4 tên miền: chỉ
`phanbonquocgia.gov.vn` (nền WordPress) có `?s=`. Ba site còn lại trả 404,
timeout, hoặc trả về nguyên trang chuyên mục bất kể từ khoá.

Đáng chú ý: ngay cả tìm kiếm của `phanbonquocgia.gov.vn` cũng chỉ trả về các
mục menu, không phải kết quả thật.

### 2.4. Bổ sung tên miền mới ✅ có thêm, nhưng ít

Từ menu của `phanbonquocgia.gov.vn` tìm được thứ mà các cổng tin khuyến nông
tỉnh không có: **chuyên mục chỉ chứa bài kỹ thuật**, không lẫn tin hoạt động.
Quét 3 chuyên mục, 20 trang mỗi chuyên mục:

- 150 liên kết bài kỹ thuật
- **Chỉ 2 bài thuộc ba cây trong phạm vi** (*"Kỹ thuật bón phân cho lúa ngắn
  ngày"*, *"Giảm thất thoát lượng đạm trong canh tác lúa"*) — cả hai đều là
  tài liệu kỹ thuật thật và đã được nạp

Phần còn lại là cà phê, cao su, chè, ngô, tiêu, cây ăn quả, hoa cảnh.

---

## 3. Kết luận về `ASM-07`

> **Web công khai Tier 1 của Việt Nam không có sẵn 50–80 tài liệu kỹ thuật
> truy cập được cho đúng ba cây lúa, cà chua, dưa chuột.**

Đây là kết luận rút ra từ số đo, không phải phỏng đoán:

- Đã quét 82 URL, 7 chuyên mục, 3 kho lưu trữ có phân trang, 1 sitemap 182
  ngày, 3 thư viện kỹ thuật
- Đã thử cả 4 hướng mở rộng đã đề ra
- Kết quả bão hoà ở 31 tài liệu

Ba nguyên nhân, theo mức độ ảnh hưởng:

1. **Nội dung có nhưng không lấy được.** 43 tài liệu của Khuyến nông Quốc gia
   nằm sau JavaScript. Đây là khối lớn nhất bị mất.
2. **Đường dẫn đã chết.** Toàn bộ URL của `khuyennong.lamdong.gov.vn` và
   `ttbvtv.lamdong.gov.vn` lấy từ chỉ mục tìm kiếm đều 404 — đã kiểm chứng lại
   bằng `curl` với https và UA trình duyệt. Lâm Đồng là nguồn Tier 1 mạnh nhất
   cho cà chua, và có sẵn một PDF quy trình ban hành chính thức.
3. **Cổng khuyến nông tỉnh là cổng tin tức.** Phần lớn nội dung là tin tập
   huấn, mô hình thử nghiệm, chỉ đạo sản xuất — không phải quy trình canh tác.

### Hệ quả: chưa kiểm chứng được khả năng đọc PDF trên tài liệu thật

Không có nguồn PDF nào tải được. `DEC-027` mới chỉ được kiểm chứng bằng PDF tự
sinh trong `tests/test_crawl.py`, chưa trên tài liệu thật.

### Đề xuất xử lý — cần quyết định

Theo đúng thứ tự ưu tiên đã ghi ở báo cáo trước, phương án trung thực là
**giữ nguyên chuẩn nguồn và ghi rõ giới hạn**, thay vì hạ chuẩn xuống Tier 3.
Ba lựa chọn, xếp theo mức độ khuyến nghị:

| # | Phương án | Đánh đổi |
|---|---|---|
| **A** | **Điều chỉnh `ASM-07` xuống 30–40 tài liệu**, giữ nguyên 3 cây, ghi rõ giới hạn trong báo cáo gửi NextFarm | Trung thực nhất. Recall@K yếu hơn nhưng vẫn đo được. Cà chua và dưa chuột chỉ 4–5 tài liệu nên nhóm `known_answer` cho hai cây này sẽ mỏng |
| B | Thu hẹp còn **lúa + dưa chuột**, bỏ cà chua | KB đặc hơn cho 2 cây, nhưng lệch khỏi phạm vi đã chốt với NextFarm ở DEC-002 |
| C | Thêm trình duyệt không giao diện để lấy 43 tài liệu JavaScript | Được thêm nhiều tài liệu Tier 1 chất lượng cao nhất, nhưng thêm phụ thuộc nặng và nằm ngoài phạm vi đã ghi ở `CRAWLER_GUIDE §8` |

**Khuyến nghị: A**, và ghi mục này vào danh sách "NextFarm cần chuẩn bị"
(§37.6) — nếu NextFarm có sẵn tài liệu kỹ thuật nội bộ cho ba cây này, đó là
cách bù khoảng trống nhanh và đáng tin hơn mọi phương án crawl.

---

## 4. Trích xuất số liệu (`extract.py`)

Trên 31 tài liệu: **193 câu ứng viên**, tất cả `verified: false`.

| Chỉ số | Số câu |
|---|---|
| `luong_phan` | 68 |
| `thoi_vu` | 54 |
| `nang_suat` | 24 |
| `mat_do_gieo` | 15 |
| `khoang_cach` | 12 |
| `ph` | 8 |
| `nhiet_do` | 6 |
| `do_am` | 4 |
| `ec` | 2 |

Theo cây: lúa 109 · dưa chuột 59 · cà chua 25. **12 câu có dấu hiệu rủi ro
cao**, phải duyệt kỹ hơn theo §24.4.

---

## 5. Ba lỗi đã phát hiện và sửa

Cả ba cùng một họ: **so khớp chuỗi con thay vì khớp theo biên từ**, hoặc
**quyết định theo thứ tự khai báo thay vì theo mức độ cụ thể**.

| # | Lỗi | Hậu quả thật | Sửa |
|---|---|---|---|
| 1 | `discover.py`: `"mạ"` khớp trong `"mạnh"` | Bài *"Bước chuyển mạnh mẽ trong xây dựng NTM"* bị gán nhãn cây lúa | Khớp theo biên từ + test hồi quy |
| 2 | `extract.py`: `"ph"` khớp trong `"cát pha"`, `"phát"`, `"phân"`, `"phủ"` | **73/129 câu bị gán nhãn pH** trong khi thực tế chỉ 8 câu nói về pH. Đã kiểm lại cả 8 câu sau khi sửa, cả 8 đều khớp thật | Khớp theo biên từ |
| 3 | `extract.py`: chọn chỉ số theo thứ tự dict | Câu *"Bón lót: … kg lân supe"* bị gán nhãn `ph` chỉ vì `ph` khai báo trước `luong_phan` | Chọn theo từ khoá dài nhất |

Lỗi 2 và 3 có sẵn trong `extract.py` gốc của `CRAWLER_GUIDE`.

**Một lỗi thứ tư, nghiêm trọng hơn, thuộc loại khác:**

`crawl.py --only` ghi đè toàn bộ `manifest.json` thay vì gộp. Một lần chạy
`--only` hai nguồn đã **xoá 80 bản ghi trước đó** — tức là mất bằng chứng thật
mà không có dấu hiệu gì. Khôi phục từ git, tách hàm `gop_manifest` và thêm 3
test hồi quy.

Lỗi này đáng chú ý vì nó vi phạm đúng nguyên tắc 2 của §23.1 (*lưu bằng chứng
gốc*) theo cách khó thấy nhất: không có thông báo lỗi, không có ngoại lệ, chỉ
là dữ liệu biến mất.

---

## 6. Ghi chú vận hành

`CRAWLER_CONTACT_EMAIL` **vẫn chưa được đặt**, nên User-Agent thiếu địa chỉ
liên hệ. `DEC-028b` yêu cầu có liên hệ thật trước khi crawl diện rộng. Cần
điền vào `.env` (đã gitignore) trước đợt crawl lớn tiếp theo.

Tổng số request đã gửi trong cả ba đợt: khoảng 500, luôn giữ tối thiểu 3 giây
giữa hai request cùng tên miền, và luôn kiểm `robots.txt` trước.
