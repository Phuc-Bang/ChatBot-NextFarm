# P6 — Đo truy xuất và chốt model embedding

> **Ngày đo:** 2026-08-20 · **Tập kiểm thử:** v3 (đã đóng băng) · **Kho tri thức:** 161 chunk index được
> Lệnh tái lập: `python evaluation/runners/eval_retrieval.py --models halong e5-small --hybrid halong e5-small`

---

## 1. Ground truth đến từ đâu

22 case của tập kiểm thử v3 có trường `source_of_truth` trỏ về một **fact đã được người duyệt**. Fact đó biết nó trích từ câu nào của tài liệu nào, nên suy ra được **chunk nào là chunk đúng**.

Đây chính là lý do §24.5 của quy chuẩn bắt duyệt số liệu **trước** khi đo truy xuất: không có fact đã duyệt thì không có ground truth, và không có ground truth thì mọi con số Recall đều là tự chấm điểm cho mình.

### Nhưng chỉ 15/22 case đo được — và 7 case còn lại không phải lỗi

| | Số case |
|---|---|
| Đo được | **15** |
| Không đo được — chunk nguồn **bị chặn** | **7** |
| Không đối chiếu được | 0 |

7 case kia có chunk nguồn mang cờ `is_high_risk = true, approved = false` — nội dung liều lượng phân bón, thuốc BVTV. **DEC-005 chặn chúng khỏi kho truy xuất** cho tới khi có người duyệt lẻ từng chunk.

Nghĩa là **không hệ thống truy xuất nào tìm ra được** những chunk đó. Đó là hành vi **đúng theo thiết kế**, không phải lỗi retrieval. Gộp chúng vào ground truth sẽ kéo Recall xuống và đổ lỗi nhầm cho model, trong khi nguyên nhân thật là *"chưa duyệt xong"*.

> Duyệt 44 chunk rủi ro cao sẽ mở lại 7 case này — và đó là việc chỉ người duyệt làm được.

---

## 2. Kết quả

```
RECALL@K  |  15 case có ground truth  |  161 chunk

model              chiều     R@1     R@3     R@5    R@10     MRR   hỏi(ms)
──────────────────────────────────────────────────────────────────────────
hybrid(halong)       768    60.0    73.3    73.3    80.0   0.687        97
keyword                0    46.7    60.0    73.3    80.0   0.576        93
hybrid(e5-small)     384    40.0    66.7    66.7    73.3   0.559        83
halong               768    13.3    80.0    80.0    86.7   0.432         3
e5-small             384    20.0    60.0    73.3    80.0   0.388         1
```

---

## 3. Đọc bảng này thế nào

### a) Vector một mình **kém nhất** về MRR — nhưng vẫn phải giữ

`halong` đứng cuối bảng MRR (0.432) và R@1 chỉ 13,3%. Nếu chỉ nhìn hai cột đó thì kết luận là "bỏ vector đi".

Nhưng nhìn **R@3 = 80%** — cao nhất bảng, hơn cả hybrid. Vector tìm đúng chunk, chỉ **xếp nó sai vị trí**. Đó đúng là thứ RRF sinh ra để chữa: hợp nhất với kênh từ khoá thì R@1 nhảy từ **13,3% → 60%**.

### b) Hai kênh **bù nhau**, không thay thế nhau

| | Từ khoá | Vector |
|---|---|---|
| Mạnh | xếp hạng chính xác (MRR 0.576) | tìm được chunk đúng (R@3 80%) |
| Yếu | bỏ sót (R@3 chỉ 60%) | xếp hạng kém (R@1 13%) |

Từ khoá khớp mặt chữ nên khi trúng thì trúng chính xác, nhưng câu hỏi diễn đạt khác từ trong tài liệu là trượt. Vector hiểu nghĩa nên bắt được câu diễn đạt khác, nhưng không phân biệt được chunk nào *chính xác hơn*.

**Hợp nhất được cả hai:** MRR 0.687 — cao hơn kênh từ khoá 19% tương đối.

### c) `halong` thắng `e5-small`, đúng như VN-MTEB dự đoán

Hybrid: 0.687 vs 0.559. Khoảng cách 23% tương đối — lớn hơn nhiều so với chênh lệch 0,94 điểm trên VN-MTEB. Trên kho nông nghiệp tiếng Việt cụ thể này, `halong` tốt hơn rõ rệt.

Giá phải trả: model lớn hơn 2,4 lần (278M vs 118M), embed cả kho mất 6,8s thay vì 1,3s. Không đáng kể vì **embed kho là việc chạy một lần**.

### d) Latency vẫn thoải mái trong ngân sách

