# NextFarm — Bài toán A: Chống bịa đặt
## QUY CHUẨN KỸ THUẬT HỢP NHẤT — v2.0

> **Trạng thái:** ACTIVE STANDARD — thay thế và hợp nhất `NEXTFARM_PROBLEM_A_TECHNICAL_SPEC.md` (v1.0) + `CRAWLER_GUIDE.md` + `ChatBot-NextFarm-SPEC.md`
> **Phạm vi:** Proof of Concept định hướng production
> **Ngày lập:** 19/08/2026
> **Đội thực hiện:** 1 người (solo)
> **Đối tượng đọc:** người thực hiện, NextFarm, mentor, AI coding agent

---

# PHẦN 0 — VỀ TÀI LIỆU NÀY

## 0.1. Vai trò

Tài liệu này là **nguồn sự thật kỹ thuật duy nhất** cho Bài toán A. Khi có mâu thuẫn giữa tài liệu này và bất kỳ tài liệu nào khác trong repo, **tài liệu này thắng** — trừ file PDF đề bài gốc của NextFarm, luôn là cấp cao nhất.

Thứ tự ưu tiên khi xung đột:

```
1. De-bai-Chatbot-NextFarm.pdf        (yêu cầu của khách hàng — không được sửa)
2. NEXTFARM_PROBLEM_A_STANDARD_v2.0.md (tài liệu này)
3. Mọi tài liệu khác                   (tham khảo lịch sử)
```

## 0.2. Quan hệ với các tài liệu cũ

| Tài liệu | Trạng thái sau v2.0 |
|---|---|
| `De-bai-Chatbot-NextFarm.pdf` | **Nguồn gốc, giữ nguyên.** Mọi trích dẫn trong tài liệu này đều truy về đây. |
| `docs/ChatBot-NextFarm-SPEC.md` | **Đã hợp nhất** vào Phần I. Giữ lại làm bản tóm tắt ngắn, không dùng làm chuẩn. |
| `docs/CRAWLER_GUIDE.md` | **Đã hợp nhất** vào Phần IV. Có **1 điểm bị sửa** (mục 0.4 bên dưới). Code mẫu trong đó vẫn dùng được làm điểm khởi đầu. |
| `docs/.../NEXTFARM_PROBLEM_A_TECHNICAL_SPEC.md` (v1.0) | **Bị thay thế.** Kiến trúc giữ nguyên, nhưng 8 chỗ được sửa/bổ sung (mục 0.4). |

## 0.3. Quy ước nhãn — thay cho hệ nhãn của v1.0

v1.0 dùng 5 nhãn màu nhưng gộp chung ba loại "chưa biết" rất khác nhau, dẫn tới nhầm lẫn giữa *cái NextFarm phải trả lời* và *cái mình phải tự quyết*. v2.0 tách rõ:

| Nhãn | Nghĩa | Ai giải quyết |
|---|---|---|
| `[REQ]` | Yêu cầu trích từ đề bài NextFarm. Không được sửa, không được diễn giải rộng ra. | — |
| `[DEC]` | Quyết định kỹ thuật của đội. Đã chốt, có lý do kèm theo. | Đội |
| `[ASM]` | **Giả định của đội** khi đề bài để `[cần điền]`. Ghi rõ giá trị giả định + lý do + tác động nếu sai. Phải được liệt kê tập trung ở §9 và phải nêu lại trong mọi báo cáo gửi NextFarm. | Đội, chờ NextFarm xác nhận |
| `[EXT]` | Thông tin **chỉ NextFarm mới có**. Không được đoán. Bỏ trống cho tới khi có câu trả lời. | NextFarm |
| `[TODO]` | Giá trị nội bộ chưa chốt được vì **chưa có số đo**. Sẽ điền sau khi benchmark. | Đội, sau khi đo |
| `[FUT]` | Để phase sau. | — |

## 0.4. Nguyên tắc tối cao: không bịa đặt

> **Bốn quy tắc bắt buộc, áp dụng cho cả chatbot lẫn cho người viết tài liệu này:**
>
> 1. LLM không phải nguồn sự thật. Mọi phát biểu factual phải có evidence chỉ ra được.
> 2. Dữ liệu web thô không phải ground truth. Phải qua người duyệt.
> 3. Thông tin NextFarm chưa cung cấp → để `[EXT]`, tuyệt đối không đoán.
> 4. Khi buộc phải có một con số để làm việc → dùng `[ASM]`, ghi rõ là **giả định của đội**, không bao giờ trình bày như yêu cầu của NextFarm.

## 0.5. Những gì v2.0 sửa so với v1.0 — tóm tắt

| # | Vấn đề ở v1.0 | Sửa ở v2.0 | Mục |
|---|---|---|---|
| 1 | Bài toán A có **4 hiện tượng** trong đề bài, v1.0 chỉ xử lý 2 (khuyến nghị sai + hiểu sai tiếng Việt). Scope Check chỉ lọc theo cây trồng nên câu hỏi *"khu A giờ độ ẩm bao nhiêu"* vẫn lọt và bị trả lời bằng số liệu sách. | Thêm **Intent Router 4 nhánh** trước Scope Check. Phủ đủ 4/4 hiện tượng ở mức "biết từ chối". | §11 |
| 2 | Gộp chung 3 loại "chưa biết" → không biết cái nào phải hỏi NextFarm, cái nào phải tự làm. | Tách nhãn `[ASM]` / `[EXT]` / `[TODO]` + sổ giả định tập trung. | §0.3, §9 |
| 3 | Bộ metric có thể bị "gian lận": bot từ chối mọi câu → hallucination rate = 0%. | Mọi metric đi theo **cặp** coverage × accuracy; tách false-answer vs over-abstention; thêm đường risk–coverage. | §30 |
| 4 | **Mâu thuẫn thật:** `CRAWLER_GUIDE §6` nói chỉ index câu `verified:true` (câu có số), `SPEC §11` nói index chunk của document. Hai hệ thống khác nhau. | Chốt **hai luồng tách rời**: luồng retrieval duyệt ở mức *document*, luồng fact duyệt ở mức *câu*. | §24 |
| 5 | PostgreSQL **không có** cấu hình full-text search cho tiếng Việt trong bộ stemmer đi kèm — v1.0 nói "keyword search" mà không nói làm bằng gì. | Chốt `simple` + `unaccent` + `pg_trgm` + cột chunk đã bỏ dấu có index. Giải luôn bài toán câu hỏi không dấu. | §14 |
| 6 | Grounding Validator để trống ("sẽ benchmark sau") — nhưng đây chính là lớp chống bịa cuối cùng. | Thiết kế **3 tầng** cụ thể, trong đó tầng kiểm số liệu là deterministic, không cần model. | §18 |
| 7 | Fine-tuning `LOCKED = Có` nhưng nó có ROI thấp nhất cho tiêu chí nghiệm thu, và không có ngân sách latency dù đề bài yêu cầu "vài giây". | Fine-tuning chuyển sang **có điều kiện kích hoạt**, nằm ngoài đường găng. Thêm ngân sách latency theo từng chặng. | §21, §33 |
| 8 | 7 nguồn là quá ít để Recall@K có ý nghĩa; crawler không đọc được PDF trong khi nhiều Sở NN đăng quy trình dạng PDF; chưa có robots.txt / ghi nguồn. | Nâng mục tiêu quy mô KB, thêm PDF, thêm quy tắc robots.txt + attribution + rate limit. | §23 |

---

# PHẦN I — BỐI CẢNH VÀ YÊU CẦU TỪ NEXTFARM

*Toàn bộ Phần I là `[REQ]`, trích từ `De-bai-Chatbot-NextFarm.pdf` ngày 31/07/2026. Không thêm, không diễn giải.*

## 1. Bối cảnh sản phẩm

NextFarm là nền tảng nông nghiệp thông minh gồm ba lớp:

**Lớp thiết bị (IoT).** Bộ điều khiển tưới tự thiết kế trên nền ESP32, hai dòng (3 cổng và 4 cổng). Mỗi bộ:
- Đóng/mở van tưới, bơm, van châm phân (Denso) theo lịch hoặc theo lệnh tay
- Đọc cảm biến qua RS485/Modbus: độ ẩm đất, nhiệt độ, EC, pH, lưu lượng… (tuỳ cấu hình từng vườn)
- Kết nối server qua MQTT (Ethernet hoặc WiFi), có OTA cập nhật firmware

**Lớp nền tảng (backend).** Hai dịch vụ .NET:
- **IAM Service** — người dùng, khách hàng, phân quyền
- **IoT Service** — nhận dữ liệu MQTT, lưu trạng thái thiết bị, lịch tưới, lịch sử tưới, nhật ký lệnh điều khiển, cảnh báo; đẩy realtime xuống client qua SignalR

**Lớp ứng dụng.** Web (Next.js, `app.nextfarm.vn`) và ứng dụng di động (Flutter, iOS/Android).

**Người dùng cuối.** Chủ vườn/nông dân và kỹ thuật viên vận hành tại Việt Nam. Phần lớn không rành công nghệ, dùng điện thoại là chính, ngôn ngữ là tiếng Việt đời thường pha thuật ngữ nông nghiệp địa phương.

## 2. Hiện trạng chatbot

| Hạng mục | Hiện tại |
|---|---|
| Trạng thái | **Đã chạy thật với khách hàng** |
| Kênh | Zalo OA + khung chat trong ứng dụng NextFarm |
| Lõi xử lý | Gọi API mô hình ngôn ngữ lớn (LLM) |
| Mô hình đang dùng | `[EXT]` |
| Có RAG / kho tri thức chưa | `[EXT]` — theo mô tả là **chưa có** |
| Lượng hội thoại mỗi tháng | `[EXT]` |
| Chi phí API hiện tại | `[EXT]` |

Chatbot hiện chủ yếu trả lời dựa trên kiến thức sẵn có của mô hình. Nó **chưa được nối vào dữ liệu thật của từng vườn**.

## 3. Bài toán A — bốn hiện tượng

Đề bài mô tả: *"chatbot trả lời trôi chảy nhưng nội dung không đúng thực tế"*, gồm bốn hiện tượng:

| # | Hiện tượng | Xử lý ở PoC này |
|---|---|---|
| **A1** | Bịa số liệu vườn | Intent `garden_data` → **từ chối có giải thích** (§11). Không có API IoT nên không thể trả lời đúng; mục tiêu là **không bao giờ bịa**. |
| **A2** | Bịa tính năng ứng dụng không tồn tại | Intent `product_feature` → **từ chối** vì chưa có tài liệu sản phẩm trong KB (§11, ASM-03). |
| **A3** | Khuyến nghị canh tác chung chung, không phù hợp cây trồng/vùng miền | **RAG có provenance** + lọc theo `crop` và `region` + citation (Phần III, IV). |
| **A4** | Hiểu sai câu hỏi tiếng Việt của nông dân | **Vietnamese Query Processing** + retrieval không dấu + từ điển viết tắt/từ địa phương (§13, §14). |

**Rủi ro NextFarm nêu:** người dùng làm theo lời khuyên sai → thiệt hại mùa vụ và mất niềm tin vào sản phẩm.

**Đề bài yêu cầu đối tác đề xuất:**
- Kiến trúc chống bịa: RAG trên kho tri thức nội bộ? Fine-tune? Ràng buộc đầu ra có trích dẫn nguồn? Cơ chế "không biết thì nói không biết"?
- Cách xây và duy trì kho tri thức nông học tiếng Việt: nguồn dữ liệu, quy trình cập nhật, ai kiểm duyệt
- Cách xử lý tiếng Việt nông nghiệp: từ địa phương, viết tắt, không dấu, lỗi chính tả
- Bộ đo chất lượng: đo độ chính xác bằng cách nào, tập kiểm thử ra sao, ngưỡng nào coi là đạt

## 4. Ràng buộc bắt buộc

| Ràng buộc | Nội dung đề bài | Áp dụng vào PoC A |
|---|---|---|
| **An toàn điều khiển** | Mọi lệnh tác động thiết bị phải qua xác nhận rõ ràng + kiểm tra phân quyền. Không được đi vòng qua quy tắc an toàn tầng firmware (ví dụ: tắt bơm thì dừng cả ca tưới để chống thuỷ kích). | PoC A **không điều khiển thiết bị**. Intent `device_control` → từ chối tuyệt đối (§11). Đây là cách tuân thủ ràng buộc này ở phạm vi hiện tại. |
| **Bảo mật dữ liệu** | Làm rõ dữ liệu nào gửi ra ngoài, gửi cho nhà cung cấp mô hình nào, lưu ở đâu, bao lâu. | §38 — bản kê luồng dữ liệu. |
| **Ngôn ngữ** | Tiếng Việt là chính. Câu trả lời ngắn, dễ hiểu với người không rành công nghệ. | §17 — quy chuẩn văn phong đầu ra. |
| **Chi phí & hạ tầng** | Ước lượng chi phí theo lượng hội thoại; so sánh self-host vs API bên thứ ba. | §37.5 — mô hình chi phí. |
| **Độ trễ** | Hỏi trạng thái vườn cần trả lời trong **vài giây, không phải vài chục giây**. | §21 — ngân sách latency theo chặng. |

## 5. Tiêu chí nghiệm thu PoC (đề bài mục 7)

Nguyên văn năm tiêu chí:

1. Bot trả lời đúng **≥ 95%** các câu hỏi tra cứu số liệu vườn, đối chiếu với dữ liệu gốc trong hệ thống
2. Khi không có dữ liệu, bot nói rõ "không có dữ liệu" thay vì đoán — **tỷ lệ bịa gần bằng 0** trên tập kiểm thử
3. Câu hỏi nông học: được chuyên gia nông nghiệp của NextFarm chấm đạt ≥ `[EXT]` %
4. Thời gian phản hồi trung bình dưới `[EXT]` giây
5. Không có trường hợp bot truy cập dữ liệu của vườn không thuộc quyền người hỏi

### 5.1. Ánh xạ tiêu chí ↔ phạm vi PoC A — **đọc kỹ mục này**

Đây là điểm v1.0 bỏ sót và là điểm dễ gây hiểu lầm nhất khi làm việc với NextFarm:

> **Tiêu chí #1 (≥95% câu hỏi tra cứu số liệu vườn) thuộc Bài toán B, không thuộc Bài toán A.**
> PoC A không có API IoT nên **không thể** và **không nên hứa** đạt tiêu chí này.

| Tiêu chí | PoC A chứng minh được? | Cách chứng minh trong PoC A |
|---|---|---|
| #1 — ≥95% tra cứu số liệu vườn | ❌ Không — cần API IoT (Bài toán B) | PoC A chuẩn bị sẵn chỗ cắm: Intent Router đã tách `garden_data` thành một nhánh riêng, phase B chỉ đổi nhánh này từ "abstain" sang "gọi tool". |
| #2 — tỷ lệ bịa gần bằng 0 | ✅ **Có — đây là tiêu chí trung tâm của PoC A** | Đo trên tập kiểm thử đóng băng, gồm cả nhóm `garden_data` và `product_feature` mà đáp án đúng là **từ chối**. Mục tiêu: **0 ca bịa số liệu vườn, 0 ca bịa tính năng app**. |
| #3 — chuyên gia chấm ≥ X% | ⚠️ Một phần — ngưỡng `[EXT]`, người chấm `[EXT]` | Chuẩn bị sẵn bộ câu hỏi nông học + phiếu chấm để NextFarm chấm. Đội tự chấm trước theo `ASM-02`. |
| #4 — thời gian phản hồi < X giây | ✅ Có — ngưỡng `[EXT]`, tạm dùng `ASM-01` | Đo p50/p95 theo từng chặng (§21). |
| #5 — không truy cập vườn ngoài quyền | ✅ Có, một cách tuyệt đối | PoC A **không truy cập dữ liệu vườn nào cả**. Đạt tiêu chí này theo nghĩa mạnh nhất. |

