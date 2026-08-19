# NextFarm – Bài toán A: Bot trả lời sai / bịa đặt
## Technical Specification & Project Agreement v1.0

> # ⚠️ BẢN NÀY ĐÃ ĐƯỢC THAY THẾ
>
> Quy chuẩn đang áp dụng là [`docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md`](../NEXTFARM_PROBLEM_A_STANDARD_v2.0.md). Bản v1.0 này được giữ lại **chỉ để tham khảo lịch sử** — đừng dùng nó làm căn cứ khi viết code.
>
> Tám điểm đã được sửa ở v2.0 (chi tiết ở mục 0.5 của bản mới):
>
> 1. Thiếu Intent Router → chỉ phủ 2/4 hiện tượng đề bài nêu; câu hỏi số liệu vườn vẫn lọt qua Scope Check và bị trả lời bằng số liệu sách kèm citation
> 2. Gộp chung ba loại "chưa biết" → v2.0 tách thành `[ASM]` / `[EXT]` / `[TODO]`
> 3. Bộ metric có thể bị gian lận bằng cách từ chối mọi câu hỏi
> 4. Mâu thuẫn với `CRAWLER_GUIDE.md` về đơn vị duyệt (câu hay tài liệu)
> 5. Không nói keyword search làm bằng gì, trong khi PostgreSQL không có cấu hình FTS tiếng Việt
> 6. Grounding Validator để trống, dù đó là hàng rào chống bịa cuối cùng
> 7. Fine-tuning khoá cứng `Có`, không có ngân sách latency
> 8. Quy mô nguồn quá nhỏ, chưa đọc được PDF, chưa có quy tắc `robots.txt`

> **Ngôn ngữ:** Tiếng Việt  
> **Trạng thái:** REQUIREMENT LOCKED v1.0  
> **Phạm vi:** Proof of Concept (PoC) định hướng production  
> **Đối tượng đọc:** Thành viên nhóm, mentor, developer, AI coding agent và người cần hiểu toàn bộ hệ thống.

---

## 0. Mục đích của tài liệu

Đây là tài liệu kỹ thuật trung tâm của project cho **Bài toán A – Bot trả lời sai / bịa đặt**.

Tài liệu có hai vai trò:

1. **Technical Source of Truth:** ghi lại requirement, quyết định kiến trúc, lý do lựa chọn, workflow, tiêu chí đánh giá và các giới hạn.
2. **Project Agreement:** những nội dung đã được nhóm thống nhất sẽ được xem là phạm vi chuẩn cho phiên bản PoC hiện tại.

### Quy ước trạng thái

- 🔵 **NEXTFARM REQUIREMENT:** yêu cầu/định hướng lấy từ tài liệu đề bài.
- 🟢 **PROJECT DECISION – LOCKED:** quyết định đã thống nhất cho project.
- 🟡 **TECHNICAL RECOMMENDATION:** đề xuất kỹ thuật, cần được xác nhận khi triển khai chi tiết.
- 🔴 **OPEN / NEEDS INPUT:** chưa có thông tin, không được tự bịa.
- ⚪ **FUTURE:** để phase sau.

> **Nguyên tắc:** Không biến một đề xuất của nhóm thành yêu cầu chính thức của NextFarm.

---

# 1. Executive Summary

## 1.1. Bài toán

Bài toán A tập trung vào hiện tượng chatbot trả lời sai hoặc bịa đặt (hallucination). Các dạng rủi ro được nêu trong đề bài gồm:

- bịa số liệu;
- bịa tính năng;
- đưa khuyến nghị canh tác không phù hợp;
- hiểu sai tiếng Việt của nông dân.

Hậu quả có thể là người dùng làm theo lời khuyên sai, gây thiệt hại mùa vụ và mất niềm tin.

## 1.2. Mục tiêu của project

Project không đơn giản là xây một chatbot nông nghiệp.

Mục tiêu là xây một **chatbot tư vấn nông nghiệp có cơ chế kiểm soát tri thức**, trong đó:

```text
Nguồn dữ liệu
    ↓
Crawl
    ↓
Kiểm tra / xác minh
    ↓
Knowledge Base
    ↓
Retrieval
    ↓
Evidence
    ↓
LLM
    ↓
Grounding / Safety Check
    ↓
Trả lời có nguồn hoặc Abstain
```

Nguyên tắc cốt lõi:

> **LLM không được coi là nguồn sự thật. Factual answer phải được grounding bằng evidence phù hợp; khi không đủ evidence, bot phải biết từ chối thay vì đoán.**

---

# 2. Nguồn tài liệu và phạm vi bằng chứng

Project hiện dựa trên các tài liệu đã được cung cấp:

1. **Đề bài NextFarm – Bài toán A/B**
2. **ChatBot-NextFarm-SPEC.md**
3. **CRAWLER_GUIDE.md**

`CRAWLER_GUIDE.md` là tài liệu kỹ thuật liên quan đến pipeline crawler/knowledge đã có trong project; nó không được coi là thay thế cho đề bài chính thức.

### Thông tin chưa có

Đề bài có một số trường để `[cần điền]`, ví dụ:

- model hiện tại;
- lượng hội thoại/tháng;
- chi phí API;
- một số ngưỡng đánh giá;
- một số thông tin vận hành.

Các giá trị này **không được tự suy đoán**.

---

# 3. Phân loại requirement

## 3.1. Requirement từ NextFarm

Đề bài yêu cầu Bài toán A nghiên cứu/đề xuất:

- kiến trúc chống bịa;
- knowledge base;
- xử lý tiếng Việt nông nghiệp;
- RAG / fine-tuning;
- citation;
- bộ đo chất lượng;
- đánh giá câu hỏi nông học;
- cân nhắc chi phí, latency và privacy.

## 3.2. Quyết định của project

Đã chốt:

- chỉ làm Bài toán A trong PoC;
- phạm vi knowledge gồm **lúa, cà chua, dưa chuột**;
- tự xây knowledge base bằng web crawling vì chưa được cung cấp data;
- source policy phân tầng + scoring + human verification;
- PostgreSQL + pgvector;
- RAG là core;
- hybrid retrieval;
- reranking;
- citation thông qua evidence ở backend và source ở UI;
- abstention;
- high-risk agricultural handling;
- open-source LLM + LoRA/QLoRA cho fine-tuning;
- chưa chọn model cụ thể, sẽ benchmark;
- dataset fine-tuning gồm verified knowledge, human QA, validated synthetic QA và abstention/hallucination examples;
- evaluation bắt buộc;
- IoT realtime để phase sau.

---

# 4. Scope

## 4.1. In Scope

### Cây trồng

1. 🌾 Lúa
2. 🍅 Cà chua
3. 🥒 Dưa chuột

### Chức năng chính

- hỏi đáp tiếng Việt;
- xử lý câu hỏi có dấu/không dấu;
- xử lý lỗi chính tả ở mức phù hợp;
- truy xuất knowledge;
- tạo evidence pack;
- trả lời có citation/source;
- từ chối khi không đủ căn cứ;
- xử lý câu hỏi ngoài phạm vi;
- xử lý câu hỏi nông học rủi ro cao;
- logging/evidence;
- evaluation;
- benchmark các cấu hình AI.

## 4.2. Out of Scope

Trong phase này không triển khai:

- realtime IoT;
- điều khiển thiết bị;
- function calling/MCP cho thiết bị;
- hệ thống IAM đầy đủ;
- mở rộng toàn bộ cây trồng Việt Nam;
- tích hợp production với toàn bộ hệ sinh thái NextFarm;
- tự động đưa mọi dữ liệu crawl vào knowledge base.

## 4.3. Future

Có thể mở rộng sau:

```text
Chatbot
   ├── Knowledge RAG
   └── IoT Tools
          └── NextFarm APIs
```

---

# 5. Các quyết định đã khóa

| ID | Hạng mục | Quyết định | Trạng thái |
|---|---|---|---|
| DEC-001 | Problem | Bài toán A | LOCKED |
| DEC-002 | Scope | 3 cây: lúa, cà chua, dưa chuột | LOCKED |
| DEC-003 | Data | Tự xây knowledge từ nguồn web công khai | LOCKED |
| DEC-004 | Source policy | Tier + scoring + verification | LOCKED |
| DEC-005 | Human approval | Bắt buộc trước khi index | LOCKED |
| DEC-006 | Vector DB | PostgreSQL + pgvector | LOCKED |
| DEC-007 | Retrieval | Hybrid vector + keyword | LOCKED |
| DEC-008 | Reranking | Có | LOCKED |
| DEC-009 | RAG | Core architecture | LOCKED |
| DEC-010 | Citation | Backend lưu evidence, UI hiển thị source | LOCKED |
| DEC-011 | Abstention | Bắt buộc | LOCKED |
| DEC-012 | High-risk | Evidence + caution; thiếu evidence → abstain | LOCKED |
| DEC-013 | Fine-tuning | Có | LOCKED |
| DEC-014 | Fine-tuning method | LoRA/QLoRA | LOCKED |
| DEC-015 | Model | Chưa chọn; benchmark trước | OPEN |
| DEC-016 | Dataset | Verified + human QA + validated synthetic + abstention | LOCKED |
| DEC-017 | Evaluation | Bắt buộc | LOCKED |
| DEC-018 | IoT | Phase sau | DEFERRED |