`hỏi(ms) = 97ms` cho toàn bộ hybrid, trong đó embed câu hỏi chỉ **3ms**. Ngân sách ASM-01 là p50 ≤ 5000ms cho cả chuỗi. Truy xuất chiếm **~2%**.

---

## 4. Chốt lại (DEC-015, phần embedding)

```
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=halong          # contextboxai/halong_embedding, 278M, 768 chiều
```

Chạy **local**, không gọi API. Ba lý do:

1. **Bảo mật (§38).** Embedding phải chạy qua toàn bộ kho tri thức và mọi câu hỏi người dùng. Chạy local thì cả hai **không rời hạ tầng**.
2. **Không tốn quota.** Để dành free tier cho khâu thật sự phải gọi API.
3. **Nhanh.** 3ms mỗi câu hỏi trên CPU.

---

## 5. Giới hạn của phép đo này — đọc kỹ trước khi trích dẫn

- **15 case là ít.** Một case đổi kết quả là ±6,7 điểm phần trăm. Con số này đủ để **chọn giữa hai model**, chưa đủ để báo cáo với NextFarm như chỉ số chất lượng hệ thống.
- **Người viết câu hỏi và người xây hệ thống là một.** Câu hỏi trong `known_answer` sinh từ chính bảng fact nên dùng từ ngữ gần tài liệu. Câu hỏi thật của nông dân sẽ khó hơn.
- **`bge-m3` chưa đo được.** Cần 2,3 GB tải về, ổ C: chỉ còn 6,4 GB (đầy 97%). Đây là ứng viên còn bỏ ngỏ — nó có cả dense lẫn sparse trong một model, về lý thuyết hợp với bài toán này.
- **Chưa đo reranker.** `RERANKER_MODEL` vẫn để trống.
- **Chưa chốt các `[TODO]` khác:** `TOP_K_MOI_KENH=20`, `K_RRF=60`, `NGUONG_TRIGRAM=0.3` vẫn là giá trị mặc định, chưa quét tham số.

## 6. Việc mở khoá thêm số đo

| Việc | Mở ra gì |
|---|---|
| Duyệt 44 chunk rủi ro cao | 7 case đang bị chặn → 22 case đo được |
| Duyệt tiếp 76 câu ứng viên | Thêm fact → thêm case `known_answer` |
| Dọn ổ C: lấy ~3 GB | Đo được `bge-m3` |

---

## Đo lại ngày 2026-08-20 — sau khi kho tri thức được cắt lại

Số ở các mục trên đo trên kho **161 chunk / 15 case**. Kho hiện tại có
**292 chunk (185 index được) / 22 case** có `source_of_truth`. Cùng một
đoạn mã, cùng một model, nhưng đầu vào đã khác — nên phải ghi lại số mới
thay vì để số cũ đứng tên cho một cấu hình không còn tồn tại.

| model | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|
| hybrid(halong) | 45.5 | 59.1 | 68.2 | 81.8 | **0.572** |
| keyword | 31.8 | 50.0 | 59.1 | 68.2 | 0.451 |
| halong (vector đơn) | 13.6 | 45.5 | 63.6 | 86.4 | 0.351 |

**Kết luận chọn model không đổi.** Thứ hạng giữ nguyên, và hiện tượng đã
mô tả ở DEC-015 vẫn đúng: vector đơn *tìm đúng, xếp sai* — R@10 cao nhất
(86.4%) nhưng R@1 thấp nhất (13.6%); hợp nhất RRF đưa R@1 từ 13.6% lên
45.5%. Cái đổi là **con số tuyệt đối**: MRR hybrid 0.687 → 0.572.

Không được dùng lẫn hai bảng. Bảng cũ đo trên kho cũ.

### Một sai lệch của phép đo, không phải của sản phẩm

`eval_retrieval.py` gọi `tim_kiem()` **không truyền `crop`**, trong khi
`app/services/pipeline.py:142` — đường chạy thật — **có truyền**. Nghĩa là
bảng trên đang đo một cấu hình *kém hơn sản phẩm thật*.

Đo hai chiều trên cùng 22 case, cùng hybrid(halong):

| | R@1 | R@3 | R@5 | MRR |
|---|---:|---:|---:|---:|
| không lọc crop (như eval đang chạy) | 40.9 | 54.5 | 68.2 | 0.521 |
| có lọc crop (như pipeline thật) | 36.4 | **59.1** | **72.7** | **0.531** |

Lọc `crop` nâng R@3 và R@5 khoảng 4,5 điểm nhưng **hạ R@1**. Đây không phải
bản sửa cho các case trượt — ghi lại đúng như đo được, không tô thêm.

### Vì sao `ka_015` trượt — chẩn đoán cũ đã SAI

