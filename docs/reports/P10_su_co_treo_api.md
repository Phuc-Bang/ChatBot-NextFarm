# Sự cố: mọi request `/api/chat` treo vô hạn

> Phát hiện và sửa 2026-08-20 · [`app/core/db.py`](../../app/core/db.py) ·
> [`app/main.py`](../../app/main.py) · test: `tests/test_ghi_log_khong_chan.py`

## Triệu chứng

`GET /api/health` trả về trong 0,02 giây. `POST /api/chat` **không bao giờ**
trả về — timeout ở mọi client, và server **không ghi một dòng log nào** cho
request đó.

Trong khi đó, gọi thẳng `tra_loi_cau_hoi()` ngoài server thì:

```
bat van 3 trong 10 phut               0.01s  tu_choi=True  device_control
app co tinh nang tuoi tu dong khong   0.00s  tu_choi=True  product_feature
```

Câu trả lời sẵn sàng sau **10 mili-giây**. Người dùng không bao giờ thấy nó.

## Ba chẩn đoán sai trước khi tìm ra

Ghi lại vì mỗi cái đều hợp lý và đều tốn thời gian:

1. **"curl trên Git Bash làm hỏng JSON"** — sai. Gửi bằng `urllib`, bằng
   socket thô, kết quả y hệt.
2. **"threadpool bị chiếm lúc nạp model"** — sai. Startup đã xong (log ghi
   `Application startup complete`), và POST tới `/api/health` vẫn trả 405
   trong 0,02s.
3. **"khoá import trong hàm"** — sai. `py-spy dump` cho thấy không thread nào
   giữ khoá import.

## Cách tìm ra: `py-spy dump`

Không đoán nữa. Gửi một request rồi chụp stack của tiến trình uvicorn:

```
Thread 30708: "AnyIO worker thread"
    _select (selectors.py:314)
    wait_conn (psycopg/waiting.py:91)
    connect (psycopg/connection.py:103)
    ket_noi (app/core/db.py:27)
    ghi_query_log (app/core/nhat_ky.py:31)
    chat (app/main.py:77)
```

Handler **đã chạy xong việc trả lời** và đang kẹt ở bước **ghi log**, cụ thể
là `psycopg.connect()`.

Và nhiều thread cùng kẹt: mỗi request treo lại chiếm một worker vĩnh viễn.

## Nguyên nhân gốc — một chữ trong chuỗi kết nối

Chẩn đoán đầu tiên của tôi ("thiếu `connect_timeout`") **chỉ là triệu chứng**.
Nguyên nhân thật tìm ra sau, và nó nhỏ đến mức khó tin:

```
127.0.0.1   kết nối trong  0,01s
localhost   kết nối trong 10,05s   <- bằng ĐÚNG connect_timeout
```

Con số 10,05s bằng đúng `connect_timeout=10` không phải trùng hợp.
**`localhost` phân giải ra cả `::1` (IPv6) lẫn `127.0.0.1`**, libpq thử IPv6
trước, còn Docker Desktop chỉ bind IPv4 — nên mỗi kết nối phải **chờ hết
timeout** rồi mới thử IPv4 và thành công.

Đặt `connect_timeout=15` chính là **kéo dài** thời gian chờ đó.

Postgres hoàn toàn khoẻ (6/100 kết nối, `pg_isready` OK). Không có gì hỏng cả
— chỉ là mọi kết nối đều đi đường vòng.

### Điều này giải thích tất cả

| triệu chứng | ghi ở đâu |
|---|---|
| `/api/chat` treo | báo cáo này |
| pytest treo giữa chừng | báo cáo này |
| "mỗi kết nối tốn ~3,2s" | [P6_retrieval_tuning.md](P6_retrieval_tuning.md) |
| công cụ quét tham số chạy mãi không xong | P6 |
| server mất 147s để khởi động | log |

**Bản sửa:** đổi `localhost` → `127.0.0.1` trong `.env` và bốn file mã.

