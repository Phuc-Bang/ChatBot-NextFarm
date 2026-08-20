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