Báo cáo trước ghi *"chunk có trong kho mà truy xuất xếp hạng kém"*. Sai.
Kiểm lại thì `source_of_truth` của `ka_015` là
`lua__cham_soc_lua_xuan_o_mien#14`, mà tài liệu đó chỉ có **12 chunk**.

Nguyên nhân: `source_of_truth` **không phải `chunk_id`**. Nó là
`source_id#sentence_index` — số thứ tự câu trong `crawler/data/candidates.json`.
Hai không gian định danh trùng nhau về hình dạng (`tên_tài_liệu#số`) nên
không ai nhận ra. Toàn bộ **22/22** case đều "trỏ tới chunk không tồn tại"
nếu đem so trực tiếp.

`eval_retrieval.py` **không** so định danh — nó tra `fact` theo
`(document_id, sentence_index)` rồi đối chiếu **bằng nội dung câu** để tìm
chunk chứa câu đó. Vì vậy phép đo Recall vẫn đúng, và dựng được ground
truth cho **22/22** case. Nhưng bất kỳ đoạn mã nào sau này đem
`source_of_truth` so thẳng với `chunk_id` sẽ nhận 0 và **im lặng**.

> **Không đổi tên trường trong tập kiểm thử đã đóng băng** (DEC-023). Chỗ
> cần sửa là tài liệu và bất kỳ chỗ nào hiểu nhầm nó, không phải dữ liệu.

### 10/22 case chưa vào được top-3

`ka_002 ka_003 ka_004 ka_012 ka_013 ka_015 ka_016 pa_002 pa_005 pa_006`

Bốn trong số đó (`ka_015 ka_016 pa_006` hỏi **lúa**, `ka_012` hỏi **dưa
chuột**) nhận top-1 là chunk của **cây khác**. Lọc `crop` xử lý được một
phần, nhưng như bảng trên cho thấy, không xử lý hết. `[TODO]` còn mở.

---

## Chốt tham số bằng quét 72 tổ hợp — 2026-08-20

Ba `[TODO]` của §14.6 (`TOP_K_MOI_KENH`, `K_RRF`, `NGUONG_TRIGRAM`) trước nay
là giá trị mặc định "để chạy được". Nay chốt bằng số: quét đủ
4 × 3 × 3 × 2 = **72 tổ hợp** trên 22 case có ground truth, kho 185 chunk.

### Ảnh hưởng riêng của từng tham số

Giữ ba tham số kia cố định, đổi một tham số:

**`TOP_K_MOI_KENH` — có ảnh hưởng, bão hoà từ 20**

| giá trị | R@1 | R@3 | R@5 | MRR |
|---:|---:|---:|---:|---:|
| 10 | 31.8 | 50.0 | 68.2 | 0.468 |
| **20** | 40.9 | 59.1 | 72.7 | **0.562** |
| 30 | 40.9 | 59.1 | 72.7 | 0.561 |
| 50 | 40.9 | 59.1 | 72.7 | 0.561 |

Từ 20 trở lên không được gì thêm, chỉ tốn thời gian. **Chốt 20.**

**`NGUONG_TRIGRAM` — ảnh hưởng mạnh, ngưỡng càng chặt càng tệ**

| giá trị | R@1 | R@3 | R@5 | MRR |
|---:|---:|---:|---:|---:|
| **0.2** | 40.9 | 59.1 | 72.7 | **0.562** |
| 0.3 (cũ) | 36.4 | 59.1 | 72.7 | 0.531 |
| 0.4 | 31.8 | 59.1 | 68.2 | 0.492 |

Ngưỡng `word_similarity` cao loại mất chunk đúng. **Đổi 0.3 → 0.2.**

**`K_RRF` — gần như không ảnh hưởng**

| giá trị | MRR |
|---:|---:|
| 10 | 0.559 |
| 30 | 0.561 |
| 60 | 0.562 |

Chênh 0.003 trên 22 case là nhiễu, không phải tín hiệu. **Giữ 60** (hằng số
RRF thông dụng) — đổi sang giá trị khác chỉ để "có tối ưu" là tự lừa mình.

**Lọc `crop` — có ảnh hưởng rõ**

| | R@1 | R@3 | R@5 | MRR |
|---|---:|---:|---:|---:|
| có lọc | 40.9 | 59.1 | 72.7 | **0.562** |
| không lọc | 40.9 | 54.5 | 68.2 | 0.521 |

Chủ yếu nhờ chặn chunk của cây khác — trước đó câu hỏi về **lúa** nhận top-1
là chunk **dưa chuột**.