```
298 test xanh trong 15 giây.
```

Trước đó cùng bộ test chạy hàng chục phút rồi treo.

> Ghi rõ trong `app/core/db.py` để không ai đổi ngược lại. Với người đọc mã,
> `localhost` và `127.0.0.1` trông như nhau.

## Vì sao `try/except` sẵn có không cứu được

Mã cũ đã có:

```python
try:
    ghi_query_log(r)
except Exception as e:
    print("khong ghi duoc query_log: " + str(e)[:150])
```

Chú thích ngay trên nó viết *"Lỗi ghi log KHÔNG được làm hỏng câu trả lời"* —
đúng ý định, nhưng **treo không phải exception**. `except` không bao giờ chạy.

> Đây là bài học đáng giữ: `try/except` bảo vệ khỏi **lỗi**, không bảo vệ khỏi
> **chờ**. Mọi lời gọi ra ngoài tiến trình (DB, HTTP, file trên mạng) cần
> **timeout**, không chỉ cần `except`.

## Hai bản sửa timeout — vẫn giữ, dù không phải nguyên nhân gốc

Hai thay đổi dưới đây làm **trước khi** tìm ra chuyện `localhost`/IPv6. Chúng
không sửa nguyên nhân, nhưng vẫn giữ lại: một sự cố DB thật (container chết,
mạng đứt) vẫn sẽ làm mọi thứ treo vĩnh viễn nếu thiếu chúng.

## Bản sửa — hai lớp, cần cả hai

**Lớp 1 — `ket_noi()` luôn có timeout** (`app/core/db.py`)

```python
TIMEOUT_KET_NOI = int(os.environ.get("DB_CONNECT_TIMEOUT", "15"))

def ket_noi(**kw):
    kw.setdefault("connect_timeout", TIMEOUT_KET_NOI)
    return psycopg.connect(dsn(), **kw)
```

Biến treo vô hạn thành lỗi sau 15 giây. Cần, nhưng chưa đủ: 15 giây vẫn quá
chậm cho một request đáng lẽ 6ms.

**Lớp 2 — ghi log rời khỏi đường trả lời** (`app/main.py`)

```python
def chat(v: CauHoiVao, nen: BackgroundTasks):
    r = tra_loi_cau_hoi(v.cau_hoi, v.context_turns or None)
    nen.add_task(_ghi_log_an_toan, r)
    return {...}
```

Câu trả lời về ngay; ghi log chạy nền và nuốt mọi lỗi.

## Kết quả đo sau khi sửa

| câu hỏi | trước | sau | nhánh |
|---|---|---:|---|
| bật van 3 trong 10 phút | treo | **0,05s** | `device_control` |
| app có tính năng tưới tự động không | treo | **0,00s** | `product_feature` |
| cà phê cần pH bao nhiêu | treo | **0,02s** | `out_of_scope` |

## Bốn test canh giữ

`tests/test_ghi_log_khong_chan.py`:

1. `ket_noi()` luôn đặt `connect_timeout`
2. bên gọi ghi đè được giá trị đó
3. `_ghi_log_an_toan()` nuốt mọi lỗi
4. thân hàm `chat()` **không** gọi thẳng `ghi_query_log` và **có** dùng
   `add_task` — đọc mã nguồn, để một lần sửa vô ý sau này làm test đỏ

## Điều đáng lo hơn con số

Sự cố này **không** bị 283 test bắt được, vì test gọi thẳng pipeline chứ
không đi qua HTTP. Nó chỉ lộ ra khi bấm thử giao diện thật.

Nếu đem demo cho NextFarm mà không thử tay trước, kết quả sẽ là một chatbot
**không trả lời gì cả** — dù mọi con số trong báo cáo đều đẹp.

---

## Cùng lỗi, dạng thứ hai: truy vấn treo (không phải kết nối treo)

