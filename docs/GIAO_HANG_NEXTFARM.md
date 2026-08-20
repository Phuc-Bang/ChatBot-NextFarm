# Bàn giao PoC — Bài toán A: Chống bịa đặt

> **Ngày:** 2026-08-20 · **Trạng thái:** PoC giai đoạn 1
> Mã nguồn: `github.com/Phuc-Bang/ChatBot-NextFarm`
> Quy chuẩn kỹ thuật: [`NEXTFARM_PROBLEM_A_STANDARD_v2.0.md`](NEXTFARM_PROBLEM_A_STANDARD_v2.0.md)

Tài liệu này trả lời 6 câu hỏi ở mục 6 của đề bài, kèm sổ giả định, bản kê luồng dữ liệu và bảng ánh xạ tiêu chí nghiệm thu.

**Nguyên tắc viết tài liệu này:** mọi con số đều đến từ một lần chạy đo cụ thể, tái lập được bằng lệnh ghi kèm. Chỗ nào chưa có dữ liệu thì ghi `[EXT]` (chờ NextFarm) hoặc `[ASM]` (giả định của đội) — **không điền số ước chừng**.

---

## Tóm tắt kết quả

Trên 222 case của tập kiểm thử đã đóng băng, cùng một model, khác nhau duy nhất ở việc **có cơ chế kiểm soát tri thức hay không**:

| | LLM trần (hiện trạng) | PoC này |
|---|---:|---:|
| Tổng ca bịa đặt | **61** | **0** |
| Trả lời sai (`false_answer_rate`) | 77,0% | 3,2% |
| Đúng khi có trả lời | 1,2% | 66,7% |
| Bắt được ca cần từ chối | 3,4% | 99,3% |
| Độ trễ p95 | 11.451 ms | 8.084 ms |

Chi tiết: [`docs/reports/BAO_CAO_SO_SANH.md`](reports/BAO_CAO_SO_SANH.md)

---

## Câu 1 — Kinh nghiệm và giải pháp sẵn có, mạnh nhất ở đâu

> `[NGƯỜI THỰC HIỆN TỰ VIẾT]`
>
> Phần này nói về năng lực và kinh nghiệm của chính người thực hiện — điền hộ
> là bịa. Gợi ý: nêu đúng những gì đã làm được và **đo được** trong PoC này,
> kèm số liệu ở phần Tóm tắt, thay vì tuyên bố năng lực chung chung.

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
⑦ Grounding Validator         cấu trúc → số liệu → [ngữ nghĩa: chưa làm]
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

**141/222 case bị chặn trước khi chạm cơ sở dữ liệu.** Câu *"bật van 3 trong 10 phút"* tốn **6 ms** và **0 token**.

**3. Không duyệt thì không vào kho.** Cổng chặn là view `indexable_chunk` ở tầng cơ sở dữ liệu, không phải lời hứa trong code:

```
292 chunk crawl được  →  161 chunk vào được kho
                          131 chunk bị chặn (13 tài liệu bị loại
                          + 44 chunk rủi ro cao chưa duyệt lẻ)
```

---

## Câu 3 — Mong muốn hợp tác

> `[NGƯỜI THỰC HIỆN TỰ VIẾT]`
>
> Phần này nói về ý định hợp tác của chính người thực hiện.

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
| Token vào/lượt | `Ti` | **702** | **Đo được** ở PoC |
| Token ra/lượt | `To` | **41** | **Đo được** ở PoC |
| Đơn giá vào | `Pi` | $0,25 / 1 triệu | Bảng giá Google, tra 2026-08-20 |
| Đơn giá ra | `Po` | $1,50 / 1 triệu | như trên |

**Chi phí mỗi lượt hỏi ≈ $0,000238** (~6 đồng).

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
| 1 | Không bịa đặt thông tin | **A** | ✅ 61 → **0** ca bịa trên 222 case |
| 2 | Từ chối đúng khi thiếu căn cứ | **A** | ✅ `abstention_recall` **99,3%** |
| 3 | Trả lời đúng cây trồng / vùng miền | **A** | ✅ `out_of_scope_leak` = **0** |
| 4 | Thời gian phản hồi vài giây | **A** | ✅ p50 11 ms · p95 8.084 ms |
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
| `ASM-01` | Độ trễ p50 ≤ 5s, p95 ≤ 10s | Đề bài nói *"vài giây"* | Chặt hơn → bỏ reranker hoặc đổi model nhỏ hơn |
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
| Kho tri thức (161 chunk) | **KHÔNG** | — (embedding chạy local) |
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

**3. Kho tri thức mới có 161 chunk.**
`answer_rate` 13,1% chủ yếu do kho nhỏ: 33/46 ca từ chối là vì không có tài liệu. Kho lớn lên thì tỷ lệ này lên theo, **cơ chế chống bịa không đổi**.

**4. Grounding Validator mới có tầng 1 và 2.**
Tầng 3 (kiểm ngữ nghĩa) chưa làm. `numeric_hallucination = 0` bảo đảm về **số liệu**, chưa bảo đảm về **diễn giải**.

**5. Chưa kết nối dữ liệu vườn.** Tiêu chí ≥95% thuộc Bài toán B.

**6. Trang quản trị chưa có đăng nhập** vì chạy cục bộ. Deploy ra ngoài thì bắt buộc thêm khoá.

**7. Một lần chạy, một model.** Chưa đo lặp lại nên chưa biết dao động.

---

## Cách kiểm chứng — chạy lại toàn bộ

```bash
make up          # PostgreSQL 16 + pgvector
make check-ext   # xác nhận 3 extension: vector, unaccent, pg_trgm
make ingest      # dựng lại toàn bộ kho tri thức từ file trong git
make test        # 283 test tự động

make smoke       # thử LLM 3 câu — chạy TRƯỚC khi tốn 222 case
make recall      # đo Recall@K, chọn model embedding
make c0          # baseline: LLM trần
make c2          # cấu hình sản phẩm

make serve       # http://localhost:8000  và  /admin
```

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
