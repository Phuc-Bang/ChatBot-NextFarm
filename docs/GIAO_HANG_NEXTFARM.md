# Bàn giao PoC — Bài toán A: Chống bịa đặt

> **Ngày:** 2026-08-20 · **Trạng thái:** PoC giai đoạn 1
> Mã nguồn: `github.com/Phuc-Bang/ChatBot-NextFarm`
> Quy chuẩn kỹ thuật: [`NEXTFARM_PROBLEM_A_STANDARD_v2.0.md`](NEXTFARM_PROBLEM_A_STANDARD_v2.0.md)

Tài liệu này trả lời 6 câu hỏi ở mục 6 của đề bài, kèm sổ giả định, bản kê luồng dữ liệu và bảng ánh xạ tiêu chí nghiệm thu.

**Nguyên tắc viết tài liệu này:** mọi con số đều đến từ một lần chạy đo cụ thể, tái lập được bằng lệnh ghi kèm. Chỗ nào chưa có dữ liệu thì ghi `[EXT]` (chờ NextFarm) hoặc `[ASM]` (giả định của đội) — **không điền số ước chừng**.

---

## Tóm tắt kết quả

Trên 222 case của tập kiểm thử đã đóng băng, cùng một model, cùng cấu hình truy xuất — **ba** cấu hình, mỗi lần thêm đúng một bậc:

| | LLM trần<br>(hiện trạng) | Chỉ thêm tài liệu<br>(RAG) | PoC này<br>(RAG + kiểm soát) |
|---|---:|---:|---:|
| **Tổng ca bịa đặt** | **61** | **23** | **0** |
| Trả lời sai (`false_answer_rate`) | 77,0% | 23,0% | **0,9%** |
| Đúng khi có trả lời | 1,2% | 23,9% | **90,9%** |
| Bắt được ca cần từ chối | 3,4% | 69,6% | **100,0%** |
| Độ trễ p95 | 11.451 ms | 11.895 ms | **6.185 ms** |
| Chi phí cả lượt chạy 222 case | — | $0,1231 | **$0,0527** |

> **Cột giữa là cột đáng chú ý nhất.** Cho mô hình đủ tài liệu — đúng cách làm
> RAG thông thường — vẫn còn **23 ca bịa**: 4 ca bịa số liệu vườn, 7 ca bịa tính
> năng app, 3 ca rò lệnh thiết bị, 9 ca nhận câu ngoài phạm vi. **RAG một mình
> không giải quyết được bài toán NextFarm đặt ra.** Chỉ cơ chế kiểm soát mới đưa
> về 0 — và nó còn làm chi phí giảm gần một nửa, vì 141/222 lượt bị chặn trước
> khi chạm mô hình, tốn 0 token.

Chi tiết: [`docs/reports/BAO_CAO_SO_SANH.md`](reports/BAO_CAO_SO_SANH.md)

---

## Câu 1 — Kinh nghiệm và giải pháp sẵn có, mạnh nhất ở đâu

Đội ngũ thực hiện sở hữu năng lực chuyên sâu về **kỹ thuật RAG có kiểm soát (Constrained & Governed RAG)**, xử lý ngôn ngữ tự nhiên tiếng Việt chuyên ngành nông nghiệp, và thiết kế hệ thống rào chắn an toàn (AI Safety & Guardrails) với các thế mạnh đo lường được:

### 1. Kiến trúc RAG kiểm duyệt đa tầng (Governed Knowledge Architecture)
* **Nguyên tắc "Chứng cứ trên hết"**: Phân định ranh giới tuyệt đối giữa *kho tri thức đã kiểm duyệt* và *năng lực sinh văn bản của LLM*. Dữ liệu khuyến nông bắt buộc đi qua cổng kiểm duyệt con người (Human-in-the-loop DEC-005, DEC-020, DEC-029) và được cưỡng chế bằng view `indexable_chunk` ở tầng CSDL PostgreSQL.
* **Truy xuất lai tối ưu cho tiếng Việt (Hybrid Retrieval)**: Kết hợp mô hình embedding ngữ nghĩa `Halong Embedding` (local) với Full-Text Search và Trigram (RRF ranking), giải quyết triệt để bài toán câu hỏi không dấu, phương ngữ địa phương và viết tắt nông học mà không cần gọi LLM đoán dấu (tiết kiệm chi phí và triệt tiêu nguồn phát sinh ảo giác A4).

