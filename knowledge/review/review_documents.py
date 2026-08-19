#!/usr/bin/env python3
"""
review_documents.py - Duyet tai lieu o MUC TAI LIEU (luong 1 cua DEC-020).

Quy chuan v2.0 muc 27.2: checklist 5 cau, khoang 2-3 phut moi tai lieu.

VAI TRO CUA NGUOI DUYET (DEC-029):

    Nguoi duyet kiem CHUNG CU, khong kiem CHAN LY.

Doi 1 nguoi khong co chuyen gia nong nghiep, nen bo tieu chi "reviewer phan
dung/sai noi dung nong hoc" - khong kiem duoc. Thay bang nhung thu kiem duoc:
nguon thuoc tier nao, dung cay va vung khong, co phai tai lieu ky thuat khong,
ban crawl co sach khong.

KET QUA SONG TRONG GIT, KHONG SONG TRONG DB
Ghi ra knowledge/review/documents.yaml, duoc version control. Postgres la ban
dan xuat - dung lai duoc tu manifest.json + file nay. Lich su duyet nam trong
git history: ai duyet, khi nao, vi sao loai.

CACH DUNG
    python review_documents.py              # duyet cac tai lieu chua duyet
    python review_documents.py --status     # chi xem tinh hinh, khong hoi
    python review_documents.py --limit 10   # duyet 10 tai lieu roi nghi
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
MANIFEST = ROOT / "crawler" / "data" / "manifest.json"
TEXT = ROOT / "crawler" / "data" / "text"
OUT = BASE / "documents.yaml"

VUNG = [
    "dong_bang_song_hong", "trung_du_mien_nui", "bac_trung_bo",
    "duyen_hai_nam_trung_bo", "tay_nguyen", "dong_nam_bo",
    "dong_bang_song_cuu_long", "toan_quoc",
]


def load_reviews() -> dict[str, dict]:
    if not OUT.exists():
        return {}
    data = yaml.safe_load(OUT.read_text(encoding="utf-8")) or {}
    return {d["document_id"]: d for d in (data.get("documents") or [])}


def save_reviews(reviews: dict[str, dict]) -> None:
    docs = sorted(reviews.values(), key=lambda d: d["document_id"])
    OUT.write_text(
        yaml.safe_dump({"documents": docs}, allow_unicode=True, sort_keys=False,
                       width=100),
        encoding="utf-8")


def hoi(prompt: str, hop_le: list[str] | None = None) -> str:
    while True:
        try:
            tra_loi = input(prompt).strip()
        except EOFError:
            print("\n(khong co dau vao - dung lai)")
            sys.exit(0)
        if hop_le is None or tra_loi.lower() in hop_le:
            return tra_loi.lower()
        print("  Chi nhan: " + " / ".join(hop_le))


def duyet_mot(rec: dict, reviewer: str) -> dict:
    sid = rec["id"]
    path = TEXT / (sid + ".txt")
    text = path.read_text(encoding="utf-8") if path.exists() else ""

    print("\n" + "=" * 74)
    print(sid + "  |  " + str(rec.get("title") or "(tai lieu khong ghi title)"))
    print("  URL       : " + rec.get("url", ""))
    print("  Publisher : " + str(rec.get("publisher")))
    print("  Khai bao  : cay=" + str(rec.get("crop")) + "  vung=" + str(rec.get("region"))
          + "  tier=" + str(rec.get("source_tier")))
    print("  Do dai    : " + str(rec.get("text_length")) + " ky tu ("
          + str(rec.get("doc_type")) + ")")
    print("-" * 74)
    print(text[:900].replace("\n", " ")[:900])
    print("-" * 74)

    ket_qua = {
        "document_id": sid,
        "url": rec.get("url"),
        "reviewer": reviewer,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    # 1. Tier
    tier = hoi("  1. Nguon thuoc Tier nao? [1/2/loai]: ", ["1", "2", "loai"])
    if tier == "loai":
        return {**ket_qua, "approved": False, "reject_reason": "nguon Tier 3 hoac khong ro"}
    ket_qua["source_tier"] = int(tier)

    # 2. Dung cay trong
    if hoi("  2. Dung cay trong da khai (" + str(rec.get("crop")) + ")? [y/n]: ",
           ["y", "n"]) == "n":
        crop_moi = input("     Cay dung la gi? (bo trong = loai): ").strip()
        if not crop_moi:
            return {**ket_qua, "approved": False, "reject_reason": "sai cay trong"}
        ket_qua["crop"] = crop_moi
    else:
        ket_qua["crop"] = rec.get("crop")

    # 3. Tai lieu ky thuat hay tin tuc
    if hoi("  3. La tai lieu KY THUAT CANH TAC? (khong phai tin tuc/quang cao) [y/n]: ",
           ["y", "n"]) == "n":
        return {**ket_qua, "approved": False,
                "reject_reason": "khong phai tai lieu ky thuat canh tac"}

    # 4. Ban crawl sach
    if hoi("  4. Ban crawl co SACH? (khong dinh menu/banner/tin lien quan) [y/n]: ",
           ["y", "n"]) == "n":
        return {**ket_qua, "approved": False,
                "reject_reason": "ban crawl ban - can sua bo tach van ban roi crawl lai"}

    # 5. Vung mien va ngay ban hanh
    print("     Vung: " + ", ".join(VUNG))
    vung = input("  5a. Vung mien (Enter = giu '" + str(rec.get("region")) + "'): ").strip()
    ket_qua["region"] = vung or rec.get("region")
    ngay = input("  5b. Ngay ban hanh neu trang co ghi (YYYY-MM-DD, Enter = khong co): ").strip()
    # Khong co ngay thi de null - KHONG doan
    ket_qua["published_at"] = ngay or None

    ghi_chu = input("  Ghi chu (Enter = bo qua): ").strip()
    if ghi_chu:
        ket_qua["note"] = ghi_chu

    ket_qua["approved"] = True
    return ket_qua


def in_tinh_hinh(records: list[dict], reviews: dict[str, dict]) -> None:
    chua = [r for r in records if r["id"] not in reviews]
    duyet = [d for d in reviews.values() if d.get("approved")]
    loai = [d for d in reviews.values() if not d.get("approved")]

    print("Tai lieu crawl thanh cong : " + str(len(records)))
    print("  da duyet (approved)     : " + str(len(duyet)))
    print("  da loai                 : " + str(len(loai)))
    print("  chua duyet              : " + str(len(chua)))

    if duyet:
        theo_cay: dict[str, int] = {}
        for d in duyet:
            key = str(d.get("crop"))
            theo_cay[key] = theo_cay.get(key, 0) + 1
        print("\nTai lieu da duyet theo cay:")
        for c, n in sorted(theo_cay.items()):
            print("  " + c.ljust(14) + str(n))

    if loai:
        print("\nLy do loai:")
        for d in loai:
            print("  " + d["document_id"].ljust(30) + str(d.get("reject_reason")))


def main() -> None:
    ap = argparse.ArgumentParser(description="Duyet tai lieu theo checklist 5 cau")
    ap.add_argument("--status", action="store_true", help="Chi xem tinh hinh")
    ap.add_argument("--limit", type=int, help="Duyet toi da N tai lieu roi dung")
    ap.add_argument("--reviewer", default="", help="Ten nguoi duyet")
    args = ap.parse_args()

    if not MANIFEST.exists():
        raise SystemExit("Chua co " + str(MANIFEST) + " - chay crawl.py truoc")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = [r for r in manifest["records"] if r.get("status") == "ok"]
    reviews = load_reviews()

    if args.status:
        in_tinh_hinh(records, reviews)
        return

    reviewer = args.reviewer or input("Ten nguoi duyet: ").strip() or "khong ro"
    chua = [r for r in records if r["id"] not in reviews]
    if not chua:
        print("Khong con tai lieu nao chua duyet.")
        in_tinh_hinh(records, reviews)
        return

    if args.limit:
        chua = chua[: args.limit]

    print("Se duyet " + str(len(chua)) + " tai lieu. Ctrl+C de dung, ket qua da "
          "duyet van duoc luu.")
    try:
        for i, rec in enumerate(chua, 1):
            print("\n[" + str(i) + "/" + str(len(chua)) + "]", end="")
            reviews[rec["id"]] = duyet_mot(rec, reviewer)
            save_reviews(reviews)          # luu sau moi tai lieu, khong mat cong
    except KeyboardInterrupt:
        print("\n\nDung lai theo yeu cau. Ket qua da duyet da duoc luu.")

    print()
    in_tinh_hinh(records, reviews)
    print("\nGhi ra " + str(OUT))


if __name__ == "__main__":
    main()