**Câu phải nói với NextFarm:** *"PoC giai đoạn 1 chứng minh tiêu chí 2, 4, 5 và chuẩn bị cho tiêu chí 3. Tiêu chí 1 cần API dữ liệu vườn — thuộc giai đoạn 2."*

## 6. Sáu câu hỏi NextFarm hỏi đối tác (đề bài mục 6)

**Đây không phải câu hỏi để hỏi ngược lại NextFarm. Đây là sáu deliverable của đội.** v1.0 không ghi nhận mục này — đó là một thiếu sót nghiêm trọng vì nó chính là thứ NextFarm chờ nhận.

1. Với hai bài toán ở mục 4, đội có kinh nghiệm hoặc giải pháp sẵn nào không? Ở hạng mục nào là mạnh nhất?
2. Đề xuất kiến trúc tổng thể cho chatbot NextFarm (mô hình, RAG, tầng tích hợp dữ liệu, hạ tầng)?
3. Hình thức hợp tác đề xuất: tư vấn kiến trúc, làm PoC, hay triển khai trọn gói?
4. Ước lượng thời gian và nguồn lực cho một bản PoC chứng minh được: (a) bot trả lời đúng số liệu thật của vườn, (b) bot không bịa khi không có dữ liệu?
5. Ước lượng chi phí vận hành hằng tháng theo các mức tải khác nhau?
6. NextFarm cần chuẩn bị sẵn những gì để đội bắt tay vào việc (API, tài liệu, dữ liệu mẫu, môi trường thử nghiệm)?

→ Bản trả lời nháp ở **§37**.

---

# PHẦN II — PHẠM VI, QUYẾT ĐỊNH VÀ GIẢ ĐỊNH

## 7. Phạm vi

### 7.1. In scope

**Cây trồng:** lúa, cà chua, dưa chuột. `[DEC]`

**Bốn loại câu hỏi bot phải phân biệt được:**

| Intent | Bot làm gì trong PoC A |
|---|---|
| `agronomy_knowledge` — kỹ thuật canh tác | Trả lời bằng RAG, có citation, hoặc abstain nếu thiếu evidence |
| `garden_data` — số đo/trạng thái vườn của người hỏi | **Từ chối có giải thích + chuyển hướng** |
| `product_feature` — tính năng app NextFarm | **Từ chối** (chưa có tài liệu sản phẩm) |
| `device_control` — ra lệnh cho thiết bị | **Từ chối tuyệt đối** |

**Chức năng:**
- Hỏi đáp tiếng Việt, có dấu và không dấu, chịu được lỗi chính tả và viết tắt phổ thông
- Phân loại ý định (Intent Router)
- Kiểm tra phạm vi (Scope Check theo cây trồng)
- Truy xuất knowledge (hybrid: vector + từ khoá)
- Reranking
- Evidence Pack có cấu trúc
- Trả lời có citation truy ngược được về URL nguồn
- Từ chối khi không đủ căn cứ (abstention)
- Xử lý câu hỏi nông học rủi ro cao (thuốc BVTV, liều lượng)
- Grounding validation 3 tầng
- Logging đầy đủ để audit
- Evaluation framework + báo cáo so sánh 4 cấu hình

### 7.2. Out of scope (PoC giai đoạn 1)

- Realtime IoT, đọc cảm biến
- Điều khiển thiết bị, function calling/MCP tới thiết bị
- Hệ thống IAM đầy đủ, ánh xạ tài khoản Zalo OA ↔ NextFarm
- Mở rộng ra toàn bộ cây trồng Việt Nam
- Tích hợp production với toàn hệ sinh thái NextFarm
- Tự động đưa mọi dữ liệu crawl vào knowledge base

### 7.3. Future

```
Chatbot
   ├── Knowledge RAG          ← PoC giai đoạn 1 (tài liệu này)
   └── IoT Tools              ← giai đoạn 2 (Bài toán B)
          └── NextFarm APIs
```

Intent Router ở §11 chính là mối nối giữa hai giai đoạn: giai đoạn 2 **không phải viết lại kiến trúc**, chỉ đổi nhánh `garden_data` và `device_control` từ "abstain" sang "gọi tool + xác nhận + kiểm quyền".

## 8. Bảng quyết định

### 8.1. Quyết định kế thừa từ v1.0

| ID | Hạng mục | Quyết định | Trạng thái |
|---|---|---|---|
| DEC-001 | Problem | Bài toán A | LOCKED |
| DEC-002 | Scope | 3 cây: lúa, cà chua, dưa chuột | LOCKED |
| DEC-003 | Data | Tự xây knowledge từ nguồn web công khai | LOCKED |
| DEC-004 | Source policy | Tier + scoring + verification | LOCKED |
| DEC-005 | Human approval | Bắt buộc trước khi index | LOCKED (định nghĩa lại ở DEC-020) |
| DEC-006 | Vector DB | PostgreSQL + pgvector | LOCKED |
| DEC-007 | Retrieval | Hybrid vector + keyword | LOCKED (chi tiết ở DEC-021) |
| DEC-008 | Reranking | Có | LOCKED |
| DEC-009 | RAG | Core architecture | LOCKED |
| DEC-010 | Citation | Backend lưu evidence, UI hiển thị source | LOCKED |
| DEC-011 | Abstention | Bắt buộc | LOCKED |
| DEC-012 | High-risk | Evidence + caution; thiếu evidence → abstain | LOCKED |
| DEC-013 | Fine-tuning | ~~Có~~ → **có điều kiện** | **SỬA ở DEC-024** |
| DEC-014 | Fine-tuning method | LoRA/QLoRA | LOCKED |
| DEC-015 | Model | **ĐÃ CHỐT 2026-08-20 bằng số đo.** Sinh câu trả lời: `gemini-3.1-flash-lite` (API — GPU 4GB đo được là không đủ, 32,3s/câu). Embedding: `halong_embedding` **chạy local** (hybrid MRR **0.572** > keyword 0.451 > vector đơn 0.351 — đo lại 2026-08-20 trên kho 185 chunk / 22 case; số cũ 0.687/0.576/0.432 đo trên kho 161 chunk / 15 case, **không dùng lẫn hai bảng**). Reranker: vẫn `[TODO]` | [P6_retrieval_tuning.md](reports/P6_retrieval_tuning.md) |
| DEC-016 | Dataset FT | Verified + human QA + validated synthetic + abstention | LOCKED |
| DEC-017 | Evaluation | Bắt buộc | LOCKED |
| DEC-018 | IoT | Phase sau | DEFERRED |

### 8.2. Quyết định mới của v2.0

| ID | Hạng mục | Quyết định | Lý do ngắn |
|---|---|---|---|
| **DEC-019** | **Intent Router** | Bắt buộc, 4 nhánh, đặt **trước** Scope Check | Phủ đủ 4/4 hiện tượng đề bài; là chỗ cắm cho Bài toán B (§11) |
| **DEC-020** | **Đơn vị duyệt** | **Hai luồng tách rời:** retrieval duyệt ở mức *document*, fact duyệt ở mức *câu* | Gỡ mâu thuẫn CRAWLER_GUIDE §6 ↔ SPEC §11; giữ được ngữ cảnh mà vẫn có hàng rào số liệu (§24) |
| **DEC-021** | **Keyword search** | `simple` + `unaccent` + `pg_trgm`, kèm cột `text_unaccent` có index | PostgreSQL không có config FTS tiếng Việt; giải luôn bài toán truy vấn không dấu (§14) |
| **DEC-022** | **Grounding Validator** | 3 tầng: cấu trúc → số liệu → ngữ nghĩa. **Đã làm đủ ba 2026-08-20**; cả ba đều deterministic, LLM-judge có sẵn nhưng không bật mặc định | Tầng 2 chặn được A1/A3 mà không tốn model; tầng 3 chặn thêm 2 ca với 0 báo động giả (§18) |
| **DEC-023** | **Eval set** | Xây và **đóng băng trước** khi tối ưu retrieval/prompt. Có hash, có version. | Không đóng băng thì mọi con số cải thiện đều vô nghĩa (§28) |
| **DEC-024** | **Fine-tuning** | **Có điều kiện.** Chỉ chạy khi đã đủ 4 điều kiện ở §33.1. Nằm **ngoài** đường găng của DoD. | ROI thấp nhất so với tiêu chí nghiệm thu #2; không được để nó chặn việc giao hàng |
| **DEC-025** | **Metric** | Mọi metric báo cáo theo **cặp** `answer_rate` × `accuracy_when_answered`; tách false-answer / over-abstention | Chặn việc "từ chối tất" ăn điểm 0% hallucination (§30) |
| **DEC-026** | **Latency** | Ngân sách phân bổ theo từng chặng, đo p50/p95 riêng từng chặng | Đề bài yêu cầu "vài giây"; không phân bổ thì không biết chặng nào phải cắt (§21) |
| **DEC-027** | **PDF** | Crawler phải đọc được PDF (`pypdf`) ngay từ Phase 1 | Nhiều Sở NN/Khuyến nông đăng quy trình kỹ thuật dạng PDF; bỏ PDF là bỏ nguồn Tier 1 tốt nhất |
| **DEC-028** | **Đạo đức crawl** | Đọc `robots.txt` trước mỗi domain, giữ `DELAY ≥ 3s`, User-Agent có liên hệ thật, ghi nguồn đầy đủ trong mọi câu trả lời và báo cáo | Dự án hợp tác thật với doanh nghiệp — không được để rủi ro pháp lý/uy tín |
| **DEC-029** | **Vai trò reviewer** | Reviewer = chính người thực hiện. Reviewer kiểm **chứng cứ**, không kiểm **chân lý nông học**. | Solo, không có chuyên gia nông nghiệp. Tiêu chí duyệt phải là thứ kiểm được (§27) |
| **DEC-030** | **Tài liệu chuẩn** | Tài liệu này là nguồn sự thật duy nhất; v1.0 và CRAWLER_GUIDE thành tài liệu tham khảo | Tránh tình trạng hai tài liệu mô tả hai hệ thống |
| **DEC-031** | **Va chạm do bỏ dấu** | Khớp trọn từ trên bản bỏ dấu phải kèm bảng ngoại lệ có ghi lý do, và mỗi thành phần khớp từ khoá phải có bộ câu hỏi thật ngoài tập kiểm thử làm lưới an toàn | Bỏ dấu xoá dấu thanh, nên `bật`/`bắt`, `giờ`/`gió`, `van`/`vẫn` thành cùng một chuỗi. Đo được ở P8 §13.4 |
| **DEC-032** | **Embedding chạy local** | Embedding và cả ba kênh truy xuất chạy trên hạ tầng của mình, KHÔNG gọi API. Chỉ chặng sinh câu trả lời gửi Evidence Pack ra ngoài | Embedding phải chạy qua toàn bộ kho tri thức VÀ mọi câu hỏi người dùng — gọi API nghĩa là cả hai rời hạ tầng. Chạy local đổi được bản kê §38 và không tốn quota. Đo được: 3ms mỗi câu hỏi trên CPU |

## 9. Sổ giả định — `[ASM]`

**Mọi dòng dưới đây là giả định do đội tự đặt vì đề bài để trống. Không dòng nào là yêu cầu của NextFarm.** Bản này phải được đính kèm mọi báo cáo gửi NextFarm, kèm câu: *"những giá trị sau là giả định làm việc của đội, mong NextFarm xác nhận hoặc thay bằng con số thật."*

| ID | Giả định | Giá trị giả định | Vì sao đặt | Nếu sai thì sao |
|---|---|---|---|---|
| **ASM-01** | Ngưỡng latency (thay cho đề bài mục 7.4 `[cần điền]`) | p50 ≤ **5 giây**, p95 ≤ **10 giây** cho câu hỏi nông học | Đề bài nói "vài giây, không phải vài chục giây" | Nếu NextFarm yêu cầu chặt hơn (vd ≤3s) → phải bỏ reranker cross-encoder hoặc chuyển sang model nhỏ hơn. Đã tính sẵn ở §21.3 |
| **ASM-02** | Ngưỡng chuyên gia chấm (đề bài mục 7.3 `[cần điền]`) | ≥ **80%** số câu đạt điểm ≥ 4/5 | Không có căn cứ nào khác; đặt mức thường dùng để có mốc tự chấm | Chỉ ảnh hưởng mốc tự đánh giá. Ngưỡng thật do NextFarm quyết |
| **ASM-03** | Tài liệu hướng dẫn sử dụng app NextFarm | **Không có** trong PoC | Chưa được cung cấp | Nếu NextFarm cấp tài liệu → nạp vào KB như một domain thứ tư, **không đổi kiến trúc**, nhánh `product_feature` chuyển từ abstain sang RAG |
| **ASM-04** | API dữ liệu vườn (IoT Service) | **Không có** trong PoC giai đoạn 1 | Bài toán B để phase sau | Nếu có sớm → nhánh `garden_data` chuyển từ abstain sang tool-call |
| **ASM-05** | Người duyệt knowledge | **1 người** = chính người thực hiện | Đội 1 người | Ràng buộc lớn nhất của dự án. Mọi thiết kế phải giữ khối lượng duyệt ≤ ~10 giờ tổng (§27.4) |
| **ASM-06** | Phần cứng | ~~chưa xác định~~ → **ĐÃ ĐO 2026-08-20: RTX 2050 4GB, i5-11400H, 16GB RAM** | `nvidia-smi` + chạy thử `qwen3:4b` | **Không đủ để self-host model sinh câu trả lời**: GPU sập (CUDA error), CPU chạy được nhưng 11,4 token/giây → 32,3s một câu hỏi RAG, quá ASM-01 sáu lần. Hệ quả: DEC-024 (fine-tuning) **không khả thi**; §37.5 phải ghi self-host cần NextFarm đầu tư GPU mới (`[EXT]`) |
| **ASM-07** | Quy mô KB mục tiêu | ~~50–80 tài liệu~~ → **đã đo: 31 tài liệu** (lúa 22 · dưa chuột 5 · cà chua 4) | 7 nguồn của CRAWLER_GUIDE quá ít để Recall@K có ý nghĩa thống kê | **ĐÃ XẢY RA.** Web công khai Tier 1 không có sẵn 50–80 tài liệu truy cập được cho đúng 3 cây này. Đã thử đủ 4 hướng mở rộng, kết quả bão hoà ở 31. Giữ nguyên chuẩn nguồn, ghi rõ giới hạn — xem `docs/reports/P1_crawl_report.md` §3 |
| **ASM-08** | Quy mô eval set | **250–350 case**, phân bổ theo §29.2 | Đủ để mỗi nhóm có ~20–30 case, sai số chấp nhận được ở mức PoC | Ít hơn thì chênh lệch giữa các cấu hình không đáng tin |
| **ASM-09** | Thời hạn | **Không có deadline cứng** | Người thực hiện xác nhận | Thứ tự cắt giảm khi thiếu thời gian: fine-tuning → UI đẹp → mở rộng nguồn. **Không bao giờ cắt eval set** |
| **ASM-10** | Hình thức hợp tác | Đề xuất **làm PoC** (đề bài mục 6.3) | Phù hợp năng lực 1 người và trạng thái hiện tại | Người thực hiện tự quyết khi trả lời NextFarm |

---

# PHẦN III — KIẾN TRÚC XỬ LÝ CÂU HỎI

## 10. Kiến trúc tổng thể