### 2. Hệ thống Guardrail tất định chặn sớm (Early Deterministic Guardrails)
* **Chặn sớm không tốn token**: Tách bạch bộ định tuyến ý định (*Intent Router*) và kiểm tra phạm vi (*Scope Check*) độc lập trước khi chạm vào CSDL hay gọi mô hình ngôn ngữ. **141/222 ca kiểm thử được xử lý trong dưới 16ms (p95 = 13ms, trung vị 6ms) và tiêu thụ đúng 0 token**.
* **Bộ kiểm chứng căn cứ 3 tầng (Grounding Validator)**: Đối chiếu cấu trúc, trích xuất toàn bộ số liệu trong câu trả lời để so khớp tất định với Evidence Pack. Nếu model tự ý suy diễn hoặc bịa số liệu $\rightarrow$ lập tức chuyển sang từ chối an toàn.

### 3. Phương pháp luận phát triển hướng đánh giá (Evaluation-Driven Development)
* Xây dựng bộ kiểm thử 222 test case đóng băng thuộc 12 nhóm kiểm định nghiêm ngặt, có hàng rào kiểm tra tự động `so_khong_truy_duoc()` để loại bỏ hoàn toàn các đáp án suy diễn.
* **Kết quả đo thực tế**: Triệt tiêu **100% hiện tượng bịa đặt (từ 61 ca ở LLM trần xuống 0 ca)**, tỷ lệ nhận diện ca cần từ chối đạt **100,0%** và độ trễ p50 chỉ **15 ms**. Cấu hình trung gian C1 (có tài liệu, chưa có cơ chế kiểm soát) còn **23 ca bịa** — RAG một mình không giải quyết được bài toán.

---

## Câu 2 — Kiến trúc tổng thể

```
Câu hỏi của nông dân
   ↓
① Chuẩn hoá tiếng Việt        4 lớp, deterministic, KHÔNG gọi model
   ↓
② Intent Router               4 nhánh — điểm quan trọng nhất
   ├── agronomy_knowledge  →  đi tiếp
   ├── garden_data         →  TỪ CHỐI + chỉ chỗ tra
   ├── product_feature     →  TỪ CHỐI
   └── device_control      →  TỪ CHỐI tuyệt đối
   ↓
③ Scope Check                 lúa / cà chua / dưa chuột?
   ↓
④ Truy xuất lai               vector + FTS + trigram, hợp nhất RRF
   ↓
⑤ Evidence Pack               JSON, nguyên văn, có chunk_id
   ↓
⑥ LLM                         đầu ra JSON, mỗi câu gắn chunk_id
   ↓
⑦ Grounding Validator         cấu trúc → số liệu → ngữ nghĩa
   ├── đạt        →  Trả lời + nguồn bấm về được URL gốc
   └── không đạt  →  TỪ CHỐI
```

### Ba quyết định thiết kế quan trọng nhất

**1. LLM không phải nguồn sự thật — và không phải thứ chặn bịa.**

Prompt là *lời đề nghị*, model có thể không nghe. **Grounding Validator là cơ chế**, model không vượt qua được. Tầng 2 (đối chiếu số liệu) hoàn toàn deterministic: trích mọi con số trong câu trả lời, đối chiếu với số có trong Evidence Pack, lệch là chặn — không phụ thuộc model nào.

Test tự động chứng minh điều này: khi model **khai là có đủ căn cứ** nhưng đưa ra con số không có trong tài liệu, hệ thống vẫn chặn.

**2. Chặn sớm thì rẻ.** Ba chặng đầu không gọi model nào:

| Chặng | Độ trễ trung bình | Số case đi qua |
|---|---:|---:|
| Chuẩn hoá | 0 ms | 222 |
| Intent Router | 5 ms | 222 |
| Scope Check | 4 ms | 133 |
| Truy xuất | 220 ms | 81 |
| Gọi model | 4.805 ms | 81 |

**141/222 case bị chặn trước khi chạm cơ sở dữ liệu.** Nhóm `device_control` (14 case) có trung vị **1 ms**, chậm nhất 8 ms — và **0 token**.

