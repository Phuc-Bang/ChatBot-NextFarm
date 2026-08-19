# Hướng dẫn: tạo nhánh `feature/data-crawler` và viết script crawl dữ liệu

Tài liệu này thuộc dự án ChatBot-NextFarm, phục vụ **Bài toán A — chống bịa đặt**.

> **ℹ️ Trạng thái:** nội dung tài liệu này đã được **hợp nhất vào** [`NEXTFARM_PROBLEM_A_STANDARD_v2.0.md`](NEXTFARM_PROBLEM_A_STANDARD_v2.0.md) (Phần IV). Code mẫu ở đây vẫn dùng được làm điểm khởi đầu, nhưng khi có mâu thuẫn thì **quy chuẩn v2.0 thắng**. Hai điểm đã đổi so với bản gốc: đơn vị duyệt (mục 6 bên dưới) và bổ sung bắt buộc về PDF, `robots.txt`, quy mô nguồn (quy chuẩn v2.0 mục 23.2).

---

## 0. Nguyên tắc bắt buộc của crawler này

Đây là phần quan trọng nhất, đọc trước khi code.

Crawler này phục vụ RAG. Nếu crawler ghi ra dữ liệu không thực sự đọc được từ nguồn, thì chatbot sẽ bịa **ngay cả khi RAG hoạt động đúng** — vì kho tri thức đã sai từ gốc. Do đó:

1. **Không hard-code số liệu nông học trong script.** Mọi con số (pH, độ ẩm, nhiệt độ) phải đến từ HTML tải về, không phải từ tay người viết code.
2. **Lưu bằng chứng gốc.** Mỗi lần crawl phải lưu HTML thô + URL + HTTP status + thời điểm tải + hash nội dung.
3. **Thất bại phải im lặng đúng cách.** Trang lỗi 404 → ghi `status: failed`, không được thay bằng dữ liệu mặc định.
4. **Tách rời 2 bước: crawl và trích xuất.** Crawl chỉ lấy văn bản. Trích xuất số liệu là bước riêng, có người kiểm duyệt.

Vi phạm bất kỳ điểm nào ở trên thì crawler trở thành nguồn hallucination.

---

## 1. Tạo nhánh mới

Trong thư mục repo đã clone:

```bash
# Đảm bảo đang ở main và đã cập nhật
git checkout main
git pull origin main

# Tạo và chuyển sang nhánh mới
git checkout -b feature/data-crawler

# Đẩy nhánh lên remote, thiết lập upstream
git push -u origin feature/data-crawler
```

Kiểm tra:

```bash
git branch          # dấu * phải nằm ở feature/data-crawler
git status
```

Nếu chưa clone repo:

```bash
git clone https://github.com/Phuc-Bang/ChatBot-NextFarm.git
cd ChatBot-NextFarm
git checkout -b feature/data-crawler
```

---

## 2. Cấu trúc thư mục cần tạo

```
ChatBot-NextFarm/
└── crawler/
    ├── requirements.txt
    ├── sources.yaml           # danh sách URL nguồn
    ├── crawl.py               # bước 1: tải trang, lưu văn bản thô
    ├── extract.py             # bước 2: trích số liệu, cần người duyệt
    └── data/
        ├── raw/               # HTML gốc (không commit)
        ├── text/              # văn bản đã tách (commit được)
        └── manifest.json      # nhật ký crawl
```

Tạo bằng lệnh:

```bash
mkdir -p crawler/data/{raw,text}
touch crawler/{requirements.txt,sources.yaml,crawl.py,extract.py}
```

Thêm vào `.gitignore`:

```
crawler/data/raw/
__pycache__/
.venv/
```

---

## 3. Cài môi trường

`crawler/requirements.txt`:

```
requests==2.32.3
beautifulsoup4==4.12.3
lxml==5.2.2
PyYAML==6.0.2
```

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r crawler/requirements.txt
```

---

## 4. Khai báo nguồn dữ liệu

`crawler/sources.yaml` — chỉ chứa URL và metadata, **không chứa số liệu**:

```yaml
sources:
  - id: hanoi_ca_chua
    crop: ca_chua
    region: dong_bang_song_hong
    publisher: So NN&MT Ha Noi
    url: https://sonnptnt.hanoi.gov.vn/cat172/2039/Ky-thuat-trong-cay-ca-chua

  - id: lamdong_ca_chua
    crop: ca_chua
    region: tay_nguyen
    publisher: Khuyen nong Lam Dong
    url: http://khuyennong.lamdong.gov.vn/ky-thuat-trong-trot/ki-thuat-trong-rau/290-quy-trinh-k-thu-t-tr-ng-cay-ca-chua

  - id: ninhbinh_dua_chuot_dong
    crop: dua_chuot
    region: dong_bang_song_hong
    publisher: Khuyen nong Ninh Binh
    url: https://khuyennong.ninhbinh.gov.vn/khoa-hoc-ky-thuat/ky-thuat-trong-va-cham-soc-dua-chuot-vu-dong-781.html

  - id: ninhbinh_dua_chuot_quytrinh
    crop: dua_chuot
    region: dong_bang_song_hong
    publisher: Khuyen nong Ninh Binh
    url: https://khuyennong.ninhbinh.gov.vn/khoa-hoc-ky-thuat/quy-trinh-san-xuat-dua-chuot-792.html

  - id: hatinh_dua_chuot_vietgap
    crop: dua_chuot
    region: bac_trung_bo
    publisher: NTM Ha Tinh
    url: https://nongthonmoi.hatinh.gov.vn/Khoa-hoc-cong-nghe/Ky-thuat-trong-dua-chuot-theo-huong-tieu-chuan-VietGAP-7401.html

  - id: laichau_dua_chuot_xuanhe
    crop: dua_chuot
    region: trung_du_mien_nui
    publisher: So NN&MT Lai Chau
    url: https://sonnmt.laichau.gov.vn/thu-vien/tai-lieu/ky-thuat-trong-va-cham-soc-cay-dua-chuot-vu-xuan-he.html

  - id: gso_lua_dong_xuan_2024
    crop: lua
    region: toan_quoc
    publisher: Tong cuc Thong ke
    url: https://www.gso.gov.vn/tin-tuc-thong-ke/2024/07/ket-qua-san-xuat-vu-dong-xuan-nam-2024/
```

Muốn thêm nguồn thì thêm vào file này, **không sửa code**.

---

## 5. Bước 1 — `crawl.py`

Nhiệm vụ duy nhất: tải trang, tách văn bản, ghi bằng chứng. Không hiểu nội dung, không suy diễn.

```python
#!/usr/bin/env python3
"""
crawl.py - Tai trang tu sources.yaml, luu van ban tho + bang chung.

Nguyen tac: script nay KHONG chua bat ky so lieu nong hoc nao.
Moi thu ghi ra deu phai den tu HTML tai ve.
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

BASE = Path(__file__).parent
RAW = BASE / "data" / "raw"
TEXT = BASE / "data" / "text"
MANIFEST = BASE / "data" / "manifest.json"

DELAY = 3          # giay giua 2 request, ton trong ha tang cua ho
TIMEOUT = 20
UA = "NextFarmBot/0.1 (nghien cuu hoc thuat; lien he: <email cua ban>)"


def fetch(url):
    """Tra ve (html, status, error). html=None neu that bai."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except requests.RequestException as e:
        return None, None, f"{type(e).__name__}: {e}"
    if r.status_code != 200:
        return None, r.status_code, f"HTTP {r.status_code}"
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text, r.status_code, None