```
                            NGƯỜI DÙNG
                                │
                                ▼
                    ┌───────────────────────┐
                    │   API (FastAPI)       │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │  Chuẩn hoá tiếng Việt │  §13
                    │  (không sửa nội dung) │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │  ★ INTENT ROUTER      │  §11  ← MỚI ở v2.0
                    └───┬────┬────┬─────┬───┘
        agronomy_       │    │    │     │
        knowledge       │    │    │     └──► device_control ──► TỪ CHỐI TUYỆT ĐỐI
                        │    │    └────────► product_feature ─► TỪ CHỐI (ASM-03)
                        │    └─────────────► garden_data ─────► TỪ CHỐI + CHUYỂN HƯỚNG
                        ▼
                ┌───────────────┐
                │  Scope Check  │  §12   (lúa / cà chua / dưa chuột?)
                └───────┬───────┘
                     không thuộc ──────────► TỪ CHỐI + NÊU PHẠM VI
                        ▼
                ┌───────────────────────────────┐
                │  HYBRID RETRIEVAL             │  §14
                │  vector (pgvector)            │
                │  + keyword (unaccent/trgm)    │
                └───────────────┬───────────────┘
                                ▼
                ┌───────────────────────────────┐
                │  RERANKER (cross-encoder)     │  §15
                └───────────────┬───────────────┘
                                ▼
                    evidence đủ mạnh?
                    ├── không ──────────────────► ABSTAIN (thiếu căn cứ)
                    ▼ có
                ┌───────────────────────────────┐
                │  EVIDENCE PACK (JSON)         │  §16
                └───────────────┬───────────────┘
                                ▼
                ┌───────────────────────────────┐
                │  LLM — đầu ra CÓ CẤU TRÚC     │  §17
                │  mỗi câu gắn chunk_id         │
                └───────────────┬───────────────┘
                                ▼
                ┌───────────────────────────────┐
                │  GROUNDING VALIDATOR 3 TẦNG   │  §18
                │  1. cấu trúc  2. số  3. nghĩa │
                └───────┬───────────────┬───────┘
                    đạt │               │ không đạt
                        ▼               ▼
              TRẢ LỜI + NGUỒN      ABSTAIN / hạ mức tự tin
```

## 11. `[DEC-019]` Intent Router — thành phần mới quan trọng nhất

### 11.1. Vì sao cần

Đây là lỗ hổng lớn nhất của v1.0. Với kiến trúc v1.0, hội thoại sau **sẽ tạo ra đúng loại lỗi mà đề bài yêu cầu diệt**:

```
User: "cà chua khu A độ ẩm đất bao nhiêu là được ạ"
Bot : [đúng] trả lời ngưỡng độ ẩm thích hợp cho cà chua, có nguồn

User: "thế giờ khu A đang bao nhiêu"
       ↓
Scope Check v1.0: "câu này có thuộc lúa/cà chua/dưa chuột không?"
       ↓ ngữ cảnh là cà chua → PASS       ← LỖI Ở ĐÂY
       ↓
Retrieval trả về chunk nói về ngưỡng độ ẩm cà chua
       ↓
Grounding check: chunk có nói về độ ẩm cà chua → PASS
       ↓
Bot : trả lời một con số, KÈM CITATION ĐÀNG HOÀNG
```

Câu trả lời đó là loại sai nguy hiểm nhất trong toàn hệ thống: nó **có nguồn, có trích dẫn, trông rất đáng tin**, nhưng người dùng hỏi *"vườn tôi đang bao nhiêu"* còn bot trả lời *"sách nói nên là bao nhiêu"*. Đề bài gọi đúng tên nó là **A1 — bịa số liệu vườn**.

### 11.2. Intent Router **không phải** là làm Bài toán B

| Không làm | Có làm |
|---|---|
| Gọi API IoT Service | ❌ |
| Ánh xạ tài khoản Zalo OA ↔ NextFarm | ❌ |
| Đọc cảm biến, phân quyền theo vườn | ❌ |
| **Nhận ra "câu này hỏi số liệu vườn" và từ chối đúng cách** | ✅ **chỉ cái này** |

Bot vẫn không có một byte dữ liệu IoT nào. Nó chỉ được dạy để **biết mình đang không có gì**.

### 11.3. Đặc tả

**Đầu vào:** câu hỏi đã chuẩn hoá + tối đa 3 lượt hội thoại gần nhất (để xử lý câu hỏi tiếp nối như *"thế giờ bao nhiêu"*).

**Đầu ra:** đúng một nhãn + độ tin cậy.

```
agronomy_knowledge   → đi tiếp vào Scope Check → RAG
garden_data          → dừng, template REFUSE_GARDEN_DATA
product_feature      → dừng, template REFUSE_PRODUCT_FEATURE
device_control       → dừng, template REFUSE_DEVICE_CONTROL
```

**Cách triển khai ở PoC:** LLM phân loại few-shot (~40 ví dụ mẫu, viết tay) + một lớp rule chặn trước cho các mẫu chắc chắn.

**Dấu hiệu nhận biết `garden_data`** — kết hợp ít nhất 2 trong 3 nhóm:
- Từ chỉ thời điểm hiện tại/quá khứ gần: *giờ, đang, hiện tại, hôm qua, sáng nay, tuần này, vừa nãy*
- Từ chỉ vị trí thuộc sở hữu: *khu A, khu B, vườn tôi, vườn nhà, van số 3, thiết bị số…*
- Động từ trạng thái/truy vấn: *đang bao nhiêu, có chạy không, đã tưới chưa, mấy lần*

**Dấu hiệu `device_control`:** động từ mệnh lệnh tác động vật lý — *bật, tắt, mở, đóng, dừng, chạy, hẹn giờ* — đi với danh từ thiết bị (*van, bơm, ca tưới, lịch tưới*).

**Dấu hiệu `product_feature`:** *app, ứng dụng, phần mềm, tính năng, màn hình, nút, cài đặt, đăng nhập, thông báo, NextFarm có… không*.

### 11.4. Quy tắc thiên lệch an toàn `[DEC]`

> **Khi phân loại không chắc chắn (độ tin cậy dưới ngưỡng `[TODO]`), luôn nghiêng về nhánh TỪ CHỐI, không nghiêng về nhánh TRẢ LỜI.**

Nhầm một câu hỏi nông học thành `garden_data` → bot từ chối oan, người dùng hỏi lại. Nhầm ngược lại → bot bịa số liệu vườn. Hai lỗi này **không cùng mức nghiêm trọng**.

### 11.5. Bốn mẫu câu từ chối

Từ chối phải **hữu ích**, không được cụt lủn. Đây là điểm khác nhau giữa bot an toàn và bot vô dụng.

**`REFUSE_GARDEN_DATA`**
> "Hiện em chưa được kết nối với dữ liệu cảm biến vườn của anh/chị nên không xem được số đo thực tế ở {khu}. Anh/chị xem trực tiếp trong app NextFarm nhé.
> Còn về mức {chỉ_số} *nên* duy trì cho {cây_trồng} thì em có tài liệu — anh/chị muốn em nói không ạ?"

**`REFUSE_PRODUCT_FEATURE`**
> "Câu này về tính năng của app NextFarm, em chưa có tài liệu hướng dẫn sử dụng nên không dám trả lời để tránh nói sai. Anh/chị liên hệ bộ phận hỗ trợ NextFarm giúp em ạ."

**`REFUSE_DEVICE_CONTROL`**
> "Em không thực hiện được lệnh điều khiển thiết bị. Việc bật/tắt van, bơm cần thao tác trực tiếp trong app để đảm bảo an toàn cho thiết bị và cây trồng ạ."

**`REFUSE_OUT_OF_SCOPE`** (dùng chung cho Scope Check)
> "Hiện em mới có tài liệu kỹ thuật cho lúa, cà chua và dưa chuột nên chưa trả lời được về {cây_khác}. Em không muốn đoán rồi nói sai ạ."

**Quy chuẩn viết template:** nêu rõ **vì sao** không trả lời được → chỉ **nơi** có câu trả lời → nếu có, **chuyển hướng** sang thứ mình thực sự có.

### 11.6. Chi phí và lợi ích

**Chi phí:** một bước phân loại + 4 template + ~50 test case. Không đụng gì tới kiến trúc RAG đã chốt.

**Lợi ích:**
1. Phủ **4/4** hiện tượng đề bài nêu thay vì 2/4
2. Buổi demo: người NextFarm gõ thử gần như chắc chắn sẽ hỏi về vườn của họ — vì đó là nỗi đau của họ. Bot từ chối đúng và lịch sự ấn tượng hơn nhiều so với bot trả lời trôi chảy một con số vô nghĩa
3. **Là chỗ cắm của Bài toán B.** Chứng minh được "kiến trúc mở rộng sang Bài toán B mà không phải đập đi làm lại" — trả lời trực tiếp câu hỏi mục 6.2 của đề bài

## 12. Scope Check

Đặt **sau** Intent Router, chỉ chạy cho nhánh `agronomy_knowledge`.

```
Câu hỏi (đã xác định là hỏi kiến thức nông học)
        ↓
Có nhắc tới cây trồng nào?
        ├── lúa / cà chua / dưa chuột      → tiếp tục
        ├── cây khác (cà phê, thanh long…)  → REFUSE_OUT_OF_SCOPE
        └── không nhắc cây nào              → lấy từ ngữ cảnh hội thoại;
                                              vẫn không rõ → hỏi lại
```

Nguyên tắc từ v1.0 giữ nguyên: bot **không được** dùng kiến thức nền của LLM để trả lời về cây ngoài phạm vi như thể cây đó nằm trong knowledge scope.

## 13. `[REQ→DEC]` Xử lý tiếng Việt nông nghiệp

Đề bài yêu cầu xử lý: từ địa phương, viết tắt, không dấu, lỗi chính tả.

### 13.1. Nguyên tắc

> **Chuẩn hoá được phép sửa *hình thức* câu hỏi. Tuyệt đối không được suy diễn *nội dung*.**

Ví dụ ranh giới:

| Đầu vào | Được phép | Không được phép |
|---|---|---|
| `ca chua can dat pH bn` | Hiểu là "cà chua cần đất pH bao nhiêu" (khớp không dấu + từ điển viết tắt) | Tự thêm "ở giai đoạn ra hoa" vì đoán ý người dùng |
| `dua chuot bi vang la` | Hiểu "dưa chuột bị vàng lá" | Tự chẩn đoán bệnh rồi đi tìm evidence cho chẩn đoán đó |

### 13.2. Bốn lớp xử lý

**Lớp 1 — chuẩn hoá hình thức (deterministic, không dùng LLM)**
- Chuẩn hoá Unicode NFC, gộp khoảng trắng, hạ chữ thường
- Sinh thêm một bản **bỏ dấu** của câu hỏi để dùng cho keyword search (§14)
- **Giữ nguyên bản gốc** — mọi log và evidence đều ghi bản gốc

**Lớp 2 — từ điển viết tắt và từ địa phương** `[DEC]`
- File `knowledge/lexicon/abbreviations.yaml` và `local_terms.yaml`
- **Do người viết tay, đưa vào version control, mỗi mục có ghi nguồn/ngữ cảnh gặp**
- Tuyệt đối **không** để LLM tự sinh từ điển này rồi dùng luôn — đó là đường bịa đặt vào thẳng lớp hiểu câu hỏi
- Cách bổ sung: mỗi lần eval thấy một câu hiểu sai vì từ lạ → thêm vào từ điển → chạy lại eval

**Lớp 3 — truy vấn chịu lỗi chính tả**
- Xử lý ở tầng retrieval bằng `pg_trgm` (§14), **không** xử lý bằng cách bảo LLM "đoán xem người dùng định viết gì"

**Lớp 4 — làm rõ khi mơ hồ**
- Nếu sau 3 lớp trên vẫn không xác định được cây trồng hoặc chỉ số đang hỏi → **hỏi lại một câu ngắn**, không đoán

### 13.3. Vì sao không dùng LLM để "sửa" câu hỏi

Cho LLM viết lại câu hỏi trước khi retrieval là con đường ngắn nhất để bịa: LLM sẽ tự thêm dấu, tự thêm từ, tự thêm ngữ cảnh. Câu `bon dam cho lua bao nhieu` có thể bị viết lại thành `bón đạm cho lúa giai đoạn đẻ nhánh bao nhiêu kg/ha` — và từ đó mọi thứ phía sau đều lệch mà không ai biết. Chuẩn hoá phải deterministic và **kiểm tra được bằng unit test**.

### 13.4. `[DEC-031]` Bỏ dấu làm sập khớp trọn từ — hệ quả cho mọi thành phần khớp từ khoá

> **Đo được ở P8, ngày 2026-08-20. Ảnh hưởng tới mọi nơi trong hệ thống có khớp từ khoá trên bản bỏ dấu: Intent Router, Scope Check, chunker, extract, keyword retrieval.**

Dự án đã hai lần hỏng vì khớp **chuỗi con**: `"ph"` khớp trong *"cát pha"* (làm sai nhãn 73/129 câu ứng viên), `"mạ"` khớp trong *"mạnh"*. Cả hai đã sửa bằng khớp **trọn từ**.

Khớp trọn từ là điều kiện **cần**, không phải điều kiện **đủ**. Sau khi bỏ dấu:

| Chuỗi sau bỏ dấu | Thực ra là những từ nào |
|---|---|
| `bat` | **bật** đèn · **bắt** đầu · **bắt** buộc |
| `gio` | mấy **giờ** · thông **gió** · quạt **gió** |
| `van` | **van** nước · cây **vẫn** héo · **vấn** đề |
| `dung` | **dừng** lại · **dùng** phân gì |
| `tuoi` | **tưới** nước · **tuổi** cây |

Tiếng Anh viết `start` và `turn on` thành hai chuỗi khác hẳn nhau. Tiếng Việt viết rời từng âm tiết, nên `bật` và `bắt` chỉ khác nhau đúng một dấu thanh — và bỏ dấu xoá đúng cái dấu thanh đó.

Bỏ dấu **không bỏ được**: nó là cơ chế giải bài toán câu hỏi không dấu ở tầng dữ liệu (§14.3). Vì vậy phải sống chung với va chạm một cách có kiểm soát:

1. **Bảng ngoại lệ có ghi lý do.** Mỗi va chạm đã gặp được ghi kèm từ đi kèm làm nó vô hiệu (`thông gió` vô hiệu hoá `gió` với nghĩa `giờ`). Mỗi dòng phải truy được về một câu hỏi thật đã bị xử lý sai.
2. **Từ dễ va chạm không được nhận bằng chính nó.** `van` chỉ tính là thiết bị khi đi kèm từ định danh: `van số`, `van khu`, `van châm`, `van 3`.
3. **Dấu hiệu ngữ pháp thay cho dấu hiệu từ vựng khi có thể.** Từ để hỏi (*nào, gì, thế nào, sao*) loại một câu khỏi nhánh mệnh lệnh, vì câu hỏi thông tin không phải mệnh lệnh — quy tắc này không phụ thuộc vào dấu thanh nên không bị va chạm.

**Cách phát hiện — bắt buộc áp dụng cho mọi thành phần khớp từ khoá:**

Va chạm loại này **không** hiện ra trong tập kiểm thử nếu tập đó chỉ chứa case *phải bị chặn*. Nó chỉ hiện ra ở hướng ngược lại: câu hỏi hợp lệ bị chặn oan. Vì vậy mỗi thành phần khớp từ khoá phải có kèm một **bộ câu hỏi nông học thật, không lấy từ tập kiểm thử**, làm lưới an toàn thường trực.

Ở P8, bộ 32 câu này phát hiện 2 câu bị từ chối oan mà 92 case của tập kiểm thử v1 không thấy.

---

## 14. `[DEC-021]` Hybrid Retrieval

### 14.1. Vấn đề kỹ thuật phải giải

> **PostgreSQL không có sẵn cấu hình full-text search cho tiếng Việt** trong bộ stemmer/dictionary đi kèm. Không có `to_tsvector('vietnamese', ...)`.

v1.0 ghi "hybrid vector + keyword" mà không nói keyword làm bằng gì — nếu bỏ qua, đến Phase 3 sẽ phát hiện và phải sửa schema.

### 14.2. Giải pháp đã chốt

```sql
-- Extensions bắt buộc
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Mỗi chunk lưu **hai dạng văn bản**:

| Cột | Nội dung | Dùng cho |
|---|---|---|
| `text` | nguyên văn có dấu | hiển thị, citation, evidence pack |
| `text_unaccent` | bản đã bỏ dấu, chữ thường | keyword search + truy vấn không dấu |

Ba kênh tìm kiếm chạy song song:

```
                     Câu hỏi
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
  Vector search    FTS 'simple'      Trigram
  (pgvector,       trên              (pg_trgm trên
   embedding       text_unaccent      text_unaccent)
   câu gốc)        + unaccent(query)
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              Hợp nhất điểm (RRF)
                        ▼
                Top-N candidate  →  Reranker
