#!/usr/bin/env python3
"""
review_chunks.py - Duyet le chunk RUI RO CAO (luong 3 cua DEC-020).

Quy chuan v2.0 muc 24.7 va 27.

VI SAO CAN LUONG THU BA

DEC-020 chia viec duyet lam ba luong, va day la luong duy nhat chua co cong
cu. Luong 1 (review_documents.py) duyet CA TAI LIEU. Luong 2
(review_facts.py) duyet TUNG CAU SO LIEU. Nhung mot tai lieu duoc duyet o
luong 1 van co the chua doan noi ve thuoc bao ve thuc vat - va doan do phai
duoc nguoi nhin tan mat mot lan nua truoc khi ra khoi kho.

View indexable_chunk thuc thi dieu do o TANG DU LIEU:

    d.approved = true AND c.approved = true

Chunk co is_high_risk khong duoc mac dinh approved. No nam ngoai view cho
den khi co mot dong trong chunks.yaml noi nguoc lai.

TAI SAO KHONG DUYET TU DONG

Do duoc 2026-08-21: 20 chunk rui ro cao chua duyet, va 18/18 case nhom
high_risk trong tap kiem thu deu bi tu choi vi thieu chung. Cam do la
manh - duyet het mot luot thi answer_rate tang ngay.

Nhung noi dung o day la lieu luong thuoc tru sau, nong do pha, thoi gian
cach ly. Mot chunk sai o day khong lam bot tra loi kem, no lam nguoi dung
phun sai thuoc. Do la ly do DEC-005 ton tai va la ly do file nay HOI TUNG
CAI MOT thay vi co mot co --duyet-het.

CACH DUNG
    python review_chunks.py --status
    python review_chunks.py --limit 10
    python review_chunks.py --chunk-id lua_dao_on#4
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
sys.path.insert(0, str(ROOT))

CHUNKS_YAML = BASE / "chunks.yaml"

from app.core.text import bam_chunk  # noqa: E402


def nap() -> dict:
    if not CHUNKS_YAML.exists():
        return {"chunks": []}
    return yaml.safe_load(CHUNKS_YAML.read_text(encoding="utf-8")) or {"chunks": []}


def ghi(data: dict) -> None:
    """Ghi lai ngay sau MOI quyet dinh, khong doi het phien.

    Duyet 20 chunk mat khoang mot tieng. Mat dien giua chung ma phai lam lai
    tu dau la cach chac chan nhat de lan sau nguoi duyet bam nhanh cho xong.
    """
    CHUNKS_YAML.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )


def lay_chunk_rui_ro(chunk_id: str | None = None) -> list[dict]:
    """Doc chunk rui ro cao tu DB, kem thong tin nguon de nguoi duyet doi chieu.

    Chi lay chunk thuoc tai lieu DA duyet o luong 1. Chunk cua tai lieu bi
    loai thi duyet le cung vo nghia - no van nam ngoai view.
    """
    from app.core.db import ket_noi

    sql = """
        SELECT c.chunk_id, c.text, c.section_title, c.crop, c.region,
               d.title, d.url, s.publisher, s.source_tier
        FROM chunk c
        JOIN document d USING (document_id)
        JOIN source s USING (source_id)
        WHERE c.is_high_risk AND d.approved
    """
    tham: list = []
    if chunk_id:
        sql += " AND c.chunk_id = %s"
        tham.append(chunk_id)
    sql += " ORDER BY c.chunk_id"

    with ket_noi() as c, c.cursor() as cur:
        cur.execute(sql, tham)
        cot = [d[0] for d in cur.description]
        return [dict(zip(cot, r)) for r in cur.fetchall()]


def da_quyet_dinh(data: dict) -> dict[str, dict]:
    """Khoa la sha256 NOI DUNG chunk, khong phai chunk_id.

    chunk_id chua `ordinal` nen no doi moi khi doi hang so cat chunk. Tra
    theo id thi mot quyet dinh duyet cu se de len mot doan van khac ma khong
    bao loi - xem app/core/text.py ham bam_chunk().

    Ban ghi thieu sha256 bi bo qua: khong tra cuu duoc thi chunk rui ro cao
    coi nhu CHUA duyet, va DEC-005 chan no. Hong theo huong an toan.
    """
    return {c["sha256"]: c for c in data.get("chunks") or [] if c.get("sha256")}


def in_trang_thai(data: dict) -> None:
    ds = lay_chunk_rui_ro()
    da = da_quyet_dinh(data)
    duyet = sum(1 for c in ds
                if da.get(bam_chunk(c["text"]), {}).get("approved") is True)
    loai = sum(1 for c in ds
               if da.get(bam_chunk(c["text"]), {}).get("approved") is False)
    con = len(ds) - duyet - loai
    print(f"Chunk rui ro cao (tai lieu da duyet): {len(ds)}")
    print(f"  da duyet : {duyet}")
    print(f"  da loai  : {loai}")
    print(f"  CON LAI  : {con}")
    if con:
        print(f"\n  python review_chunks.py --limit {min(con, 10)}")


CHECKLIST = """  1. Doan nay co ghi RO LIEU LUONG / NONG DO / THOI GIAN CACH LY khong,
     hay chi noi chung chung ("phun thuoc dac tri")?
  2. Con so co kem DON VI va kem DOI TUONG ap dung (cay gi, giai doan nao)?
  3. Van ban co bi cat cut giua chung lam sai nghia khong?
  4. Neu nong dan lam DUNG Y nguyen van doan nay, co an toan khong?"""


def duyet_mot(c: dict, nguoi: str) -> dict | None:
    """Hoi ve mot chunk. Tra ve ban ghi quyet dinh, hoac None neu bo qua."""
    print("\n" + "=" * 78)
    print(f"chunk_id : {c['chunk_id']}")
    print(f"tai lieu : {c['title']}")
    print(f"nguon    : {c['publisher']} (tier {c['source_tier']})  {c['url']}")
    print(f"muc      : {c['section_title'] or '(khong co)'}")
    print(f"cay/vung : {c['crop'] or '-'} / {c['region'] or '-'}")
    print("-" * 78)
    print(c["text"])
    print("-" * 78)
    print(CHECKLIST)

    while True:
        tl = input("\n  [d]uyet / [l]oai / [b]o qua / [t]hoat > ").strip().lower()
        if tl in ("t", "thoat"):
            return "THOAT"  # type: ignore[return-value]
        if tl in ("b", ""):
            return None
        if tl in ("d", "duyet"):
            note = input("  ghi chu (doan nay noi ve gi): ").strip()
            if not note:
                print("  !! phai ghi chu. Duyet ma khong noi duoc no la gi")
                print("     nghia la chua doc ky.")
                continue
            return {
                "chunk_id": c["chunk_id"],
                "sha256": bam_chunk(c["text"]),
                "approved": True,
                "note": note,
                "reviewer": nguoi,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }
        if tl in ("l", "loai"):
            ly_do = input("  ly do loai: ").strip()
            if not ly_do:
                print("  !! phai ghi ly do. Tai lieu bi loai van nam trong file -")
                print("     do la bang chung quy trinh duyet co that (muc 27).")
                continue
            return {
                "chunk_id": c["chunk_id"],
                "sha256": bam_chunk(c["text"]),
                "approved": False,
                "reject_reason": ly_do,
                "reviewer": nguoi,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }
        print("  khong hieu, go d / l / b / t")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--chunk-id")
    p.add_argument("--status", action="store_true")
    p.add_argument("--reviewer", default="")
    a = p.parse_args()

    data = nap()
    data.setdefault("chunks", [])

    if a.status:
        in_trang_thai(data)
        return 0

    ds = lay_chunk_rui_ro(a.chunk_id)
    da = da_quyet_dinh(data)
    con = [c for c in ds if bam_chunk(c["text"]) not in da]

    if not con:
        print("Khong con chunk rui ro cao nao chua duyet.")
        in_trang_thai(data)
        return 0

    nguoi = a.reviewer or input("Ten nguoi duyet: ").strip()
    if not nguoi:
        print("Phai co ten nguoi duyet - DEC-005 yeu cau truy duoc ai duyet.")
        return 1

    print(f"\nCon {len(con)} chunk chua duyet. Phien nay: {min(a.limit, len(con))}.")
    print("Ket qua luu ngay sau moi quyet dinh, thoat giua chung khong mat gi.")

    dem = 0
    for c in con[: a.limit]:
        kq = duyet_mot(c, nguoi)
        if kq == "THOAT":
            break
        if kq is None:
            continue
        data["chunks"].append(kq)
        ghi(data)
        dem += 1

    print(f"\nDa quyet dinh {dem} chunk trong phien nay.")
    if dem:
        print("Chay `make ingest` de dua thay doi vao DB.")
    in_trang_thai(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