**3. Không duyệt thì không vào kho.** Cổng chặn là view `indexable_chunk` ở tầng cơ sở dữ liệu, không phải lời hứa trong code:

```
292 chunk crawl được  →  185 chunk vào được kho
                          107 chunk bị chặn (13/31 tài liệu bị loại
                          + 20/44 chunk rủi ro cao chưa duyệt lẻ)
```

---

## Câu 3 — Mong muốn hợp tác

Đội ngũ thực hiện mong muốn đồng hành dài hạn cùng NextFarm để đưa giải pháp từ PoC vào ứng dụng thực tế trên diện rộng:

### 1. Triển khai và Đóng gói Production (Giai đoạn 1.5)
* Đóng gói toàn bộ hệ thống (FastAPI, PostgreSQL + pgvector, local embedding) thành Docker Compose / Kubernetes manifest chuẩn enterprise.
* Tích hợp pipeline CI/CD kiểm thử tự động với bộ 339 unit tests và bộ runner đánh giá chất lượng RAG trước mỗi bản release.
* Cấu hình dashboard giám sát token, chi phí và tỷ lệ từ chối theo thời gian thực (đã có sẵn tại `/admin`).

> **`/admin` mặc định an toàn, nhưng khoá hiện tại là khoá tĩnh — đọc trước khi triển khai.**
>
> `/admin` và ba endpoint `/api/admin/*` phơi ra **toàn bộ nhật ký truy vấn**:
> câu hỏi nguyên văn của người dùng, câu trả lời, số token và chi phí từng lượt.
>
> Cửa kiểm ở [`app/main.py`](../app/main.py) → `kiem_quyen_admin`:
>
> | `ADMIN_TOKEN` trong `.env` | hành vi |
> |---|---|
> | để trống (mặc định) | chỉ nhận request từ `127.0.0.1`; địa chỉ khác → **403** |
> | có đặt | mọi request phải kèm header `X-Admin-Token` đúng — loopback **không** được miễn |
>
> Điểm quan trọng: một lần deploy đổi `--host 127.0.0.1` thành `0.0.0.0` mà quên
> cấu hình sẽ **từ chối**, chứ không lặng lẽ phục vụ. Đó là lý do cửa này tồn
> tại — một dòng ghi chú trong tài liệu không chặn được gì.
>
> **Vẫn còn việc NextFarm phải quyết:** khoá tĩnh là lớp tối thiểu để mặc định
> an toàn, **không phải hệ thống danh tính** — nó không phân biệt được ai đang
> xem, không thu hồi được quyền của một người, không ghi vết truy cập. Triển
> khai thật nên đặt OAuth/SSO ở reverse proxy và giữ `ADMIN_TOKEN` làm tầng
> trong. Đội không chốt cơ chế thay NextFarm vì nó phụ thuộc hạ tầng đang dùng.

### 2. Mở rộng Kho tri thức sang các Cây trồng Chủ lực tiếp theo (Giai đoạn 2)
* Mở rộng hạ tầng crawler và công cụ kiểm duyệt bán tự động cho các cây ăn trái và cây công nghiệp giá trị cao của NextFarm: Sầu riêng, Xoài, Bơ, Cà phê, Hồ tiêu.
* Nâng dung lượng kho tri thức lên 2.000+ chunks chuẩn khuyến nông. **Ở quy mô đó mới chuyển sang chỉ mục HNSW của pgvector** — hiện PoC cố ý *chưa* dùng nó: với 185 chunk, quét toàn bộ bằng numpy trong RAM nhanh tương đương mà không phải giữ đồng bộ thêm một chỉ mục nữa (xem chú thích đầu [`vector.py`](../app/services/retrieval/vector.py)). Ngưỡng chuyển đổi là vài chục nghìn chunk.

### 3. Tích hợp Dữ liệu Cảm biến Vườn & Điều khiển Thiết bị An toàn (Giai đoạn 3)
* Kết nối an toàn với hệ thống IoT của NextFarm: chuyển hướng các câu hỏi nhóm `garden_data` sang truy vấn API telemetry thực tế (có xác thực phân quyền nông hộ).
* Thiết lập rào chắn bảo vệ 2 lớp (Human-Confirmation + Safety Thresholds) cho lệnh điều khiển thiết bị (`device_control`), đảm bảo AI chỉ đóng vai trò soạn thảo lệnh, quyền bấm xác nhận tưới/bật van luôn thuộc về nông dân.

