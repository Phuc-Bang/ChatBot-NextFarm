# ChatBot-NextFarm — Bài toán A: Chống bịa đặt

Proof of Concept cho bài toán chatbot nông nghiệp **trả lời sai / bịa đặt** của NextFarm.

Mục tiêu không phải là làm một chatbot nông nghiệp trôi chảy. Mục tiêu là làm một chatbot **có cơ chế kiểm soát tri thức**: mọi phát biểu factual phải truy được về một tài liệu có thật, và khi không đủ căn cứ thì bot phải **biết từ chối đúng lý do** thay vì đoán.

> **Nguyên tắc số một:** LLM không phải nguồn sự thật.

---

## Tài liệu

| Tài liệu | Vai trò |
|---|---|
| [`De-bai-Chatbot-NextFarm.pdf`](De-bai-Chatbot-NextFarm.pdf) | Đề bài gốc của NextFarm (31/07/2026) — **cấp cao nhất, không sửa** |
| [`docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md`](docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md) | **Quy chuẩn kỹ thuật đang áp dụng** — nguồn sự thật duy nhất cho mọi quyết định |
| [`docs/GIAO_HANG_NEXTFARM.md`](docs/GIAO_HANG_NEXTFARM.md) | **Tài liệu bàn giao** — trả lời 6 câu hỏi mục 6 của đề bài |
| [`docs/reports/BAO_CAO_SO_SANH.md`](docs/reports/BAO_CAO_SO_SANH.md) | Báo cáo so sánh C0 vs C2 kèm phân tích lỗi |
| [`docs/PHIEU_CHAM_CHUYEN_GIA.md`](docs/PHIEU_CHAM_CHUYEN_GIA.md) | 50 câu + phiếu chấm cho chuyên gia nông nghiệp NextFarm |
| [`docs/CRAWLER_GUIDE.md`](docs/CRAWLER_GUIDE.md) | Hướng dẫn crawler (đã hợp nhất vào quy chuẩn v2.0 Phần IV) |
| [`docs/ChatBot-NextFarm-SPEC.md`](docs/ChatBot-NextFarm-SPEC.md) | Bản tóm tắt đề bài dạng Markdown |
| [`docs/NEXTFARM_PROBLEM_A_DOCUMENTATION_v1.0/`](docs/NEXTFARM_PROBLEM_A_DOCUMENTATION_v1.0/) | Spec v1.0 — đã được thay thế, giữ để tham khảo lịch sử |

**Khi có mâu thuẫn giữa các tài liệu:** PDF đề bài > quy chuẩn v2.0 > mọi tài liệu khác.

---

## Bài toán

Đề bài nêu bốn hiện tượng của chatbot hiện tại:

| Mã | Hiện tượng | Cách xử lý |
|---|---|---|
| A1 | Bịa số liệu vườn | Intent Router nhận diện → từ chối kèm giải thích |
| A2 | Bịa tính năng ứng dụng không tồn tại | Intent Router nhận diện → từ chối |
| A3 | Khuyến nghị canh tác không hợp cây trồng / vùng miền | RAG có provenance, lọc theo cây và vùng |
| A4 | Hiểu sai câu hỏi tiếng Việt của nông dân | Chuẩn hoá 4 lớp + truy xuất không dấu |

Phạm vi PoC: **lúa, cà chua, dưa chuột**.

---

## Kiến trúc

```
Câu hỏi
   ↓
Chuẩn hoá tiếng Việt          (deterministic, không suy diễn nội dung)
   ↓
Intent Router                 4 nhánh — điểm mới quan trọng nhất của v2.0
   ├── agronomy_knowledge  →  đi tiếp
   ├── garden_data         →  từ chối + chuyển hướng
   ├── product_feature     →  từ chối
   └── device_control      →  từ chối tuyệt đối
   ↓
Scope Check                   (lúa / cà chua / dưa chuột?)
   ↓
Hybrid Retrieval              vector (pgvector) + từ khoá (unaccent + trigram)
   ↓
Reranker
   ↓
Evidence Pack                 (JSON có chunk_id, nguyên văn)
   ↓
LLM                           (đầu ra JSON, mỗi câu gắn chunk_id)
   ↓
Grounding Validator           3 tầng: cấu trúc → số liệu → ngữ nghĩa
   ├── đạt        →  Trả lời + nguồn truy ngược được
   └── không đạt  →  Từ chối
```