---

# 6. Vì sao chọn phạm vi 3 cây?

## Lý do

PoC cần chứng minh được cơ chế chống hallucination, không phải chứng minh chatbot biết mọi cây trồng.

Ba cây:

- đủ để tạo knowledge domain;
- đủ để có nhiều loại câu hỏi;
- đủ để kiểm thử retrieval;
- giảm chi phí crawl và review;
- dễ xây evaluation dataset;
- dễ benchmark các model.

## Nguyên tắc

Nếu người dùng hỏi:

> “Cà phê cần pH bao nhiêu?”

Bot không được dùng kiến thức chung của LLM để trả lời như thể cà phê nằm trong knowledge scope.

Behavior kỳ vọng:

```text
Out of scope
     ↓
Abstain
     ↓
Giải thích phạm vi hỗ trợ
```

---

# 7. Knowledge Strategy

## 7.1. Vì sao knowledge là phần quan trọng nhất?

Một RAG system chỉ tốt khi knowledge phía dưới đáng tin.

Nếu:

```text
Crawler sai
   ↓
Knowledge sai
   ↓
Retrieval đúng
   ↓
LLM trả lời rất trôi chảy
```

thì kết quả cuối vẫn sai.

Do đó:

> **Garbage in → grounded hallucination out.**

## 7.2. Nguyên tắc Knowledge Integrity

Không được:

```text
Web
 ↓
LLM extraction
 ↓
Vector DB
```

một cách không kiểm soát.

Phải:

```text
Web
 ↓
Raw source
 ↓
Extraction
 ↓
Candidate knowledge
 ↓
Validation
 ↓
Human approval
 ↓
Approved knowledge
 ↓
Chunk
 ↓
Embedding
 ↓
pgvector
```

---

# 8. Source Governance

## 8.1. Source Tier

### Tier 1 – authoritative

Ưu tiên:

- cơ quan nhà nước;
- viện nghiên cứu;
- trường đại học;
- cơ quan chuyên môn;
- hệ thống khuyến nông;
- tài liệu kỹ thuật chính thức.

### Tier 2 – professional

Ví dụ:

- tổ chức chuyên ngành;
- doanh nghiệp nông nghiệp có tài liệu kỹ thuật;
- tài liệu kỹ thuật chuyên môn.

### Tier 3 – low-trust

Ví dụ:

- blog;
- forum;
- nội dung SEO;
- nguồn không rõ tác giả.

Tier 3 không mặc định là nguồn bị cấm, nhưng không được xem ngang Tier 1.

## 8.2. Source score

Không chỉ dựa vào tier.

Nên đánh giá:

```text
Authority
+
Freshness
+
Region relevance
+
Crop relevance
+
Content quality
+
Human verification
```

## 8.3. Metadata tối thiểu

```yaml
source_id:
url:
publisher:
title:
source_tier:
published_at:
crawled_at:
region:
crop:
language:
http_status:
content_hash:
verified:
reviewer:
reviewed_at:
version:
```

---

# 9. Crawler Architecture

Crawler phải là một pipeline chứ không phải một script đơn lẻ.

```text
Source Registry
      ↓
Crawler
      ↓
Raw HTML / Raw Text
      ↓
Extraction
      ↓
Candidate Knowledge
      ↓
Validation
      ↓
Human Review
      ↓
Approved Knowledge
```

## 9.1. Crawler không được làm

- tự bịa nội dung;
- tự biến suy luận thành fact;
- bỏ URL;
- bỏ timestamp;
- bỏ raw source;
- tự động index mọi thứ.

## 9.2. Crawl và extraction tách nhau

### Crawl

Nhiệm vụ:

- tải;
- lưu raw;
- lưu metadata;
- lưu hash.

### Extraction

Nhiệm vụ:

- lấy title;
- lấy nội dung;
- loại boilerplate;
- phát hiện nội dung phù hợp.

### Review

Nhiệm vụ:

- xác minh factual content;
- xác minh phạm vi;
- đánh dấu verified.

---

# 10. Human Verification

Candidate knowledge mặc định:

```text
verified = false
```

Chỉ:

```text
verified = true
```

mới được index vào knowledge base chính thức.

Human reviewer cần kiểm tra:

- nguồn;
- nội dung;
- cây trồng;
- vùng;
- thời điểm;
- claim;
- tính phù hợp.

---

# 11. Knowledge Data Model

Nên tách:

```text
Source
Document
KnowledgeChunk
Review
Embedding
```

Ví dụ:

```text
Source
 └── Document
       └── Chunk
             └── Embedding
```

Mỗi chunk phải truy ngược được:

```text
Chunk
 ↓
Document
 ↓
Source
 ↓
URL
```

Đây là cơ sở cho citation và audit.

---

# 12. PostgreSQL + pgvector

## Quyết định

**LOCKED: PostgreSQL + pgvector**

## Vì sao?

Project cần cả:

- relational metadata;
- provenance;
- review state;
- crop;
- region;
- evaluation;
- vector search.

Một PostgreSQL duy nhất giúp PoC đơn giản hơn.

## Alternative

Có thể cân nhắc:

- Qdrant;
- Milvus;
- Chroma.

Nhưng ở PoC hiện tại, thêm một hệ vector database riêng sẽ tạo thêm infrastructure mà chưa chắc đem lại lợi ích tương xứng.

## Nguyên tắc mở rộng

Nên có abstraction:

```text
VectorStore
    └── PgVectorStore
```

để sau này có thể thay backend nếu cần.

---

# 13. RAG Architecture

```text
User Query
   ↓
Query Processing
   ↓
Scope Check
   ↓
Hybrid Retrieval
   ↓
Reranking
   ↓
Evidence Pack
   ↓
LLM
   ↓
Grounding Check
   ├── Supported → Answer + Citation
   └── Unsupported → Abstain
```

---

# 14. Vietnamese Query Processing

Đề bài yêu cầu xử lý tiếng Việt nông nghiệp, gồm:

- từ địa phương;
- viết tắt;
- không dấu;
- lỗi chính tả.

Ví dụ:

```text
ca chua can dat pH bn
```

có thể được hiểu là:

```text
Cà chua cần đất pH bao nhiêu?
```

Nhưng normalization không được biến thành tự suy diễn nội dung.

---

# 15. Scope Check

Trước retrieval nên kiểm tra:

```text
Question
   ↓
Supported crop?
```

Nếu không thuộc:

```text
Lúa
Cà chua
Dưa chuột
```

thì:

```text
ABSTAIN / OUT OF SCOPE
```

Điều này giảm việc LLM lấy kiến thức nền bên ngoài phạm vi.

---

# 16. Hybrid Retrieval

Không chỉ vector search.

```text
                 Query
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
 Vector Search          Keyword Search
        │                     │
        └──────────┬──────────┘
                   ▼
             Hybrid Ranking
                   ▼
                Reranker
                   ▼
                Evidence
```

## Vì sao?

Vector search tốt cho semantic similarity.

Keyword search hữu ích với:

- tên bệnh;
- tên giống;
- số liệu;
- pH;
- thuật ngữ;
- cụm từ chuyên môn.

Kết hợp hai loại giúp retrieval cân bằng hơn.

---

# 17. Reranking

Retrieval ban đầu có thể lấy nhiều candidate.

Reranker dùng để:

- xếp lại mức độ liên quan;
- ưu tiên evidence thực sự trả lời câu hỏi;
- giảm context nhiễu.

Chỉ evidence phù hợp mới được đưa vào prompt cuối.

---

# 18. Evidence Pack

LLM không nên nhận một đống văn bản không cấu trúc.

Evidence Pack nên chứa:

```json
{
  "source_id": "...",
  "title": "...",
  "url": "...",
  "crop": "tomato",
  "region": "...",
  "chunk_id": "...",
  "text": "...",
  "relevance_score": 0.0
}
```

Score cụ thể sẽ được xác định khi triển khai/benchmark.

---

# 19. Fine-tuning

## Quyết định

**Open-source LLM + LoRA/QLoRA**

## Vì sao chưa chọn model cụ thể?

