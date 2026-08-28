#!/usr/bin/env python3
"""
freeze.py - Kiem tra luoc do va DONG BANG tap kiem thu.

DEC-023, quy chuan v2.0 muc 28:

    Tap kiem thu phai duoc xay va DONG BANG truoc khi bat dau toi uu
    retrieval, prompt hay model.

Neu vua sua he thong vua sua de thi thi moi con so "cai thien" deu vo nghia,
va khong tra loi duoc cau hoi "cai gi lam no tot len" - ma do chinh la thu
de bai muc 6 cau 2 hoi.

Muon them case moi -> tao PHIEN BAN MOI, chay lai toan bo cau hinh cu tren
phien ban moi de so sanh cong bang. KHONG sua tai cho.

CACH DUNG
    python freeze.py --check       # chi kiem tra luoc do, khong ghi
    python freeze.py               # kiem tra roi ghi manifest.json
    python freeze.py --verify      # so hash hien tai voi manifest da luu
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent
DATASETS = BASE / "datasets"

HANH_VI = {"answer", "abstain", "answer_if_evidence"}

# Bon ly do tu choi phai phan biet duoc voi nhau. Tu choi dung nhung noi sai
# ly do van la trai nghiem te - do bang abstain_type_accuracy (muc 30.5).
LY_DO_TU_CHOI = {
    "garden_data", "product_feature", "device_control",
    "out_of_scope", "insufficient_evidence",
}

KHOA_HOP_LE = {
    "case_id", "question", "context_turns", "expected_behavior",
    "expected_abstain_type", "expected_facts", "must_not_contain_number",
    "must_not_claim_action", "source_of_truth", "note", "crop", "tags",
    # case_id cua case goc, cho cac nhom sinh bang bien doi (no_diacritic,
    # typo, paraphrase). Co truong nay thi do duoc dieu thuc su can do:
    # hanh vi co GIU NGUYEN so voi case goc hay khong - thay vi so voi mot
    # ky vong chep tay, vi chep tay se troi.
    "derived_from",
    # Cau tra loi BAT BUOC kem cau canh bao (muc 19 case C4). Cung ho voi
    # must_not_contain_number va must_not_claim_action: mot khang dinh ve
    # hanh vi, cham duoc tu dong.
    "must_have_caution",
}
KHOA_BAT_BUOC = {"case_id", "question", "expected_behavior"}


def kiem_tra_file(path: Path, da_thay_id: dict[str, str]) -> list[str]:
    loi: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    if data.get("group") != path.stem:
        loi.append(path.name + ": truong 'group' (" + str(data.get("group"))
                   + ") khong khop ten file")
    if not data.get("version"):
        loi.append(path.name + ": thieu truong 'version'")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        loi.append(path.name + ": khong co case nao")
        return loi

    for i, case in enumerate(cases):
        nhan = path.name + " case #" + str(i + 1)
        if not isinstance(case, dict):
            loi.append(nhan + ": khong phai mot muc hop le")
            continue

        thieu = KHOA_BAT_BUOC - set(case)
        if thieu:
            loi.append(nhan + ": thieu truong " + ", ".join(sorted(thieu)))

        la = set(case) - KHOA_HOP_LE
        if la:
            loi.append(nhan + " (" + str(case.get("case_id")) + "): truong la "
                       + ", ".join(sorted(la)))

        cid = case.get("case_id")
        if cid in da_thay_id:
            loi.append(nhan + ": case_id '" + str(cid) + "' trung voi "
                       + da_thay_id[cid])
        elif cid:
            da_thay_id[cid] = path.name

        hv = case.get("expected_behavior")
        if hv not in HANH_VI:
            loi.append(nhan + " (" + str(cid) + "): expected_behavior khong hop le: "
                       + str(hv))

        ly_do = case.get("expected_abstain_type")
        if hv == "abstain":
            if ly_do not in LY_DO_TU_CHOI:
                loi.append(nhan + " (" + str(cid) + "): abstain phai co "
                           "expected_abstain_type thuoc " + str(sorted(LY_DO_TU_CHOI)))
        elif ly_do not in (None, "null"):
            loi.append(nhan + " (" + str(cid) + "): khong abstain thi khong duoc "
                       "dat expected_abstain_type")

        ct = case.get("context_turns")
        if ct is not None and (not isinstance(ct, list)
                               or not all(isinstance(x, str) for x in ct)):
            loi.append(nhan + " (" + str(cid) + "): context_turns phai la danh sach chuoi")

    return loi


def bam_file(path: Path) -> str:
    # Bam theo NOI DUNG, khong theo byte tho.
    #
    # SUA 2026-08-28. Ban cu la `hashlib.sha256(path.read_bytes())`. No bam ca
    # ky tu ket thuc dong, nen cung mot file cho hai ma bam khac nhau giua may
    # Windows (CRLF) va runner Linux (LF) - xem .gitattributes.
    #
    # Hau qua that: test_eval_frozen bao "file da bi sua sau khi dong bang" cho
    # ca ba phien ban tren MOI lan chay CI, trong khi khong ai sua gi. Bo canh
    # keu oan lien tuc thi mat tac dung canh gac.
    #
    # Chuan hoa CRLF/CR -> LF truoc khi bam. Ket thuc dong khong phai noi dung
    # cua mot case kiem thu; sua mot con so trong case VAN doi ma bam.
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def phien_ban_dang_dung() -> str:
    """Phien ban tap kiem thu DANG DUNG de do - phien ban da dong bang moi nhat.

    DEC-023 cam sua tap kiem thu tai cho, nen mot loi phat hien ra sau khi
    dong bang chi sua duoc bang cach cat phien ban moi. Cac phien ban cu
    KHONG bi xoa: chung la bang chung cua quy trinh (muc 27.2) va la thu cho
    NextFarm thay VI SAO quy chuan cam dung LLM sinh dap an.

    Hau qua: phien ban cu van con loi da biet trong do, va do la co y. Moi
    kiem tra chat luong vi vay phai chay tren phien ban dang dung, khong phai
    tren toan bo thu muc datasets/.
    """
    # Sap theo SO, khong theo ten: sap theo ten thi v10 dung truoc v2 va
    # he thong se lang le do tren mot tap kiem thu cu.
    def khoa(ten: str):
        so = re.match(r"v(\d+)$", ten)
        return (0, int(so.group(1))) if so else (1, 0, ten)

    co = sorted((d.name for d in DATASETS.iterdir()
                 if d.is_dir() and (d / "manifest.json").exists()), key=khoa)
    if not co:
        raise SystemExit("Chua co phien ban nao duoc dong bang")
    return co[-1]


def thu_thap(version_dir: Path) -> list[Path]:
    return sorted(p for p in version_dir.glob("*.yaml") if p.name != "manifest.json")


def main() -> None:
    ap = argparse.ArgumentParser(description="Kiem tra va dong bang tap kiem thu")
    ap.add_argument("--version", default="v1", help="Thu muc phien ban, mac dinh v1")
    ap.add_argument("--check", action="store_true", help="Chi kiem tra luoc do")
    ap.add_argument("--verify", action="store_true",
                    help="So hash hien tai voi manifest da luu")
    args = ap.parse_args()

    vdir = DATASETS / args.version
    if not vdir.is_dir():
        raise SystemExit("Khong tim thay " + str(vdir))

    files = thu_thap(vdir)
    if not files:
        raise SystemExit("Khong co file nhom nao trong " + str(vdir))

    # 1. Kiem tra luoc do
    da_thay_id: dict[str, str] = {}
    tat_ca_loi: list[str] = []
    for f in files:
        tat_ca_loi.extend(kiem_tra_file(f, da_thay_id))

    if tat_ca_loi:
        print("LUOC DO KHONG HOP LE - " + str(len(tat_ca_loi)) + " loi:")
        for l in tat_ca_loi:
            print("  - " + l)
        sys.exit(1)

    # 2. Thong ke
    tong = 0
    theo_nhom: dict[str, int] = {}
    theo_hanh_vi: dict[str, int] = {}
    theo_ly_do: dict[str, int] = {}
    for f in files:
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        cases = data["cases"]
        theo_nhom[data["group"]] = len(cases)
        tong += len(cases)
        for c in cases:
            hv = c["expected_behavior"]
            theo_hanh_vi[hv] = theo_hanh_vi.get(hv, 0) + 1
            if hv == "abstain":
                ld = c["expected_abstain_type"]
                theo_ly_do[ld] = theo_ly_do.get(ld, 0) + 1

    print("Luoc do hop le. " + str(len(files)) + " nhom, " + str(tong) + " case.")
    print("\nTheo nhom:")
    for g, n in sorted(theo_nhom.items()):
        print("  " + g.ljust(24) + str(n))
    print("\nTheo hanh vi mong doi:")
    for h, n in sorted(theo_hanh_vi.items()):
        print("  " + h.ljust(24) + str(n))
    if theo_ly_do:
        print("\nLy do tu choi:")
        for l, n in sorted(theo_ly_do.items()):
            print("  " + l.ljust(24) + str(n))

    # 3. Hash
    hashes = {f.name: bam_file(f) for f in files}
    tong_hop = hashlib.sha256(
        "\n".join(name + ":" + h for name, h in sorted(hashes.items())).encode()
    ).hexdigest()

    manifest_path = vdir / "manifest.json"

    if args.check:
        print("\n(--check: khong ghi manifest)")
        return

    if args.verify:
        if not manifest_path.exists():
            raise SystemExit("Chua co manifest de doi chieu: " + str(manifest_path))
        cu = json.loads(manifest_path.read_text(encoding="utf-8"))
        if cu.get("combined_sha256") != tong_hop:
            print("\nTAP KIEM THU DA BI SUA SAU KHI DONG BANG.")
            for name, h in sorted(hashes.items()):
                truoc = cu.get("files", {}).get(name)
                if truoc != h:
                    print("  " + name + ": " + str(truoc)[:12] + " -> " + h[:12])
            for name in set(cu.get("files", {})) - set(hashes):
                print("  " + name + ": DA BI XOA")
            sys.exit(1)
        print("\nHash khop manifest. Tap kiem thu con nguyen ven.")
        return

    manifest_path.write_text(
        json.dumps({
            "version": args.version,
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "total_cases": tong,
            "groups": theo_nhom,
            "files": hashes,
            "combined_sha256": tong_hop,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8")

    print("\nDa dong bang: " + str(manifest_path))
    print("combined_sha256 = " + tong_hop)
    print("\nTu day KHONG sua file nao trong " + args.version + " nua.")
    print("Muon them case -> tao thu muc phien ban moi.")


if __name__ == "__main__":
    main()
