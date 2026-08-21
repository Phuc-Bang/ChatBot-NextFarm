# Plan 003: Đồng bộ số test trong tài liệu và thêm hàng rào chống lệch

> **Executor instructions**: Làm theo từng bước, chạy mọi lệnh kiểm chứng. Gặp
> "STOP conditions" thì dừng và báo. Xong thì cập nhật `plans/README.md`.
>
> **Drift check**: `git diff --stat 94fad86..HEAD -- README.md docs/ tests/`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `94fad86`, 2026-08-22

## Why this matters

Bảy chỗ trong tài liệu ghi bộ kiểm thử có **310 test**. Chạy thật hôm nay ra
**318**. Con số này xuất hiện trong tài liệu giao cho NextFarm và trong báo cáo
tổng kết, ở vị trí bằng chứng chất lượng.

Sai lệch 8 test không gây hại kỹ thuật. Nhưng nó gây hại theo cách khác: đây là
dự án bán một lời hứa **"mọi con số đều kiểm chứng được"**. Một con số dễ kiểm
nhất — chạy một lệnh là biết — mà lại sai thì mọi con số khó kiểm hơn trong cùng
tài liệu cũng mất trọng lượng.

Đây là dạng lệch sẽ tái diễn: mỗi lần thêm test là bảy chỗ phải sửa tay. Plan
này sửa cả hai — số hiện tại, và cơ chế để lần sau phát hiện được.

## Current state

**Bảy vị trí ghi 310:**

```
docs/BAO_CAO_TONG_KET_NEXTFARM.md:7    > **Trạng thái kiểm thử:** 310/310 Unit Tests PASSED (100%) · Working Tree Clean
docs/BAO_CAO_TONG_KET_NEXTFARM.md:156  * **Bộ kiểm thử tự động:** **310/310 Unit Tests PASSED (100%)** ...
docs/BAO_CAO_TONG_KET_NEXTFARM.md:164  ... kết nối CI/CD tự động chạy 310 tests khi triển khai.
docs/GIAO_HANG_NEXTFARM.md:109         ... bộ 310 unit tests và bộ runner đánh giá chất lượng RAG ...
docs/GIAO_HANG_NEXTFARM.md:369         make test        # 310 test tự động
README.md:102                          | Test tự động | **310 xanh** |
README.md:252                          make test        # 310 test tự động
```

**Số thật, xác nhận 2026-08-22:**

```
$ python -m pytest tests/ -q
318 passed in 4.39s

$ python -m pytest tests/ --collect-only -q
318 tests collected in 0.34s
```

**Vì sao lệch:** phiên làm việc ngày 21-22/08 thêm 8 test —
`tests/test_review_chunks.py` (6 test mới), cộng một test canh giữ trong
`tests/test_keyword_retrieval.py` và một trong `tests/test_rerank.py`. Tài liệu
không được cập nhật theo.

### Quy ước của repo phải theo

- Tài liệu `docs/` và `README.md`: **tiếng Việt CÓ DẤU**.
- Test `tests/`: chú thích **tiếng Việt KHÔNG DẤU**, docstring giải thích **vì
  sao test tồn tại** và **sự cố thật nào đã sinh ra nó**. Mẫu tốt:
  `tests/test_ghi_log_khong_chan.py` — mở đầu bằng "SU CO THAT 2026-08-20" rồi
  kể lại chẩn đoán.
- Test đọc mã nguồn để canh giữ quy ước là **mẫu đã dùng trong repo**, không
  phải phát minh mới. Xem `tests/test_review_chunks.py:75` (phân tích cây cú
  pháp) và `tests/test_ghi_log_khong_chan.py:79` (đọc mã nguồn hàm).

## Commands you will need

| Mục đích | Lệnh | Kết quả mong đợi |
|---|---|---|
| Đếm test | `python -m pytest tests/ --collect-only -q \| tail -1` | `318 tests collected...` |
| Chạy test | `python -m pytest tests/ -q` | 318 passed (319 sau Step 3) |
| Tìm số cũ | `grep -rn "310" README.md docs/` | không còn dòng nào nói về test |

## Scope

**In scope**:
- `README.md`
- `docs/GIAO_HANG_NEXTFARM.md`
- `docs/BAO_CAO_TONG_KET_NEXTFARM.md`
- `tests/test_so_lieu_tai_lieu.py` (tạo mới)
- `plans/README.md`

**Out of scope**:
- `docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md` — quy chuẩn không nêu số test.
- `docs/reports/*.md` — báo cáo đo lường, mỗi bản ghi số tại thời điểm đo và
  **phải giữ nguyên**. Sửa số trong báo cáo cũ là làm hỏng bản ghi lịch sử.
- Bất kỳ file nào trong `evaluation/` hoặc `app/`.

## Git workflow

- Nhánh: `advisor/003-dong-bo-so-test`
- Commit tiếng Việt có dấu.

## Steps

### Step 1: Xác nhận số thật trước khi sửa gì

```
python -m pytest tests/ --collect-only -q | tail -1
```

Ghi lại con số. **Dùng con số vừa chạy ra, không dùng 318 trong plan này** —
plan viết ở commit `94fad86`, có thể đã thêm test từ đó.

