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
| P2 | Duyệt tri thức (2 luồng) | 🔧 công cụ xong, **chờ người duyệt** |
| P3 | Tập kiểm thử — **đóng băng** | 🔄 10/13 nhóm, 200 case — chưa đóng băng |
| P4 | Đo baseline C0 (LLM trần) | ⛔ chờ khoá API hoặc model cục bộ |
| P5 | Cơ sở dữ liệu tri thức | ✅ xong — lược đồ, chunking, nạp dữ liệu |
| P6 | Truy xuất lai | 🔄 chuẩn hoá + từ khoá xong; vector chờ model |
| P7 | RAG (C1) | ⛔ chờ model |
| P8 | Guardrail (C2) — cấu hình sản phẩm | 🔄 Intent Router + Scope Check + mẫu từ chối xong; lớp LLM và Grounding chờ model |
| P9 | Báo cáo so sánh | ☐ |
| P10 | API + giao diện | ☐ |
| P11 | Tài liệu giao hàng | ☐ |
| P12 | Fine-tuning (tuỳ chọn, có điều kiện) | ☐ |

### Số liệu hiện tại

| | |
|---|---|
| Tài liệu crawl được | 31 (lúa 22 · dưa chuột 5 · cà chua 4) |
| Chunk | 292 (rủi ro cao 44 · cần cảnh báo 93) |
| Chunk **index được** | **0** — chưa tài liệu nào được duyệt |
| Câu ứng viên số liệu | 193 (12 rủi ro cao) |
| Case kiểm thử | 200 / 10 nhóm (chưa đóng băng) |
| Test tự động | 217 xanh |

> Con số **0 chunk index được** là hành vi đúng, không phải lỗi: DEC-005 quy
> định không duyệt thì không vào kho tri thức. Cổng chặn là view
> `indexable_chunk`, được cài ở tầng dữ liệu chứ không phải ở lời hứa.

### Tầng từ chối — đo được ngay, không cần model

Ba bước đầu của chuỗi xử lý (chuẩn hoá → Intent Router → Scope Check) không
gọi model nào, nên đo được ngay hôm nay:

```bash
python evaluation/runners/eval_tu_choi.py
```

| Trên 200 case của tập kiểm thử v1 | |
|---|---|
| Case phải bị chặn | 124 |
| — chặn đúng loại | **118** |
| — chặn an toàn nhưng kém cụ thể | 6 |
| — **lọt sang nhánh trả lời** | **0** |
| Case phải đi tiếp | 76 |
| — **bị chặn oan** | **0** |
| Câu hỏi biến dạng giữ nguyên hành vi | 48/51 (3 case đổi đều theo hướng *an toàn hơn*) |

Con số này **cao hơn con số trên câu hỏi thật**, vì người viết luật và người
viết tập kiểm thử là một. Nó dùng để biết tầng từ chối có chạy đúng không,
không dùng để báo cáo với NextFarm như tỷ lệ chính xác của hệ thống — con số
đó chỉ đến từ C0/C1/C2 và từ bộ câu hỏi do chuyên gia NextFarm chấm (§32).
Xem [`docs/reports/P8_intent_router.md`](docs/reports/P8_intent_router.md).

---

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
```

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
- **Chưa có tài liệu sản phẩm NextFarm**, nên câu hỏi về tính năng app luôn bị từ chối.
- Một số ngưỡng trong quy chuẩn là **giả định của đội** (`[ASM]`), chờ NextFarm xác nhận — xem §9.
- **Intent Router mới có lớp rule.** Lớp LLM few-shot (§11.3) chưa làm được vì chưa chốt model (DEC-015). Khi không luật nào khớp, router trả về `nguồn = "mac_dinh"` với độ tin cậy 0 — đó là *"lớp rule không biết"*, không phải *"câu này là nông học"*.
- **Tập kiểm thử chưa đóng băng.** Còn ba nhóm (`known_answer`, `paraphrase`, `contradictory`) phụ thuộc vào số liệu đã duyệt ở P2. Đóng băng khi đủ 13 nhóm.
- **Bỏ dấu làm sập khớp trọn từ** (DEC-031, §13.4). Tiếng Việt viết rời từng âm tiết nên `bật`/`bắt`, `giờ`/`gió`, `van`/`vẫn`, `tôi`/`tỏi` thành cùng một chuỗi sau khi bỏ dấu. Đã xử lý bằng khớp có dấu khi người dùng gõ dấu, cộng bảng ngoại lệ — nhưng đây là rủi ro thường trực cho mọi thành phần khớp từ khoá về sau.
