#!/usr/bin/env python3
"""
eval_tu_choi.py - Do TOAN BO tang tu choi deterministic tren tap kiem thu.

    python evaluation/runners/eval_tu_choi.py
    python evaluation/runners/eval_tu_choi.py --chi-tiet

DAY LA PHAN CHAY DUOC KHI CHUA CO MODEL

Chuoi xu ly day du (muc 10 quy chuan):

    cau hoi -> chuan hoa -> Intent Router -> Scope Check -> Retrieval
            -> LLM -> Grounding Validator -> tra loi / tu choi

Ba buoc dau khong can model nao. Chung cung la ba buoc chan phan lon cac ca
tu choi. File nay do dung ba buoc do, va do nghiem tuc theo ca HAI huong sai:

  tu_choi_thieu (unsafe)  cau dang le phai bi chan ma di tiep duoc
                          -> duong dan thang toi hien tuong A1/A2 cua de bai
  tu_choi_thua            cau nong hoc that bi chan lai
                          -> bot kho chiu, khong nguy hiem

Bao cao hai con so tach nhau. Gop lai thanh mot "do chinh xac" la che mat su
khac nhau ve muc nghiem trong - dung kieu lam dep so lieu ma muc 30 goi ten.

DIEU PHAI DOC KEM MOI CON SO O DAY

  1. Con thieu lop LLM few-shot cua router (muc 11.3) va toan bo Grounding
     Validator (muc 18). Case nao ba buoc deterministic khong ket luan duoc
     se dem rieng thanh "nhuong lop sau" - doc nhu "chua do duoc", khong phai
     "da dung".

  2. Nguoi viet luat va nguoi viet tap kiem thu la MOT. Con so o day vi vay
     cao hon con so tren cau hoi that, va khong dung de bao cao voi NextFarm
     nhu ty le chinh xac cua he thong. Con so bao cao duoc chi den tu C0/C1/C2
     va tu bo cau hoi do chuyen gia NextFarm cham (muc 32).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

from app.services.abstention import templates as tpl  # noqa: E402
from app.services.intent import scope  # noqa: E402
from app.services.intent.router import (  # noqa: E402
    AGRONOMY, DEVICE_CONTROL, GARDEN_DATA, PRODUCT_FEATURE, phan_loai,
)

DATASET = BASE / "evaluation" / "datasets" / "v1"

OUT_OF_SCOPE = "out_of_scope"
CAN_LAM_RO = "can_lam_ro"
DI_TIEP = "di_tiep"

NHAN_ROUTER = {
    "garden_data": GARDEN_DATA,
    "product_feature": PRODUCT_FEATURE,
    "device_control": DEVICE_CONTROL,
}
LOAI_TU_CHOI = set(NHAN_ROUTER.values()) | {OUT_OF_SCOPE}


def nap_case() -> list[dict]:
    ra = []
    for f in sorted(DATASET.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in data.get("cases") or []:
            c["group"] = data.get("group", f.stem)
            ra.append(c)
    return ra


def mong_doi(case: dict) -> str:
    """Ket qua DUNG cua tang tu choi deterministic cho mot case.

    Case answer_if_evidence phai di tiep: quyet dinh tra loi hay khong con
    phu thuoc vao co tim duoc bang chung khong, ma do la viec cua Retrieval
    va Grounding Validator - hai tang chua ton tai.
    """
    if case.get("expected_behavior") != "abstain":
        return DI_TIEP
    loai = case.get("expected_abstain_type")
    if loai in NHAN_ROUTER:
        return NHAN_ROUTER[loai]
    if loai == OUT_OF_SCOPE:
        return OUT_OF_SCOPE
    return DI_TIEP


def chay_mot_case(case: dict) -> tuple[str, str, str]:
    """Chay chuoi deterministic. Tra ve (ket qua, nguon, cau tra loi/tu choi)."""
    kq = phan_loai(case["question"], case.get("context_turns"))

    if kq.phai_tu_choi:
        cau = (tpl.garden_data(khu=kq.khu, chi_so=kq.chi_so, cay=kq.cay,
                               co_tai_lieu=False)
               if kq.nhan == GARDEN_DATA else tpl.theo_nhan(kq.nhan))
        return kq.nhan, kq.nguon, cau

    r = scope.kiem_tra(case["question"], case.get("context_turns"))
    if r.ket_luan == scope.NGOAI_PHAM_VI:
        ten = r.cay_ngoai_nhan_duoc[0] if r.cay_ngoai_nhan_duoc else None
        return OUT_OF_SCOPE, "scope", tpl.out_of_scope(ten)
    if r.ket_luan == scope.CAN_LAM_RO:
        return CAN_LAM_RO, "scope", ""
    return DI_TIEP, kq.nguon, ""


def chay(chi_tiet: bool = False) -> dict:
    cases = nap_case()
    kq = [(c,) + chay_mot_case(c) + (mong_doi(c),) for c in cases]

    phai_chan = [x for x in kq if x[4] in LOAI_TU_CHOI]
    phai_qua = [x for x in kq if x[4] == DI_TIEP]

    # can_lam_ro la mot dang tu choi hop le: bot hoi lai thay vi doan. Voi case
    # ngoai pham vi no van la hanh vi an toan, chi kem cu the hon.
    dung = [x for x in phai_chan if x[1] == x[4]]
    an_toan = [x for x in phai_chan if x[1] != x[4] and x[1] in LOAI_TU_CHOI | {CAN_LAM_RO}]
    thieu = [x for x in phai_chan if x[1] not in LOAI_TU_CHOI | {CAN_LAM_RO}]

    qua_dung = [x for x in phai_qua if x[1] == DI_TIEP]
    thua = [x for x in phai_qua if x[1] in LOAI_TU_CHOI]
    hoi_lai = [x for x in phai_qua if x[1] == CAN_LAM_RO]

    print("=" * 70)
    print("TANG TU CHOI DETERMINISTIC  |  tap kiem thu v1, " + str(len(cases)) + " case")
    print("chuan hoa -> Intent Router (lop rule) -> Scope Check")
    print("=" * 70)
    print()
    print("Case PHAI bi chan (" + str(len(phai_chan)) + ")")
    print("  chan dung loai                : " + str(len(dung)))
    print("  chan an toan nhung khac loai  : " + str(len(an_toan))
          + "   (van tu choi, mau kem cu the)")
    print("  DI TIEP DUOC                  : " + str(len(thieu))
          + "   <- tu_choi_thieu, phai bang 0")
    print()
    print("Case PHAI di tiep (" + str(len(phai_qua)) + ")")
    print("  di tiep dung                  : " + str(len(qua_dung)))
    print("  BI CHAN OAN                   : " + str(len(thua))
          + "   <- tu_choi_thua")
    print("  bi hoi lai (chua ro cay)      : " + str(len(hoi_lai))
          + "   (hoi lai la hanh vi dung khi that su khong ro)")
    print()

    theo_nhom: dict[str, list[int]] = {}
    for c, ra, _, _, m in kq:
        n = theo_nhom.setdefault(c["group"], [0, 0])
        n[0] += 1
        n[1] += int(ra == m)
    print("Theo nhom")
    for g, (tong, ok) in sorted(theo_nhom.items()):
        print("  " + g.ljust(18) + str(ok) + "/" + str(tong))
    print()

    # --- Nhom sinh bang bien doi: do HANH VI CO GIU NGUYEN khong ---
    theo_id = {c["case_id"]: (ra, m) for c, ra, _, _, m in kq}
    dan_xuat = [(c, ra) for c, ra, _, _, _ in kq if c.get("derived_from")]
    if dan_xuat:
        lech = [(c, ra, theo_id[c["derived_from"]][0]) for c, ra in dan_xuat
                if c["derived_from"] in theo_id
                and ra != theo_id[c["derived_from"]][0]]
        print("Nhom sinh bang bien doi - hanh vi co giu nguyen so voi case goc")
        print("  tong case dan xuat            : " + str(len(dan_xuat)))
        print("  giu nguyen hanh vi            : " + str(len(dan_xuat) - len(lech)))
        print("  DOI HANH VI                   : " + str(len(lech)))
        print()
        if lech:
            print("--- BIEN DANG LAM DOI HANH VI ---")
            for c, ra, goc_ra in lech:
                print("  " + c["case_id"] + " (tu " + c["derived_from"] + "): "
                      + goc_ra + " -> " + ra)
                print("      " + c["question"])
            print()

    for ten, ds in (("DI TIEP DUOC (nghiem trong)", thieu), ("BI CHAN OAN", thua)):
        if ds:
            print("--- " + ten + " ---")
            for c, ra, ng, _, m in ds:
                print("  " + c["case_id"] + " [" + c["group"] + "] mong " + m
                      + ", ra " + ra + " (" + ng + ")")
                print("      " + c["question"])
    if chi_tiet and hoi_lai:
        print("--- HOI LAI ---")
        for c, _, _, _, _ in hoi_lai:
            print("  " + c["case_id"] + ": " + c["question"])

    return {"tong": len(cases), "tu_choi_thieu": len(thieu),
            "tu_choi_thua": len(thua), "hoi_lai": len(hoi_lai)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi-tiet", action="store_true")
    a = ap.parse_args()
    r = chay(a.chi_tiet)
    sys.exit(1 if r["tu_choi_thieu"] else 0)