Chi tiết đầy đủ ở [quy chuẩn v2.0](docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md), Phần III và Phần IV.

---

## Trạng thái

| Phase | Nội dung | Trạng thái |
|---|---|---|
| P0 | Nền móng repo, hạ tầng Postgres | ✅ xong |
| P1 | Crawler (HTML + PDF, robots.txt, sitemap, phân trang) | ✅ xong — 31 tài liệu |
| P2 | Duyệt tri thức (2 luồng) | 🔄 18/31 tài liệu duyệt, 65/141 số liệu xác nhận |
| P3 | Tập kiểm thử — **đóng băng** | ✅ v3 đóng băng — 12 nhóm, 222 case |
| P4 | Đo baseline C0 (LLM trần) | ✅ đo xong trên 222 case |
| P5 | Cơ sở dữ liệu tri thức | ✅ xong — lược đồ, chunking, nạp dữ liệu |
| P6 | Truy xuất lai | ✅ hybrid RRF ba kênh — MRR **0,620**, R@10 95,5% · tham số chốt bằng quét 72 tổ hợp · reranker đã đo |
| P7 | RAG (C1) | ✅ **222/222 case** — chạy trọn 2026-08-22, không lỗi 429 |
| P8 | Guardrail (C2) | ✅ đo xong — 5/5 chỉ số chống bịa bằng 0 · Grounding **đủ ba tầng** |
| P9 | Báo cáo so sánh | ✅ **C0 · C1 · C2 đủ ba cột** kèm phân tích lỗi và đường risk–coverage |
| P10 | API + giao diện | ✅ API + hai trang tiếng Việt |
| P11 | Tài liệu giao hàng | ✅ [GIAO_HANG_NEXTFARM.md](docs/GIAO_HANG_NEXTFARM.md) + [phiếu chấm 50 câu](docs/PHIEU_CHAM_CHUYEN_GIA.md) · còn 2 mục `[NGƯỜI THỰC HIỆN TỰ VIẾT]` |
| P12 | Fine-tuning (tuỳ chọn) | ⛔ **không khả thi** — GPU 4GB, xem §Giới hạn |

### Số liệu hiện tại

| | |
|---|---|
| Tài liệu crawl được | 31 (lúa 22 · dưa chuột 5 · cà chua 4) |
| Chunk | 292 (rủi ro cao 44 · cần cảnh báo 93) |
| Chunk **index được** | **185** (18 tài liệu đã duyệt · 31/44 chunk rủi ro cao đã duyệt lẻ) |
| Câu ứng viên số liệu | 193 — **65 fact đã xác nhận** |
| Case kiểm thử | **222 / 12 nhóm — v3 đã đóng băng** |
| Test tự động | **321 xanh** |

> **185 / 292 chunk** vào được kho tri thức. 107 chunk còn lại thuộc 13 tài
> liệu bị loại ở luồng 1, cộng 13 chunk rủi ro cao chưa duyệt lẻ — tất cả
> **cố tình** nằm ngoài: DEC-005 quy định không duyệt thì không vào kho. Cổng
> chặn là view `indexable_chunk`, cài ở tầng dữ liệu chứ không phải ở lời hứa.

### Tầng từ chối — đo được ngay, không cần model

Ba bước đầu của chuỗi xử lý (chuẩn hoá → Intent Router → Scope Check) không
gọi model nào, nên đo được ngay hôm nay:

```bash
python evaluation/runners/eval_tu_choi.py
```

| Trên 222 case của tập kiểm thử **v3** | |
|---|---|
| Case phải bị chặn | 124 |
| — chặn đúng loại | **118** |
| — chặn an toàn nhưng kém cụ thể | 6 |
| — **lọt sang nhánh trả lời** | **0** |
| Case phải đi tiếp | 98 |
| — **bị chặn oan** | **0** |
| Câu hỏi biến dạng giữ nguyên hành vi | 54/57 (3 case đổi đều theo hướng *an toàn hơn*) |

Con số này **cao hơn con số trên câu hỏi thật**, vì người viết luật và người
viết tập kiểm thử là một. Nó dùng để biết tầng từ chối có chạy đúng không,
không dùng để báo cáo với NextFarm như tỷ lệ chính xác của hệ thống — con số
đó chỉ đến từ C0/C1/C2 và từ bộ câu hỏi do chuyên gia NextFarm chấm (§32).
Xem [`docs/reports/P8_intent_router.md`](docs/reports/P8_intent_router.md).

---

### Kết quả: C0 so với C2

Cùng tập kiểm thử đã đóng băng, cùng model, cùng cấu hình truy xuất. Ba cấu
hình khác nhau đúng một bậc mỗi lần: **C0** không tài liệu · **C1** có tài liệu
· **C2** có tài liệu và có cơ chế kiểm soát.

| | C0 — LLM trần | C1 — RAG | C2 — RAG + guardrail |
|---|---:|---:|---:|
| `answer_rate` | 97,7% | 41,4% | 14,4% |
| `accuracy_when_answered` | **1,2%** | 23,9% | **90,9%** |
| `false_answer_rate` | **77,0%** | 23,0% | **0,9%** |
| `abstention_recall` | 3,4% | 69,6% | **100,0%** |
| **Tổng ca bịa** | **61** | **23** | **0** |

| Chống bịa | C0 | C1 | C2 |
|---|---:|---:|---:|
| A1 · bịa số liệu vườn | 8 | 4 | **0** |
| A2 · bịa tính năng app | 17 | 7 | **0** |
| A3 · sai cây/vùng | 22 | 9 | **0** |
| Khẳng định đã điều khiển thiết bị | 14 | 3 | **0** |
| `unsafe_misroute_rate` | — | — | **0 / 36** |

**Cột C1 là cột quan trọng nhất.** Cho mô hình đủ tài liệu vẫn còn **23 ca
bịa** — RAG một mình không giải quyết được bài toán. Chỉ cơ chế kiểm soát mới
đưa về 0.

Ví dụ cụ thể — *"bật van 3 trong 10 phút"*:

> **C0:** *"Đã xác nhận lệnh… **Hệ thống đang tiến hành mở van ngay bây giờ.**"*
> **C2:** *"Em không thực hiện được lệnh điều khiển thiết bị…"*

Bot ở C0 chưa hề chạm tới thiết bị nào.

**Kiến trúc rẻ hơn, đo được:** 141/222 case bị chặn ở ba chặng đầu — trước khi
chạm cơ sở dữ liệu hay gọi model. Câu trên bị chặn ở **6 ms** và **0 token**.

| | C0 | C2 | Ngân sách |
|---|---:|---:|---|
| p50 | 2.621 ms | **15 ms** | ≤ 5.000 ms |
| p95 | 11.451 ms | **6.185 ms** | ≤ 10.000 ms |

`answer_rate` tụt xuống 14,4% chủ yếu vì **kho tri thức mới có 185 chunk**, không
phải vì hệ thống quá thận trọng: 25/42 ca từ chối trong nhóm đáng lẽ trả lời được
là do kho không có tài liệu.

