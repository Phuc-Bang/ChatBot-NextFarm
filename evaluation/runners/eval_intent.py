#!/usr/bin/env python3
"""
eval_intent.py - Do lop rule cua Intent Router tren tap kiem thu da dong bang.

    python evaluation/runners/eval_intent.py
    python evaluation/runners/eval_intent.py --sai      # chi in case sai

DO CAI GI

Router co hai kieu sai, va chung KHONG cung muc nghiem trong (muc 11.4):

  unsafe_misroute  cau hoi so lieu vuon / dieu khien thiet bi / tinh nang app
                   bi cho di tiep vao nhanh tra loi. Day la duong dan thang
                   toi hien tuong A1: bot tra ve mot con so trong sach, kem
                   trich dan dang hoang, trong rat dang tin. Chi so nay phai
                   bang 0.

  tu_choi_oan      cau hoi nong hoc that bi chan lai. Nguoi dung hoi lai la
                   xong. Kho chiu, khong nguy hiem.

Bao cao hai con so tach nhau, khong gop thanh mot "do chinh xac". Gop lai la
che mat su khac nhau ve muc nghiem trong - chinh la kieu bao cao ma muc 30
goi ten la lam dep so lieu.

DIEU PHAI DOC KEM MOI CON SO O DAY

  1. Day moi la LOP RULE. Lop LLM few-shot cua muc 11.3 chua ton tai (chua
     chot model, DEC-015). Case nao lop rule khong khop se roi vao nhanh
     "mac_dinh" - trong bao cao dem rieng thanh cot `nhuong_llm`. Doc cot do
     nhu "chua do duoc", khong phai "da tra loi dung".

  2. Nguoi viet luat va nguoi viet tap kiem thu la MOT. Con so o day vi vay
     cao hon con so tren cau hoi that. No dung de biet lop rule co chay
     khong, khong dung de bao cao voi NextFarm nhu ty le chinh xac.
     Con so bao cao duoc chi den tu C0/C1/C2 chay tren cau hoi cua chuyen
     gia NextFarm (muc 32).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

from app.services.intent.router import (  # noqa: E402
    AGRONOMY, DEVICE_CONTROL, GARDEN_DATA, PRODUCT_FEATURE, phan_loai,
)

DATASET = BASE / "evaluation" / "datasets" / "v1"

# Nhan router tuong ung voi expected_abstain_type cua tap kiem thu.
# out_of_scope KHONG co o day: viec chan cau hoi ngoai pham vi thuoc Scope
# Check (muc 12), chay SAU router. Voi router, mot cau hoi ve ca phe van la
# cau hoi nong hoc - no phai di tiep de Scope Check chan.
NHAN_ROUTER = {
    "garden_data": GARDEN_DATA,
    "product_feature": PRODUCT_FEATURE,
    "device_control": DEVICE_CONTROL,
}


def nap_case() -> list[dict]:
    ra = []
    for f in sorted(DATASET.glob("*.yaml")):
        if f.name == "manifest.json":
            continue
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in data.get("cases") or []:
            c["group"] = data.get("group", f.stem)
            ra.append(c)
    return ra


def mong_doi(case: dict) -> str:
    """Nhan router DUNG cho mot case.

    Moi case khong thuoc ba nhom tu choi cua router deu phai di tiep vao
    nhanh nong hoc - ke ca case ngoai pham vi va case gai bay. Chan chung o
    router la chan sai tang.
    """
    return NHAN_ROUTER.get(case.get("expected_abstain_type") or "", AGRONOMY)


def chay(chi_in_sai: bool = False) -> dict:
    cases = nap_case()
    ket_qua = []
    for c in cases:
        kq = phan_loai(c["question"], c.get("context_turns"))
        ket_qua.append((c, kq, mong_doi(c)))

    unsafe = [(c, k) for c, k, m in ket_qua
              if m in NHAN_ROUTER.values() and k.nhan == AGRONOMY]
    oan = [(c, k) for c, k, m in ket_qua
           if m == AGRONOMY and k.nhan != AGRONOMY]
    nham_mau = [(c, k, m) for c, k, m in ket_qua
                if m in NHAN_ROUTER.values()
                and k.nhan != AGRONOMY and k.nhan != m]
    nhuong = [(c, k) for c, k, m in ket_qua if k.nguon == "mac_dinh"]

    can_chan = [x for x in ket_qua if x[2] in NHAN_ROUTER.values()]
    can_qua = [x for x in ket_qua if x[2] == AGRONOMY]

    print("=" * 68)
    print("INTENT ROUTER - LOP RULE  |  tap kiem thu v1, " + str(len(cases)) + " case")
    print("=" * 68)
    print()
    print("Case phai bi chan lai (garden_data / product_feature / device_control)")
    print("  tong                      : " + str(len(can_chan)))
    print("  chan dung nhanh           : "
          + str(len(can_chan) - len(unsafe) - len(nham_mau)))
    print("  chan nhung nham mau       : " + str(len(nham_mau))
          + "   (van tu choi, chi sai template)")
    print("  LOT SANG NHANH TRA LOI    : " + str(len(unsafe))
          + "   <- unsafe_misroute, phai bang 0")
    print()
    print("Case phai di tiep (nong hoc, ngoai pham vi, gai bay)")
    print("  tong                      : " + str(len(can_qua)))
    print("  di tiep dung              : " + str(len(can_qua) - len(oan)))
    print("  bi tu choi oan            : " + str(len(oan)))
    print()
    print("Do phu cua lop rule")
    print("  luat khop, ket luan duoc  : " + str(len(cases) - len(nhuong)))
    print("  nhuong cho lop LLM        : " + str(len(nhuong))
          + "   (chua do duoc, khong phai da dung)")
    print()

    if unsafe:
        print("--- LOT SANG NHANH TRA LOI (nghiem trong) ---")
        for c, k in unsafe:
            print("  " + c["case_id"] + ": " + c["question"])
    if oan:
        print("--- TU CHOI OAN ---")
        for c, k in oan:
            print("  " + c["case_id"] + " [" + c["group"] + "] -> " + k.nhan
                  + " : " + c["question"])
            print("      bang chung: " + "; ".join(k.bang_chung))
    if nham_mau:
        print("--- NHAM MAU TU CHOI ---")
        for c, k, m in nham_mau:
            print("  " + c["case_id"] + ": mong " + m + ", ra " + k.nhan
                  + " : " + c["question"])

    if not chi_in_sai and nhuong:
        print()
        print("--- NHUONG CHO LOP LLM (" + str(len(nhuong)) + " case) ---")
        theo_nhom: dict[str, int] = {}
        for c, _ in nhuong:
            theo_nhom[c["group"]] = theo_nhom.get(c["group"], 0) + 1
        for g, n in sorted(theo_nhom.items(), key=lambda x: -x[1]):
            print("  " + g + ": " + str(n))

    return {
        "tong": len(cases),
        "unsafe_misroute": len(unsafe),
        "tu_choi_oan": len(oan),
        "nham_mau": len(nham_mau),
        "nhuong_llm": len(nhuong),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sai", action="store_true", help="chi in case sai")
    a = ap.parse_args()
    r = chay(a.sai)
    sys.exit(1 if r["unsafe_misroute"] else 0)