Hiện chưa có đủ dữ liệu benchmark để kết luận model nào tốt nhất.

Quy trình:

```text
Candidate Models
      ↓
Vietnamese Benchmark
      ↓
RAG Benchmark
      ↓
Latency / Cost
      ↓
Hallucination / Abstention
      ↓
Select
      ↓
LoRA / QLoRA
```

## Fine-tuning không thay RAG

Fine-tuning chủ yếu nhằm cải thiện:

- behavior;
- instruction following;
- tiếng Việt;
- response format;
- abstention behavior.

Knowledge factual vẫn đến từ RAG.

---

# 20. Fine-tuning Dataset

Gồm:

## A. Verified knowledge

Nguồn sự thật.

## B. Human-written QA

Câu hỏi và câu trả lời được người tạo/kiểm tra.

## C. Validated synthetic QA

LLM có thể hỗ trợ tạo dữ liệu, nhưng phải validation trước.

## D. Abstention / hallucination cases

Ví dụ:

```text
Question:
Cây X có cần Y không?

Evidence:
Không có

Expected behavior:
ABSTAIN
```

## Cảnh báo

Không được:

```text
LLM-generated
   ↓
Fine-tune ngay
```

vì có thể tạo vòng lặp:

```text
Hallucination
 ↓
Synthetic data
 ↓
Fine-tuning
 ↓
Reinforced hallucination
```

---

# 21. Training vs Evaluation

Phải tách:

```text
Dataset
 ├── Training
 └── Evaluation
```

Evaluation set không được dùng để fine-tune.

---

# 22. Anti-Hallucination Policy

## Case 1 – Evidence đủ

```text
Evidence
 ↓
Answer
 +
Source
```

## Case 2 – Không có evidence

```text
No evidence
 ↓
ABSTAIN
```

## Case 3 – Evidence yếu

```text
Weak evidence
 ↓
Abstain / Ask clarification
```

## Case 4 – High-risk

Nếu đủ evidence:

- cung cấp thông tin tham khảo;
- nêu nguồn;
- cảnh báo phù hợp.

Nếu không đủ:

```text
ABSTAIN
```

Không tự suy đoán thuốc, liều lượng hoặc quy trình nguy hiểm.

---

# 23. Citation

Backend phải giữ:

```text
Answer
+
Evidence
+
Source metadata
```

UI có thể hiển thị:

```text
Nguồn tham khảo
- Tài liệu A
- Tài liệu B
```

Citation phải truy ngược được về source.

---

# 24. Grounding Validator

Không nên tin output của LLM ngay.

```text
LLM Answer
    ↓
Claim Extraction / Checking
    ↓
Evidence Support?
    ├── YES → Answer
    └── NO  → Abstain / revise
```

Mức triển khai cụ thể sẽ được benchmark sau.

---

# 25. Evaluation Framework

Evaluation là thành phần bắt buộc.

Không chỉ demo bằng mắt.

## Pipeline

```text
Baseline
   ↓
Basic RAG
   ↓
RAG + Guardrail
   ↓
RAG + Fine-tuning
   ↓
Compare
```

Mục tiêu là chứng minh cải thiện bằng số liệu.

---

# 26. Evaluation Dataset

Nên có các nhóm:

```text
known_answer
paraphrase
no_diacritic
typo
local_terms
out_of_scope
insufficient_evidence
adversarial
high_risk
contradictory
```

Số lượng test case chưa được tự đặt ở giai đoạn này.

---

# 27. Metrics

## Retrieval

**Recall@K**

Evidence đúng có xuất hiện trong top K không?

## Answer correctness

Câu trả lời có đúng không?

## Groundedness

Các factual claims có được evidence hỗ trợ không?

## Hallucination rate

Tỷ lệ câu trả lời có factual claim không được hỗ trợ.

## Abstention accuracy

Bot có biết từ chối khi cần không?

## Citation accuracy

Source có thực sự hỗ trợ câu trả lời không?

## Scope compliance

Bot có trả lời ngoài 3 cây hay không?

## Unsupported Claim Rate

```text
Unsupported factual claims
──────────────────────────
Total factual claims
```

---

# 28. Human Evaluation

Có thể đánh giá:

- correctness;
- relevance;
- groundedness;
- clarity;
- agricultural suitability.

Đề bài có yêu cầu đánh giá câu hỏi nông học bởi chuyên gia NextFarm, nhưng ngưỡng cụ thể đang để `[cần điền]`.