> p95 = 6.185 ms đạt ngân sách, nhưng **tính trên cả 141 ca bị chặn sớm**. Riêng
> 81 ca có gọi model thì p95 là **21.188 ms** — vượt ASM-01. Lập kế hoạch hạ tầng
> phải nhìn con số sau.

Chi tiết: [`BAO_CAO_SO_SANH.md`](docs/reports/BAO_CAO_SO_SANH.md) ·
[`C0_baseline.md`](docs/reports/C0_baseline.md)

### Mô hình đã chốt — bằng số đo, không phải trên giấy

DEC-015 giữ trạng thái `[TODO]` cho tới khi có số. Giờ đã có:

| | Chốt | Vì sao |
|---|---|---|
| **Sinh câu trả lời** | `gemini-3.1-flash-lite` (API) | GPU 4GB không chạy nổi — xem dưới |
| **Embedding** | `halong_embedding` (**local**) | MRR 0,620 khi hợp nhất, cao nhất trong các cấu hình đo |
| **Reranker** | `itdainb/PhoRanker` — **mặc định TẮT** | R@5 72,7% → 90,9% nhưng tốn +2,4 giây trên CPU |

**Truy xuất lai đo trên 22 case có ground truth, 185 chunk:**

| Cấu hình | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|
| **hybrid(halong)** | **50,0%** | **77,3%** | **95,5%** | **0,620** |
| chỉ từ khoá | 36,4% | 68,2% | 86,4% | 0,500 |
| chỉ vector | 13,6% | 63,6% | 86,4% | 0,351 |

Vector một mình kém nhất về MRR — nhưng R@10 của nó ngang bảng: nó **tìm đúng**
chunk, chỉ **xếp sai** vị trí. Hợp nhất với từ khoá thì R@1 nhảy **13,6% → 50%**.

**R@10 = 95,5%** nghĩa là hầu như mọi câu hỏi đều tìm được chunk đúng trong 10
kết quả đầu — việc còn lại là **xếp hạng**, không phải tìm kiếm. Đó là chỗ
reranker có tác dụng, và cũng là lý do cụ thể để cân nhắc GPU.

Chi tiết: [`docs/reports/P6_retrieval_tuning.md`](docs/reports/P6_retrieval_tuning.md)
· [`P6_reranker.md`](docs/reports/P6_reranker.md)

### Kho tri thức không rời máy

Embedding chạy **local**, nên bản kê luồng dữ liệu (§38) đổi hẳn:

```
Kho tri thức (185 chunk)   → KHÔNG rời máy    (embedding local)
Câu hỏi → tìm kiếm          → KHÔNG rời máy    (embedding + trigram + FTS local)
Câu hỏi + Evidence Pack     → Google Gemini    (chỉ chặng viết câu trả lời)
Dữ liệu vườn / định danh    → KHÔNG có         (PoC không truy cập)
```

### Hai giao diện

```bash
make up && python -m uvicorn app.main:app --port 8000
```

| | |
|---|---|
| `/` | Trang chat cho nông dân — chữ 17px, từ chối hiển thị khác hẳn trả lời, nguồn luôn hiện |
| `/admin` | Trang quản trị — kho tri thức, độ trễ từng chặng, chi phí, và **bộ lọc "chỉ xem ca đã chặn"** |

Trang admin **mặc định chỉ phục vụ máy cục bộ**. Cụ thể ([`app/main.py`](app/main.py) → `kiem_quyen_admin`):

| `ADMIN_TOKEN` trong `.env` | hành vi |
|---|---|
| để trống (mặc định) | chỉ nhận request từ `127.0.0.1`. Địa chỉ khác → **403**, kể cả khi server bind `0.0.0.0` |
| có đặt | mọi request phải kèm `X-Admin-Token` đúng, **loopback cũng không được miễn** |

Nghĩa là một lần deploy quên cấu hình sẽ **từ chối**, chứ không lặng lẽ phục vụ
toàn bộ nhật ký truy vấn ra mạng. `make serve` vẫn bind `127.0.0.1` — hai lớp,
không phải một.

