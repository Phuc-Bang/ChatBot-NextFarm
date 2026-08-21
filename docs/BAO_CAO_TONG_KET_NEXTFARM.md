# BÁO CÁO TỔNG KẾT DỰ ÁN NEXTFARM — BÀI TOÁN A: CHỐNG BỊA ĐẶT

> **Dự án:** Trợ lý Nông nghiệp Thông minh NextFarm AI (PoC Giai đoạn 1)  
> **Mã nguồn:** `github.com/Phuc-Bang/ChatBot-NextFarm`  
> **Ngày hoàn thành:** 21/08/2026  
> **Quy chuẩn kỹ thuật tham chiếu:** `NEXTFARM_PROBLEM_A_STANDARD_v2.0.md`  
> **Trạng thái kiểm thử:** 310/310 Unit Tests PASSED (100%) · Working Tree Clean

---

## 1. TỔNG QUAN DỰ ÁN & MỤC TIÊU CỐT LÕI

Dự án NextFarm PoC Giai đoạn 1 tập trung giải quyết **Bài toán A: Chống bịa đặt (Anti-Hallucination & AI Safety)** trong hệ thống tư vấn kỹ thuật nông nghiệp cho nông dân trồng **Lúa**, **Cà chua** và **Dưa chuột**.

### Bốn hiện tượng rủi ro của hệ thống cũ (LLM trần)
1. **Hiện tượng A1 (Bịa số liệu vườn):** Nông dân hỏi *"độ ẩm nhà màng khu B hiện tại bao nhiêu?"*, LLM tự ý bịa ra *"độ ẩm hiện tại là 75%"*, gây nguy cơ làm chết cây trồng.
2. **Hiện tượng A2 (Bịa tính năng ứng dụng):** Nông dân hỏi *"ứng dụng NextFarm có tính năng dự báo giá nông sản không?"*, LLM tự nhận có tính năng dù hệ thống chưa phát triển.
3. **Hiện tượng A3 (Khuyến nghị sai cây trồng / vùng sinh thái):** Áp dụng quy trình bón phân của vùng đất cát Ninh Bình cho vùng đất phèn ĐBSCL, hoặc tư vấn kỹ thuật cho cây ngoài phạm vi (cà phê, sầu riêng).
4. **Hiện tượng A4 (Tiếng Việt không dấu & phương ngữ):** Nông dân gõ *"ca chua bi sau duc qua"* hoặc dùng từ địa phương (*"sào Bắc Bộ"*, *"sào Trung Bộ"*), LLM đoán dấu sai dẫn đến tư vấn nhầm liều lượng.

---

## 2. KẾT QUẢ THỰC NGHIỆM ĐỐI CHỨNG (C0 vs C2)

Thực nghiệm đo lường trên **222 test case độc lập** thuộc bộ kiểm thử đóng băng `v3`, chạy trên cùng mô hình nền tảng `gemini-3.1-flash-lite`:

| Chỉ số Đánh giá | C0: LLM Trần (Hiện trạng) | C2: NextFarm PoC (Giải pháp) | Mức độ Cải thiện |
|---|:---:|:---:|:---:|
| **Tổng số ca bịa số liệu** | **61 ca** (27,5%) | **0 ca** (0,0%) | **Triệt tiêu 100%** |
| • Bịa số liệu vườn (A1) | 8 ca | **0 ca** | Triệt tiêu hoàn toàn |
| • Bịa tính năng ứng dụng (A2) | 17 ca | **0 ca** | Triệt tiêu hoàn toàn |
| • Rò rỉ lệnh điều khiển thiết bị | 14 ca | **0 ca** | An toàn tuyệt đối |
| • Nhận câu hỏi ngoài phạm vi (A3) | 22 ca | **0 ca** | Chặn 100% |
| **Tỷ lệ trả lời sai (`false_answer_rate`)** | **77,0%** | **3,2%** | Giảm 24 lần |
| **Độ chính xác khi trả lời (`accuracy_on_answered`)** | **1,2%** | **66,7%** | Tăng 55 lần |
| **Tỷ lệ nhận diện ca cần từ chối (`abstention_recall`)** | **3,4%** | **99,3%** | Bắt trúng 147/148 ca |
| **Độ trễ xử lý $p_{50}$** | 1.840 ms | **11 ms** | Nhanh hơn 167 lần |
| **Độ trễ xử lý $p_{95}$** | 11.451 ms | **8.084 ms** | Đạt ngân sách kỹ thuật |
| **Chi phí API / 222 câu hỏi** | $0.0369 | **$0.0526** | ~$0.0002 / câu hỏi |

---

## 3. NGUYÊN TẮC THIẾT KẾ & KIẾN TRÚC KỸ THUẬT 7 CHẶNG

Hệ thống được thiết kế theo nguyên lý **"LLM không phải nguồn sự thật và không thể tự chặn bịa"**. Rào chắn an toàn được thực thi bằng thuật toán tất định (*deterministic code*) và cổng dữ liệu tại CSDL:

```
                              CÂU HỎI NÔNG DÂN
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  [Chặng 1] CHUẨN HOÁ TIẾNG VIỆT 4 LỚP (Deterministic)   │
        │  • Khử dấu kết hợp  • Chuyển ngữ địa phương             │
        │  • Chuẩn hoá đơn vị • Bóc tách thực thể cây trồng       │
        └────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  [Chặng 2] INTENT ROUTER 4 NHÁNH (<10ms, 0 Token)       │
        │  ├── garden_data    ───► [TỪ CHỐI AN TOÀN] (Chặn A1)    │
        │  ├── product_feature───► [TỪ CHỐI AN TOÀN] (Chặn A2)    │
        │  ├── device_control ───► [TỪ CHỐI AN TOÀN] (Chặn Lệnh)  │
        │  └── agronomy_knowledge ──► Đi tiếp                     │
        └────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  [Chặng 3] SCOPE CHECK: Lúa / Cà chua / Dưa chuột?      │
        │  • Ngoài phạm vi ──► [TỪ CHỐI] (Chặn A3)                │
        │  • Chưa rõ cây   ──► [HỎI LẠI ĐỂ LÀM RÕ]                │
        │  • Đúng phạm vi  ──► Đi tiếp                            │
        └────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  [Chặng 4] HYBRID RETRIEVAL (Kênh truy xuất lai)        │
        │  • Halong Embedding Local (Vector) + FTS + Trigram      │
        │  • Hợp nhất xếp hạng RRF (Reciprocal Rank Fusion)       │
        │  • Cổng chặn DEC-005: CHỈ đọc từ view indexable_chunk   │
        └────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  [Chặng 5] EVIDENCE PACK GENERATOR                      │
        │  • Đóng gói JSON nguyên văn kèm chunk_id & Source Tier  │
        └────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  [Chặng 6] MÔ HÌNH NGÔN NGỮ (LLM GENERATOR)             │
        │  • Đọc Evidence Pack, sinh câu trả lời có gắn [cid]     │
        │  • Cấu hình thinking_budget=0 tối ưu chi phí & tốc độ   │
        └────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │  [Chặng 7] GROUNDING VALIDATOR 3 TẦNG (Rào chắn cuối)   │
        │  • Tầng 1: Kiểm tra cấu trúc trích dẫn                  │
        │  • Tầng 2: Đối chiếu số liệu tất định (Regex extractor) │
        │  • Tầng 3: Kiểm chứng nội dung ngữ nghĩa                │
        │  ├── ĐẠT       ───► Trả lời kèm trích dẫn nguồn URL gốc │
        │  └── KHÔNG ĐẠT ───► Chuyển sang TỪ CHỐI AN TOÀN         │
        └─────────────────────────────────────────────────────────┘
```

### Điểm nhấn kiến trúc:
1. **Chặn sớm không tốn chi phí:** 141/222 case (63,5%) được xử lý và từ chối dứt điểm ở Chặng 1, 2, 3 trong dưới 16ms (p95 = 13ms, trung vị 6ms), tiêu thụ **đúng 0 token** và không chạm vào CSDL.
2. **Kênh Vector Local tốc độ cao:** Sử dụng mô hình `Halong Embedding` chạy trực tiếp trong RAM bằng `numpy`, không tốn chi phí gọi API bên ngoài, độ trễ chỉ 5–15ms.
3. **Cổng kiểm soát dữ liệu DEC-005 tại CSDL:** Toàn bộ câu lệnh tìm kiếm đều chỉ truy vấn qua view `indexable_chunk` (`WHERE document.approved = true AND chunk.approved = true AND (NOT is_high_risk OR reviewed_high_risk)`). Không một văn bản chưa duyệt nào có thể lọt vào bộ nhớ RAG.

---

## 4. QUY TRÌNH KIỂM DUYỆT TRI THỨC (HUMAN-IN-THE-LOOP)

Nhằm đảm bảo tính chính thống và an toàn pháp lý cho khuyến nông:
* **Tài liệu nguồn (Documents):** Thu thập 31 văn bản kỹ thuật từ 6 cơ quan khuyến nông uy tín (Sở NN&PTNT Ninh Bình, Hà Tĩnh, Lai Châu...). Đã duyệt **18 tài liệu chuẩn** (`documents.yaml`), loại bỏ 13 tài liệu dạng tin bài tổng hợp.
* **Số liệu Fact bóc tách:** Bóc tách 141 fact candidates. Đã xác nhận **65 facts chính thức** (`facts.yaml`) về độ pH, mật độ gieo trồng, liều lượng bón phân qua các thời kỳ.
* **Chunk rủi ro cao (High-risk Chunks - DEC-029):** 
  * Rà soát 44 chunk mang nội dung phân bón / thuốc BVTV.
  * **23 chunk ĐÃ DUYỆT (`approved = true`)**: Các quy trình liều lượng chuẩn xác cho dưa chuột, cà chua, lúa.
  * **21 chunk LOẠI BỎ (`approved = false`)**: Các chunk tiêu đề, footer, tin tức cá nhân.
  * Kho tri thức tìm kiếm chính thức đạt **185 chunks indexable**.