Không tự đặt ngưỡng thay NextFarm.

---

# 29. Experimental Design

So sánh ít nhất:

### Baseline

LLM không có RAG.

### RAG

LLM + retrieval.

### RAG + Guardrail

Thêm scope/evidence/abstention.

### RAG + Guardrail + Fine-tuning

Cấu hình cuối.

Mục đích:

> Chứng minh từng thành phần đóng góp gì.

---

# 30. Các điểm mạnh của kiến trúc

## 30.1. Scope rõ

Chỉ 3 cây nên dễ kiểm soát.

## 30.2. Knowledge có provenance

Có thể biết answer đến từ đâu.

## 30.3. Human verification

Giảm nguy cơ garbage-in.

## 30.4. RAG

Tách knowledge khỏi model.

## 30.5. Abstention

Giải quyết đúng trọng tâm “không biết thì nói không biết”.

## 30.6. Evaluation

Có khả năng chứng minh bằng số liệu.

## 30.7. PostgreSQL + pgvector

Hạ tầng đơn giản cho PoC.

## 30.8. Có đường mở rộng

Có thể thêm:

- model;
- cây trồng;
- IoT;
- tools;
- NextFarm API.

---

# 31. Điểm yếu / rủi ro

## R1. Crawl dữ liệu kém

→ RAG vẫn trả lời sai.

**Mitigation:** source policy + verification.

## R2. Retrieval sai

→ LLM nhận evidence sai.

**Mitigation:** hybrid retrieval + reranker + evaluation.

## R3. LLM vẫn hallucinate

→ grounding validator + abstention.

## R4. Synthetic dataset nhiễu

→ validation trước training.

## R5. Fine-tuning overfit

→ tách evaluation + benchmark.

## R6. Scope creep

→ khóa 3 cây + IoT phase sau.

## R7. Không có data từ NextFarm

→ xây knowledge PoC từ nguồn công khai và ghi rõ giới hạn.

---

# 32. Những gì KHÔNG được tự bịa

Các trường sau hiện phải để OPEN nếu chưa có nguồn:

- model hiện tại của NextFarm;
- lượng hội thoại;
- chi phí API;
- latency target chính thức;
- ngưỡng chuyên gia chính thức;
- số lượng knowledge documents;
- số lượng evaluation cases;
- model fine-tuning cuối;
- embedding model cuối;
- reranker cuối;
- threshold production.

---

# 33. Folder Structure đề xuất

```text
ChatBot-NextFarm/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── retrieval/
│   │   ├── llm/
│   │   ├── grounding/
│   │   ├── citation/
│   │   └── abstention/
│   └── main.py
│
├── crawler/
│   ├── sources.yaml
│   ├── crawl.py
│   ├── extract.py
│   └── data/
│
├── knowledge/
│   ├── ingestion/
│   ├── validation/
│   ├── chunking/
│   └── embedding/
│
├── training/
│   ├── datasets/
│   ├── scripts/
│   └── configs/
│
├── evaluation/
│   ├── datasets/
│   ├── runners/
│   ├── metrics/
│   └── reports/
│
├── frontend/
├── tests/
├── docker-compose.yml
├── SPEC.md
└── README.md
```

Đây là kiến trúc đề xuất, chưa phải trạng thái code hiện tại.

---

# 34. Development Workflow

## Phase 0 – Requirement

- khóa scope;
- khóa decisions;
- ghi open questions.

## Phase 1 – Knowledge

- source registry;
- crawler;
- raw data;
- extraction;
- validation;
- human approval.

## Phase 2 – Knowledge DB

- PostgreSQL;
- schema;
- chunking;
- embedding;
- pgvector.

## Phase 3 – Retrieval

- query processing;
- hybrid retrieval;
- reranker.

## Phase 4 – RAG

- evidence pack;
- prompt;
- citation;
- abstention.

## Phase 5 – Evaluation

- dataset;
- baseline;
- RAG;
- guardrail;
- metrics.

## Phase 6 – Fine-tuning

- model benchmark;
- dataset;
- LoRA/QLoRA;
- compare.

## Phase 7 – UI/API

- chatbot;
- source display;
- status;
- logs.

## Phase 8 – Review

- security;
- quality;
- documentation;
- demo.

---

# 35. Definition of Done

PoC được xem là hoàn thành khi:

- [ ] Scope 3 cây hoạt động.
- [ ] Knowledge pipeline hoạt động.
- [ ] Source provenance được lưu.
- [ ] Human verification hoạt động.
- [ ] PostgreSQL + pgvector hoạt động.
- [ ] Retrieval hoạt động.
- [ ] Reranking được benchmark.
- [ ] RAG hoạt động.
- [ ] Citation hoạt động.
- [ ] Out-of-scope handling hoạt động.
- [ ] Abstention hoạt động.
- [ ] High-risk handling hoạt động.
- [ ] Evaluation dataset được xây dựng.
- [ ] Baseline được đo.
- [ ] RAG được đo.
- [ ] Guardrail được đo.
- [ ] Fine-tuned model được đo nếu nguồn lực cho phép.
- [ ] Có báo cáo comparison.
- [ ] Không có claim chưa có nguồn được trình bày như fact.

---

# 36. Open Questions

Các câu hỏi cần hỏi NextFarm hoặc xác minh sau:

1. Model hiện tại là gì?
2. Provider hiện tại là gì?
3. Lượng hội thoại/tháng?
4. Chi phí API?
5. Ngưỡng latency?
6. Có data nội bộ không?
7. Có nguồn tài liệu chính thức nào bắt buộc ưu tiên?
8. Ai sẽ review knowledge?
9. Ngưỡng đánh giá chuyên gia?
10. Có yêu cầu privacy/data retention nào?
11. Có yêu cầu deployment cụ thể không?

Không tự trả lời các câu này nếu chưa có nguồn.

---

# 37. Final Architecture

```text
                         USER
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    └──────┬───────┘
                           │
                           ▼
                  Query Processing
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               Scope Check    Normalization
                    │             │
                    └──────┬──────┘
                           ▼
                   Hybrid Retrieval
                           │
                           ▼
                       Reranker
                           │
                           ▼
                     Evidence Pack
                           │
                           ▼
                 Fine-tuned / Base LLM
                           │
                           ▼
                   Grounding Check
                    ┌──────┴──────┐
                    ▼             ▼
                Supported     Unsupported
                    │             │
                    ▼             ▼
             Answer + Source    Abstain


Knowledge Pipeline

Web Sources
    ↓
Source Registry
    ↓
Crawler
    ↓
Raw Data
    ↓
Extraction
    ↓
Validation
    ↓
Human Approval
    ↓
Chunking
    ↓
Embedding
    ↓
PostgreSQL + pgvector
    ↓
RAG
```

---

# 38. Final Project Agreement

### Chúng ta đang xây:

> **Một chatbot tư vấn nông nghiệp tiếng Việt cho 3 cây lúa, cà chua và dưa chuột, sử dụng knowledge base có provenance và human verification, RAG với hybrid retrieval, evidence grounding, citation, abstention và evaluation; fine-tuning bằng open-source LLM + LoRA/QLoRA được nghiên cứu như một lớp cải thiện behavior, không thay thế knowledge grounding.**

### Nguyên tắc số 1

> **Không có evidence đủ mạnh → không được tự tin trả lời factual.**

### Nguyên tắc số 2

> **Raw web data không phải ground truth.**

### Nguyên tắc số 3

> **Fine-tuning không thay thế RAG.**

### Nguyên tắc số 4

> **Không đánh giá chatbot bằng vài câu demo; phải có evaluation framework.**

### Nguyên tắc số 5

> **Thông tin chưa được cung cấp phải được đánh dấu OPEN, không được bịa.**

---

# 39. Roadmap mở rộng sau PoC

Sau khi Bài toán A ổn định:

```text
Problem A
   │
   ├── More crops
   ├── Better Vietnamese understanding
   ├── Better knowledge governance
   │
   └── IoT Integration
           │
           ├── Garden data
           ├── Sensor data
           ├── Irrigation history
           ├── Device status
           └── Alerts
```

IoT là phase mở rộng, không làm loãng PoC hiện tại.

---

# 40. Kết luận

Kiến trúc được chọn ưu tiên **độ tin cậy, khả năng audit, khả năng đo lường và khả năng mở rộng**, thay vì chỉ tối ưu việc tạo ra câu trả lời nghe tự nhiên.

Pipeline trung tâm:

```text
Crawl
 → Verify
 → Store
 → Retrieve
 → Ground
 → Answer / Abstain
 → Evaluate
```

được xem là xương sống của Bài toán A.

**Status: REQUIREMENT LOCKED v1.0**