Nếu số khác 318, dùng số mới và ghi chú điều đó khi báo cáo.

**Verify**: có một con số cụ thể trong tay

### Step 2: Sửa bảy vị trí

Thay `310` bằng số ở Step 1 tại đúng bảy dòng liệt kê ở "Current state".

Cẩn thận: `grep -rn "310"` có thể trúng những chỗ khác (số tiền, số dòng, mã
lỗi). **Chỉ sửa dòng nào đang nói về số lượng test.**

**Verify**:
```
grep -rn "310" README.md docs/GIAO_HANG_NEXTFARM.md docs/BAO_CAO_TONG_KET_NEXTFARM.md
```
→ không còn dòng nào nói về test (nếu còn dòng nào chứa 310 vì lý do khác, đọc
và xác nhận nó không liên quan)

### Step 3: Thêm test canh giữ

Tạo `tests/test_so_lieu_tai_lieu.py`. Test này **tự đếm số test đang có** rồi
đối chiếu với con số ghi trong `README.md`, và đỏ lên khi hai bên lệch.

Cách đếm không được gọi lại pytest (đệ quy). Dùng `pytest --collect-only` qua
`subprocess` thì chậm và mong manh. Cách gọn hơn: dùng hook `pytest_collection_modifyitems`
trong `tests/conftest.py` để ghi lại số item đã thu thập, rồi test đọc con số đó.

Nếu cách trên vượt quá mức bạn tự tin làm đúng, **giải pháp thay thế được chấp
nhận**: test chỉ khẳng định các con số nêu trong `README.md`,
`docs/GIAO_HANG_NEXTFARM.md` và `docs/BAO_CAO_TONG_KET_NEXTFARM.md` **giống
nhau** — không kiểm chúng có khớp thực tế không. Nó vẫn bắt được lỗi phổ biến
nhất là sửa một chỗ quên sáu chỗ. Chọn cách nào cũng được, nhưng phải ghi rõ
trong docstring là test đang canh cái gì và **không** canh cái gì.

Docstring phải kể sự cố thật: bảy chỗ ghi 310 trong khi thật là 318, phát hiện
2026-08-22, và lý do vì sao con số này quan trọng hơn vẻ ngoài của nó.

**Verify**: `python -m pytest tests/test_so_lieu_tai_lieu.py -q` → pass

### Step 4: Chạy lại toàn bộ và cập nhật số một lần nữa

Thêm test mới làm tổng số tăng lên. Chạy lại, lấy số mới, sửa lại bảy vị trí
(và test vừa viết nếu nó chứa số cứng).

```
python -m pytest tests/ -q
```

**Verify**: số trong tài liệu = số pytest in ra. Chạy lại lần nữa để chắc chắn
đã hội tụ.

## Test plan

- `tests/test_so_lieu_tai_lieu.py` — 1–2 test theo Step 3.
- Lấy `tests/test_review_chunks.py` làm mẫu cấu trúc: dùng `Path(__file__).resolve().parents[1]`
  để tìm gốc repo, đọc file bằng `encoding="utf-8"`.
- **Đừng dùng regex quá rộng.** Test bắt nhầm số tiền hay số dòng sẽ đỏ vì lý do
  sai và bị người sau xoá đi.

## Done criteria

- [ ] `python -m pytest tests/ -q` → exit 0, số passed = số ghi trong `README.md`
- [ ] `grep -rn "310 test\|310/310\|310 xanh\|310 unit" README.md docs/GIAO_HANG_NEXTFARM.md docs/BAO_CAO_TONG_KET_NEXTFARM.md` → không kết quả
- [ ] `tests/test_so_lieu_tai_lieu.py` tồn tại và pass
- [ ] `git status` → không có file nào ngoài in-scope bị sửa
- [ ] `docs/reports/` **không** bị sửa: `git diff --name-only | grep "docs/reports"` → rỗng
- [ ] Dòng trạng thái plan 003 trong `plans/README.md` đã cập nhật

## STOP conditions

- `pytest --collect-only` báo lỗi thu thập (test suite đang hỏng) — sửa cái đó
  trước, không phải việc của plan này.
- Số test đếm được thay đổi giữa hai lần chạy liên tiếp mà không sửa gì — có test
  phụ thuộc thứ tự hoặc trạng thái ngoài; báo lại, đừng chọn đại một con số.
- Sửa số ở `docs/BAO_CAO_TONG_KET_NEXTFARM.md` làm lộ ra con số khác cũng lệch
  (ví dụ số chunk, số case) — ghi lại và báo, đừng tự sửa những con số ngoài
  phạm vi plan này.

## Maintenance note

Con số này sẽ lệch lại mỗi lần thêm test, trừ khi Step 3 làm theo cách tự đếm.
Nếu chọn cách thay thế (chỉ kiểm ba tài liệu khớp nhau) thì ghi vào `README.md`
một dòng nhắc: sửa số test thì sửa cả ba chỗ.

Cách bền hơn cả — nhưng ngoài phạm vi plan này — là **bỏ hẳn con số cứng khỏi
tài liệu**, thay bằng câu "chạy `make test` để xem số hiện tại". Đáng cân nhắc
nếu con số này lệch lần nữa.