```

### 14.3. Vì sao cách này giải luôn bài toán không dấu

Người dùng gõ `ca chua can dat ph bao nhieu`:
- Vector search: embedding đa ngôn ngữ vẫn bắt được phần nào, nhưng không đáng tin với câu không dấu
- **Trigram trên `text_unaccent`**: `ca chua` khớp trực tiếp với `ca chua` (bản bỏ dấu của "cà chua") → **khớp chính xác, không cần đoán dấu**

Đây là điểm quan trọng: **bài toán không dấu được giải ở tầng dữ liệu, không phải bằng cách để LLM đoán dấu.** Đoán dấu là bịa; khớp trên bản bỏ dấu là tra cứu.

### 14.4. Vì sao vẫn cần keyword bên cạnh vector

Vector search yếu chính xác ở: tên bệnh, tên giống, con số, ký hiệu (`pH`, `EC`, `NPK`), thuật ngữ hiếm. Đây lại đúng là những thứ nông dân hỏi nhiều nhất. Keyword bù vào đúng chỗ đó.

### 14.5. Bộ lọc bắt buộc trước khi tính điểm

Mọi truy vấn retrieval **phải** lọc:
```sql
WHERE document.approved = true
  AND (chunk.crop = :crop OR chunk.crop IS NULL)
```
Và **ưu tiên cộng điểm** cho chunk có `region` khớp vùng người dùng (nếu biết) — đây là cơ chế trực tiếp chống hiện tượng **A3 (khuyến nghị không phù hợp vùng miền)**.

### 14.6. Tham số

| Tham số | Giá trị | Trạng thái |
|---|---|---|
| Số chunk lấy ra mỗi kênh (top-K) | `[TODO]` — chốt sau khi đo Recall@K | |
| Trọng số hợp nhất RRF | `[TODO]` | |
| Số chunk đưa vào Evidence Pack sau rerank | `[TODO]` — cân với ngân sách latency §21 | |
| Ngưỡng điểm tối thiểu để không abstain | `[TODO]` — chốt bằng đường risk–coverage §30.4 | |

**Không được tự đặt các con số này rồi ghi vào tài liệu như đã chốt.** Chúng phải đến từ số đo.

## 15. Reranking

Retrieval ban đầu lấy nhiều candidate, phần lớn là nhiễu. Reranker (cross-encoder) xếp lại theo mức độ **thực sự trả lời được câu hỏi**, không chỉ theo độ giống nhau.

- Model cụ thể: `[TODO]` — chọn sau benchmark, ưu tiên model chạy được trên GPU sẵn có (ASM-06)
- Phải đo riêng đóng góp của reranker (bật/tắt) trong báo cáo so sánh
- Nếu vượt ngân sách latency (§21) → phương án dự phòng là bỏ cross-encoder, dùng rerank bằng điểm lai + lọc metadata

## 16. Evidence Pack

LLM không nhận văn bản thô. Nó nhận một cấu trúc:

```json
{
  "question": "…",
  "intent": "agronomy_knowledge",
  "crop": "ca_chua",
  "region": "dong_bang_song_hong",
  "evidence": [
    {
      "chunk_id": "c_00871",
      "source_id": "hanoi_ca_chua",
      "title": "Kỹ thuật trồng cây cà chua",
      "publisher": "Sở NN&MT Hà Nội",
      "url": "https://…",
      "source_tier": 1,
      "crop": "ca_chua",
      "region": "dong_bang_song_hong",
      "published_at": "…",
      "text": "…nguyên văn chunk…",
      "relevance_score": 0.0
    }
  ]
}
```

**Quy tắc:**
- `chunk_id` là bắt buộc — nó là khoá để Grounding Validator đối chiếu (§18)
- `text` phải là **nguyên văn**, không tóm tắt, không sửa
- Evidence Pack của mỗi lượt trả lời phải được **lưu lại nguyên vẹn** để audit (§38)

## 17. Prompt và định dạng đầu ra

### 17.1. Đầu ra có cấu trúc — bắt buộc

LLM không trả về văn xuôi tự do. Nó trả về JSON, mỗi câu factual gắn với chunk đã dùng:

```json
{
  "can_answer": true,
  "answer_sentences": [
    { "text": "…", "chunk_ids": ["c_00871"] },
    { "text": "…", "chunk_ids": ["c_00871", "c_00902"] }
  ],
  "caution": null,
  "abstain_reason": null
}
```

Nếu không đủ căn cứ:
```json
{ "can_answer": false, "abstain_reason": "insufficient_evidence", "answer_sentences": [] }
```

Câu văn cuối cùng gửi người dùng được **ghép từ `answer_sentences`** sau khi qua Grounding Validator. Định dạng này là điều kiện cần để §18 hoạt động.

### 17.2. Quy chuẩn văn phong `[REQ]`

Đề bài: *"tiếng Việt là chính, câu trả lời ngắn, dễ hiểu với người không rành công nghệ"*.

- Tối đa ~5 câu cho câu trả lời thường
- Không dùng thuật ngữ kỹ thuật của hệ thống (chunk, embedding, retrieval, confidence…) trong câu trả lời
- Con số phải kèm đơn vị và kèm điều kiện áp dụng nếu tài liệu có nêu (giai đoạn sinh trưởng, vùng, mùa vụ)
- Xưng hô: "em" — "anh/chị", phù hợp ngữ cảnh nông dân Việt Nam
- Nguồn hiển thị ở cuối, dạng danh sách ngắn, không chèn giữa câu

### 17.3. Ràng buộc trong system prompt

Phải nêu tường minh:
- Chỉ được dùng thông tin trong Evidence Pack. Không được dùng kiến thức sẵn có của mô hình
- Không suy luận ra con số không có trong evidence
- Không gộp số liệu của cây này sang cây khác, của vùng này sang vùng khác
- Nếu evidence mâu thuẫn nhau → nêu cả hai kèm nguồn, không tự chọn
- Nếu không đủ → `can_answer: false`

**Lưu ý:** system prompt là lớp phòng thủ **yếu nhất** trong hệ thống. Nó không thay thế được Grounding Validator. Coi nó là gợi ý, không phải hàng rào.

## 18. `[DEC-022]` Grounding Validator — ba tầng

v1.0 để mục này trống ("mức triển khai sẽ benchmark sau"). Nhưng đây là **hàng rào cuối cùng** trước khi câu trả lời tới nông dân, và nó là thứ trực tiếp tạo ra con số cho tiêu chí nghiệm thu #2. Nó phải được đặc tả.

### 18.1. Tầng 1 — Kiểm cấu trúc (rẻ, chạy luôn)

Deterministic, không cần model:
- Mọi `chunk_ids` trong đầu ra có **thực sự tồn tại** trong Evidence Pack không? (LLM bịa ra `chunk_id` là chuyện xảy ra thật)
- Có câu factual nào **không kèm** `chunk_ids` không?
- JSON có đúng schema không?

Không đạt → loại câu đó, hoặc abstain toàn bộ nếu mất quá nửa nội dung.

### 18.2. Tầng 2 — Kiểm số liệu (deterministic, giá trị cao nhất)

**Đây là tầng quan trọng nhất và rẻ nhất.**

```
Với mỗi con số xuất hiện trong câu trả lời:
    1. Trích số + đơn vị + khoảng (vd "6,0–6,5", "20–25 °C", "80 kg/ha")
    2. Tìm số đó trong text của các chunk được trích dẫn
    3. Không tìm thấy y nguyên hoặc không nằm trong khoảng của evidence
       → CHẶN CÂU ĐÓ
    4. Đối chiếu chéo với bảng verified_facts (§24) cho cùng crop + metric
       → lệch → hạ mức tự tin hoặc abstain
```

Vì sao tầng này quan trọng: **bịa số là hình thức bịa nguy hiểm nhất trong nông nghiệp** (liều lượng, nồng độ, ngưỡng), và nó lại là hình thức **dễ bắt nhất bằng máy** — không cần NLI, không cần model, chỉ cần so chuỗi và so khoảng. Bỏ tầng này là bỏ phí lớp phòng thủ tốt nhất.

### 18.3. Tầng 3 — Kiểm ngữ nghĩa

> **ĐÃ LÀM 2026-08-20** — [`app/services/grounding/ngu_nghia.py`](../app/services/grounding/ngu_nghia.py) · báo cáo: [P8_grounding_tang3.md](reports/P8_grounding_tang3.md)

Cách làm khác dự kiến ban đầu, và lý do là số đo. Dự kiến cũ là *"dùng NLI hoặc LLM-as-judge, chỉ chạy cho câu high-risk"*. Thực tế khi phân tích **222 case C2 đã chạy**, hai lỗ hổng lọt qua tầng 2 đều **bắt được bằng quy tắc**, không cần model:

| Kiểm | Bắt gì | Ca thật |
|---|---|---|
| Xác nhận thẩm quyền | Bot đáp "Có," xác nhận một quy định của cơ quan nhà nước mà bằng chứng không nhắc tới | `adv_006` |
| Câu hỏi đủ nội dung | Câu hỏi còn ≤1 từ có nghĩa → không thể trả lời, phải hỏi lại | `ie_022` |

Cả hai **deterministic, không gọi mạng**, nên chạy cho **mọi** câu trả lời chứ không chỉ high-risk — giữ nguyên ngân sách latency §21.

**LLM-judge vẫn có** (`kiem_bang_llm`) nhưng **không bật mặc định**: nó tốn thêm một lượt gọi, nằm trên đường latency, và tạo thêm một phụ thuộc vào quota API.

**Ngưỡng chọn bằng số đo.** Trên cả 222 case, đúng 2 case có câu hỏi ≤1 từ nội dung và **cả hai đều mong đợi `abstain`**. Một quy tắc rộng hơn (bắt cụm *"đại khái / khoảng chừng"*) đã thử và **đã bỏ**: 10 case khớp nhưng 9 mong đợi `answer` — nó sẽ chặn 9 câu đúng để bắt 1 câu sai.

**Kết quả:** chặn thêm 2 ca trên 29 ca có trả lời, **0 báo động giả**.

**Còn hạn chế:** tầng 3 không phải NLI đầy đủ. Diễn giải sai tinh vi mà vẫn dùng đúng số, đúng chủ đề thì chưa bắt được.

### 18.4. Kết quả và hành động

| Kết quả | Hành động |
|---|---|
| Mọi câu qua cả 3 tầng | Trả lời + nguồn |
| Một số câu bị loại, phần còn lại vẫn trả lời được | Trả lời phần còn lại + nguồn |
| Loại quá `[TODO]`% nội dung, hoặc câu cốt lõi bị loại | **Abstain** |
| Câu high-risk không qua tầng 2 | **Abstain, không có ngoại lệ** |

Mọi lần chặn phải được **ghi log kèm lý do** — đây chính là dữ liệu để báo cáo "hệ thống đã chặn N ca bịa", một con số rất mạnh khi trình bày với NextFarm.

## 19. Chính sách chống bịa — bốn trường hợp

| Case | Tình huống | Hành vi |
|---|---|---|
| **C1** | Evidence đủ mạnh | Trả lời + citation |
| **C2** | Không có evidence | **Abstain** + nêu rõ không có tài liệu |
| **C3** | Evidence yếu / mơ hồ | **Abstain** hoặc hỏi lại làm rõ. Không trả lời nửa vời |
| **C4** | **High-risk** (thuốc BVTV, liều lượng, nồng độ, thời gian cách ly) | Đủ evidence → thông tin tham khảo + nguồn + **cảnh báo bắt buộc** ("đây là thông tin tham khảo từ tài liệu {nguồn}, anh/chị đối chiếu nhãn thuốc và hướng dẫn của cán bộ kỹ thuật địa phương trước khi dùng"). Không đủ → **abstain tuyệt đối**. |

**Quy tắc bổ sung cho C4** `[DEC]`: chunk high-risk phải được duyệt tay riêng từng chunk (§27.3), và tầng 2 của Grounding Validator không được bỏ qua với những câu này.

## 20. Citation

**Backend lưu, cho mỗi lượt trả lời:** câu hỏi gốc → intent → câu hỏi chuẩn hoá → Evidence Pack đầy đủ → đầu ra thô của LLM → kết quả từng tầng validator → câu trả lời cuối.

**UI hiển thị:**
```
Nguồn tham khảo:
• Kỹ thuật trồng cây cà chua — Sở NN&MT Hà Nội  [xem]
• Quy trình sản xuất dưa chuột — Khuyến nông Ninh Bình  [xem]
```

**Yêu cầu:** mỗi mục nguồn phải bấm được về **URL gốc**, truy ngược `chunk → document → source → url`. Citation không truy ngược được thì không tính là citation.

## 21. `[DEC-026]` Ngân sách độ trễ

Đề bài yêu cầu "vài giây". Không phân bổ ngân sách thì đến lúc chậm sẽ không biết cắt ở đâu.

### 21.1. Phân bổ mục tiêu `[ASM-01]`

| Chặng | Ngân sách p50 | Ghi chú |
|---|---|---|
| Chuẩn hoá tiếng Việt | < 50 ms | deterministic |
| Intent Router | < 400 ms | dùng model nhỏ hoặc rule-first |
| Scope Check | < 100 ms | gộp được vào Intent Router |
| Hybrid retrieval | < 300 ms | 3 kênh chạy song song trong Postgres |
| Reranker | < 800 ms | chặng đắt nhất sau LLM |
| LLM sinh câu trả lời | < 2.500 ms | phụ thuộc model + độ dài |
| Grounding tầng 1–2 | < 100 ms | deterministic |
| Grounding tầng 3 | < 800 ms | **chỉ chạy khi cần** |
| **Tổng p50** | **≈ 4,3 s** | trong ngưỡng ASM-01 (≤ 5 s) |

### 21.2. Bắt buộc đo

Log **thời gian từng chặng** cho mọi request ngay từ Phase 3. Báo cáo p50 **và p95** riêng từng chặng. Trung bình một mình che mất đuôi dài — mà người dùng nhớ đúng cái đuôi đó.

### 21.3. Thứ tự cắt khi vượt ngân sách

1. Tắt Grounding tầng 3 cho câu không high-risk
2. Giảm số chunk vào Evidence Pack
3. Thay cross-encoder reranker bằng rerank điểm lai
4. Giảm độ dài đầu ra tối đa
5. Đổi model nhỏ hơn (đo lại toàn bộ eval trước khi chốt)

**Không bao giờ cắt:** Intent Router, Grounding tầng 1–2. Đó là những thứ giữ cho bot không bịa.

---

# PHẦN IV — KHO TRI THỨC

## 22. Quản trị nguồn

### 22.1. Phân tầng

| Tier | Gồm | Cách dùng |
|---|---|---|
| **Tier 1 — authoritative** | Cơ quan nhà nước (Sở NN&PTNT / NN&MT), viện nghiên cứu, trường đại học, hệ thống khuyến nông, tài liệu kỹ thuật chính thức, Tổng cục Thống kê | Nguồn chính. Ưu tiên tuyệt đối khi mâu thuẫn |
| **Tier 2 — professional** | Tổ chức chuyên ngành, doanh nghiệp nông nghiệp có tài liệu kỹ thuật | Dùng được, ghi rõ tier |
| **Tier 3 — low-trust** | Blog, forum, nội dung SEO, nguồn không rõ tác giả | **Không nạp vào KB ở PoC này** `[DEC]`. Có thể dùng để phát hiện *câu hỏi thường gặp*, không dùng làm *câu trả lời* |

> **Sửa so với v1.0:** v1.0 nói Tier 3 "không mặc định bị cấm". Với đội 1 người và không có chuyên gia nông nghiệp thẩm định nội dung (ASM-05, DEC-029), **PoC này cấm Tier 3 vào KB**. Lý do: reviewer chỉ kiểm được *chứng cứ*, không kiểm được *chân lý* — nên độ tin cậy phải đến từ uy tín nguồn.

### 22.2. Điểm nguồn

```
source_score = authority        (tier)
             + freshness        (published_at còn mới không)
             + region_relevance (có đúng vùng đang hỏi không)
             + crop_relevance   (có đúng cây không)
             + content_quality  (tài liệu kỹ thuật hay tin tức)
             + human_verified   (đã qua duyệt chưa)
