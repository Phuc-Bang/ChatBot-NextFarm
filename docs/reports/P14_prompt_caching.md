# P14 — Prompt caching: đã đo, KHÔNG áp dụng được

Ngày đo: 2026-08-21
Model: `gemini-3.1-flash-lite`

---

## Vì sao xét

Tài liệu giao hàng ghi prompt caching là *"khả thi và đáng làm"* nhưng chưa
đo. Với `Ti` = 1.925 token trên mỗi lượt có gọi model, nghe như một khoản
tiết kiệm đáng kể.

## Tách prompt ra hai phần

Prompt gửi đi gồm ba phần (`app/services/rag/sinh_cau_tra_loi.py:34`):

```
MAU_PROMPT.format(bang_chung=..., cau_hoi=...)
```

Đếm bằng `count_tokens` của chính Gemini, 4 câu hỏi thật:

| câu hỏi | Evidence Pack | câu hỏi | tổng |
|---|---:|---:|---:|
| cà chua cần đất pH bao nhiêu | 1.826 | 9 | 2.010 |
| lúa bón thúc lần 1 khi nào | 1.349 | 11 | 1.535 |
| dưa chuột trồng vụ nào | 1.052 | 7 | 1.234 |
| mật độ gieo sạ lúa bao nhiêu | 1.848 | 13 | 2.036 |

| phần | token | tỷ lệ | cache được? |
|---|---:|---:|---|
| mẫu prompt cố định | **175** | 10,3% | có |
| Evidence Pack + câu hỏi | **1.529** | 89,7% | **không** |
| **tổng trung bình** | **1.704** | 100% | |

## Thử thật, và bị từ chối

```python
kh.caches.create(model=m, config=types.CreateCachedContentConfig(
    system_instruction=co_dinh, ttl="300s"))
```

```
400 INVALID_ARGUMENT
Cached content is too small.
total_token_count=175, min_total_token_count=1024
```

175 token không đạt ngưỡng tối thiểu 1.024 của Gemini. Không phải giới hạn
tự đặt — là API từ chối thẳng.

## Vì sao không sửa được bằng cách nào

Phần lớn prompt là **Evidence Pack**, và Evidence Pack đổi theo từng câu hỏi
— đó chính là điều RAG làm. Cache nó thì không có gì để tái dùng, vì câu hỏi
tiếp theo lấy chunk khác.

Nói cách khác: **prompt caching thưởng cho kiến trúc gửi cùng một khối lớn
lặp đi lặp lại. RAG cố ý làm ngược lại.**

## Kết luận

**Không áp dụng được.** Ghi vào tài liệu giao hàng là *đã đo và bị từ chối*,
không phải *chưa làm*.

## Điều kiện xét lại

Cache trở nên đáng giá nếu kiến trúc đổi theo một trong hai hướng:

1. **Mẫu prompt phình lên quá 1.024 token** — ví dụ thêm nhiều ví dụ few-shot
   cố định vào system prompt. Lúc đó phần cache được vượt ngưỡng.
2. **Có tập chunk "nóng" dùng lại nhiều lần** — ví dụ 20 chunk trả lời 80% câu
   hỏi. Cache riêng nhóm đó. Hiện chưa đo phân bố này.

## Điều đáng nói với NextFarm

Chi phí ở kiến trúc này được cắt bằng **không gọi model**, không phải bằng
làm cho lượt gọi rẻ đi:

| cơ chế | tiết kiệm | trạng thái |
|---|---|---|
| chặn trước khi gọi model | **63,5% số lượt, 0 token** | đã có, đã đo |
| embedding chạy local | chi phí biên = 0 | đã có |
| prompt caching | — | **không áp dụng được** |

Con số `Ti` = 702 trong mô hình chi phí đã bao gồm sẵn khoản đầu tiên.