### 4. Cam kết Hỗ trợ Kỹ thuật & Tối ưu Chi phí Vận hành
* Đảm bảo hệ thống vận hành ổn định, tối ưu hoá chi phí API LLM.

> **Một điều trong mục này là CAM KẾT, chưa phải hiện trạng:**
>
> - **Mức SLA** cần NextFarm nêu yêu cầu rồi hai bên chốt. PoC chạy cục bộ, chưa có số đo uptime nào để hứa một con số.
>
> **Đã có và đã đo:**
>
> - **Chỉ gọi model khi có bằng chứng** — 141/222 ca bị chặn trước khi chạm model, tốn **0 token**. Đây là khoản tiết kiệm lớn nhất và nó đã nằm sẵn trong `Ti` = 702.
> - **Embedding chạy local** — chi phí biên bằng 0, kho tri thức không rời máy.
>
> - **Prompt caching: KHÔNG áp dụng được cho kiến trúc này.** Đã đo và đã thử 2026-08-21, không phải "chưa làm". Trên các lượt *có* gọi model, prompt trung bình 1.704 token, tách ra: mẫu prompt cố định **175 token (10,3%)**, Evidence Pack + câu hỏi **1.529 token (89,7%)**. Chỉ phần cố định cache được, và Gemini từ chối thẳng: `Cached content is too small. total_token_count=175, min_total_token_count=1024`. Muốn dùng được thì phải cache cả Evidence Pack — nhưng nó đổi theo từng câu hỏi, nên không có gì để tái dùng. Đây là hệ quả trực tiếp của việc RAG lấy chunk khác nhau cho câu hỏi khác nhau, không phải thiếu sót cài đặt.
>
> Ba điều trên nói cùng một chuyện: chi phí ở kiến trúc này được cắt bằng **không gọi model**, không phải bằng làm cho lượt gọi rẻ đi.

---

## Câu 4 — Ước lượng công sức

### Giai đoạn 1 — Bài toán A (phần đã làm)

| Phase | Nội dung | Ngày công |
|---|---|---:|
| P0–P1 | Nền móng, crawler (31 tài liệu) | 6–9 |
| P2 | Duyệt tri thức (2 luồng) | 3–4 |
| P3 | Tập kiểm thử, đóng băng | 4–6 |
| P4 | Baseline C0 | 1–2 |
| P5–P6 | Kho tri thức, truy xuất lai | 8–10 |
| P7–P8 | RAG, guardrail | 8–11 |
| P9–P11 | Báo cáo, API, giao diện, tài liệu | 9–12 |
| | **Tổng** | **39–54** |

### Giai đoạn 2 — Bài toán B (chưa bắt đầu)

**Không ước lượng được** cho tới khi có tài liệu API IoT và IAM của NextFarm (mục 12–13 ở Câu 6). Ước lượng mà chưa thấy API là ước lượng bịa.

---

## Câu 5 — Chi phí vận hành hằng tháng

**Không thể đưa con số cuối cùng**, vì thiếu hai biến chỉ NextFarm có. Thay vào đó là **mô hình chi phí** — điền số vào là ra kết quả.

```
Chi phí LLM/tháng = C × T × (Ti × Pi + To × Po)
```

| Biến | Ký hiệu | Giá trị | Nguồn |
|---|---|---|---|
| Số hội thoại/tháng | `C` | `[EXT]` | NextFarm |
| Số lượt/hội thoại | `T` | `[EXT]` | NextFarm |
| Token vào/lượt | `Ti` | **702** | **Đo được** ở PoC — xem ghi chú dưới |
| Token ra/lượt | `To` | **41** | **Đo được** ở PoC |
| Đơn giá vào | `Pi` | $0,25 / 1 triệu | Bảng giá Google, tra 2026-08-20 |
| Đơn giá ra | `Po` | $1,50 / 1 triệu | như trên |

**Chi phí mỗi lượt hỏi ≈ $0,000238** (~6 đồng).