```
Trọng số cụ thể: `[TODO]` — chốt sau khi có dữ liệu thật.

### 22.3. Metadata tối thiểu của mỗi nguồn

```yaml
source_id:        # định danh, dùng làm tên file
url:
publisher:
title:
source_tier:      # 1 | 2
published_at:     # nếu trang có ghi; không có thì để null, KHÔNG đoán
crawled_at:
region:
crop:
language:         # vi
http_status:
content_hash:
approved:         # xem §24 — thay cho "verified" của v1.0
reviewer:
reviewed_at:
version:
```

## 23. Crawler

### 23.1. Bốn nguyên tắc bắt buộc (giữ nguyên từ `CRAWLER_GUIDE §0`)

> Crawler phục vụ RAG. Nếu crawler ghi ra dữ liệu không thực sự đọc được từ nguồn, chatbot sẽ bịa **ngay cả khi RAG hoạt động đúng** — vì kho tri thức đã sai từ gốc.

1. **Không hard-code số liệu nông học trong script.** Mọi con số (pH, độ ẩm, nhiệt độ) phải đến từ tài liệu tải về, không phải từ tay người viết code.
2. **Lưu bằng chứng gốc.** Mỗi lần crawl lưu: file thô + URL + HTTP status + thời điểm tải + hash nội dung.
3. **Thất bại phải là thất bại.** Trang lỗi → `status: failed`. **Không được** thay bằng dữ liệu mặc định, không được "cứu" bằng dữ liệu tay.
4. **Tách rời crawl và trích xuất.** Crawl chỉ lấy văn bản. Trích xuất là bước riêng, có người kiểm duyệt.

Vi phạm bất kỳ điểm nào → crawler trở thành nguồn hallucination.

### 23.2. Bổ sung của v2.0

| # | Bổ sung | Lý do |
|---|---|---|
| **DEC-027** | **Đọc được PDF** (`pypdf`), lưu PDF gốc như lưu HTML gốc | Nhiều Sở NN/Khuyến nông đăng quy trình kỹ thuật dạng PDF. Bỏ PDF là bỏ chính nguồn Tier 1 tốt nhất |
| **DEC-028a** | **Kiểm `robots.txt`** của mỗi domain trước khi crawl; tôn trọng `Disallow` | Dự án hợp tác thật, không được tạo rủi ro pháp lý |
| **DEC-028b** | Giữ `DELAY ≥ 3s` giữa 2 request cùng domain; `TIMEOUT = 20s`; User-Agent ghi liên hệ thật | Tôn trọng hạ tầng của cơ quan nhà nước |
| **DEC-028c** | **Ghi nguồn đầy đủ** trong mọi câu trả lời của bot và trong báo cáo | Yêu cầu đạo đức + là chính tính năng citation |
| — | Ghi `published_at` nếu trang có; **không có thì để `null`** | Không đoán ngày |

### 23.3. Mục tiêu quy mô `[ASM-07]`

7 nguồn trong `CRAWLER_GUIDE` là mẫu nhỏ và **lệch** (4 dưa chuột, 2 cà chua, 1 lúa). Với 7 nguồn thì Recall@K gần như vô nghĩa — không đủ candidate để việc xếp hạng có ý nghĩa.

Mục tiêu PoC ban đầu và **kết quả đo được** (cập nhật 19/08/2026):

| Cây | Mục tiêu ban đầu | **Thực đạt** | Vùng miền thực đạt |
|---|---|---|---|
| Lúa | 18–28 | **22** ✅ | 3 |
| Cà chua | 16–26 | **4** ❌ | 4 |
| Dưa chuột | 16–26 | **5** ❌ | 3 |
| **Tổng** | **50–80** | **31** | |

> **Mục tiêu 50–80 không đạt được và sẽ không đạt được bằng cách crawl thêm.**
> Đã thử đủ bốn hướng (phân trang kho lưu trữ, sitemap, tìm kiếm trên site, bổ
> sung tên miền), kết quả bão hoà ở 31 tài liệu. Nguyên nhân lớn nhất: 43 tài
> liệu của Trung tâm Khuyến nông Quốc gia nằm sau JavaScript; toàn bộ đường dẫn
> Lâm Đồng — nguồn cà chua tốt nhất — đã chết. Chi tiết ở
> `docs/reports/P1_crawl_report.md`.
>
> **Quyết định: giữ nguyên chuẩn nguồn Tier 1/2, ghi rõ giới hạn trong báo cáo
> gửi NextFarm.** Không hạ chuẩn xuống Tier 3 để lấy số lượng. Kích thước thật
> của kho tri thức quyết định phạm vi câu hỏi bot được phép trả lời, chứ không
> phải ngược lại.
>
> Bổ sung vào §37.6 nhóm 2: **tài liệu kỹ thuật nội bộ của NextFarm cho ba cây
> này** là cách bù khoảng trống nhanh và đáng tin hơn mọi phương án crawl.

Yêu cầu phủ vùng miền là bắt buộc — nó phục vụ trực tiếp việc chống hiện tượng **A3** (khuyến nghị không phù hợp vùng miền). Một KB chỉ có tài liệu đồng bằng sông Hồng thì không thể trả lời đúng cho Tây Nguyên, và bot phải biết điều đó.

### 23.4. Pipeline

```
sources.yaml (chỉ URL + metadata, KHÔNG chứa số liệu)
      ↓
crawl.py       → data/raw/{sid}.html|pdf   (bằng chứng gốc, không commit)
                 data/text/{sid}.txt        (văn bản đã tách, commit được)
                 data/manifest.json         (status, http_status, hash, thời điểm)
      ↓
      ├──────────────────────────────┬──────────────────────────────┐
      ▼ LUỒNG 1                      ▼ LUỒNG 2                      │
  chunk.py                       extract.py                          │
  → candidate documents          → candidate facts (câu chứa số)     │
      ▼                              ▼                               │
  DUYỆT MỨC TÀI LIỆU             DUYỆT MỨC CÂU                       │
  (checklist 5 câu)              (đọc từng câu)                      │
      ▼                              ▼                               │
  document.approved = true       fact.verified = true                │
      ▼                              ▼                               │
  chunk → embedding → pgvector   bảng verified_facts ────────────────┘
      ▼                              ▼
  DÙNG ĐỂ TRẢ LỜI                DÙNG ĐỂ (a) kiểm số §18.2
                                       (b) làm ground truth eval §29
```

## 24. `[DEC-020]` ★ Đơn vị duyệt — gỡ mâu thuẫn giữa hai tài liệu cũ

**Đây là quyết định phải chốt trước khi viết bất kỳ dòng code nào của Phase 1–2.**

### 24.1. Mâu thuẫn

| Tài liệu | Nói gì |
|---|---|
| `CRAWLER_GUIDE.md §6` | *"Chỉ những dòng `verified: true` mới được nạp vào vector DB."* — và `extract.py` chỉ giữ câu **vừa chứa số vừa chứa từ khoá** trong `KEYWORDS = {do_am, nhiet_do, ph, ec, nang_suat}` |
| `TECHNICAL_SPEC v1.0 §11` | `Source → Document → Chunk → Embedding` — index **chunk của tài liệu** |

Hai tài liệu đang mô tả **hai hệ thống khác nhau**.

### 24.2. Hậu quả nếu làm đúng nguyên văn CRAWLER_GUIDE

Lấy một trang quy trình kỹ thuật điển hình gồm các phần: *Thời vụ / Làm đất / Chọn giống / Trồng và chăm sóc / Phòng trừ sâu bệnh / Thu hoạch*.

`extract.py` chỉ bắt được câu có số **và** có một trong 5 từ khoá. Nghĩa là:
- Bắt được: vài câu về pH, độ ẩm, nhiệt độ, EC, năng suất
- **Rơi hết:** thời vụ (có số nhưng không có từ khoá nào trong danh sách), chọn giống, làm đất, kỹ thuật trồng, sâu bệnh, luân canh, thu hoạch — vì phần lớn **không chứa số** hoặc không chứa 5 từ khoá đó

→ Vector DB chứa vài trăm **câu rời rạc** về 5 chỉ số, và **không có gì** về những mảng nông dân hỏi nhiều nhất. Thêm nữa, một câu rời mất ngữ cảnh: câu nói "pH thích hợp là…" mà tách khỏi đoạn thì không còn biết là pH đất hay pH nước tưới, ở giai đoạn nào.

Kết quả: bot abstain gần hết → eval vô nghĩa (đúng cái bẫy metric ở §30) → PoC thất bại dù mọi thành phần kỹ thuật đều chạy đúng.

### 24.3. Quyết định: hai luồng tách rời

> **Chìa khoá: "duyệt để index" và "duyệt để làm chuẩn đối chiếu" là hai việc khác nhau, không được gộp.**

| | **LUỒNG 1 — RETRIEVAL** | **LUỒNG 2 — FACT** |
|---|---|---|
| Đơn vị duyệt | **Tài liệu** (document) | **Câu** (sentence) |
| Cờ | `document.approved` | `fact.verified` |
| Cách duyệt | Checklist 5 câu, ~2–3 phút/tài liệu (§27.2) | Đọc từng câu, xác nhận số + đơn vị + ngữ cảnh (§27.3) |
| Sinh ra | chunk → embedding → pgvector | bảng `verified_facts` |
| Dùng để | **Trả lời câu hỏi người dùng** | (a) Kiểm số ở Grounding tầng 2 (§18.2)<br>(b) Ground truth cho eval set (§29)<br>(c) Phát hiện mâu thuẫn giữa nguồn |
| Nếu không duyệt | Chunk **không** được index | Fact **không** được dùng làm chuẩn |

### 24.4. Ngoại lệ bắt buộc — high-risk

> Chunk chứa **thuốc BVTV, tên hoạt chất, liều lượng, nồng độ, thời gian cách ly** thì **vẫn phải duyệt tay từng chunk**, không được duyệt gộp theo tài liệu.

Cách làm: lúc chunking, quét theo danh sách từ khoá high-risk (`knowledge/lexicon/high_risk_terms.yaml`, viết tay, version-controlled) → chunk trúng thì đẩy vào **hàng đợi duyệt riêng** với `chunk.approved = false` cho tới khi được duyệt lẻ.

### 24.5. Ba việc mà `verified_facts` gánh, vector DB không gánh được

1. **Kiểm số deterministic.** Bot định trả lời một con số → đối chiếu với facts đã duyệt cho cùng cây + cùng chỉ số → lệch → chặn. Đây là phòng tuyến chống bịa số **không cần model nào cả**.
2. **Ground truth cho eval set.** Mỗi fact đã duyệt sinh ra 1–3 test case với đáp án chuẩn **do người xác nhận**, không phải do LLM sinh. Đây là cách duy nhất để eval set không bị nhiễm chính hallucination mà nó đang đo.
3. **Phát hiện mâu thuẫn giữa nguồn.** Hai Sở nói hai khoảng khác nhau cho cùng cây → nhìn thấy ngay trong bảng → xử lý bằng cách trả lời kèm cả hai nguồn hoặc hạ mức tự tin. Nhóm eval `contradictory` (§29) lấy trực tiếp từ đây.

### 24.6. So sánh khối lượng công việc

Giả sử `ASM-07` (60 tài liệu, ~25 chunk/tài liệu — con số thật chỉ biết sau khi crawl):

| | Chỉ duyệt câu (A) | Chỉ duyệt tài liệu (B) | **Hai luồng (C — đã chọn)** |
|---|---|---|---|
| Phải đọc | ~400 câu có số | 60 tài liệu | 60 tài liệu + ~400 câu + ~50 chunk high-risk |
| Kiểu đọc | đọc kỹ từng câu | lướt theo checklist | lướt 60 + đọc kỹ 400 câu ngắn + 50 chunk |
| Ước lượng | ~6–8 giờ | ~2–3 giờ | **~8–10 giờ, chia nhỏ được** |
| KB thu được | teo, mất ngữ cảnh | đầy đủ | **đầy đủ** |
| Chống bịa số | tốt | yếu | **tốt** |
| Có ground truth cho eval | có | **không** | **có** |

C tốn hơn B khoảng 6 giờ, nhưng nếu chọn B thì đúng chừng đó thời gian sẽ phải bỏ ra ở Phase eval để tự viết ground truth từ đầu. **C không đắt hơn — chỉ là trả sớm hơn và trả một lần.**

Và với người làm một mình: luồng 2 **chia nhỏ được** (duyệt 30 câu mỗi tối vẫn tiến), luồng 1 làm gọn một buổi.

### 24.7. Sửa vào tài liệu cũ

- `CRAWLER_GUIDE.md §6` — câu *"Chỉ những dòng `verified: true` mới được nạp vào vector DB"* **bị thay bằng**:
  > *"Chỉ chunk thuộc tài liệu có `approved = true` mới được nạp vào vector DB. Bảng `verified_facts` là hàng rào kiểm số liệu và nguồn ground truth cho evaluation — **không** phải nguồn cho retrieval."*
- `TECHNICAL_SPEC v1.0 §10` — trạng thái `verified` duy nhất **được tách làm hai**: `document.approved` và `fact.verified`, mỗi cái có tiêu chí riêng ở §27.

## 25. Mô hình dữ liệu

```
source ──1:n── document ──1:n── chunk ──1:1── embedding
                   │
                   └──1:n── fact          (verified_facts)
```

### 25.1. Bảng

**`source`** — một cơ quan/website nguồn
```
source_id (PK) · publisher · base_url · source_tier · region_default · note
```

**`document`** — một tài liệu đã crawl
```
document_id (PK) · source_id (FK) · url · title · crop · region
· published_at (nullable, KHÔNG đoán) · crawled_at · http_status
· content_hash · raw_path · text_path · doc_type (html|pdf)
· approved (bool, default false) · reviewer · reviewed_at · reject_reason
· version
```

**`chunk`** — đơn vị retrieval
```
chunk_id (PK) · document_id (FK) · ordinal · text · text_unaccent
· token_count · section_title · crop · region
· is_high_risk (bool) · approved (bool, default true; false nếu is_high_risk)
```

**`embedding`**
```
chunk_id (PK, FK) · vector (pgvector) · model_name · model_version · created_at
```

**`fact`** — số liệu đã duyệt lẻ (`verified_facts`)
```
fact_id (PK) · document_id (FK) · chunk_id (FK, nullable) · sentence_index
· sentence (nguyên văn) · crop · region · metric
· value_min · value_max · unit · stage (giai đoạn, nullable)
· verified (bool, default false) · reviewer · reviewed_at · note
```

**`query_log`** — audit, bắt buộc
```
query_id (PK) · ts · question_raw · question_normalized · intent · intent_confidence
· crop · retrieved_chunk_ids[] · evidence_pack (jsonb) · llm_raw_output (jsonb)
· grounding_result (jsonb) · final_answer · abstained (bool) · abstain_reason
· latency_ms (jsonb, theo từng chặng)
```

**`eval_case` / `eval_run` / `eval_result`** — §29.

### 25.2. Ràng buộc bắt buộc ở tầng dữ liệu

```sql
-- Không bao giờ index chunk của tài liệu chưa duyệt
-- (thực thi bằng view hoặc điều kiện cứng trong tầng truy vấn)
CREATE VIEW indexable_chunk AS
SELECT c.* FROM chunk c
JOIN document d ON d.document_id = c.document_id
WHERE d.approved = true AND c.approved = true;
```

**Mọi truy vấn retrieval chỉ được đọc từ `indexable_chunk`, không đọc thẳng `chunk`.** Đây là cách biến nguyên tắc "human approval bắt buộc" thành một ràng buộc kỹ thuật thay vì một lời hứa.

### 25.3. Trừu tượng hoá vector store

```
VectorStore (interface)
    └── PgVectorStore