## Chạy thử

Yêu cầu: Docker, Python 3.11+.

```bash
# 1. Chuẩn bị biến môi trường
cp .env.example .env      # rồi điền giá trị thật

# 2. Khởi động PostgreSQL 16 + pgvector
make up

# 3. Kiểm tra ba extension bắt buộc — phải thấy pg_trgm, unaccent, vector
make check-ext

# 4. Cài phụ thuộc
make install
make install-crawler

# 5. Dựng lại kho tri thức từ file trong git
make ingest

# 6. Chạy thử
make test        # 321 test tự động
make serve       # http://localhost:8000  và  /admin
```

`.env` cần ít nhất:

```
GEMINI_API_KEY=<khoá của bạn>
LLM_MODEL=gemini-3.1-flash-lite
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=halong
```

### Đo lại các con số trong README này

```bash
make smoke       # thử LLM 3 câu — chạy TRƯỚC khi tốn 222 case
make eval-tu-choi # tầng từ chối, không cần model
make recall      # Recall@K, chọn model embedding
make c0          # baseline LLM trần
make c2          # cấu hình sản phẩm
```

> **Free tier Gemini rất chặt.** Các lệnh `c0`/`c1`/`c2` đã cài sẵn `--nghi 1.5`
> để giãn nhịp. Chạy liên tục không giãn là đụng trần 429 — đã gặp thật:
> `gemini-2.5-flash` cạn quota sau vài chục lần gọi. Kết quả lưu sau **từng
> case** nên đụng trần thì mất 1 case chứ không mất cả lượt.

Xem `make help` để biết đầy đủ các lệnh.

---

## Nguyên tắc làm việc

Bốn điều **tuyệt đối không làm** (quy chuẩn v2.0 §23.1):

1. **Không hard-code số liệu nông học** trong bất kỳ script nào. Mọi con số phải đến từ tài liệu đã crawl.
2. **Thất bại phải là thất bại.** Nguồn lỗi thì ghi `status: failed`, không thay bằng dữ liệu mặc định.
3. **Không sửa tập kiểm thử sau khi đóng băng.** Muốn thêm thì tạo phiên bản mới.
4. **Không tự điền thông tin NextFarm chưa cung cấp.** Để `[EXT]`, hoặc dùng `[ASM]` và ghi rõ đó là giả định của đội.

Quy ước commit: tiếng Việt, dạng `<loại>(<phạm vi>): <mô tả>`.

---

## Giới hạn đã biết

Ghi ở đây để không ai hiểu nhầm về phạm vi:

- **Chưa kết nối dữ liệu vườn.** PoC này không truy cập API IoT của NextFarm. Tiêu chí nghiệm thu "≥95% câu hỏi tra cứu số liệu vườn" thuộc Bài toán B — xem bảng ánh xạ ở §5.1 của quy chuẩn.
- **Người duyệt tri thức không phải chuyên gia nông nghiệp.** Quy trình duyệt kiểm *chứng cứ* (nguồn, tier, cây, vùng), không kiểm *chân lý nông học*.
- **Chưa có tài liệu sản phẩm NextFarm**, nên câu hỏi về tính năng app luôn bị từ chối. C0 cho thấy đây là chỗ LLM trần bịa nhiều nhất (17/18 case).
- **GPU 4GB không chạy được model sinh câu trả lời.** Đã đo thật: `qwen3:4b` sập trên GPU (CUDA error, 2.5GB model không đủ chỗ cho KV-cache trên 3,96GB trống); chạy CPU thì được 11,4 token/giây — một câu hỏi RAG thật mất **32,3 giây**, quá ngưỡng ASM-01 (p50 ≤ 5s) sáu lần. Vì vậy **P12 (fine-tuning) không khả thi** trên phần cứng hiện có, và §37.5 phải viết lại: phương án self-host cần NextFarm đầu tư GPU mới, và đó là con số `[EXT]`.
- **Free tier Gemini rất chặt.** `gemini-2.5-flash` cạn quota sau vài chục lần gọi — 80/80 case đầu của C0 trả về 429. Đã đổi sang `gemini-3.1-flash-lite`. Mọi lần chạy đo lường nên dùng `--nghi` để giãn nhịp.
- **Grounding Validator mới có tầng 1 và 2.** Tầng 3 (ngữ nghĩa, NLI/LLM-judge) chưa làm.
- **Trang admin chỉ có khoá tĩnh** (`ADMIN_TOKEN`) — đủ để mặc định an toàn, chưa phải hệ thống danh tính. Deploy thật nên đặt OAuth/SSO ở reverse proxy và giữ `ADMIN_TOKEN` làm tầng trong.
- Một số ngưỡng trong quy chuẩn là **giả định của đội** (`[ASM]`), chờ NextFarm xác nhận — xem §9.
- **Intent Router mới có lớp rule.** Lớp LLM few-shot (§11.3) chưa làm được vì chưa chốt model (DEC-015). Khi không luật nào khớp, router trả về `nguồn = "mac_dinh"` với độ tin cậy 0 — đó là *"lớp rule không biết"*, không phải *"câu này là nông học"*.
- **Tập kiểm thử có ba phiên bản, bản đang dùng là `v3`.** DEC-023 cấm sửa tại chỗ, nên mỗi lỗi phát hiện sau khi đóng băng đều phải cắt phiên bản mới; bản cũ giữ nguyên làm bằng chứng.
  - `v1` — 30 case `known_answer`, trong đó **9 case đáp án do LLM sinh, không có tài liệu chống lưng**. Giữ lại vì đây là ví dụ cụ thể nhất cho việc *vì sao quy chuẩn cấm dùng LLM sinh đáp án chuẩn*.
  - `v2` — sinh thẳng từ bảng fact đã duyệt nên hết bịa cả câu, nhưng còn **một đơn vị suy diễn**: `4 kg NPK/1000m2/10 ngày` trong khi câu gốc chỉ nói *"liều lượng cho 1 lần bón: 4 kg Better NPK … pha loãng vào nước để tưới"* — không nêu diện tích nào. Chuỗi `/1000m2` được suy từ câu **liền kề** nói về **sản phẩm khác** (Better KNO3 `200g/16 lít nước/1000 m2`) ở **giai đoạn khác**.
  - `v3` — đã sửa fact đó và thêm hàng rào: mọi con số trong `expected_facts` bị đối chiếu với câu nguyên văn, lệch là không sinh case.
- **Nhóm `contradictory` chưa có.** Cả ba cặp bị đánh dấu mâu thuẫn đều là **mâu thuẫn giả** — hai tài liệu nói về hai vụ khác nhau (đông xuân tháng 10–11 vs hè thu tháng 6–7) chứ không hề trái nhau. Trường `stage` ghi *"thời vụ gieo trồng"* cho cả hai nên máy không tách được. Sinh một nhóm "mâu thuẫn" toàn mâu thuẫn giả cũng là bịa, chỉ là bịa kiểu khác.
- **`known_answer` chỉ có 16 case** vì mỗi case phải truy được về một fact đã duyệt. Con số này tăng khi duyệt thêm số liệu, không tăng bằng cách viết thêm câu hỏi.
- **Bỏ dấu làm sập khớp trọn từ** (DEC-031, §13.4). Tiếng Việt viết rời từng âm tiết nên `bật`/`bắt`, `giờ`/`gió`, `van`/`vẫn`, `tôi`/`tỏi` thành cùng một chuỗi sau khi bỏ dấu. Đã xử lý bằng khớp có dấu khi người dùng gõ dấu, cộng bảng ngoại lệ — nhưng đây là rủi ro thường trực cho mọi thành phần khớp từ khoá về sau.
