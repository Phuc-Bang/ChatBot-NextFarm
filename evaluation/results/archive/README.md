# Kết quả cũ — giữ để đối chứng, KHÔNG dùng cho báo cáo hiện tại

Các công cụ (`risk_coverage.py`, các runner) tìm file theo mẫu
`c{0,1,2}_{version}_*.jsonl` trong `evaluation/results/`. Đặt bản cũ ở đây để
chúng không bị vớ nhầm.

> Đã vấp một lần: `risk_coverage.py:138` lấy `ds[-1]` — file cuối theo bảng chữ
> cái. Bản sao lưu tên `..._rerank_off.jsonl` sắp sau bản chính nên bị chọn, và
> công cụ báo "thiếu trường" trong khi bản chính có đủ.

| File | Là gì | Vì sao giữ |
|---|---|---|
| `c0_v3_gemini-2.5-flash.jsonl` | 261 bản ghi, **toàn bộ đều lỗi 429** | Bằng chứng quota `gemini-2.5-flash` cạn kiệt sau vài chục lượt gọi — cơ sở của quyết định đổi sang `3.1-flash-lite`. Xem `.env`. |
| `c1_v3_..._rerank_off.jsonl` | C1 dở dang, 169/206 ok, reranker TẮT | Đối chứng cho C1 chạy lại đầy đủ với reranker BẬT (2026-08-22) |
| `c2_v3_..._rerank_off.jsonl` | C2 trọn 222 case, reranker TẮT | Đối chứng cho C2 với reranker BẬT. Chính cặp này đo được đóng góp end-to-end của reranker — xem `docs/reports/P6_reranker.md` |

Muốn chạy công cụ trên một file ở đây thì trỏ thẳng:

```
python evaluation/runners/risk_coverage.py --ket-qua evaluation/results/archive/<file>
```