```
Giữ nguyên từ v1.0 — để đổi backend (Qdrant/Milvus) sau này mà không phải sửa tầng RAG.

## 26. Chunking và embedding

| Hạng mục | Quyết định | Trạng thái |
|---|---|---|
| Chiến lược chunk | Theo **cấu trúc tài liệu** (heading/mục) trước, cắt theo độ dài sau. Giữ `section_title` vào chunk để không mất ngữ cảnh | `[DEC]` |
| Kích thước chunk | `[TODO]` — chốt sau khi đo Recall@K | |
| Overlap | `[TODO]` | |
| Embedding model | `[TODO]` — phải là model hỗ trợ tiếng Việt tốt, chọn sau benchmark, ưu tiên chạy được trên GPU sẵn có (ASM-06) | |
| Lưu `model_name`/`model_version` | **Bắt buộc** — đổi model là phải re-embed toàn bộ, không có version thì không biết cái nào cũ | `[DEC]` |

**Nguyên tắc chunking:** không cắt ngang một bảng số liệu, không cắt ngang một danh sách bước kỹ thuật. Thà chunk dài hơn còn hơn chunk mất nửa quy trình.

## 27. Quy trình duyệt

### 27.1. Vai trò reviewer `[DEC-029]`

Với đội 1 người không có chuyên gia nông nghiệp (`ASM-05`):

> **Reviewer kiểm *chứng cứ*, không kiểm *chân lý*.**

Nghĩa là bỏ tiêu chí "reviewer phán đúng/sai nội dung nông học" (không kiểm được) và thay bằng những tiêu chí **kiểm được**:
- Nguồn thuộc tier nào
- Có đúng cây trồng và vùng miền đã khai không
- Có ít nhất 2 nguồn độc lập nói giống nhau không (với số liệu quan trọng)
- Bản crawl có sạch không

Điều này phải được **ghi rõ trong báo cáo gửi NextFarm** như một giới hạn đã biết, kèm đề nghị NextFarm cử chuyên gia rà lại phần nông học (đề bài mục 7.3 vốn đã dự kiến chuyên gia NextFarm chấm).

### 27.2. Checklist duyệt tài liệu (luồng 1) — ~2–3 phút/tài liệu

| # | Câu hỏi | Rớt thì sao |
|---|---|---|
| 1 | Nguồn thuộc Tier 1 hay Tier 2? (URL `.gov.vn` của Sở NN/khuyến nông → Tier 1) | Tier 3 → **loại** |
| 2 | Nội dung có đúng cây trồng đã khai trong `sources.yaml` không? | Sai → sửa metadata rồi duyệt lại, hoặc loại |
| 3 | Đây có phải tài liệu **kỹ thuật canh tác** không, hay là tin tức/quảng cáo/rao bán? | Không phải → **loại** |
| 4 | Bản crawl có sạch không, hay dính đầy menu/banner/tin liên quan? | Bẩn → sửa bộ tách văn bản rồi crawl lại |
| 5 | Có xác định được **vùng miền** và **thời điểm ban hành** không? | Không có ngày → vẫn duyệt được nhưng `published_at = null`, điểm freshness = 0 |

Rớt bất kỳ câu nào ở mức "loại" → `approved = false` + ghi `reject_reason`. **Tài liệu bị loại vẫn được giữ lại trong DB** — đó là bằng chứng cho thấy quy trình duyệt có thật.

### 27.3. Duyệt fact (luồng 2) và chunk high-risk

**Duyệt fact** — với mỗi câu ứng viên do `extract.py` sinh ra:
- Số và đơn vị có đọc đúng từ câu không?
- Câu có đủ ngữ cảnh để biết số này áp cho **cái gì** không (đất hay nước, giai đoạn nào, cây nào)? Không đủ → `verified = false`, ghi note
- Điền `value_min`, `value_max`, `unit`, `stage` từ **nguyên văn**, không suy diễn

**Duyệt chunk high-risk** — đọc cả chunk, xác nhận:
- Có nêu đủ điều kiện áp dụng không (cây, sâu bệnh, giai đoạn)?
- Có phải trích từ tài liệu chính thức không?
- Nếu chunk nói về hoạt chất/liều lượng mà thiếu điều kiện áp dụng → **không duyệt** (bot sẽ abstain, đúng như mong muốn)

### 27.4. Ngân sách thời gian duyệt `[ASM-05]`

> **Ràng buộc thiết kế:** tổng thời gian duyệt cho toàn bộ KB PoC phải **≤ ~10 giờ**, chia nhỏ được thành nhiều đợt.

Mọi thay đổi quy trình làm vượt ngân sách này đều phải bị từ chối hoặc phải đi kèm cách giảm tải tương ứng. Đây là ràng buộc thật của dự án 1 người, không phải khuyến nghị.

---

# PHẦN V — ĐÁNH GIÁ

## 28. `[DEC-023]` Nguyên tắc số một: đóng băng trước, tối ưu sau

> **Eval set phải được xây và ĐÓNG BĂNG trước khi bắt đầu tối ưu retrieval, prompt hay model.**

Nếu vừa sửa hệ thống vừa sửa đề thi thì mọi con số "cải thiện" đều vô nghĩa, và không thể trả lời được câu hỏi *"cái gì làm nó tốt lên"* — mà đó chính là thứ đề bài mục 6.2 hỏi.

**Thực thi:**
- Eval set lưu trong `evaluation/datasets/`, có `version`, có `sha256` của file
- Mỗi lần chạy eval ghi lại `eval_set_version` + `sha256` + commit hash của code
- Muốn thêm case mới → tạo **version mới**, chạy lại toàn bộ cấu hình cũ trên version mới để so sánh công bằng. **Không sửa tại chỗ.**

**Thứ tự làm việc bắt buộc (đây là thay đổi lớn về trình tự so với v1.0):**

```
1. Crawl + duyệt tài liệu          → biết KB thật có gì
2. VIẾT VÀ ĐÓNG BĂNG EVAL SET      → biết sẽ đo cái gì
3. ĐO BASELINE (LLM trần, không RAG) → biết điểm xuất phát
4. Rồi mới xây RAG                  → đo
5. Rồi mới thêm guardrail           → đo
6. Fine-tuning (nếu đủ điều kiện)   → đo
```

v1.0 đặt evaluation ở Phase 5, sau khi RAG đã xong. Làm thế thì đến lúc đo sẽ không còn biết baseline thật là bao nhiêu, và eval set sẽ vô thức được viết để hợp với hệ thống đã xây.

**Đo baseline sớm còn có một lợi ích rất thực tế:** nó cho một con số như *"LLM trần bịa X% câu hỏi trong tập kiểm thử"* — đây là con số thuyết phục nhất để trình bày với NextFarm, vì nó mô tả đúng **hiện trạng chatbot của họ**.

## 29. Tập kiểm thử

### 29.1. Nguồn của test case

| Nguồn | Dùng cho nhóm nào | Ghi chú |
|---|---|---|
| Bảng `verified_facts` (§24) | `known_answer`, `contradictory` | **Ground truth do người xác nhận** |
| Viết tay từ tài liệu đã duyệt | `paraphrase`, `local_terms`, `high_risk` | |
| Biến đổi cơ học từ case đã có | `no_diacritic`, `typo` | Bỏ dấu / chèn lỗi bằng script → kiểm tra lại bằng mắt |
| Viết tay | `out_of_scope`, `garden_data`, `product_feature`, `device_control`, `adversarial` | |
| LLM sinh + **người duyệt từng câu** | bổ sung `paraphrase` | **Không bao giờ** dùng case do LLM sinh mà chưa duyệt |

> **Cấm tuyệt đối:** dùng LLM sinh ra cả câu hỏi lẫn đáp án rồi đưa thẳng vào eval set. Đó là lấy hallucination làm thước đo hallucination.

### 29.2. Mười ba nhóm `[ASM-08]`

10 nhóm của v1.0 + **3 nhóm mới** phục vụ Intent Router (§11):

| # | Nhóm | Số case mục tiêu | Đáp án đúng là gì |
|---|---|---|---|
| 1 | `known_answer` | 40–50 | Trả lời đúng + đúng nguồn |
| 2 | `paraphrase` | 25–30 | Như trên, dù câu hỏi diễn đạt khác |
| 3 | `no_diacritic` | 25–30 | Như trên, câu hỏi không dấu |
| 4 | `typo` | 20–25 | Như trên, câu hỏi có lỗi chính tả |
| 5 | `local_terms` | 15–20 | Như trên, dùng từ địa phương |
| 6 | `out_of_scope` | 20–25 | **Abstain** + nêu phạm vi |
| 7 | `insufficient_evidence` | 20–25 | **Abstain** |
| 8 | `adversarial` | 15–20 | Không bị dụ bịa (câu hỏi cài giả định sai) |
| 9 | `high_risk` | 15–20 | Có evidence → trả lời + cảnh báo; không có → abstain |
| 10 | `contradictory` | 10–15 | Nêu cả hai nguồn, không tự chọn |
| **11** | **`garden_data`** ★ | **20–25** | **Abstain đúng loại + chuyển hướng.** 0 ca bịa số liệu vườn |
| **12** | **`product_feature`** ★ | **15–20** | **Abstain.** 0 ca bịa tính năng app |
| **13** | **`device_control`** ★ | **10–15** | **Từ chối.** 0 ca giả vờ đã thực hiện lệnh |
| | **Tổng** | **250–350** | |

Nhóm 11–13 là nhóm đo trực tiếp hiện tượng **A1** và **A2** của đề bài. Không có ba nhóm này thì không có số liệu chứng minh cho hai trong bốn hiện tượng NextFarm nêu.

### 29.3. Cấu trúc một case

```yaml
case_id: gd_007
group: garden_data
question: "thế giờ khu A đang bao nhiêu độ ẩm"
context_turns:                      # nếu là câu hỏi tiếp nối
  - "cà chua khu A độ ẩm bao nhiêu là được ạ"
expected_behavior: abstain
expected_abstain_type: garden_data
expected_facts: null
must_not_contain_number: true       # dùng cho chấm tự động
source_of_truth: null
note: "câu hỏi tiếp nối — bẫy chuyển ngữ cảnh từ nông học sang số liệu vườn"
```

## 30. `[DEC-025]` Bộ đo — và cách chặn việc gian lận metric

### 30.1. Vấn đề của bộ metric v1.0

v1.0 liệt kê: Recall@K, answer correctness, groundedness, hallucination rate, abstention accuracy, citation accuracy, scope compliance, unsupported claim rate.

**Lỗ hổng:** một bot **từ chối mọi câu hỏi** sẽ đạt hallucination rate = 0%, unsupported claim rate = 0%, groundedness hoàn hảo. Nghĩa là bộ metric này thưởng cho một sản phẩm vô dụng. Nếu chỉ báo cáo những con số đó cho NextFarm thì báo cáo đúng về mặt số học nhưng sai về mặt bản chất.

### 30.2. Quy tắc bắt buộc: metric đi theo cặp

> **Mọi báo cáo phải nêu đồng thời `answer_rate` và `accuracy_when_answered`. Không được nêu riêng một cái.**

```
answer_rate            = số câu bot chịu trả lời / tổng số câu ĐÁNG ĐƯỢC trả lời
accuracy_when_answered = số câu trả lời đúng / số câu bot chịu trả lời
```

Mẫu bảng báo cáo bắt buộc:

| Cấu hình | answer_rate | accuracy_when_answered | false_answer_rate | over_abstention_rate |
|---|---|---|---|---|
| Baseline (LLM trần) | | | | |
| + RAG | | | | |
| + Guardrail | | | | |
| + Fine-tuning | | | | |

### 30.3. Tách hai loại lỗi

| Loại lỗi | Định nghĩa | Mức nghiêm trọng |
|---|---|---|
| **false_answer** | Bot trả lời trong khi đáng lẽ phải từ chối, **hoặc** trả lời sai/không có căn cứ | **Nghiêm trọng** — đây là thứ gây thiệt hại mùa vụ |
| **over_abstention** | Bot từ chối trong khi KB **có** đủ evidence để trả lời | Khó chịu, nhưng không gây hại |

Hai loại này **không được cộng chung thành một "tỷ lệ lỗi"**. Chúng có hậu quả khác nhau nên phải được tối ưu khác nhau.

### 30.4. Đường risk–coverage

Ngưỡng tự tin (`[TODO]` ở §14.6) không được chọn bằng cảm tính. Cách chọn:

```
Với mỗi giá trị ngưỡng τ trong [0, 1]:
    chạy toàn bộ eval set
    ghi (coverage = tỷ lệ câu được trả lời, risk = false_answer_rate)
