# Báo Cáo Đo Lường Kỹ Thuật: Quét Tối Ưu Kích Thước Chunk (§40.2 Mục 4)

> **Tiêu chuẩn tham chiếu:** `NEXTFARM_PROBLEM_A_STANDARD_v2.0.md` — Mục 26 & Mục 40.2
> **Thời điểm thực thi:** 22/08/2026
> **Dữ liệu đánh giá:** 18 tài liệu crawl đã duyệt · 141 facts xác nhận · 222 test cases đóng băng

---

## 1. Bảng Kết Quả So Sánh Đa Cấu Hình

| Kích thước mục tiêu | Tổng Chunk | Độ dài TB (min–max) | Tỷ lệ Rủi ro cao | Fact Coverage | Hit Rate (In-scope) | Thời gian xử lý |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **800 ký tự** | 251 | 570.8 (94–1194) | 14.3% (36/251) | **100.0% (141/141)** | **100.0% (22/22)** | 92.1 ms |
| **1000 ký tự** | 217 | 645.3 (94–1260) | 16.6% (36/217) | **100.0% (141/141)** | **100.0% (22/22)** | 98.8 ms |
| **1200 ký tự** | 192 | 722.7 (94–1266) | 16.1% (31/192) | **100.0% (141/141)** | **100.0% (22/22)** | 99.7 ms |
| **1500 ký tự** | 172 | 793.4 (94–1536) | 16.9% (29/172) | **100.0% (141/141)** | **100.0% (22/22)** | 98.0 ms |

---

## 2. Bảng trên nói được gì

**Không phân biệt được cấu hình nào.** Cả 4 cấu hình đều cho Fact Coverage 100.0% (141/141) và Hit Rate 100.0% (22/22). Hai chỉ số chất lượng duy nhất trong bảng đứng yên trên toàn dải 800–1500 ký tự.

Nghĩa là phép đo này **không đủ độ phân giải để chọn kích thước chunk**. Nó chứng minh được một điều hẹp hơn nhưng có thật: trong dải đã thử, không kích thước nào làm mất fact hay trượt câu hỏi in-scope.

Những chỉ số CÓ khác nhau giữa các cấu hình — tổng số chunk, độ dài trung bình, tỷ lệ chunk rủi ro cao — là đặc tính của phép cắt, không phải thước đo chất lượng trả lời. Không thể chốt tham số bằng chúng.

> Bản báo cáo trước kết luận 1.200 ký tự là *"cấu hình tối ưu kỹ thuật đã được chứng minh thực nghiệm"*, kèm nhận định 800 ký tự *"cắt ngang bảng định lượng phân bón"* và 1.500 ký tự *"tăng nhiễu từ khóa"*. Không có số nào trong bảng đo hai điều đó. Đã bỏ.

## 3. Vì sao vẫn giữ 1.200

Không phải vì phép đo chọn nó. Vì **đổi kích thước chunk sẽ vô hiệu hoá toàn bộ quyết định duyệt lẻ đang có**.

`chunk_id` dựng theo thứ tự trong tài liệu (`knowledge/ingestion/load.py:153`):

```python
cid = rec["id"] + "#" + str(c.ordinal)
```

Đổi hằng số cắt → mọi `ordinal` xê dịch → một `chunk_id` cũ trỏ sang đoạn văn khác. Khoá duyệt đã chuyển sang sha256 nội dung nên hỏng theo hướng an toàn (không khớp = chưa duyệt = bị chặn), nhưng hậu quả vận hành vẫn là **31 chunk rủi ro cao phải duyệt lại từ đầu**.

Đo thực nghiệm 2026-08-22 khi hạ 1200 → 700: 292 chunk thành 440, 31 chunk rủi ro cao thành 41. Nếu còn khoá theo `chunk_id`, 10 quyết định duyệt cũ sẽ đè lên văn bản khác — một trong số đó mang `approved=True`.

## 4. Kết luận §40.2 Mục 4

> **Giữ `KICH_THUOC_MUC_TIEU = 1200`, `KICH_THUOC_TOI_DA = 2200`, `CHONG_LAN = 150`.**
>
> Lý do là **chi phí duyệt lại**, không phải ưu thế đo được. Trên dải 800–1500, phép đo hiện có không phân biệt được cấu hình nào tốt hơn. Muốn chốt bằng số đo thật thì cần một thước phân biệt được — ví dụ Recall@K theo từng cấu hình trên tập v3, hoặc chấm tay chất lượng trích dẫn — và cần chấp nhận ngân sách duyệt lại 31 chunk.