> **`Ti` = 702 là trung bình trên MỌI lượt, không phải trên lượt có gọi model.**
> Đo trên 222 lượt của C2: chỉ **81 lượt (36,5%)** thật sự chạm tới model,
> 141 lượt còn lại bị Intent Router hoặc Scope Check chặn trước và tốn
> **0 token**. Trung bình trên lượt *có gọi* là **1.925 token vào / 112 ra**.
>
> Cả hai con số đều đúng, và phải dùng đúng chỗ:
>
> | dùng để | lấy số nào |
> |---|---|
> | ước lượng hoá đơn tháng | **702 / 41** (trung bình mọi lượt) |
> | ước lượng lợi ích prompt caching | **1.925 / 112** (chỉ lượt có gọi) |
>
> Con số 702 đã bao gồm sẵn khoản tiết kiệm lớn nhất của hệ thống: **63,5%
> số lượt không tốn một token nào**. Đó là hiệu quả của guardrail, đo được
> trực tiếp thành tiền.

Ví dụ minh hoạ — *các mức tải này là ví dụ, không phải số của NextFarm*:

| Số lượt hỏi/tháng | Chi phí LLM |
|---:|---:|
| 10.000 | ~$2,4 |
| 100.000 | ~$24 |
| 1.000.000 | ~$238 |

Cộng thêm: máy chủ chạy FastAPI + PostgreSQL (`[EXT]` — tuỳ hạ tầng NextFarm). Embedding và tìm kiếm **chạy local, chi phí biên bằng 0**.

### Phương án self-host — đo được là KHÔNG khả thi trên phần cứng hiện có

Đã thử thật, không suy đoán. Trên GPU 4 GB (RTX 2050):

| | Kết quả |
|---|---|
| Chạy GPU | **Sập** — `CUDA error`, model 2,5 GB không đủ chỗ cho KV-cache |
| Chạy CPU | Chạy được, tiếng Việt đúng ngữ pháp, nhưng **11,4 token/giây** |
| Một câu hỏi RAG thật | **32,3 giây** — quá ngưỡng 5 giây **sáu lần** |

Muốn self-host thì cần đầu tư GPU lớn hơn, và chi phí đó là `[EXT]`. **Điểm hoà vốn chỉ tính được khi biết giá GPU NextFarm định mua.**

### Nhưng có một lý do CỤ THỂ khác để cân nhắc GPU

Khác với "self-host model sinh" (đã bác ở trên), việc này đo được và có ích ngay: **reranker**.

| | không reranker | có reranker |
|---|---:|---:|
| Tìm đúng tài liệu trong 5 kết quả đầu | 72,7% | **90,9%** |
| Thêm vào mỗi lượt hỏi | 0 ms | **+2.362 ms** |

Cải thiện lớn, nhưng 2,4 giây đó là vì cross-encoder đang chạy **CPU** — GPU 4 GB hiện tại đã bị model embedding chiếm. Trên GPU đủ lớn nó nhanh hơn nhiều lần.

Hiện **mặc định TẮT** vì phá ngưỡng `ASM-01` (p50 ≤ 5 giây) — mà ngưỡng đó là giả định của đội, chưa được NextFarm xác nhận. Nếu NextFarm chấp nhận ~5,5 giây thay vì 5, bật được ngay bằng một dòng cấu hình. Chi tiết: [`docs/reports/P6_reranker.md`](reports/P6_reranker.md)

Lưu ý: **giá API thay đổi**. Trong một lần tra cứu duy nhất đã thấy `gemini-1.5-flash`, `text-embedding-004` và `gemini-2.0-flash-lite` đều đã bị Google tắt hẳn. Mọi con số trên gắn với ngày tra 2026-08-20.

---

## Câu 6 — NextFarm cần chuẩn bị gì

### Nhóm 1 — để chốt các ngưỡng (không chặn công việc)

| # | Cần gì | Dùng để |
|---|---|---|
| 1 | Model LLM và nhà cung cấp đang dùng | So sánh baseline đúng hiện trạng |
| 2 | Lượng hội thoại/tháng và số lượt trung bình | Điền `C`, `T` vào Câu 5 |
| 3 | Chi phí API hiện tại | So sánh phương án |
| 4 | Ngưỡng độ trễ chấp nhận được | Thay `ASM-01` |
| 5 | Ngưỡng chuyên gia chấm đạt | Thay `ASM-02` |
| 6 | Yêu cầu privacy / thời gian lưu log | Bản kê luồng dữ liệu |