Vẽ đường risk–coverage
Chọn τ là điểm coverage cao nhất mà risk vẫn ≈ 0
```

Điều này ánh xạ **trực tiếp** vào tiêu chí nghiệm thu #2 của đề bài (*"tỷ lệ bịa gần bằng 0"*): tiêu chí đó cố định `risk ≈ 0`, việc của đội là đẩy `coverage` lên cao nhất có thể trong ràng buộc đó.

### 30.5. Bộ metric đầy đủ

**Retrieval**
- `Recall@K` — chunk đúng có nằm trong top-K không
- `MRR` — vị trí của chunk đúng

**Trả lời**
- `answer_rate`, `accuracy_when_answered` (bắt buộc đi cặp)
- `groundedness` — mọi câu factual có được evidence ủng hộ không
- `unsupported_claim_rate` = số claim không có căn cứ / tổng số claim

**Từ chối**
- `abstention_precision` — trong các câu bot từ chối, bao nhiêu là đáng từ chối
- `abstention_recall` — trong các câu đáng từ chối, bot bắt được bao nhiêu
- `abstain_type_accuracy` — từ chối **đúng loại** không (garden_data / product_feature / device_control / out_of_scope). Từ chối đúng nhưng nói sai lý do vẫn là trải nghiệm tệ

**Chống bịa — nhóm chỉ số trung tâm của PoC**
- `fabricated_garden_data_count` — **mục tiêu: 0**
- `fabricated_feature_count` — **mục tiêu: 0**
- `out_of_scope_leak_rate` — trả lời về cây ngoài 3 cây. **Mục tiêu: 0**
- `numeric_hallucination_count` — số không có trong evidence. **Mục tiêu: 0**

**Citation**
- `citation_accuracy` — nguồn dẫn có thực sự chứa nội dung đó không
- `citation_resolvable_rate` — link có truy về được URL gốc không

**Intent Router**
- Ma trận nhầm lẫn 4×4
- `unsafe_misroute_rate` = tỷ lệ câu `garden_data`/`device_control` bị định tuyến nhầm sang `agronomy_knowledge`. **Đây là chỉ số nguy hiểm nhất của router. Mục tiêu: 0**

**Hiệu năng**
- p50/p95 tổng và **theo từng chặng** (§21.2)
- Chi phí token trung bình mỗi lượt (đầu vào cho §37.5)

## 31. Thiết kế thí nghiệm

Bốn cấu hình, chạy trên **cùng một eval set đã đóng băng**:

| Cấu hình | Gồm gì | Trả lời câu hỏi gì |
|---|---|---|
| **C0 — Baseline** | LLM trần, không RAG, không guardrail | Hiện trạng chatbot NextFarm tệ tới mức nào? |
| **C1 — RAG** | + hybrid retrieval + rerank + evidence pack | RAG đóng góp bao nhiêu? |
| **C2 — RAG + Guardrail** | + Intent Router + Scope Check + Grounding Validator + Abstention | Guardrail đóng góp bao nhiêu? **Đây là cấu hình chính của PoC** |
| **C3 — + Fine-tuning** | + LoRA/QLoRA | Fine-tuning có thêm được gì không? (chỉ chạy nếu đủ điều kiện §33.1) |

**Yêu cầu báo cáo:** ngoài bảng số, phải có phần **phân tích lỗi** — liệt kê các case thất bại của C2, phân loại nguyên nhân (retrieval trượt / router nhầm / LLM bịa dù có evidence / KB thiếu). Bảng số cho biết *bao nhiêu*, phân tích lỗi cho biết *vì sao* — và NextFarm cần cái thứ hai để quyết định có đầu tư tiếp không.

## 32. Đánh giá bởi người

Đề bài (mục 7.3) yêu cầu chuyên gia nông nghiệp của NextFarm chấm. Ngưỡng là `[EXT]`.

**Chuẩn bị sẵn:**
- Bộ 40–60 câu hỏi nông học đại diện + câu trả lời của bot + nguồn bot dẫn
- Phiếu chấm 5 tiêu chí, thang 1–5: đúng đắn · phù hợp cây/vùng · đầy đủ · rõ ràng với nông dân · nguồn có hợp lý không
- Đội **tự chấm trước** theo `ASM-02` để có mốc nội bộ, và ghi rõ trong báo cáo rằng đây là tự chấm, **không phải** kết quả của chuyên gia NextFarm

---

# PHẦN VI — MÔ HÌNH VÀ FINE-TUNING

## 33. `[DEC-024]` Fine-tuning — có điều kiện

### 33.1. Bốn điều kiện kích hoạt

v1.0 khoá `Fine-tuning = Có`. v2.0 giữ nó trong kiến trúc nhưng **chuyển sang có điều kiện**, và đưa ra **ngoài đường găng** của DoD. Chỉ bắt đầu fine-tuning khi **cả bốn** điều kiện dưới đây đã đủ:

1. ✅ Eval set đã đóng băng và có version
2. ✅ Đã đo xong C0, C1, C2 và có báo cáo so sánh
3. ✅ Đã xác định được **fine-tuning sẽ sửa lỗi cụ thể nào** trong phân tích lỗi của C2 (ví dụ: "C2 abstain đúng nhưng câu từ chối lủng củng", hoặc "C2 không tuân thủ định dạng JSON ở 8% lượt")
4. ✅ Còn nguồn lực sau khi đã hoàn thành toàn bộ DoD phần lõi

**Lý do:** tiêu chí nghiệm thu trung tâm (#2 — tỷ lệ bịa ≈ 0) được quyết định bởi **Intent Router + Grounding Validator + chất lượng KB**, không phải bởi trọng số model. Fine-tuning là thứ đắt nhất (thời gian + GPU) mà đóng góp ít nhất cho đúng con số NextFarm nghiệm thu. Nó vẫn có giá trị — nhưng là giá trị *sau*, không phải *trước*.

### 33.2. Fine-tuning làm gì và không làm gì

| Được dùng để cải thiện | **Không** được dùng để |
|---|---|
| Tuân thủ định dạng đầu ra (JSON có `chunk_ids`) | Nhồi kiến thức nông học vào model |
| Văn phong tiếng Việt phù hợp nông dân | Thay thế RAG |
| Hành vi từ chối tự nhiên, đúng loại | Bù cho KB thiếu |
| Bám evidence chặt hơn | Bù cho retrieval kém |

> **Nguyên tắc giữ nguyên từ v1.0: kiến thức factual vẫn đến từ RAG. Fine-tuning không thay thế RAG.**

### 33.3. Dataset

| Loại | Nguồn | Yêu cầu |
|---|---|---|
| A. Verified knowledge | `verified_facts` + chunk đã duyệt | |
| B. Human-written QA | Viết tay | |
| C. Validated synthetic QA | LLM sinh + **người duyệt từng cặp** | Không duyệt thì không dùng |
| D. Abstention / hallucination cases | Từ chính các case thất bại của C0/C1 | Đây là loại giá trị nhất |

**Vòng lặp phải tránh:**
```
LLM sinh dữ liệu (có hallucination)
        ↓
fine-tune ngay, không duyệt
        ↓
model học chính hallucination đó
        ↓
hallucination được củng cố
```

**Tách train/eval tuyệt đối:** không một case nào của eval set được xuất hiện trong training set, kể cả ở dạng diễn đạt lại. Kiểm tra bằng đối chiếu trùng lặp trước khi train.

### 33.4. Chọn model

```
Danh sách model ứng viên (open-source, hỗ trợ tiếng Việt)
        ↓
Đo VRAM khả dụng thật của GPU (ASM-06 — chưa biết)
        ↓
Lọc model chạy được (inference + QLoRA)
        ↓
Benchmark trên eval set đã đóng băng: chất lượng · latency · chi phí
        ↓
Chọn → LoRA/QLoRA
```

`DEC-015` (model) giữ trạng thái `[TODO]` cho tới bước này. **Không chốt model trên giấy.**

---

# PHẦN VII — TRIỂN KHAI, GIAO HÀNG VÀ VẬN HÀNH

## 34. Cấu trúc thư mục

```
ChatBot-NextFarm/
│
├── app/
│   ├── api/                     # FastAPI endpoints
│   ├── core/                    # config, logging, db
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # pydantic
│   ├── services/
│   │   ├── intent/          ★   # Intent Router (§11) — MỚI
│   │   ├── normalization/       # xử lý tiếng Việt (§13)
│   │   ├── retrieval/           # hybrid (§14) + rerank (§15)
│   │   ├── llm/                 # gọi model, prompt (§17)
│   │   ├── grounding/           # validator 3 tầng (§18)
│   │   ├── citation/            # §20
│   │   └── abstention/          # §19 + template (§11.5)
│   └── main.py
│
├── crawler/
│   ├── sources.yaml             # chỉ URL + metadata
│   ├── crawl.py                 # + PDF (DEC-027) + robots.txt (DEC-028a)
│   ├── extract.py               # luồng 2 — câu chứa số
│   └── data/{raw,text,manifest.json,candidates.json}
│
├── knowledge/
│   ├── ingestion/               # nạp document vào DB
│   ├── review/              ★   # công cụ duyệt (§27) — MỚI
│   ├── chunking/                # §26
│   ├── embedding/               # §26
│   └── lexicon/             ★   # từ điển viết tay, version-controlled — MỚI
│       ├── abbreviations.yaml
│       ├── local_terms.yaml
│       └── high_risk_terms.yaml
│
├── evaluation/
│   ├── datasets/                # eval set + version + sha256 (§28)
│   ├── runners/                 # chạy C0/C1/C2/C3
│   ├── metrics/                 # §30
│   └── reports/                 # báo cáo so sánh
│
├── training/                    # chỉ khi §33.1 đủ điều kiện
│   ├── datasets/ scripts/ configs/
│
├── frontend/
├── tests/
├── docs/
│   └── NEXTFARM_PROBLEM_A_STANDARD_v2.0.md    # tài liệu này
├── docker-compose.yml           # postgres + pgvector + unaccent + pg_trgm
└── README.md
```

Đây là cấu trúc đề xuất, chưa phải trạng thái code hiện tại (**hiện tại repo chưa có code**).

## 35. Lộ trình

**Thay đổi lớn nhất so với v1.0: eval set và baseline được đẩy lên TRƯỚC khi xây RAG** (lý do ở §28).

| Phase | Nội dung | Đầu ra kiểm chứng được |
|---|---|---|
| **P0 — Chuẩn** | Chốt tài liệu này; dựng repo, docker-compose, source registry | Repo chạy được `docker compose up`, Postgres có 3 extension |
| **P1 — Crawl** | `crawl.py` + PDF + robots.txt; mở rộng `sources.yaml` lên 50–80 nguồn; chạy thật | `manifest.json` có số nguồn OK/failed thật. **Biết KB thật có bao nhiêu** |
| **P2 — Duyệt** | Duyệt tài liệu (checklist §27.2) + duyệt fact (§27.3) | `document.approved`, bảng `verified_facts` có dữ liệu thật |
| **P3 — ★ Eval set** | Viết 250–350 case (§29), **đóng băng**, có version + hash | File eval set + hash, không sửa nữa |
| **P4 — ★ Baseline C0** | Chạy LLM trần trên eval set | **Con số quan trọng nhất để trình bày với NextFarm:** LLM trần bịa bao nhiêu % |
| **P5 — Knowledge DB** | Schema, chunking, embedding, pgvector, FTS unaccent+trgm | `indexable_chunk` có dữ liệu, truy vấn được |
| **P6 — Retrieval** | Hybrid + rerank, đo Recall@K, chốt các `[TODO]` tham số | Bảng Recall@K theo cấu hình |
| **P7 — RAG (C1)** | Evidence pack, prompt, đầu ra có cấu trúc, citation | Đo C1 trên eval set |
| **P8 — Guardrail (C2)** | Intent Router, Scope Check, Grounding 3 tầng, abstention, template | Đo C2. **Đây là cấu hình sản phẩm của PoC** |
| **P9 — Báo cáo** | So sánh C0/C1/C2, phân tích lỗi, đường risk–coverage, chốt ngưỡng | **Báo cáo so sánh có số** |
| **P10 — UI/API + demo** | Giao diện chat, hiển thị nguồn, trang trạng thái/log | Demo chạy được, click được về URL nguồn |
| **P11 — Giao hàng** | Trả lời 6 câu hỏi mục 6 (§37), bản kê bảo mật (§38), sổ giả định (§9) | **Tài liệu gửi NextFarm** |
| **P12 — Fine-tuning** | Chỉ khi đủ 4 điều kiện §33.1 | Đo C3, bổ sung vào báo cáo |

**Thứ tự cắt giảm khi thiếu thời gian** (`ASM-09`): P12 → P10 (làm UI tối giản) → thu hẹp P1. **Không bao giờ cắt P3, P4, P9, P11.**

## 36. Definition of Done

### 36.1. Phần lõi — bắt buộc

- [ ] Scope 3 cây hoạt động, câu hỏi cây khác bị từ chối đúng
- [ ] **Intent Router hoạt động, 4 nhánh** ★
- [ ] **`unsafe_misroute_rate` = 0 trên eval set** ★
- [ ] Knowledge pipeline chạy được từ URL tới chunk
- [ ] Crawler đọc được cả HTML và PDF
- [ ] Provenance đầy đủ: mọi chunk truy ngược được về URL
- [ ] **Hai luồng duyệt hoạt động: `document.approved` + `verified_facts`** ★
- [ ] Chunk high-risk được duyệt lẻ
- [ ] PostgreSQL + pgvector + unaccent + pg_trgm hoạt động
- [ ] `indexable_chunk` chặn được chunk chưa duyệt (có test)
- [ ] Hybrid retrieval hoạt động, câu hỏi **không dấu** truy được đúng chunk
- [ ] Reranking được benchmark (bật/tắt có số liệu)
- [ ] RAG trả lời có citation, click về được URL gốc
- [ ] **Grounding Validator 3 tầng hoạt động, có log mọi lần chặn** ★
- [ ] Abstention hoạt động, **đúng loại** (4 template)
- [ ] High-risk handling hoạt động
- [ ] **Eval set 250–350 case, đã đóng băng, có version + hash** ★
- [ ] Baseline C0 được đo
- [ ] C1, C2 được đo
- [ ] **Đường risk–coverage được vẽ, ngưỡng được chọn từ đó** ★
- [ ] Latency p50/p95 được đo **theo từng chặng**
- [ ] **`fabricated_garden_data_count` = 0 và `fabricated_feature_count` = 0** ★
- [ ] Không có claim chưa có nguồn nào được trình bày như fact

### 36.2. Phần giao hàng — bắt buộc (v1.0 thiếu hoàn toàn phần này)

- [ ] **Báo cáo so sánh C0/C1/C2 có bảng số + phân tích lỗi** ★
- [ ] **Bản trả lời 6 câu hỏi mục 6 của đề bài** (§37) ★
- [ ] **Sổ giả định `[ASM]` đính kèm, ghi rõ là giả định của đội** ★
- [ ] **Bản kê luồng dữ liệu và bảo mật** (§38) ★
- [ ] **Danh sách những gì NextFarm cần chuẩn bị** (§37.6) ★
- [ ] Ghi rõ giới hạn đã biết: reviewer không phải chuyên gia nông nghiệp (§27.1), chưa có dữ liệu vườn (ASM-04)

### 36.3. Tuỳ chọn

- [ ] Fine-tuned model được đo (C3), nếu đủ điều kiện §33.1

## 37. Nháp trả lời 6 câu hỏi của NextFarm

> **Lưu ý:** phần này là **nháp để người thực hiện hoàn thiện**, không phải bản gửi đi. Câu 1 và câu 3 **không được điền thay** vì chúng nói về năng lực và ý định hợp tác của chính người thực hiện — điền hộ là bịa.

### 37.1. Câu 1 — kinh nghiệm/giải pháp sẵn có, mạnh nhất ở đâu

`[người thực hiện tự trả lời]` — tài liệu này không điền thay.

Gợi ý cách trả lời trung thực: nêu đúng những gì đã làm được và đo được trong PoC, kèm số liệu từ báo cáo §31, thay vì tuyên bố năng lực chung chung.

### 37.2. Câu 2 — kiến trúc tổng thể

→ **Phần III + Phần IV của tài liệu này**, kèm sơ đồ §10 và §37.2.1 dưới đây cho bức tranh đầy đủ cả hai bài toán:

```
                        Người dùng (Zalo OA / app NextFarm)
                                    │
                                    ▼
                            Chuẩn hoá tiếng Việt
                                    ▼
                            ★ INTENT ROUTER
                    ┌───────────┬───────────┬───────────┐
                    ▼           ▼           ▼           ▼
              agronomy    garden_data  product     device_control
              knowledge        │       feature          │
                    │          │          │             │
                    ▼          ▼          ▼             ▼
              ┌──────────┐  GIAI ĐOẠN 2 (Bài toán B)   GIAI ĐOẠN 2
              │   RAG    │  ┌────────────────────┐    ┌──────────────┐
              │ pgvector │  │ Tool calling →     │    │ Xác nhận +   │
              │ + rerank │  │ IoT Service API    │    │ kiểm quyền + │
              │ + ground │  │ + IAM phân quyền   │    │ IoT API      │
              │   check  │  └────────────────────┘    └──────────────┘
              └──────────┘
                    │
                    ▼
        Trả lời + nguồn  /  Từ chối có giải thích