> Kết quả này **lật lại** nhận định ở mục trước ("lọc crop nâng R@3/R@5 nhưng
> hạ R@1"). Lần đo đó chạy với `NGUONG_TRIGRAM=0.3`; ở ngưỡng 0.2 thì lọc
> crop tốt hơn ở **mọi** chỉ số. Hai tham số tương tác với nhau, nên đo từng
> cái một mà giữ cái kia ở giá trị cũ sẽ ra kết luận sai.

### Một lỗi của phép đo phải nói ra

**Lần quét đầu tiên cho kết quả sai và tôi suýt ghi nó vào báo cáo.** 72 dòng
đó cho thấy `K_RRF` và `NGUONG_TRIGRAM` **không ảnh hưởng gì** — mọi giá trị
đều ra MRR y hệt.

Nguyên nhân: cả hai được dùng làm **giá trị mặc định của tham số hàm**:

```python
def tim_trigram(cau, crop=None, top_k=TOP_K_MOI_KENH,
                nguong=NGUONG_TRIGRAM, conn=None): ...
```

Python cố định giá trị mặc định **lúc định nghĩa hàm**, nên gán
`KW.NGUONG_TRIGRAM = 0.2` ở thời điểm chạy không có tác dụng gì. Bản quét sửa
lại gọi thẳng từng kênh và truyền tham số tường minh.

Dấu hiệu nhận ra: **một tham số không đổi kết quả một chút nào** thường là lỗi
đo, không phải phát hiện.

### Chi phí đo — một chi tiết hạ tầng đáng ghi

Bản quét đầu chạy mãi không xong. Nguyên nhân đo được: mỗi lần mở kết nối
Postgres qua Docker Desktop trên Windows tốn **~3,2 giây** (140,6s cho 44
truy vấn). Với 3 kênh × 22 case × 72 tổ hợp = **4.752 lần mở kết nối** thì
không bao giờ chạy xong.

Dùng chung **một** kết nối cho cả lần quét: **340 giây** cho toàn bộ 72 tổ hợp.

Chi tiết này không ảnh hưởng tới sản phẩm (`pipeline.py` mở một kết nối mỗi
lượt hỏi, không phải mỗi kênh), nhưng ảnh hưởng tới **mọi công cụ đo** — ghi
lại để lần sau không mất buổi.

### Bảng chính thức sau khi chốt tham số

`TOP_K_MOI_KENH=20 · K_RRF=60 · NGUONG_TRIGRAM=0.2 · có lọc crop`

| model | chiều | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| **hybrid(halong)** | 768 | **50.0** | **59.1** | **77.3** | **95.5** | **0.620** |
| keyword | — | 36.4 | 50.0 | 68.2 | 86.4 | 0.500 |
| halong (vector đơn) | 768 | 13.6 | 45.5 | 63.6 | 86.4 | 0.351 |

So với trước khi chốt tham số (MRR 0.572 → **0.620**, R@10 81.8 → **95.5**).

**R@10 = 95.5%** — hầu như mọi câu hỏi đều tìm được chunk đúng trong 10 kết
quả đầu. Phần còn thiếu là **xếp hạng**, không phải tìm kiếm: R@1 mới 50%.
Đó chính là chỗ một reranker sẽ có tác dụng, và cũng là `[TODO]` còn lại.

Kết luận chọn model **vẫn không đổi** qua cả ba lần đo: hybrid > keyword >
vector đơn, và vector đơn *tìm đúng, xếp sai*.

### Case còn trượt top-3: 10 → 9

Sau khi chốt tham số, số case không vào được top-3 giảm từ 10 xuống 9. Nhưng
thay đổi đáng kể hơn con số đó là **lỗi "lạc cây" đã hết**:

| case | trước (top-1) | sau (top-1) |
|---|---|---|
| `ka_015` (hỏi lúa) | `hatinh_dua_chuot_vietgap#16` | `lua__khac_phuc_anh_huong_mua_bao#3` |
| `pa_006` (hỏi lúa) | `hatinh_dua_chuot_vietgap#16` | `lua__khac_phuc_anh_huong_mua_bao#3` |
| `ka_012` (hỏi dưa chuột) | `lua__ky_thuat_bon_phan_cho_lua#4` | `hatinh_dua_chuot_vietgap#13` |

Chín case còn lại đều lấy **đúng tài liệu, đúng cây**, chỉ xếp sai thứ hạng
(hạng 4–10). Một case duy nhất — `ka_013` — vẫn không tìm ra trong top-10.

Đây là bằng chứng cho nhận định ở trên: **vấn đề còn lại là xếp hạng, không
phải tìm kiếm.**

### Còn lại

- **Reranker chưa thử.** `RERANKER_MODEL` để trống. Với R@10 95.5% mà R@1
  50%, đây là hạng mục có tiềm năng cao nhất.
- Số chunk vào Evidence Pack (`top_k=5` ở `pipeline.py`) chưa quét riêng.