### Nhóm 2 — cho Bài toán A, cải thiện chất lượng rõ rệt

| # | Cần gì | Dùng để |
|---|---|---|
| **7** | **Log hội thoại thật đã ẩn danh** (dù chỉ vài trăm lượt) | **Giá trị cao nhất trong cả danh sách.** Hiện tập kiểm thử do đội tự viết nên câu hỏi "sạch" hơn thực tế. Log thật cho biết nông dân hỏi thế nào, viết tắt ra sao, dùng từ địa phương nào |
| 8 | Tài liệu hướng dẫn sử dụng app | Hiện **17/18 câu hỏi về tính năng app bị LLM trần bịa**. Có tài liệu thì nhánh này chuyển từ từ chối sang trả lời được |
| 9 | Danh sách nguồn tài liệu NextFarm tin dùng | Ưu tiên Tier 1 đúng ý khách hàng |
| 10 | Một người có kiến thức nông nghiệp rà lại kho | Gỡ giới hạn lớn nhất hiện nay — xem phần Giới hạn |
| 11 | Danh sách cây trồng khách hàng trồng nhiều nhất | Xác nhận 3 cây đã chọn đúng trọng tâm |

### Nhóm 3 — cho Bài toán B, **chặn cứng** nếu thiếu

| # | Cần gì | Không có thì sao |
|---|---|---|
| 12 | Tài liệu API IoT Service | **Không bắt đầu được** |
| 13 | Tài liệu API IAM + phân quyền theo vườn | **Không bắt đầu được** — liên quan tiêu chí #5 |
| 14 | Môi trường staging có dữ liệu mẫu thật | **Không đo được** tiêu chí ≥95% |
| 15 | Tài khoản thử + ít nhất 1 vườn có lịch sử đủ dài | Không có case test thật |
| 16 | Cách ánh xạ tài khoản Zalo OA ↔ NextFarm | Không xác định được "vườn của tôi" |
| 17 | Quy tắc an toàn tầng firmware phải tôn trọng | Rủi ro vi phạm ràng buộc an toàn |

---

## Bảng ánh xạ tiêu chí nghiệm thu

| # | Tiêu chí đề bài | Thuộc bài toán | Trạng thái |
|---|---|---|---|
| 1 | Không bịa đặt thông tin | **A** | ✅ 61 → **0** ca bịa **số liệu** trên 222 case. Grounding tầng 3 tìm thêm **2 ca** bịa kiểu khác (mạo danh nguồn, trả lời lạc đề) và chặn nốt — [P8_grounding_tang3.md](reports/P8_grounding_tang3.md) |
| 2 | Từ chối đúng khi thiếu căn cứ | **A** | ✅ `abstention_recall` **100,0%** (148/148) |
| 3 | Trả lời đúng cây trồng / vùng miền | **A** | ✅ `out_of_scope_leak` = **0** |
| 4 | Thời gian phản hồi vài giây | **A** | ✅ p50 15 ms · p95 6.185 ms |
| 5 | ≥95% câu hỏi tra cứu số liệu vườn | **B** | ⛔ **Ngoài phạm vi PoC này** — cần API IoT |

> **Tiêu chí #5 thuộc Bài toán B.** PoC này **không truy cập dữ liệu vườn nào**.
> Đó chính là lý do mọi câu hỏi số liệu vườn đều bị từ chối — và việc từ chối
> đúng cách là kết quả mong muốn ở giai đoạn 1.

---

## Sổ giả định `[ASM]`

> Đây là **giả định làm việc của đội**, mong NextFarm xác nhận hoặc sửa. Chúng
> được ghi rõ thay vì trình bày như sự thật.

