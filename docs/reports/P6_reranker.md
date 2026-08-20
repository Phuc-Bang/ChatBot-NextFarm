# Reranker — đo được, và là một đánh đổi thật

> Đo 2026-08-20 · 22 case có ground truth · kho 185 chunk
> Mã: [`app/services/retrieval/rerank.py`](../../app/services/retrieval/rerank.py)
> Công cụ: `python evaluation/runners/eval_rerank.py`

## Vì sao thử reranker

Bảng Recall ở [P6_retrieval_tuning.md](P6_retrieval_tuning.md) cho một dấu
hiệu rất rõ:

```
R@10 = 95,5%     hầu như MỌI câu đều tìm được chunk đúng trong top-10
R@1  = 50,0%     nhưng một nửa bị xếp sai hạng
```

Vấn đề còn lại là **xếp hạng**, không phải **tìm kiếm**. Đó đúng là việc của
cross-encoder: bi-encoder (embedding) mã hoá câu hỏi và chunk *riêng* rồi so
vector; cross-encoder đọc *cả hai cùng lúc* nên bắt được quan hệ mà phép so
vector bỏ qua.

## Chọn model: PhoRanker

| model | dung lượng | ngôn ngữ |
|---|---:|---|
| **`itdainb/PhoRanker`** | **540 MB** | **tiếng Việt** |
| `BAAI/bge-reranker-base` | 2.224 MB | đa ngữ |
| `BAAI/bge-reranker-v2-m3` | 2.271 MB | đa ngữ |
| `namdp-ptit/ViRanker` | 2.271 MB | tiếng Việt |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | 296 MB | chỉ tiếng Anh |

PhoRanker là model tiếng Việt **nhỏ nhất**. Dung lượng là ràng buộc thật ở
đây — xem [`app/__init__.py`](../../app/__init__.py) về chuyện ổ đĩa.

## Kết quả

| | TẮT | BẬT | chênh |
|---|---:|---:|---:|
| R@1 | 40,9 | **45,5** | +4,5 |
| R@3 | 59,1 | **72,7** | **+13,6** |
| R@5 | 72,7 | **90,9** | **+18,2** |
| MRR | 0,562 | **0,605** | +0,043 |
| chi phí | 0 ms | **4.208 ms** | **+4.208 ms** |

Chất lượng tăng thật và tăng nhiều — **R@5 từ 72,7% lên 90,9%**.

**Nhưng 4,2 giây mỗi lượt.** Ngân sách `ASM-01` là p50 ≤ 5.000 ms cho *toàn
bộ* lượt hỏi, mà riêng reranker đã ăn 4,2 giây, chưa kể truy xuất (~220 ms)
và gọi model (~2.600 ms).

Nguyên nhân: cross-encoder chạy **CPU**. GPU 4 GB của máy này đã bị model
embedding chiếm; nạp thêm cross-encoder lên cùng GPU thì vỡ với
`CUDA error: device-side assert triggered`.

## Chốt `top_k_rerank = 12` bằng số đo

Đưa cho reranker bao nhiêu chunk? Quét N trên cùng 22 case:

| N | R@1 | R@3 | R@5 | MRR | ms/câu |
|---:|---:|---:|---:|---:|---:|
| TẮT | 40,9 | 59,1 | 72,7 | 0,562 | 0 |
| 3 | 31,8 | 59,1 | 59,1 | **0,455** | 1.011 |
| 5 | 31,8 | 63,6 | 72,7 | **0,477** | 1.105 |
| 8 | 40,9 | 68,2 | 86,4 | 0,575 | 1.630 |
| **12** | **45,5** | **72,7** | **90,9** | **0,605** | **2.362** |
| 20 | 45,5 | 72,7 | 90,9 | 0,605 | 3.915 |

Hai điều đọc được:

**N nhỏ làm TỆ ĐI, không phải "ít cải thiện hơn".** N=3 cho MRR 0,455 và
N=5 cho 0,477 — đều **thấp hơn** khi tắt hẳn (0,562). Lý do: rerank ít chunk
thì đổi thứ tự mà **không đổi tập hợp**, trong khi chunk đúng thường nằm
ngoài top-k (R@1 50% nhưng R@10 95,5%). Reranker khi đó chỉ xáo lại một tập
đã thiếu chunk đúng.

**N=12 cho đúng chất lượng của N=20 với 60% thời gian** (2.362 ms so với
3.915 ms). Chốt 12.

> Con số ms dao động theo tải máy — lần đo trước cho N=20 là 4.208 ms, lần
> này 3.915 ms. Thứ hạng và các chỉ số chất lượng thì ổn định. Đọc bảng này
> theo **xu hướng**, đừng đọc theo mili-giây tuyệt đối.

Với N=12, tổng một lượt hỏi ước tính: 220 ms truy xuất + 2.362 ms rerank +
~2.600 ms gọi model ≈ **5,2 giây** — vẫn nhỉnh hơn `ASM-01` (p50 ≤ 5s) nhưng
sát ngưỡng, khác hẳn 7 giây của N=20.

## Ba lỗi đã va phải, lỗi thứ ba đáng ngại nhất

**1. `max_length=512`** — PhoRanker khai `max_position_embeddings = 258`
trong `config.json`. Đặt 512 thì vỡ: `index 258 is out of bounds for
dimension 1 with size 258`. Đổi thành 256.

**2. Chạy GPU** — như trên. Ép CPU, ghi đè được bằng `RERANKER_DEVICE`.

**3. Lỗi bị nuốt và hiện ra như một kết luận** — `xep_lai()` nuốt mọi lỗi và
lui về thứ tự cũ. Đó là thiết kế đúng: reranker hỏng **không được** làm sập
câu trả lời.

Nhưng hệ quả: reranker lỗi ở **cả 22 case**, mỗi lần lui về thứ tự cũ, và
bảng kết quả in ra:

```
Chenh lech: R@1 +0.0  R@3 +0.0  R@5 +0.0  MRR +0.000
```

Con số đó trông **y hệt một kết luận** ("reranker không giúp gì") chứ không
trông như một lỗi. Suýt nữa nó vào báo cáo.

> Đã thêm bộ đếm `so_lan_loi()`, và `eval_rerank.py` in cảnh báo to khi nó
> lớn hơn 0, nói thẳng rằng bảng số **không** đo được reranker. Có test riêng
> cho việc **đếm** lỗi chứ không chỉ nuốt lỗi.
>
> Bài học: một cơ chế phòng vệ tốt (nuốt lỗi để không sập) có thể biến lỗi
> thành **dữ liệu trông hợp lý**. Nuốt lỗi thì phải đếm.

## Khuyến nghị

**Mặc định TẮT** (`RERANKER_MODEL` để trống). Với `top_k_rerank=12` thì tổng
một lượt ước tính ~5,2 giây — vẫn nhỉnh hơn `ASM-01` (p50 ≤ 5s), dù sát
ngưỡng. Và `ASM-01` là `[ASM]` — giả định của đội, chưa được NextFarm xác
nhận.

Bật khi có một trong hai:

1. **NextFarm nới ngưỡng độ trễ.** Chỉ cần chấp nhận ~5,5 giây thay vì 5 —
   R@5 từ 72,7% lên 90,9% là cải thiện lớn cho một khoảng nới rất nhỏ.
2. **Có GPU đủ lớn.** Cross-encoder trên GPU nhanh hơn CPU nhiều lần. Đây là
   một lý do cụ thể để NextFarm cân nhắc đầu tư GPU, và khác với lý do
   "self-host model sinh" đã bị bác ở §37.5.

Bật bằng một dòng, không phải sửa mã:

```
RERANKER_MODEL=itdainb/PhoRanker
```