def to_text(html):
    """Tach van ban hien thi. Bo script/style/nav/footer."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "noscript"]):
        tag.decompose()
    lines = [ln.strip() for ln in soup.get_text("\n").splitlines()]
    return "\n".join(ln for ln in lines if ln)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((BASE / "sources.yaml").read_text(encoding="utf-8"))
    records = []

    for src in cfg["sources"]:
        sid, url = src["id"], src["url"]
        print(f"[..] {sid}", flush=True)

        html, status, err = fetch(url)
        now = datetime.now(timezone.utc).isoformat()

        if html is None:
            print(f"[XX] {sid}: {err}")
            records.append({**src, "status": "failed", "http_status": status,
                            "error": err, "fetched_at": now})
            time.sleep(DELAY)
            continue

        text = to_text(html)
        if len(text) < 200:
            # Trang tai duoc nhung gan nhu khong co noi dung -> coi la that bai
            print(f"[XX] {sid}: noi dung qua ngan ({len(text)} ky tu)")
            records.append({**src, "status": "empty", "http_status": status,
                            "text_length": len(text), "fetched_at": now})
            time.sleep(DELAY)
            continue

        (RAW / f"{sid}.html").write_text(html, encoding="utf-8")
        (TEXT / f"{sid}.txt").write_text(text, encoding="utf-8")

        print(f"[OK] {sid}: {len(text)} ky tu")
        records.append({
            **src,
            "status": "ok",
            "http_status": status,
            "fetched_at": now,
            "text_length": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "text_file": f"data/text/{sid}.txt",
        })
        time.sleep(DELAY)

    MANIFEST.write_text(
        json.dumps({"crawled_at": datetime.now(timezone.utc).isoformat(),
                    "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    ok = sum(1 for r in records if r["status"] == "ok")
    print(f"\nXong: {ok}/{len(records)} nguon thanh cong")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

Chạy:

```bash
cd crawler
python crawl.py
```

Kết quả mong đợi: một số nguồn `[OK]`, một số có thể `[XX]`. **Nguồn lỗi thì để lỗi** — đừng sửa code để "cứu" nó bằng dữ liệu tay.

---

## 6. Bước 2 — `extract.py`

Bước này tìm **câu chứa số liệu**, kèm theo vị trí gốc, để người kiểm duyệt xác nhận. Nó không tự quyết định giá trị nào là đúng.

```python
#!/usr/bin/env python3
"""
extract.py - Tim cac cau chua so lieu trong van ban da crawl.

Output la DE XUAT, chua phai tri thuc. Moi dong deu co
verified=false cho den khi nguoi kiem duyet doi thanh true.
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).parent
TEXT = BASE / "data" / "text"
MANIFEST = BASE / "data" / "manifest.json"
OUT = BASE / "data" / "candidates.json"

# Tu khoa chi so - dung de LOC cau, khong dung de gan gia tri
KEYWORDS = {
    "do_am": ["độ ẩm", "ẩm độ"],
    "nhiet_do": ["nhiệt độ"],
    "ph": ["pH", "độ ph", "độ pH"],
    "ec": ["EC", "độ dẫn điện"],
    "nang_suat": ["năng suất", "tạ/ha"],
}

NUMBER = re.compile(r"\d+([.,]\d+)?")


def sentences(text):
    for raw in re.split(r"(?<=[.!?;])\s+|\n", text):
        s = raw.strip()
        if s:
            yield s


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []

    for rec in manifest["records"]:
        if rec.get("status") != "ok":
            continue
        text = (TEXT / f"{rec['id']}.txt").read_text(encoding="utf-8")

        for idx, sent in enumerate(sentences(text)):
            if not NUMBER.search(sent):
                continue
            if len(sent) > 400:
                continue
            for metric, kws in KEYWORDS.items():
                if any(kw.lower() in sent.lower() for kw in kws):
                    out.append({
                        "source_id": rec["id"],
                        "crop": rec["crop"],
                        "region": rec["region"],
                        "publisher": rec["publisher"],
                        "url": rec["url"],
                        "metric": metric,
                        "sentence_index": idx,
                        "sentence": sent,
                        "verified": False,       # nguoi kiem duyet doi thanh true
                        "reviewer": None,
                        "note": None,
                    })
                    break

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    by_metric = {}
    for c in out:
        by_metric[c["metric"]] = by_metric.get(c["metric"], 0) + 1
    print(f"Tim duoc {len(out)} cau ung vien:")
    for m, n in sorted(by_metric.items()):
        print(f"  {m}: {n}")
    print(f"\nGhi ra {OUT}. Tat ca verified=false, can nguoi doc va duyet.")