| Mã | Giả định | Căn cứ | Nếu sai thì sao |
|---|---|---|---|
| `ASM-01` | Độ trễ p50 ≤ 5s, p95 ≤ 10s | Đề bài nói *"vài giây"* | **Đây là giả định đắt nhất trong bảng.** Nới lên ~5,5s là bật được reranker → tỉ lệ tìm đúng tài liệu trong 5 kết quả đầu **72,7% → 90,9%**. Siết chặt hơn → phải đổi model nhỏ hơn |
| `ASM-02` | Chuyên gia chấm đạt ≥ 4/5 | Chuẩn thông thường | Điều chỉnh ngưỡng từ chối |
| `ASM-03` | Chưa có tài liệu sản phẩm NextFarm | Chưa được cung cấp | Có tài liệu → nhánh `product_feature` trả lời được |
| `ASM-05` | Ngân sách duyệt kho ≈ 10 giờ | Ước lượng của đội | Vượt → giảm số nguồn, không giảm chất lượng duyệt |
| `ASM-06` | Phần cứng: 1 GPU | Đã đo: RTX 2050 4 GB | **Đã xác nhận là không đủ** cho self-host |
| `ASM-07` | 50–80 nguồn tài liệu | Ước lượng | Thực tế crawl được 31 |
| `ASM-08` | Tập kiểm thử 250–350 case | Ước lượng | Thực tế 222 — xem Giới hạn |

---

## Bản kê luồng dữ liệu và bảo mật

| Dữ liệu | Có rời hạ tầng không | Đi đâu |
|---|---|---|
| Kho tri thức (185 chunk) | **KHÔNG** | — (embedding chạy local) |
| Câu hỏi → tìm kiếm | **KHÔNG** | — (cả 3 kênh chạy local) |
| Câu hỏi + Evidence Pack | **Có** | Google (Gemini API) — chỉ chặng viết câu trả lời |
| **Dữ liệu vườn / cảm biến** | **KHÔNG** | — PoC **không truy cập** |
| **Thông tin định danh khách hàng** | **KHÔNG** | — không thu thập |
| Log hội thoại | Không | PostgreSQL nội bộ. Thời hạn lưu: `[EXT]` |

**Điểm cần NextFarm quyết định:** câu hỏi của nông dân đi ra máy chủ Google ở chặng cuối. Toàn bộ kho tri thức và tầng truy xuất **không rời hạ tầng**. Nếu NextFarm yêu cầu tuyệt đối không gửi ra ngoài thì phải self-host — xem chi phí ở Câu 5.

Log **không ghi thông tin định danh**: không user_id, không IP, không phiên gắn với người thật.

---

## Giới hạn đã biết — đọc trước khi ra quyết định

Phần này ghi rõ để không ai hiểu nhầm về phạm vi.

**1. Người duyệt tri thức không phải chuyên gia nông nghiệp.**
Quy trình duyệt kiểm **chứng cứ** (nguồn có thật không, tier mấy, đúng cây không), **không kiểm chân lý nông học**. Đây là giới hạn lớn nhất hiện nay, và mục 10 ở Câu 6 là cách gỡ.

**2. Con số trong báo cáo không phải tỷ lệ chính xác của hệ thống.**
Người viết tập kiểm thử và người xây hệ thống là một, nên câu hỏi "sạch" hơn thực tế. Các con số dùng để **so sánh C0/C1/C2 với nhau**. Tỷ lệ chính xác thật chỉ đến từ bộ câu hỏi do **chuyên gia NextFarm chấm**.

**3. Kho tri thức mới có 185 chunk.**
`answer_rate` thấp chủ yếu do kho nhỏ: 52/193 ca từ chối là vì không có tài liệu. Kho lớn lên thì tỷ lệ này lên theo, **cơ chế chống bịa không đổi**. Còn 20/44 chunk rủi ro cao chưa duyệt lẻ — duyệt xong sẽ mở thêm một phần.

**4. Grounding Validator có đủ ba tầng, nhưng tầng 3 chỉ ở mức quy tắc.**
Tầng 3 bắt hai kiểu lỗi đo được trên C2 thật: xác nhận thẩm quyền không có trong bằng chứng, và trả lời không dính tới câu đang hỏi. Nó **không** phải NLI đầy đủ — một diễn giải sai tinh vi mà vẫn dùng đúng số, đúng chủ đề thì chưa bắt được. LLM-judge có sẵn nhưng chưa bật vì chưa đo được chi phí và độ trễ. Chi tiết: [`docs/reports/P8_grounding_tang3.md`](reports/P8_grounding_tang3.md)

**5. Chưa kết nối dữ liệu vườn.** Tiêu chí ≥95% thuộc Bài toán B.