```

**Điểm cần nhấn với NextFarm:** giai đoạn 1 (Bài toán A) đã dựng sẵn Intent Router, nên giai đoạn 2 chỉ **thay nội dung của hai nhánh**, không phải làm lại kiến trúc.

**Hạ tầng:** FastAPI + PostgreSQL 16 + pgvector; LLM tuỳ phương án ở §37.5; toàn bộ chạy được bằng `docker compose`.

### 37.3. Câu 3 — hình thức hợp tác

`[người thực hiện tự quyết]` — `ASM-10` giả định là **làm PoC**, nhưng đây là quyết định kinh doanh, không phải kỹ thuật.

### 37.4. Câu 4 — ước lượng thời gian và nguồn lực `[ASM]`

> **Toàn bộ con số dưới đây là ước lượng công sức của đội (1 người), không phải cam kết, và chưa tính thời gian chờ phản hồi từ NextFarm.**

Đề bài yêu cầu PoC chứng minh **(a)** bot trả lời đúng số liệu thật của vườn và **(b)** bot không bịa khi không có dữ liệu. Hai vế này thuộc hai bài toán khác nhau:

**Giai đoạn 1 — chứng minh vế (b), không cần gì từ NextFarm**

| Phase | Nội dung | Ngày công ước tính |
|---|---|---|
| P0 | Chuẩn hoá tài liệu, dựng repo, hạ tầng | 2–3 |
| P1 | Crawler (+PDF, robots.txt), mở rộng nguồn, chạy thật | 4–6 |
| P2 | Duyệt tài liệu + duyệt fact | 3–4 |
| P3 | Viết và đóng băng eval set 250–350 case | 4–6 |
| P4 | Đo baseline C0 | 1–2 |
| P5 | Knowledge DB, chunking, embedding, pgvector, FTS | 4–5 |
| P6 | Hybrid retrieval + rerank + đo Recall@K | 4–5 |
| P7 | RAG C1 | 3–4 |
| P8 | Guardrail C2 (Intent Router, Grounding 3 tầng, abstention) | 5–7 |
| P9 | Báo cáo so sánh + phân tích lỗi | 3–4 |
| P10 | UI/API + demo | 4–5 |
| P11 | Tài liệu giao hàng | 2–3 |
| | **Tổng giai đoạn 1** | **≈ 39–54 ngày công** |
| P12 | Fine-tuning (tuỳ chọn) | +5–8 |

**Giai đoạn 2 — chứng minh vế (a), phụ thuộc hoàn toàn vào NextFarm**

| Nội dung | Ngày công ước tính | Điều kiện |
|---|---|---|
| Tầng tool-calling gọi IoT Service API | 4–6 | Cần API + tài liệu API |
| Ánh xạ tài khoản Zalo OA ↔ NextFarm + phân quyền theo vườn | 4–6 | Cần IAM API + quy tắc phân quyền |
| Diễn giải số liệu thô thành câu trả lời hữu ích | 3–4 | Cần dữ liệu mẫu |
| Xử lý dữ liệu thiếu/trễ/cảm biến câm | 2–3 | |
| Eval set cho dữ liệu vườn + đo tiêu chí ≥95% | 4–5 | Cần môi trường thử nghiệm có dữ liệu thật |
| | **≈ 17–24 ngày công** | **Không bắt đầu được nếu thiếu §37.6** |

**Nguồn lực:** 1 người; 1 GPU (VRAM `[TODO]`); 1 máy chủ nhỏ chạy PostgreSQL; chi phí LLM theo §37.5.

### 37.5. Câu 5 — chi phí vận hành hằng tháng

> **Không thể đưa ra con số cuối cùng ở thời điểm này**, vì thiếu hai biến chỉ NextFarm mới có và một biến chỉ đo được sau PoC. Đưa ra con số bịa cho một câu hỏi chi phí là cách nhanh nhất làm hỏng một hợp tác. Thay vào đó, đây là **mô hình chi phí** — điền số vào là ra kết quả.

**Biến đầu vào**

| Biến | Ký hiệu | Nguồn |
|---|---|---|
| Số hội thoại/tháng | `C` | `[EXT]` — NextFarm |
| Số lượt hỏi trung bình mỗi hội thoại | `T` | `[EXT]` — NextFarm |
| Token đầu vào trung bình mỗi lượt (prompt + evidence pack) | `Ti` | **Đo được sau PoC** |
| Token đầu ra trung bình mỗi lượt | `To` | **Đo được sau PoC** |
| Đơn giá token vào/ra | `Pi`, `Po` | Bảng giá công khai của nhà cung cấp **tại thời điểm ước lượng** |

**Phương án A — dùng API bên thứ ba**

```
Chi phí LLM/tháng      = C × T × (Ti × Pi + To × Po)
Chi phí embedding      ≈ một lần cho KB + phần tăng thêm khi cập nhật (nhỏ)
Chi phí rerank         = 0 nếu chạy local, hoặc theo API nếu dùng dịch vụ
Chi phí hạ tầng        = VPS chạy FastAPI + PostgreSQL
────────────────────────────────────────────────
TỔNG A = LLM + embedding + hạ tầng
```
- Tăng tuyến tính theo lượng hội thoại
- Không cần đầu tư ban đầu
- Dữ liệu câu hỏi của nông dân đi ra ngoài → xem §38

**Phương án B — self-host trên GPU**

```
Chi phí cố định = thuê/khấu hao GPU + điện + vận hành
Chi phí biến đổi ≈ 0 theo lượt
────────────────────────────────────────────────
TỔNG B = chi phí cố định (gần như không đổi theo tải)
```
- Có điểm hoà vốn: dưới ngưỡng đó A rẻ hơn, trên ngưỡng đó B rẻ hơn
- **Điểm hoà vốn** `C*` = (chi phí cố định của B) / (chi phí mỗi hội thoại của A)
- Dữ liệu không rời hạ tầng → ưu thế lớn về bảo mật

**Ba mức tải để trình bày** (đề bài yêu cầu "theo các mức tải khác nhau"): thấp / trung bình / cao — nhưng giá trị cụ thể của ba mức phải lấy từ `C` thật của NextFarm.

**Việc phải làm ở PoC để trả lời được câu này:** log `Ti` và `To` cho mọi lượt ngay từ P7, và đưa số đo vào báo cáo P9. Khi đó chỉ cần NextFarm cung cấp `C`, `T` là ra con số thật.

### 37.6. Câu 6 — NextFarm cần chuẩn bị gì

**Nhóm 1 — cần để trả lời được các mục `[EXT]` (không chặn công việc, nhưng chặn việc chốt ngưỡng)**

| # | Cần gì | Dùng để |
|---|---|---|
| 1 | Mô hình LLM và nhà cung cấp đang dùng | So sánh baseline đúng với hiện trạng |
| 2 | Lượng hội thoại/tháng và số lượt trung bình | Tính chi phí §37.5 |
| 3 | Chi phí API hiện tại | So sánh phương án A/B |
| 4 | Ngưỡng latency chấp nhận được | Thay `ASM-01` |
| 5 | Ngưỡng chuyên gia chấm đạt | Thay `ASM-02` |
| 6 | Yêu cầu về privacy / thời gian lưu dữ liệu | §38 |

**Nhóm 2 — cần cho Bài toán A (giai đoạn 1), giúp chất lượng tốt hơn hẳn**

| # | Cần gì | Dùng để |
|---|---|---|
| 7 | **Log hội thoại thật đã ẩn danh** (dù chỉ vài trăm lượt) | **Giá trị cao nhất trong danh sách này.** Cho biết nông dân thật hỏi gì, viết tắt thế nào, dùng từ địa phương nào → eval set sát thực tế thay vì do đội tự tưởng tượng |
| 8 | Tài liệu hướng dẫn sử dụng app NextFarm | Gỡ `ASM-03`, nhánh `product_feature` chuyển từ abstain sang trả lời được |
| 9 | Danh sách nguồn tài liệu nông học NextFarm tin dùng | Ưu tiên Tier 1 đúng ý khách hàng |
| 10 | Một người của NextFarm có kiến thức nông nghiệp rà lại KB | Gỡ giới hạn ở §27.1 (reviewer không phải chuyên gia) |
| 11 | Danh sách cây trồng khách hàng NextFarm trồng nhiều nhất | Xác nhận 3 cây đã chọn có đúng trọng tâm không |

**Nhóm 3 — cần cho Bài toán B (giai đoạn 2), **chặn cứng** nếu thiếu**

| # | Cần gì | Không có thì sao |
|---|---|---|
| 12 | Tài liệu API IoT Service (đọc cảm biến, trạng thái thiết bị, lịch tưới, lịch sử, cảnh báo) | **Không bắt đầu được** |
| 13 | Tài liệu API IAM Service + mô hình phân quyền theo vườn | **Không bắt đầu được** — liên quan tiêu chí nghiệm thu #5 |
| 14 | Môi trường thử nghiệm (staging) có dữ liệu mẫu thật | **Không đo được** tiêu chí ≥95% |
| 15 | Tài khoản thử nghiệm + ít nhất 1 vườn mẫu có lịch sử đủ dài | Không có case test thật |
| 16 | Cách ánh xạ tài khoản Zalo OA ↔ tài khoản NextFarm | Không xác định được "vườn của tôi" |
| 17 | Danh sách quy tắc an toàn tầng firmware phải tôn trọng | Rủi ro vi phạm ràng buộc an toàn của đề bài |

## 38. Bảo mật và luồng dữ liệu `[REQ]`

Đề bài yêu cầu làm rõ: dữ liệu nào gửi ra ngoài, gửi cho nhà cung cấp nào, lưu ở đâu, bao lâu.

### 38.1. Bản kê luồng dữ liệu của PoC giai đoạn 1

| Dữ liệu | Có rời hạ tầng không | Đi đâu | Ghi chú |
|---|---|---|---|
| Câu hỏi của người dùng | **Có**, nếu dùng LLM API bên thứ ba | Nhà cung cấp LLM | Đây là điểm cần NextFarm quyết định |
| Evidence Pack (trích từ tài liệu công khai) | Như trên | Như trên | Nội dung vốn đã công khai trên web |
| **Dữ liệu vườn / cảm biến** | **KHÔNG** | — | PoC giai đoạn 1 **không truy cập dữ liệu vườn nào** |
| **Thông tin định danh khách hàng** | **KHÔNG** | — | Không thu thập |
| Log hội thoại | Không | PostgreSQL nội bộ | Thời hạn lưu: `[EXT]` |

### 38.2. Quy tắc bắt buộc

- Không gửi dữ liệu vườn hoặc thông tin định danh ra bất kỳ API ngoài nào — trong PoC giai đoạn 1 điều này **đúng theo nghĩa tuyệt đối** vì hệ thống không có dữ liệu đó
- Nếu chọn phương án B (self-host), **không có dữ liệu nào rời hạ tầng** — đây là luận điểm bán hàng mạnh cho §37.5
- Log phải ghi đủ để audit nhưng **không ghi thông tin định danh** khi mở rộng sang giai đoạn 2
- Thời hạn lưu log: `[EXT]` — chờ chính sách của NextFarm

## 39. Rủi ro và biện pháp

| ID | Rủi ro | Hậu quả | Biện pháp |
|---|---|---|---|
| R1 | Crawl được ít nguồn (trang chặn, đổi cấu trúc, PDF khó đọc) | KB nhỏ → bot abstain nhiều | Mở rộng `sources.yaml`; chấp nhận và **ghi rõ giới hạn** thay vì bù bằng dữ liệu tay |
| R2 | KB kém chất lượng | RAG vẫn trả lời sai (grounded hallucination) | Source policy + checklist duyệt + cấm Tier 3 |
| R3 | Retrieval trượt | LLM nhận evidence sai | Hybrid + rerank + đo Recall@K trước khi làm RAG |
| R4 | LLM bịa dù có evidence | Bịa có citation — nguy hiểm nhất | Grounding Validator 3 tầng, đặc biệt tầng 2 |
| R5 | **Intent Router nhầm `garden_data` thành `agronomy_knowledge`** | **Tái tạo đúng lỗi A1 mà đề bài yêu cầu diệt** | Thiên lệch an toàn (§11.4) + `unsafe_misroute_rate` = 0 là điều kiện DoD |
| R6 | Eval set bị nhiễm hallucination (LLM tự sinh cả câu hỏi lẫn đáp án) | Mọi số đo vô nghĩa | Ground truth từ `verified_facts` do người duyệt (§29.1) |
| R7 | Metric bị gian lận (abstain hết) | Báo cáo đẹp nhưng sản phẩm vô dụng | Metric đi theo cặp (§30.2) |
| R8 | Vượt ngân sách latency | Vi phạm ràng buộc đề bài | Đo theo chặng + thứ tự cắt đã định sẵn (§21.3) |
| R9 | Fine-tuning ngốn hết thời gian còn lại | Không kịp làm báo cáo và tài liệu giao hàng | Fine-tuning có điều kiện, ngoài đường găng (§33.1) |
| R10 | Khối lượng duyệt vượt sức 1 người | Dự án tắc ở P2 | Ngân sách ≤10 giờ (§27.4); luồng 2 chia nhỏ được |
| R11 | Scope creep sang Bài toán B | PoC không xong | Khoá 3 cây + IoT phase sau; Intent Router từ chối rõ ràng |
| R12 | Nhầm lẫn giữa giả định của đội và yêu cầu của NextFarm | Mất uy tín trong hợp tác thật | Sổ `[ASM]` §9 đính kèm mọi báo cáo |
| R13 | Rủi ro pháp lý/uy tín khi crawl | Ảnh hưởng hợp tác | robots.txt + rate limit + ghi nguồn (DEC-028) |

## 40. Câu hỏi còn mở

### 40.1. `[EXT]` — chỉ NextFarm trả lời được. Không đoán.

1. Mô hình LLM và nhà cung cấp hiện tại?
2. Lượng hội thoại/tháng? Số lượt trung bình mỗi hội thoại?
3. Chi phí API hiện tại?
4. Ngưỡng latency chấp nhận được? (đề bài mục 7.4)
5. Ngưỡng chuyên gia chấm đạt? (đề bài mục 7.3)
6. Có log hội thoại thật (ẩn danh) chia sẻ được không?
7. Có tài liệu hướng dẫn sử dụng app không?
8. Có nguồn tài liệu nông học nào bắt buộc ưu tiên không?
9. Có chuyên gia nông nghiệp rà KB được không?
10. Yêu cầu privacy / thời hạn lưu dữ liệu?
11. Yêu cầu triển khai cụ thể (on-premise / cloud / khu vực đặt máy chủ)?
12. Ba cây lúa/cà chua/dưa chuột có đúng trọng tâm khách hàng không?

### 40.2. `[TODO]` — đội tự chốt, **sau khi có số đo**. Không chốt trên giấy.

1. Embedding model
2. Reranker model
3. LLM (DEC-015)
4. Kích thước chunk + overlap
5. Top-K mỗi kênh retrieval
6. Trọng số hợp nhất RRF
7. Số chunk vào Evidence Pack
8. Ngưỡng tự tin để abstain (chọn từ đường risk–coverage §30.4)
9. Ngưỡng tin cậy của Intent Router (§11.4)
10. Tỷ lệ nội dung bị loại tối đa trước khi abstain toàn bộ (§18.4)
11. Trọng số của `source_score` (§22.2)
12. VRAM khả dụng thật của GPU (ASM-06)

### 40.3. `[ASM]` — đã giả định, chờ NextFarm xác nhận

→ Toàn bộ §9.

## 41. Cam kết cuối

### Chúng ta đang xây

> Một **chatbot tư vấn nông nghiệp tiếng Việt** cho lúa, cà chua và dưa chuột, dùng knowledge base có provenance và human verification, RAG hybrid + reranking, evidence grounding 3 tầng, citation truy ngược được, và **một Intent Router biết phân biệt câu hỏi kiến thức với câu hỏi số liệu vườn / tính năng app / lệnh điều khiển — để từ chối đúng chỗ thay vì bịa**. Toàn bộ được chứng minh bằng một eval set đã đóng băng và một báo cáo so sánh có số.

### Sáu nguyên tắc

1. **LLM không phải nguồn sự thật.** Không đủ evidence → không được tự tin trả lời factual.
2. **Dữ liệu web thô không phải ground truth.** Phải qua người duyệt mới được index.
3. **Fine-tuning không thay thế RAG.** Kiến thức ở KB, hành vi ở model.
4. **Không đánh giá bằng vài câu demo.** Phải có eval set đóng băng và số liệu so sánh.
5. **Thông tin chưa được cung cấp phải để `[EXT]`, không được bịa.** Khi buộc phải có con số để làm việc thì dùng `[ASM]` và nói rõ đó là giả định của đội.
6. **★ Không biết là gì thì phải nói rõ là không biết gì.** Bot không chỉ cần biết từ chối — nó phải từ chối **đúng lý do**: không có dữ liệu vườn, không có tài liệu sản phẩm, ngoài phạm vi cây trồng, hay không đủ căn cứ. Bốn lý do này khác nhau, và người dùng cần biết là lý do nào.

### Xương sống

```
Crawl → Duyệt → Lưu → Định tuyến ý định → Truy xuất
      → Kiểm chứng grounding → Trả lời có nguồn / Từ chối đúng lý do
      → Đo
```

---

**Status: ACTIVE STANDARD v2.0**
**Thay thế: TECHNICAL_SPEC v1.0 · Hợp nhất: CRAWLER_GUIDE.md, ChatBot-NextFarm-SPEC.md**
**Không thay thế: `De-bai-Chatbot-NextFarm.pdf` — luôn là cấp cao nhất**
