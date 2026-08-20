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

**Mặc định TẮT** (`RERANKER_MODEL` để trống). Lý do: 4,2 giây phá ngân sách
`ASM-01`, và ngân sách đó là `[ASM]` — giả định của đội, chưa được NextFarm
xác nhận.

Bật khi có một trong hai:

1. **NextFarm nới ngưỡng độ trễ.** Nếu chấp nhận ~7 giây mỗi câu, bật ngay —
   R@5 90,9% là cải thiện lớn.
2. **Có GPU đủ lớn.** Cross-encoder trên GPU nhanh hơn CPU nhiều lần. Đây là
   một lý do cụ thể để NextFarm cân nhắc đầu tư GPU, và khác với lý do
   "self-host model sinh" đã bị bác ở §37.5.

Bật bằng một dòng, không phải sửa mã:

```
RERANKER_MODEL=itdainb/PhoRanker
```