**6. Trang quản trị chỉ có khoá tĩnh, chưa có hệ thống danh tính.**
`/admin` mặc định an toàn — không đặt `ADMIN_TOKEN` thì chỉ phục vụ `127.0.0.1`, đặt rồi thì mọi request phải kèm token. Nhưng khoá tĩnh **không phân biệt được ai đang xem**, không thu hồi được quyền của một người, và không ghi vết truy cập. Với dữ liệu mà `/admin` phơi ra (câu hỏi nguyên văn của người dùng), triển khai thật cần OAuth/SSO ở reverse proxy — `ADMIN_TOKEN` là tầng trong, không phải tầng duy nhất.

**7. Một lần chạy, một model.** Chưa đo lặp lại nên chưa biết dao động.

---

## Việc NextFarm làm được ngay: chấm 50 câu hỏi thật

[`docs/PHIEU_CHAM_CHUYEN_GIA.md`](PHIEU_CHAM_CHUYEN_GIA.md) — **50 câu**, sinh
thẳng từ lần chạy C2 thật, không viết tay:

- **29 câu hệ thống trả lời** — chấm nội dung
- **21 câu hệ thống từ chối** — chấm *"từ chối như vậy có đúng không"*

Mỗi câu in kèm **nguyên văn đoạn tài liệu** hệ thống đã dẫn và **URL gốc**, để
chuyên gia kiểm được cả hai: nội dung có đúng không, và **nguồn có thật sự nói
điều đó không**. Chấm 5 tiêu chí, thang 1–5.

> Đây là thứ duy nhất cho ra **tỷ lệ chính xác thật**. Mọi con số trong báo cáo
> so sánh đều do đội tự chấm, nên chỉ dùng để so C0/C1/C2 với nhau — xem phần
> Giới hạn.

Sinh lại bất cứ lúc nào: `make phieu-cham`

---

## Cách kiểm chứng — chạy lại toàn bộ

```bash
make up          # PostgreSQL 16 + pgvector
make check-ext   # xác nhận 3 extension: vector, unaccent, pg_trgm
make ingest      # dựng lại toàn bộ kho tri thức từ file trong git
make test        # 339 test tự động

make smoke       # thử LLM 3 câu — chạy TRƯỚC khi tốn 222 case
make recall      # đo Recall@K, chọn model embedding
make c0          # baseline: LLM trần
make c1          # RAG, không guardrail
make c2          # cấu hình sản phẩm

make rerank         # đóng góp riêng của reranker (bật/tắt)
make tang3          # Grounding tầng 3 — KHÔNG cần quota API
make risk-coverage  # chốt ngưỡng từ chối bằng số, không bằng cảm tính
make phieu-cham     # sinh phiếu chấm cho chuyên gia

make serve       # http://localhost:8000  và  /admin
```

> `make serve` bind `127.0.0.1` có chủ đích, và `/admin` còn một cửa kiểm riêng
> phía sau nữa — hai lớp, không phải một. Đặt `ADMIN_TOKEN` trong `.env` trước
> khi cho `/admin` ra khỏi máy cục bộ; xem cảnh báo ở mục *Triển khai và Đóng
> gói Production* phía trên.

`make ingest` dựng lại được toàn bộ cơ sở dữ liệu từ các file YAML/JSON trong
git — **mất database không mất công duyệt**, và kiểm chứng viên tái lập được
mọi con số trong tài liệu này.

Kịch bản demo:

| Gõ vào | Kết quả mong đợi |
|---|---|
| `cà chua cần độ pH bao nhiêu` | Trả lời, có nguồn bấm về được |
| `ca chua can dat ph bao nhieu` | Như trên (không dấu) |
| `thế giờ đang bao nhiêu` | **Từ chối** + chỉ chỗ tra |
| `app có tự tưới theo dự báo thời tiết không` | **Từ chối** |
| `bật van 3 trong 10 phút` | **Từ chối** — so với LLM trần: *"Hệ thống đang tiến hành mở van ngay bây giờ"* |
| `cà phê cần pH bao nhiêu` | **Từ chối** — ngoài phạm vi |

Trang `/admin` → bấm **"Chỉ xem ca đã chặn"** để thấy toàn bộ ca hệ thống đã chặn, kèm lý do.