---

## 5. CHUỖI 3 PHIÊN BẢN KIỂM THỬ (v1 $\rightarrow$ v2 $\rightarrow$ v3)

Để chứng minh tính khách quan và khoa học của thực nghiệm:
* **Phiên bản `v1`:** Bộ test sơ khai sinh bằng LLM $\rightarrow$ Phát hiện 9/30 ca bịa số liệu do LLM tự suy diễn. Được giữ nguyên làm chứng tích đối chứng.
* **Phiên bản `v2`:** Dựng từ bảng Fact đã duyệt $\rightarrow$ Phát hiện lọt đơn vị suy diễn qua tay người duyệt (ví dụ: `/1000m2` suy diễn từ câu lân cận).
* **Phiên bản `v3` (Đóng băng chính thức):**
  * Xây dựng hàng rào kỹ thuật `so_khong_truy_duoc()`: Mọi con số trong đáp án chuẩn bắt buộc phải có trong câu nguyên văn hoặc trường `value_min`/`value_max` người duyệt chép ra.
  * Quy mô: **12 nhóm, 222 test case, 0 con số bịa/suy diễn**.
  * Toàn bộ 222 case được niêm phong bằng chữ ký SHA-256 trong `manifest.json`.

---

## 6. GIAO DIỆN NGƯỜI DÙNG & CÔNG CỤ QUẢN TRỊ

Hệ thống cung cấp 2 giao diện chuyên biệt được xây dựng theo tiêu chuẩn UI/UX hiện đại (Glassmorphism, Responsive, Light/Dark Mode):

### 1. 🌾 Giao diện Chat Nông dân (`/`)
* Giao diện tối ưu hóa cho bà con nông dân: cỡ chữ lớn, ngôn ngữ thân thiện, hỗ trợ tiếng Việt có dấu lẫn không dấu.
* Phân biệt rõ ràng bằng màu sắc: Câu trả lời có căn cứ màu xanh ngọc kèm trích dẫn văn bản chính thống `[cid]`; Câu từ chối an toàn màu vàng ấm áp kèm giải thích lịch sự.

### 2. 📊 Bảng Quản trị & Kiểm định RAG (`/admin`)
* **KPI Bento Grid:** Tổng lượt hỏi, tỷ lệ chặn an toàn, dung lượng kho tri thức (185 chunk), độ trễ $p_{50}/p_{95}$, tổng token và chi phí tích lũy (USD).
* **Biểu đồ Tiến trình:** Phân rã độ trễ qua 5 chặng và phân loại các lý do từ chối an toàn.
* **Audit Log Thời gian thực:** Bảng nhật ký truy vấn có tính năng tìm kiếm từ khóa tức thì (`Instant Search`) và bộ lọc trạng thái (*Tất cả / Chỉ ca đã chặn / Chỉ ca đã trả lời*).

---

## 7. ĐÁNH GIÁ CHẤT LƯỢNG MÃ NGUỒN & ĐỘ TIN CẬY

* **Bộ kiểm thử tự động:** **310/310 Unit Tests PASSED (100%)** với độ phủ toàn diện từ chuẩn hóa, định tuyến, phân mảnh, truy xuất lai, kiểm duyệt fact, đến mô phỏng pipeline qua HTTP thật.
* **Bảo vệ rò rỉ dữ liệu:** Toàn bộ API keys, chuỗi kết nối CSDL và biến môi trường được cách ly trong `.env`, loại trừ tuyệt đối khỏi Git repository.
* **Khả năng tái lập 100%:** Chỉ với 1 lệnh `make ingest`, toàn bộ kho tri thức 292 chunk / 185 chunk indexable / 141 fact được tái lập hoàn hảo từ các tệp cấu hình YAML có version control trong Git.

---

## 8. LỘ TRÌNH PHÁT TRIỂN & BÀN GIAO TIẾP THEO

1. **Giai đoạn 1.5 (Production Packaging):** Đóng gói Docker Compose / Helm Chart cho Kubernetes, kết nối CI/CD tự động chạy 310 tests khi triển khai.
2. **Giai đoạn 2 (Mở rộng Cây trồng):** Mở rộng kho khuyến nông cho các cây ăn trái & công nghiệp giá trị cao (Sầu riêng, Xoài, Bơ, Cà phê, Hồ tiêu), quy mô 2.000+ chunks.
3. **Giai đoạn 3 (Tích hợp IoT NextFarm):** Kết nối API cảm biến vườn thực tế (chuyển nhóm `garden_data` sang truy vấn có phân quyền) và thiết lập rào chắn bảo vệ xác nhận 2 lớp cho lệnh điều khiển thiết bị (`device_control`).

---

*Báo cáo được lập bởi Đội ngũ Kỹ thuật NextFarm PoC.*