if __name__ == "__main__":
    main()
```

Chạy:

```bash
python extract.py
```

Mở `data/candidates.json`, đọc từng câu, đổi `verified` thành `true` cho câu đúng và bỏ câu sai. Đây chính là "quy trình kiểm duyệt" mà đề bài NextFarm yêu cầu ở mục 4 (Bài toán A).

> **⚠️ Đã sửa ở quy chuẩn v2.0 (DEC-020, mục 24).** Bản gốc của tài liệu này viết *"Chỉ những dòng `verified: true` mới được nạp vào vector DB"*. Câu đó mâu thuẫn với mô hình dữ liệu `Source → Document → Chunk → Embedding`, và nếu làm đúng nguyên văn thì kho tri thức chỉ còn các câu rời rạc chứa số — mất hết phần thời vụ, chọn giống, làm đất, sâu bệnh. Quy tắc hiện hành là:
>
> **Chỉ chunk thuộc tài liệu có `approved = true` mới được nạp vào vector DB. Bảng `verified_facts` là hàng rào kiểm số liệu và nguồn ground truth cho evaluation — không phải nguồn cho retrieval.**
>
> Nói cách khác có **hai luồng duyệt tách rời**: luồng retrieval duyệt ở mức *tài liệu*, luồng fact duyệt ở mức *câu*. Xem mục 24 của `docs/NEXTFARM_PROBLEM_A_STANDARD_v2.0.md`.

---

## 7. Commit và tạo Pull Request

```bash
git add crawler/ .gitignore
git commit -m "feat(crawler): thu thap tai lieu ky thuat canh tac tu nguon nha nuoc

- crawl.py: tai trang, luu van ban tho + manifest co hash va HTTP status
- extract.py: loc cau chua so lieu, danh dau verified=false cho khau kiem duyet
- sources.yaml: 7 nguon tu So NN, Khuyen nong tinh va Tong cuc Thong ke
- khong hard-code so lieu nong hoc trong code"

git push
```

Rồi mở Pull Request `feature/data-crawler` → `main` trên GitHub.

---

## 8. Những điều crawler này **chưa** làm

Ghi rõ để không nhầm lẫn về phạm vi:

- Chưa xử lý file PDF (một số sở đăng tài liệu dạng PDF, cần thêm `pypdf`).
- Chưa chunk văn bản và chưa sinh embedding — đó là bước sau.
- Chưa xử lý trang render bằng JavaScript.
- Danh sách 7 nguồn hiện tại là mẫu nhỏ; kho tri thức thật cần nhiều hơn.
- Chưa có bước kiểm tra bản quyền/điều khoản sử dụng của từng trang. Bạn nên đọc `robots.txt` của mỗi domain trước khi crawl diện rộng, và với dự án công bố công khai thì nên ghi rõ nguồn.

---

## 9. Việc tiếp theo sau khi merge

1. Chạy `crawl.py`, xem thực tế bao nhiêu nguồn tải được.
2. Duyệt `candidates.json` — đây là lúc bạn biết dữ liệu thật có bao nhiêu.
3. Từ số liệu đã duyệt, xây tập kiểm thử cho Bài toán A.
4. Rồi mới tới chunking, embedding, vector DB.

Đừng bỏ qua bước 2. Kích thước thật của kho tri thức quyết định phạm vi câu hỏi mà bot được phép trả lời — ngoài phạm vi đó, bot phải nói "không có dữ liệu".
