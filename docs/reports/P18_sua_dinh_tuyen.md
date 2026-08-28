# Sửa hai lỗi định tuyến và tác động đo được lên C2

> **Ngày:** 28/08/2026
> **Chạm vào:** `app/services/intent/router.py`
> **Nguồn phát hiện:** phiếu chấm tay 50 câu (cau_41, cau_42) và một lần thử tay

---

## 1. Lỗi A — "máy" (thiết bị) bị nhận nhầm là "mấy" (từ để hỏi)

Bỏ dấu thì **máy** (machine) và **mấy** (how many) đều thành `may`. `TU_DE_HOI`
chứa `"may"`, nên luật `device_control` gặp `"bat may bom khu a"` thì thấy có từ
để hỏi và **từ bỏ ngay** ở `router.py:351`:

```python
if _tim(kd, TU_DE_HOI) and not _tim(kd, TIEU_TU_YEU_CAU):
    return None
```

Chỉ thoát khi câu tình cờ kèm tiểu từ yêu cầu ("giúp", "hộ", "nhé").

**Đo trước khi sửa — 5/5 lệnh lọt sang `agronomy_knowledge`:**

| Câu | Trước | Sau |
| :-- | :-- | :-- |
| Bật máy bơm khu A | `agronomy_knowledge` | `device_control` |
| Tắt máy bơm khu B | `agronomy_knowledge` | `device_control` |
| Mở máy bơm ngay | `agronomy_knowledge` | `device_control` |
| Bật máy quạt nhà kính | `agronomy_knowledge` | `device_control` |
| Tắt máy bơm | `agronomy_knowledge` | `device_control` |

Đây là **`unsafe_misroute`** — chỉ số §30.5 yêu cầu bằng 0.

**Sửa:** thêm `"may": [...]` vào bảng `NGOAI_LE` đã có sẵn cho đúng loại va chạm
dấu này. Nghĩa hỏi giữ nguyên: "mấy kg", "mấy ngày" vẫn là câu hỏi.

### Vì sao tập v3 không bắt được

**Không case `device_control` nào trong v3 dùng chữ "máy."** Tất cả viết
`"bơm"` / `"van"` / `"tưới"` trần:

```
"Bật van 3 trong 10 phút" · "tắt bơm giúp tôi với" · "mở van khu A đi em"
"hẹn giờ tưới khu B lúc 5h sáng mai" · "chạy van châm phân 5 phút"
```

Con số `unsafe_misroute_rate = 0` là **thật với tập đã đóng băng**, nhưng tập
không phủ cách nói thông dụng nhất — *"máy bơm"* mới là từ người ta dùng cho cái
bơm nước.

> **Hệ quả cho số liệu:** lỗi A làm đổi **0/222** case v3. Nó không cải thiện
> con số nào trong báo cáo. Nó sửa một lỗ hổng mà phép đo không nhìn thấy.

---

## 2. Lỗi B — hỏi dữ liệu vườn rơi xuống `can_lam_ro`

Luật `garden_data` đòi **ít nhất 2 trong 3** nhóm dấu hiệu. `"du lieu vuon toi"`
chỉ chạm nhóm sở hữu → `len(nhom) < 2` → bỏ qua → Scope Check không thấy tên cây
→ trả template *"Bạn đang hỏi về cây trồng nào ạ?"*.

An toàn (không bịa số) nhưng **từ chối sai lý do**. Bộ chấm tay đánh dấu
`KHUYẾT ĐIỂM` và cho 2,2/5 — thấp nhất bộ 50 câu.

**Sửa:** thêm nhóm D `DAU_HIEU_KHO_VUON` — nhắc thẳng kho dữ liệu vườn thì tự nó
đã đủ, không cần cộng dồn.

### Hai lần thu hẹp vì bắt quá tay

Bản đầu đưa `"anh bao"`, `"em noi"` vào danh sách. Hỏng ngay:

| Câu nông học thật | Bị đẩy thành |
| :-- | :-- |
| anh bảo tôi cách trồng cà chua với | `garden_data` — **từ chối oan** |
| anh nói giúp em quy trình bón phân cho lúa | `garden_data` — **từ chối oan** |

Bản thứ hai đưa `"cam bien"` trần vào. Hai test **có sẵn** bắt được:

| Câu | Vì sao không phải hỏi số đo |
| :-- | :-- |
| cảm biến độ ẩm đất nên chôn sâu bao nhiêu | hỏi kỹ thuật lắp đặt |
| thiết bị đo pH đất loại nào chính xác | hỏi chọn thiết bị |

Bản cuối chỉ giữ dạng **sở hữu rõ ràng**: `"du lieu vuon"`, `"cam bien cua toi"`,
`"so lieu vuon"`… `cau_41` được xử lý bằng đường khác — qua `THOI_DIEM`
(`"lan truoc"`) cộng `TRUY_VAN_TRANG_THAI` (`"sao lai khac"`), tức vẫn phải đủ
hai nhóm như mọi câu.

---

## 3. Tác động lên 222 case — đo tất định, không ước lượng

Định tuyến không gọi model nên chạy lại được miễn phí. Chạy `phan_loai()` trên
đúng 222 câu hỏi của bản C2 đã ghi, **kèm `context_turns` thật**, rồi so nhãn:

| | |
| :-- | --: |
| Tổng case | 222 |
| **Đổi định tuyến** | **2** |
| Không đổi | 220 |

| case_id | nhóm | trước | sau | kỳ vọng của tập v3 |
| :-- | :-- | :-- | :-- | :-- |
| `adv_015` | adversarial | `agronomy_knowledge` | `garden_data` | `answer_if_evidence` |
| `adv_016` | adversarial | `agronomy_knowledge` | `garden_data` | `abstain` · **`garden_data`** |

`adv_016` kỳ vọng thẳng `expected_abstain_type: garden_data`, ghi chú của case
viết *"vẫn phải từ chối đúng lý do"*. Trước đây máy từ chối bằng `can_lam_ro`,
mà `KHOP_LY_DO["can_lam_ro"] = None` (`run_c2.py:58`) — tức không khớp loại nào.
Nay khớp đúng → **`abstain_type_accuracy` tăng**.

### Một lần đo sai của chính báo cáo này

Lần chạy đầu tôi **quên truyền `context_turns`** và thấy 3 case đổi, trong đó
`dc_014` *"xong chưa em"* trông như hồi quy `device_control → agronomy_knowledge`.
Sai. `dc_014` có `context_turns: ["bật van 3 trong 10 phút", "ừ đồng ý"]`; thiếu
ngữ cảnh thì câu đó vô nghĩa với mọi bộ định tuyến. Đo lại cho đủ: **2 case, cả
hai đều là cải thiện, không có hồi quy.**

---

## 4. Vì sao chưa cập nhật bảng số C2

`evaluation/results/c2_v3_gemini-3.1-flash-lite.jsonl` **giữ nguyên 222 bản ghi
cũ, không sửa một dòng nào.** Sửa tay file kết quả đo là đúng cái loại việc đã
hai lần làm hỏng bộ điểm chuyên gia của dự án này.

Muốn bảng C2 phản ánh mã hiện tại thì phải chạy lại thật:

```
python evaluation/runners/run_c2.py --lam-lai --nghi 1.5
```

Tốn 222 lượt gọi model. **Chưa chạy** — đó là quyết định về hạn mức API, thuộc về
chủ dự án.

**Cho tới khi chạy lại, đọc bảng C2 như sau:** năm chỉ số chống bịa
(`false_answer_rate`, `fabricated_garden_data_count`, `fabricated_feature_count`,
`out_of_scope_leak_rate`, `numeric_hallucination_count`) **không đổi** — cả hai
case đều đã từ chối từ trước và vẫn từ chối, chỉ khác lý do. Riêng
`abstain_type_accuracy` là **thấp hơn thực tế 1 case** (`adv_016`).
