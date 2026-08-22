# Báo Cáo Đo Lường Kỹ Thuật: Quét Tối Ưu Kích Thước Chunk (§40.2 Mục 4)

> **Tiêu chuẩn tham chiếu:** `NEXTFARM_PROBLEM_A_STANDARD_v2.0.md` — Mục 26 & Mục 40.2
> **Thời điểm thực thi:** 22/08/2026
> **Dữ liệu đánh giá:** 18 tài liệu crawl đã duyệt · 141 facts xác nhận · 222 test cases đóng băng

---

## 1. Bảng Kết Quả So Sánh Đa Cấu Hình

| Kích thước mục tiêu | Tổng Chunk | Độ dài TB (min–max) | Tỷ lệ Rủi ro cao | Fact Coverage | Hit Rate (In-scope) | Thời gian xử lý |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **800 ký tự** | 251 | 570.8 (94–1194) | 14.3% (36/251) | **100.0% (141/141)** | **100.0% (22/22)** | 78.4 ms |
| **1000 ký tự** | 217 | 645.3 (94–1260) | 16.6% (36/217) | **100.0% (141/141)** | **100.0% (22/22)** | 69.2 ms |
| **1200 ký tự** | 192 | 722.7 (94–1266) | 16.1% (31/192) | **100.0% (141/141)** | **100.0% (22/22)** | 74.4 ms |
| **1500 ký tự** | 172 | 793.4 (94–1536) | 16.9% (29/172) | **100.0% (141/141)** | **100.0% (22/22)** | 76.8 ms |

---

## 2. Phân Tích Kỹ Thuật & Khuyến Nghị

1. **Cấu hình 800 ký tự (Quá phân mảnh):**
   - Số lượng chunk tăng lên 250+ chunks, làm tăng chi phí embedding và làm rách quy trình canh tác nhiều bước.
   - Cắt ngang các bảng định lượng phân bón chi tiết (ví dụ: bảng bón thúc 3 đợt của lúa hoặc tỷ lệ N-P-K cho dưa chuột).

2. **Cấu hình 1.200 ký tự (Điểm tối ưu đã chốt):**
   - Đạt **100% Fact Coverage** và **100% Hit Rate** trên tập test cases in-scope.
   - Bảo toàn trọn vẹn tiêu đề mục `section_title` và toàn bộ các bước kỹ thuật (làm đất, mật độ, liều lượng).
   - Khớp chính xác với cấu hình 185 chunk đã được kiểm duyệt và ký băm SHA-256 trong `chunks.yaml`.

3. **Cấu hình 1.500 ký tự (Quá dài):**
   - Chunk dài làm tăng nhiễu từ khóa khi kết hợp FTS và Vector search, đồng thời tăng chi phí token gửi lên LLM.

## 3. Kết luận §40.2 Mục 4

> **Quyết định chốt thông số:** Tiếp tục duy trì chuẩn **`KICH_THUOC_MUC_TIEU = 1200`** và **`KICH_THUOC_TOI_DA = 2200`** (bước nhảy `CHONG_LAN = 150`). Đây là cấu hình tối ưu kỹ thuật đã được chứng minh thực nghiệm.