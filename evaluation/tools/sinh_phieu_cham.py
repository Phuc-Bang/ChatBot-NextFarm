#!/usr/bin/env python3
"""
Sinh bo cau hoi + phieu cham cho chuyen gia NextFarm (muc 32).

VI SAO PHAI SINH TU KET QUA THAT

De bai muc 7.3 doi chuyen gia nong nghiep cua NextFarm cham. Ho phai cham
tren cau tra loi THAT cua he thong, kem NGUON that ma he thong da dan - de
ho kiem duoc ca hai thu: noi dung co dung khong, va nguon co that su noi
dieu do khong.

Viet tay bo cau hoi roi tu dien cau tra loi "mau" vao la vo nghia: ho se
cham mot thu khong ton tai.

Vi vay cong cu nay doc thang tu ket qua C2 da chay (file .jsonl), khong
sinh them gi.

NAM TIEU CHI (muc 32)
  1. Dung dan ve nong hoc
  2. Phu hop cay trong / vung mien
  3. Day du
  4. Ro rang voi nong dan
  5. Nguon co hop ly khong

    python evaluation/tools/sinh_phieu_cham.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

import freeze                                             # noqa: E402

# Nhom co cau hoi nong hoc that. Bo qua garden_data / product_feature /
# device_control: do la cau hoi ve HE THONG, khong phai ve nong hoc, nen
# chuyen gia nong nghiep khong cham duoc.
NHOM_NONG_HOC = {
    "known_answer", "paraphrase", "no_diacritic", "typo", "local_terms",
    "high_risk", "adversarial", "insufficient_evidence",
}

TIEU_CHI = [
    ("Đúng đắn về nông học", "Thông tin có đúng không?"),
    ("Phù hợp cây / vùng", "Có đúng cây trồng và vùng miền không?"),
    ("Đầy đủ", "Có thiếu điều kiện áp dụng quan trọng nào không?"),
    ("Rõ ràng với nông dân", "Nông dân đọc có hiểu và làm theo được không?"),
    ("Nguồn hợp lý", "Nguồn dẫn có thật sự nói điều đó không?"),
]


def nap_chunk_text(chunk_ids: list[str]) -> dict[str, tuple[str, str, str, str]]:
    """chunk_id -> (nguyen van, url, tieu de, co quan)."""
    if not chunk_ids:
        return {}
    from app.core.db import ket_noi
    with ket_noi() as con, con.cursor() as cur:
        # url va title nam o bang `document`, khong phai `chunk` - phai join.
        # Chuyen gia can URL de mo tai lieu goc kiem lai, do la ca diem cua
        # tieu chi 5.
        cur.execute(
            "SELECT c.chunk_id, c.text, d.url, d.title, s.publisher "
            "FROM chunk c "
            "JOIN document d ON d.document_id = c.document_id "
            "LEFT JOIN source s ON s.source_id = d.source_id "
            "WHERE c.chunk_id = ANY(%s)", (list(chunk_ids),))
        return {r[0]: (" ".join(r[1].split()), r[2] or "",
                       r[3] or "", r[4] or "") for r in cur.fetchall()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ket-qua", help="File .jsonl cua lan chay C2")
    ap.add_argument("--so-cau", type=int, default=50,
                    help="Muc tieu 40-60 cau (muc 32)")
    ap.add_argument("--ra", default="docs/PHIEU_CHAM_CHUYEN_GIA.md")
    a = ap.parse_args()

    version = freeze.phien_ban_dang_dung()
    if a.ket_qua:
        f = Path(a.ket_qua)
    else:
        ds = sorted((BASE / "evaluation" / "results").glob("c2_" + version + "_*.jsonl"))
        if not ds:
            raise SystemExit("Chua co ket qua C2. Chay run_c2.py truoc.")
        f = ds[-1]

    rs = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()
          if x.strip()]
    print("Doc " + str(len(rs)) + " ket qua tu " + f.name)

    # Uu tien cau CO TRA LOI - do la thu chuyen gia cham duoc noi dung.
    # Nhung van giu mot phan cau BI TU CHOI: cham "tu choi co dung khong"
    # cung la mot cau hoi that, va neu chi dua cau tra loi thi bo cau hoi
    # nay se ve mot he thong khac voi he thong that.
    nong_hoc = [r for r in rs if r["group"] in NHOM_NONG_HOC]
    co_tl = [r for r in nong_hoc if not r["da_tu_choi"]]
    tu_choi = [r for r in nong_hoc if r["da_tu_choi"]]

    n_tl = min(len(co_tl), int(a.so_cau * 0.6))
    n_tc = min(len(tu_choi), a.so_cau - n_tl)
    chon = co_tl[:n_tl] + tu_choi[:n_tc]
    print("Chon " + str(len(chon)) + " cau: " + str(n_tl) + " co tra loi, "
          + str(n_tc) + " bi tu choi")

    moi_chunk = {c for r in chon for c in (r.get("nguon") or [])}
    text = nap_chunk_text(sorted(moi_chunk))

    d: list[str] = []
    a_ = d.append
    a_("# Phiếu chấm cho chuyên gia nông nghiệp NextFarm")
    a_("")
    a_("> **Tập kiểm thử:** " + version + " · **Nguồn:** `" + f.name + "`")
    a_("> Cấu hình đo: C2 (RAG + guardrail) — cấu hình sản phẩm của PoC")
    a_("")
    a_("## Cách chấm")
    a_("")
    a_("Mỗi câu chấm **5 tiêu chí, thang 1–5**:")
    a_("")
    a_("| # | Tiêu chí | Câu hỏi tự đặt khi chấm |")
    a_("|---|---|---|")
    for i, (ten, hoi) in enumerate(TIEU_CHI, 1):
        a_("| " + str(i) + " | " + ten + " | " + hoi + " |")
    a_("")
    a_("**Thang điểm:** 1 = sai/không dùng được · 3 = tạm được · 5 = tốt")
    a_("")
    a_("Với câu hệ thống **từ chối trả lời**, chỉ chấm tiêu chí 1 theo nghĩa")
    a_("*\"từ chối như vậy có đúng không\"* — nếu kho tài liệu thật sự không có")
    a_("căn cứ thì từ chối là **đúng**, cho điểm cao.")
    a_("")
    a_("> **Xin đừng bỏ qua phần nguồn.** Nguyên văn đoạn tài liệu hệ thống đã")
    a_("> dẫn được in kèm bên dưới mỗi câu. Tiêu chí 5 chính là để kiểm xem")
    a_("> nguồn đó **có thật sự nói điều đó không** — đây là chỗ dễ sai nhất")
    a_("> của mọi hệ thống RAG.")
    a_("")
    a_("---")
    a_("")

    for i, r in enumerate(chon, 1):
        a_("## Câu " + str(i))
        a_("")
        a_("**Hỏi:** " + r["question"])
        a_("")
        if r["da_tu_choi"]:
            a_("**Hệ thống TỪ CHỐI** (lý do máy ghi: `"
               + str(r["ly_do"]) + "`)")
            a_("")
            a_("> " + r["answer"].replace("\n", " "))
        else:
            a_("**Trả lời:**")
            a_("")
            a_("> " + r["answer"].replace("\n", "\n> "))
        a_("")

        ng = r.get("nguon") or []
        if ng:
            a_("**Nguồn hệ thống đã dẫn:**")
            a_("")
            for cid in ng:
                t = text.get(cid)
                if not t:
                    a_("- `" + cid + "` — *không đọc được nội dung*")
                    continue
                noi_dung, url, tieu_de, co_quan = t
                a_("- **" + (tieu_de or cid) + "**"
                   + (" — " + co_quan if co_quan else ""))
                if url:
                    a_("  " + url)
                a_("  > " + noi_dung[:600]
                   + ("…" if len(noi_dung) > 600 else ""))
            a_("")

        a_("| Tiêu chí | 1 | 2 | 3 | 4 | 5 |")
        a_("|---|---|---|---|---|---|")
        for ten, _ in TIEU_CHI:
            a_("| " + ten + " | ☐ | ☐ | ☐ | ☐ | ☐ |")
        a_("")
        a_("**Nhận xét:**")
        a_("")
        a_("---")
        a_("")

    a_("## Tổng kết (người chấm điền)")
    a_("")
    a_("| | |")
    a_("|---|---|")
    a_("| Người chấm | |")
    a_("| Đơn vị / chuyên môn | |")
    a_("| Ngày chấm | |")
    a_("| Điểm trung bình 5 tiêu chí | |")
    a_("| Số câu có sai sót nghiêm trọng | |")
    a_("")
    a_("**Nhận xét chung:**")
    a_("")
    a_("**Điều nguy hiểm nhất anh/chị thấy (nếu có):**")
    a_("")

    out = BASE / a.ra
    out.write_text("\n".join(d), encoding="utf-8")
    print("Ghi ra " + str(out) + " (" + str(len(chon)) + " câu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