Sau khi sửa, chạy lại toàn bộ test thì **pytest treo** ở
`test_keyword_retrieval.py`. `py-spy dump` cho stack khác:

```
wait_select (psycopg/waiting.py:244)
  wait (psycopg/connection.py:394)
    execute (psycopg/cursor.py:93)      <- TREO o day, khong phai connect
      tim_fts (app/services/retrieval/keyword.py:179)
```

Lần này kết nối **mở được**; chính **truy vấn** không bao giờ xong. Và
`pg_stat_activity` **không thấy kết nối nào** — tức kết nối đã đứt ở tầng
mạng mà client không biết, nên nó chờ mãi một phản hồi sẽ không tới.

`connect_timeout` không cứu được trường hợp này: nó chỉ áp cho lúc bắt tay.

**Bản sửa:** thêm `statement_timeout` vào mọi kết nối.

```python
TIMEOUT_CAU_LENH = int(os.environ.get("DB_STATEMENT_TIMEOUT_MS", "30000"))
kw.setdefault("options", "-c statement_timeout=" + str(TIMEOUT_CAU_LENH))
```

30 giây, trong khi truy vấn nặng nhất đo được (quét 185 chunk) mất dưới 1
giây — đủ rộng để không cắt nhầm việc thật, đủ chặt để không treo vĩnh viễn.

Áp dụng cho cả bốn chỗ gọi `psycopg.connect` trực tiếp:
`tests/test_keyword_retrieval.py`, `tests/test_schema.py`, `db/migrate.py`.

> **Quy tắc rút ra cho cả dự án:** mọi lời gọi ra ngoài tiến trình cần **hai**
> timeout — một cho lúc kết nối, một cho lúc chờ kết quả. Thiếu cái nào cũng
> để lại một đường treo vĩnh viễn.

---

## Đo lại end-to-end sau khi sửa

Server khởi động sạch (`Da nap model embedding trong 17.8s` — trước là 147s),
gọi qua HTTP thật:

| câu hỏi | tổng | truy xuất | LLM | kết quả |
|---|---:|---:|---:|---|
| bật van 3 trong 10 phút | **0,08s** | — | — | `device_control` |
| thế giờ đang bao nhiêu (lượt 2) | **0,03s** | — | — | `garden_data` |
| cà chua cần đất pH bao nhiêu | **2,82s** | 222ms | 2.581ms | **trả lời được** |
| dưa chuột cần độ ẩm đất bao nhiêu | 34,42s | 216ms | 34.174ms | `loi_he_thong` |

**Truy xuất 216–222ms** — khoẻ, đúng như đo được ở P6.

Câu cuối 34 giây **không phải lỗi mã**. Log server:

```
[429] cho 2.8s roi thu lai (1/5)
[429] cho 4.6s roi thu lai (2/5)
[429] cho 8.3s roi thu lai (3/5)
[429] cho 16.8s roi thu lai (4/5)
```

2,8 + 4,6 + 8,3 + 16,8 = đúng 32,5 giây backoff sau bốn lần 429. Quota free
tier đã cạn (xem [BAO_CAO_SO_SANH.md](BAO_CAO_SO_SANH.md)). Hệ thống lùi và
thử lại **đúng thiết kế**, rồi từ chối tử tế thay vì bịa.

**Một chẩn đoán sai nữa cần đính chính:** lần đo trước cho `truy_xuat=30.335ms`
và tôi định quy cho kênh vector. Sai — đó là server cũ nạp kho vector lần đầu
ngay trong request (nó khởi động khi `.env` còn `localhost` nên lifespan nạp
hụt). Server khởi động sạch cho 222ms.

## Tầng 3 chạy đúng trên sản phẩm thật

`ie_022` gọi qua HTTP với `context_turns` → bị chặn với lý do
`grounding_khong_dat`. Đây là xác nhận trên đường chạy thật, không phải chỉ
trên dữ liệu đã lưu.
