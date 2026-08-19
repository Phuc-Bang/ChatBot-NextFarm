#!/usr/bin/env python3
"""
load.py - Nap kho tri thuc vao PostgreSQL.

POSTGRES LA BAN DAN XUAT (quy chuan v2.0 muc 25, ghi chu thiet ke o §4 ke hoach)

Nguon su that nam trong git:
    crawler/data/manifest.json          <- bang chung crawl
    crawler/data/text/*.txt             <- van ban da tach
    knowledge/review/documents.yaml     <- ket qua duyet muc tai lieu (luong 1)
    knowledge/review/facts.yaml         <- ket qua duyet muc cau   (luong 2)

Mat DB thi chay lai lenh nay la co lai. Mat cong duyet thi khong lay lai duoc,
nen cong duyet phai nam trong git chu khong nam trong DB.

TAI LIEU CHUA DUYET VAN DUOC NAP, voi approved=false.
Ly do: tai lieu bi loai la BANG CHUNG cho thay quy trinh duyet co that. Cong
chan la view indexable_chunk, khong phai viec giau du lieu di.

CACH DUNG
    python knowledge/ingestion/load.py            # nap/cap nhat
    python knowledge/ingestion/load.py --rebuild  # xoa sach roi nap lai
    python knowledge/ingestion/load.py --status   # xem tinh hinh trong DB
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "knowledge" / "chunking"))
import chunker  # noqa: E402

MANIFEST = ROOT / "crawler" / "data" / "manifest.json"
TEXT = ROOT / "crawler" / "data" / "text"
DOC_REVIEW = ROOT / "knowledge" / "review" / "documents.yaml"
FACT_REVIEW = ROOT / "knowledge" / "review" / "facts.yaml"

DEFAULT_DSN = "postgresql://nextfarm:nextfarm@localhost:15432/nextfarm"
CAY_HOP_LE = {"lua", "ca_chua", "dua_chuot"}


def dsn() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DSN).replace(
        "postgresql+psycopg://", "postgresql://")


def ma_source(publisher: str) -> str:
    """Sinh source_id on dinh tu ten co quan."""
    s = publisher.replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s[:60] or "khong_ro"


def doc_yaml(path: Path, khoa: str) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    muc = data.get(khoa) or []
    if khoa == "documents":
        return {d["document_id"]: d for d in muc}
    return {f["fact_key"]: f for f in muc}


def nap(conn, rebuild: bool) -> dict[str, int]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ban_ghi = [r for r in manifest["records"] if r.get("status") == "ok"]
    duyet_doc = doc_yaml(DOC_REVIEW, "documents")
    duyet_fact = doc_yaml(FACT_REVIEW, "facts")
    tu_khoa_rui_ro, tu_khoa_canh_bao = chunker.tai_tu_khoa_rui_ro()

    dem = {"source": 0, "document": 0, "chunk": 0, "chunk_rui_ro": 0,
           "chunk_canh_bao": 0, "fact": 0, "bo_qua": 0}

    with conn.cursor() as cur:
        if rebuild:
            # Thu tu xoa theo rang buoc khoa ngoai
            cur.execute("TRUNCATE fact, embedding, chunk, document, source CASCADE")

        for rec in ban_ghi:
            crop = rec.get("crop")
            if crop not in CAY_HOP_LE:
                print("[bo qua] " + rec["id"] + ": cay ngoai pham vi (" + str(crop) + ")")
                dem["bo_qua"] += 1
                continue

            path = TEXT / (rec["id"] + ".txt")
            if not path.exists():
                print("[bo qua] " + rec["id"] + ": thieu file van ban")
                dem["bo_qua"] += 1
                continue

            # --- source ---
            pub = rec.get("publisher") or "khong ro"
            sid = ma_source(pub)
            cur.execute(
                "INSERT INTO source (source_id, publisher, base_url, source_tier) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (source_id) DO NOTHING",
                (sid, pub, None, int(rec.get("source_tier") or 1)))
            dem["source"] += cur.rowcount

            # --- document ---
            dr = duyet_doc.get(rec["id"], {})
            approved = bool(dr.get("approved"))
            cur.execute(
                """
                INSERT INTO document (document_id, source_id, url, title, crop,
                    region, published_at, crawled_at, http_status, content_hash,
                    raw_path, text_path, doc_type, approved, reviewer, reviewed_at,
                    reject_reason)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (document_id) DO UPDATE SET
                    approved = EXCLUDED.approved,
                    region = EXCLUDED.region,
                    published_at = EXCLUDED.published_at,
                    reviewer = EXCLUDED.reviewer,
                    reviewed_at = EXCLUDED.reviewed_at,
                    reject_reason = EXCLUDED.reject_reason,
                    version = document.version + 1
                """,
                (rec["id"], sid, rec["url"], rec.get("title"),
                 dr.get("crop") or crop,
                 dr.get("region") or rec.get("region"),
                 dr.get("published_at"),          # None neu khong co - khong doan
                 rec["fetched_at"], rec.get("http_status"), rec.get("sha256"),
                 rec.get("raw_file"), rec.get("text_file"),
                 rec.get("doc_type", "html"), approved,
                 dr.get("reviewer"), dr.get("reviewed_at"), dr.get("reject_reason")))
            dem["document"] += 1

            # --- chunk ---
            cur.execute("DELETE FROM chunk WHERE document_id = %s", (rec["id"],))
            for c in chunker.cat(path.read_text(encoding="utf-8"),
                                 tu_khoa_rui_ro, tu_khoa_canh_bao):
                # Chunk rui ro cao nap vao voi approved=false, cho duyet le
                # tung chunk (muc 24.4). Rang buoc trong luoc do se chan neu ai
                # do co dat approved=true ma chua duyet.
                cur.execute(
                    "INSERT INTO chunk (chunk_id, document_id, ordinal, text, "
                    "text_unaccent, token_count, section_title, crop, region, "
                    "is_high_risk, needs_caution, reviewed_high_risk, approved) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE,%s)",
                    (rec["id"] + "#" + str(c.ordinal), rec["id"], c.ordinal,
                     c.text, c.text_unaccent, len(c.text.split()),
                     c.section_title, dr.get("crop") or crop,
                     dr.get("region") or rec.get("region"),
                     c.is_high_risk, c.needs_caution, not c.is_high_risk))
                dem["chunk"] += 1
                if c.is_high_risk:
                    dem["chunk_rui_ro"] += 1
                if c.needs_caution:
                    dem["chunk_canh_bao"] += 1

        # --- fact ---
        for f in duyet_fact.values():
            did = f.get("source_id")
            if not did:
                continue
            cur.execute(
                """
                INSERT INTO fact (document_id, sentence_index, sentence, crop,
                    region, metric, value_min, value_max, unit, stage, high_risk,
                    verified, reviewer, reviewed_at, note)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (document_id, sentence_index) DO UPDATE SET
                    verified = EXCLUDED.verified,
                    value_min = EXCLUDED.value_min,
                    value_max = EXCLUDED.value_max,
                    unit = EXCLUDED.unit,
                    stage = EXCLUDED.stage,
                    reviewer = EXCLUDED.reviewer,
                    reviewed_at = EXCLUDED.reviewed_at,
                    note = EXCLUDED.note
                """,
                (did, f["sentence_index"], f["sentence"], f.get("crop"),
                 f.get("region"), f["metric"], f.get("value_min"),
                 f.get("value_max"), f.get("unit"), f.get("stage"),
                 bool(f.get("high_risk")), bool(f.get("verified")),
                 f.get("reviewer"), f.get("reviewed_at"), f.get("note")))
            dem["fact"] += 1

    conn.commit()
    return dem


def in_tinh_hinh(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
              (SELECT count(*) FROM source),
              (SELECT count(*) FROM document),
              (SELECT count(*) FROM document WHERE approved),
              (SELECT count(*) FROM chunk),
              (SELECT count(*) FROM chunk WHERE is_high_risk),
              (SELECT count(*) FROM chunk WHERE needs_caution),
              (SELECT count(*) FROM indexable_chunk),
              (SELECT count(*) FROM fact),
              (SELECT count(*) FROM fact WHERE verified)
        """)
        s, d, da, c, cr, cc, ic, f, fv = cur.fetchone()

    print("source                    : " + str(s))
    print("document                  : " + str(d) + " (da duyet: " + str(da) + ")")
    print("chunk                     : " + str(c) + " (rui ro cao: " + str(cr)
          + ", can canh bao: " + str(cc) + ")")
    print("chunk INDEX DUOC          : " + str(ic))
    print("fact                      : " + str(f) + " (da xac nhan: " + str(fv) + ")")

    if ic == 0 and c > 0:
        print("\n=> Chua chunk nao index duoc vi chua tai lieu nao duoc duyet.")
        print("   Day la hanh vi DUNG cua DEC-005: khong duyet thi khong vao KB.")
        print("   Chay: python knowledge/review/review_documents.py")


def main() -> None:
    ap = argparse.ArgumentParser(description="Nap kho tri thuc vao PostgreSQL")
    ap.add_argument("--rebuild", action="store_true", help="Xoa sach roi nap lai")
    ap.add_argument("--status", action="store_true", help="Chi xem tinh hinh")
    args = ap.parse_args()

    try:
        import psycopg
    except ImportError:
        sys.exit("Thieu psycopg. Chay: pip install -r requirements.txt")

    if not MANIFEST.exists():
        sys.exit("Chua co " + str(MANIFEST) + " - chay crawler truoc")

    with psycopg.connect(dsn()) as conn:
        if args.status:
            in_tinh_hinh(conn)
            return

        dem = nap(conn, args.rebuild)
        print("\nDa nap:")
        for k, v in dem.items():
            print("  " + k.ljust(16) + str(v))
        print()
        in_tinh_hinh(conn)


if __name__ == "__main__":
    main()
