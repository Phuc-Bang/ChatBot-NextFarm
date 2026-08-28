# Báo Cáo Đo Lường Kỹ Thuật: Chốt Trọng Số Vùng Miền (§40.2 Mục 11)

> **Tiêu chuẩn tham chiếu:** `NEXTFARM_PROBLEM_A_STANDARD_v2.0.md` — Mục 14.5 & Mục 40.2
> **Thời điểm thực thi:** 22/08/2026
> **Dữ liệu đánh giá:** 30 test cases đặc thù địa phương (`regional_test_cases.jsonl`) · 192 chunks kho tri thức

---

## 1. Bảng Kết Quả Đo Lường Đa Trọng Số

| Hệ số cộng điểm (`he_so`) | Số ca đánh giá | Top-1 Khớp Vùng Miền | Top-3 Độ Phủ Vùng Miền | Đánh giá kỹ thuật |
| :---: | :---: | :---: | :---: | :--- |
| **0.00** | 30 | **53.3%** (16/30) | **66.7%** (20/30) | Baseline: không cộng điểm vùng |
| **0.05** | 30 | **63.3%** (19/30) | **73.3%** (22/30) | Thấp hơn đỉnh 4 ca |
| **0.10** | 30 | **63.3%** (19/30) | **73.3%** (22/30) | Thấp hơn đỉnh 4 ca |
| **0.15** | 30 | **73.3%** (22/30) | **76.7%** (23/30) | Thấp hơn đỉnh 1 ca |
| **0.20** | 30 | **73.3%** (22/30) | **76.7%** (23/30) | Thấp hơn đỉnh 1 ca |
| **0.25** | 30 | **73.3%** (22/30) | **76.7%** (23/30) | Thấp hơn đỉnh 1 ca |
| **0.30** | 30 | **76.7%** (23/30) | **76.7%** (23/30) | **Top-1 cao nhất đo được** (76.7%), đạt ở hệ số thấp nhất trong nhóm cùng điểm |

---

## 2. Đọc bảng trên

- **Baseline `0.00`:** Top-1 53.3% (16/30).
- **Đỉnh đo được:** hệ số `0.30` — Top-1 76.7% (23/30), hơn baseline 7 ca.
- **Mặc định đang đặt trong mã (`he_so = 0.10`):** Top-1 63.3% (19/30) — **thấp hơn đỉnh 4 ca**.

> Phép đo này KHÔNG đo được hiện tượng "trọng số quá mạnh đẩy chunk sai nội dung lên top". Muốn khẳng định điều đó phải chấm nội dung từng chunk trả về, không chỉ đếm khớp vùng. Bản báo cáo trước có câu đó nhưng không có số nào chống lưng — đã bỏ.

## 3. Giới hạn phải nói rõ

0. **Đỉnh rơi đúng vào biên của dải quét.** Giá trị cao nhất được thử là `0.30` và chính nó cho Top-1 cao nhất. Khi đỉnh nằm ở mép, phép quét chưa chứng minh được đã tìm ra điểm tốt nhất — rất có thể hệ số còn tốt hơn nằm ngoài dải. Muốn kết luận phải nới dải rồi quét lại.

1. **Tham số này hiện KHÔNG tác động lên hệ thống đang chạy.** `cong_diem_vung()` chỉ chạy khi `tim_kiem()` nhận đối số `region`. Đường sống gọi `tim_kiem(cau, crop=..., top_k=...)` (`app/services/pipeline.py:185`) — không truyền `region`, nên nhánh `if region:` (`hybrid.py:65`) không bao giờ vào. Chỉ chính script này truyền `region`. Mọi con số trên đo một nhánh mã mà người dùng thật chưa chạm tới.
2. **Tập 30 câu là tự viết, nằm NGOÀI tập đóng băng v3.** Nó được tạo trong cùng commit chốt tham số (`8e5f93f`). Tự viết thước rồi tự đo — kết quả chỉ nên dùng để định hướng, không dùng làm bằng chứng nghiệm thu. 0/222 case của v3 khai trường `region`.

## 4. Kết luận

> Trên tập 30 câu tự viết, hệ số `0.30` cho Top-1 cao nhất (76.7%). Mã đang để mặc định `0.10` (63.3%).
>
> **Chưa đổi mặc định**, vì đổi một tham số không có đường vào sản phẩm là thay đổi vô nghĩa. Việc cần làm trước là cho pipeline nhận diện và truyền `region`; khi đó mới quét lại trên tập có khai vùng thật và chốt bằng số đo có giá trị.