---

## Cập nhật 2026-08-21 — BẬT reranker. Chẩn đoán cũ sai.

### Chẩn đoán cũ sai ở đâu

Báo cáo trên kết luận **TẮT** reranker vì 4.208 ms/lượt, và ghi nguyên nhân:

> Nguyên nhân: cross-encoder chạy **CPU**. GPU 4 GB của máy này đã bị model
> embedding chiếm; nạp thêm cross-encoder lên cùng GPU thì vỡ với
> `CUDA error: device-side assert triggered`.

**Sai.** Đo lại 2026-08-21:

```
nvidia-smi : 4096 MiB tổng, 1779 MiB đang dùng, 2186 MiB trống
torch      : free 3.22 GB / total 4.00 GB
PhoRanker  : 540 MB
```

VRAM thừa gấp sáu lần. Không hề thiếu chỗ.

Nguyên nhân thật là **thứ tự import** — đúng cái bẫy đã ghi trong
[`app/__init__.py`](../../app/__init__.py) cho model embedding, và nó áp cho
cross-encoder y hệt:

```python
# Import sentence_transformers SAU các module khác:
$ DEV=cuda python rr.py
device muc tieu: cuda
import xong
Segmentation fault          <- sập ở đây, không phải CUDA assert

# Import sentence_transformers TRƯỚC mọi thứ khác:
$ DEV=cuda python rr2.py
XONG 0.45s loi=0
   ninhbinh_gntt_ca_chua#2      0.9421
```

`CUDA error: device-side assert triggered` mà báo cáo cũ ghi lại là **triệu
chứng của lỗi `max_length=512` trên model khai `max_position_embeddings=258`**
— lỗi đó đã sửa từ 2026-08-20 nhưng kết luận "GPU không dùng được" thì không
ai đo lại.

### Số đo mới

Trên 22 case có ground truth, `evaluation/runners/eval_rerank.py`:

| | CPU (báo cáo cũ) | **GPU (mới)** |
|---|---:|---:|
| R@1 | 45,5 | 45,5 |
| R@3 | 72,7 | 72,7 |
| R@5 | **90,9** | **90,9** |
| MRR | 0,605 | 0,605 |
| chi phí | 4.208 ms | **1.107 ms** |

**Chất lượng giống hệt. Chi phí giảm 3.101 ms.**

### Latency thật trên đường truy xuất

Runner đo cả overhead của chính nó. Đo trên `tim_kiem()` thật, 8 câu hỏi,
có làm nóng model trước:

| | p50 | p95 | max |
|---|---:|---:|---:|
| không rerank | 167 ms | 187 ms | 189 ms |
| **có rerank** | **626 ms** | **636 ms** | **642 ms** |

Chi phí thật: **+459 ms**.

### Ngân sách ASM-01

| chặng | ms |
|---|---:|
| truy xuất + rerank | 626 |
| gọi LLM | ~2.600 |
| **tổng** | **~3.226** |

Dưới `ASM-01` (p50 ≤ 5.000 ms) với biên khoảng 1,8 giây.

### Quyết định

**BẬT.** `RERANKER_MODEL=itdainb/PhoRanker`, `RERANKER_DEVICE=cuda`.

Đổi lại **R@5 từ 72,7% lên 90,9%** — gần một phần năm số câu hỏi trước đây
không có chunk đúng trong top-5 thì nay có.

### Điều kiện phải xét lại

1. **Máy triển khai không có GPU** → quay về 4.208 ms/lượt, vượt ngân sách.
   Đây là ràng buộc phải nói với NextFarm, không phải chi tiết nội bộ.
2. `RERANKER_DEVICE=cpu` là đường lùi an toàn, không cần sửa mã.
3. Mọi tiến trình nạp reranker **phải** import `sentence_transformers` trước
   các module khác, nếu không sẽ segfault. `pipeline.py:24` đã làm đúng.
