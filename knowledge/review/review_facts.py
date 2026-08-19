#!/usr/bin/env python3
"""
review_facts.py - Duyet so lieu o MUC CAU (luong 2 cua DEC-020).

Quy chuan v2.0 muc 27.3.

CAU DUYET O DAY KHONG DI VAO VECTOR DB.

Bang verified_facts phuc vu ba viec khac (muc 24.5):
  a) Kiem so lieu deterministic o Grounding Validator tang 2
  b) Ground truth cho tap kiem thu - dap an do NGUOI xac nhan, khong phai
     do LLM sinh. Day la cach duy nhat de tap kiem thu khong bi nhiem chinh
     hallucination ma no dang do
  c) Phat hien mau thuan giua cac nguon

CHIA NHO DUOC
Doi 1 nguoi, ngan sach duyet toan bo KB la khoang 10 gio (muc 27.4). Dung
--limit de duyet tung dot, ket qua luu ngay sau moi cau.

NGUYEN TAC DIEN GIA TRI
Dien value_min / value_max / unit / stage tu NGUYEN VAN cau, khong suy dien,
khong quy doi don vi. Cau khong du ngu canh de biet so nay ap cho cai gi ->
tu choi duyet, ghi ly do.

CACH DUNG
    python review_facts.py --limit 30
    python review_facts.py --status
    python review_facts.py --metric ph --limit 10
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
CANDIDATES = ROOT / "crawler" / "data" / "candidates.json"
OUT = BASE / "facts.yaml"


def khoa(c: dict) -> str:
    """Khoa on dinh cho mot cau ung vien."""
    return c["source_id"] + "#" + str(c["sentence_index"])


def load_facts() -> dict[str, dict]:
    if not OUT.exists():
        return {}
    data = yaml.safe_load(OUT.read_text(encoding="utf-8")) or {}
    return {f["fact_key"]: f for f in (data.get("facts") or [])}


def save_facts(facts: dict[str, dict]) -> None:
    rows = sorted(facts.values(), key=lambda f: f["fact_key"])
    OUT.write_text(
        yaml.safe_dump({"facts": rows}, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8")


def nhap(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        print("\n(khong co dau vao - dung lai)")
        sys.exit(0)


def duyet_mot(c: dict, reviewer: str) -> dict:
    print("\n" + "=" * 74)
    if c.get("high_risk"):
        print("  *** NOI DUNG RUI RO CAO - doc ky, thieu dieu kien ap dung thi KHONG duyet ***")
    print("  Chi so : " + c["metric"] + "   |   Cay: " + str(c.get("crop"))
          + "   |   Vung: " + str(c.get("region")))
    print("  Nguon  : " + str(c.get("publisher")) + " (tier " + str(c.get("source_tier")) + ")")
    print("  " + c.get("url", "")[:100])
    print("-" * 74)
    print("  CAU     : " + c["sentence"])
    print("-" * 74)
    print("  NGU CANH: " + (c.get("context_hint") or "")[:400])
    print("-" * 74)

    kq = {
        "fact_key": khoa(c),
        "source_id": c["source_id"],
        "sentence_index": c["sentence_index"],
        "sentence": c["sentence"],
        "crop": c.get("crop"),
        "region": c.get("region"),
        "metric": c["metric"],
        "url": c.get("url"),
        "high_risk": bool(c.get("high_risk")),
        "reviewer": reviewer,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    while True:
        chon = nhap("  [y] duyet  [n] loai  [s] bo qua lan nay  [q] dung: ").lower()
        if chon in ("y", "n", "s", "q"):
            break

    if chon == "q":
        raise KeyboardInterrupt
    if chon == "s":
        return {}
    if chon == "n":
        kq["verified"] = False
        kq["note"] = nhap("  Ly do loai: ") or "khong ghi ly do"
        return kq

    # Duyet - dien gia tri tu NGUYEN VAN
    print("  Dien tu nguyen van cau tren. Khong suy dien, khong quy doi don vi.")
    kq["value_min"] = nhap("  value_min (Enter = bo trong): ") or None
    kq["value_max"] = nhap("  value_max (Enter = bo trong): ") or None
    kq["unit"] = nhap("  unit      (vd: pH, %, kg/ha, do C): ") or None
    kq["stage"] = nhap("  stage     (giai doan ap dung, Enter = khong ghi): ") or None
    ghi_chu = nhap("  Ghi chu   (Enter = bo qua): ")
    if ghi_chu:
        kq["note"] = ghi_chu
    kq["verified"] = True
    return kq


def in_tinh_hinh(cands: list[dict], facts: dict[str, dict]) -> None:
    duyet = [f for f in facts.values() if f.get("verified")]
    loai = [f for f in facts.values() if f.get("verified") is False]
    chua = [c for c in cands if khoa(c) not in facts]

    print("Cau ung vien        : " + str(len(cands)))
    print("  da xac nhan       : " + str(len(duyet)))
    print("  da loai           : " + str(len(loai)))
    print("  chua duyet        : " + str(len(chua)))

    if duyet:
        theo: dict[str, int] = {}
        for f in duyet:
            k = str(f.get("crop")) + " / " + f["metric"]
            theo[k] = theo.get(k, 0) + 1
        print("\nFact da xac nhan:")
        for k, n in sorted(theo.items()):
            print("  " + k.ljust(28) + str(n))

    rui_ro = [c for c in cands if c.get("high_risk") and khoa(c) not in facts]
    if rui_ro:
        print("\nCon " + str(len(rui_ro)) + " cau rui ro cao chua duyet.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Duyet so lieu theo tung cau")
    ap.add_argument("--status", action="store_true", help="Chi xem tinh hinh")
    ap.add_argument("--limit", type=int, help="Duyet toi da N cau roi dung")
    ap.add_argument("--metric", nargs="*", help="Chi duyet cac chi so nay")
    ap.add_argument("--crop", nargs="*", help="Chi duyet cac cay nay")
    ap.add_argument("--high-risk", action="store_true", help="Chi duyet cau rui ro cao")
    ap.add_argument("--reviewer", default="", help="Ten nguoi duyet")
    args = ap.parse_args()

    if not CANDIDATES.exists():
        raise SystemExit("Chua co " + str(CANDIDATES) + " - chay extract.py truoc")

    cands = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    facts = load_facts()

    if args.status:
        in_tinh_hinh(cands, facts)
        return

    chon = [c for c in cands if khoa(c) not in facts]
    if args.metric:
        chon = [c for c in chon if c["metric"] in set(args.metric)]
    if args.crop:
        chon = [c for c in chon if c.get("crop") in set(args.crop)]
    if args.high_risk:
        chon = [c for c in chon if c.get("high_risk")]
    if args.limit:
        chon = chon[: args.limit]

    if not chon:
        print("Khong con cau nao phu hop de duyet.")
        in_tinh_hinh(cands, facts)
        return

    reviewer = args.reviewer or nhap("Ten nguoi duyet: ") or "khong ro"
    print("Se duyet " + str(len(chon)) + " cau. [q] hoac Ctrl+C de dung, "
          "ket qua da duyet van duoc luu.")

    try:
        for i, c in enumerate(chon, 1):
            print("\n[" + str(i) + "/" + str(len(chon)) + "]", end="")
            kq = duyet_mot(c, reviewer)
            if kq:
                facts[kq["fact_key"]] = kq
                save_facts(facts)          # luu sau moi cau
    except KeyboardInterrupt:
        print("\n\nDung lai. Ket qua da duyet da duoc luu.")

    print()
    in_tinh_hinh(cands, facts)
    print("\nGhi ra " + str(OUT))


if __name__ == "__main__":
    main()
