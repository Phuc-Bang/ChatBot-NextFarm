#!/usr/bin/env python3
"""
Duong risk-coverage (muc 30.4) - chot nguong tu choi BANG SO, khong bang
cam tinh.

Y TUONG

Moi cau tra loi co mot diem tin cay. Dat nguong tau: chi tra loi khi diem
>= tau, con lai tu choi. Tau cang cao thi:

    coverage (ty le tra loi)      GIAM
    risk (ty le tra loi SAI)      GIAM

Quet tau, ve quan he giua hai duong do, roi chon diem coverage CAO NHAT ma
risk van ~0. Do la nguong.

Khong lam the thi nguong den tu cam tinh, va "he thong tu choi bao nhieu
la vua" tro thanh y kien chu khong phai so do.

HAI NGUON DIEM

    diem_cao_nhat       diem RRF cua chunk tot nhat (truy xuat co chac khong)
    intent_do_tin_cay   do tin cay cua Intent Router (phan loai co chac khong)

Do rieng tung cai: chung tra loi hai cau hoi khac nhau, va muc 11.4 doi mot
nguong cho router con muc 14.6 doi mot nguong cho truy xuat.

    python evaluation/runners/risk_coverage.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

import yaml                                                # noqa: E402

import freeze                                              # noqa: E402
from metrics.cham import cham_mot                          # noqa: E402


def nap_case(version: str) -> dict[str, dict]:
    ra = {}
    for f in sorted((BASE / "evaluation" / "datasets" / version).glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in d.get("cases") or []:
            c["group"] = d.get("group", f.stem)
            ra[c["case_id"]] = c
    return ra


def quet(rs: list[dict], cases: dict, truong: str) -> list[tuple]:
    """Tra ve [(tau, coverage, risk, so_tra_loi, so_sai)]."""
    # Chi xet case CO tra loi va CO diem. Case bi chan som (Intent Router,
    # Scope Check) khong co diem truy xuat - chung khong nam tren duong nay.
    co_diem = [r for r in rs
               if not r.get("loi") and r.get(truong) is not None]
    if not co_diem:
        return []

    diem = sorted({float(r[truong]) for r in co_diem})
    # Them mot nguong duoi tat ca de co diem "tra loi het"
    moc = [diem[0] - 1e-9] + diem

    ra = []
    for tau in moc:
        tra_loi = so_sai = 0
        for r in co_diem:
            if float(r[truong]) < tau:
                continue                # duoi nguong -> tu choi
            if r.get("da_tu_choi"):
                continue                # he thong da tu choi vi ly do khac
            tra_loi += 1
            cs = cases.get(r["case_id"])
            if not cs:
                continue
            k = cham_mot(cs, r["answer"])
            if k.dung is False:
                so_sai += 1
        n = len(co_diem)
        ra.append((tau, 100.0 * tra_loi / n,
                   (100.0 * so_sai / tra_loi) if tra_loi else 0.0,
                   tra_loi, so_sai))
    return ra


def ve(ket: list[tuple], ten: str) -> None:
    if not ket:
        print("  (khong co du lieu cho " + ten + ")")
        return
    print()
    print("=== " + ten + " ===")
    print("%10s %10s %10s %8s %6s" % ("tau", "coverage%", "risk%",
                                      "tra loi", "sai"))
    print("-" * 50)
    truoc = None
    for tau, cov, risk, n_tl, n_sai in ket:
        # Chi in khi coverage doi - khong thi bang dai ma khong them thong tin
        if truoc is not None and abs(cov - truoc) < 1e-9:
            continue
        truoc = cov
        print("%10.4f %10.1f %10.1f %8d %6d" % (tau, cov, risk, n_tl, n_sai))

    # Diem chot: coverage cao nhat ma risk = 0
    sach = [x for x in ket if x[2] == 0.0 and x[3] > 0]
    if sach:
        tot = max(sach, key=lambda x: x[1])
        print()
        print("  Nguong de xuat: tau = %.4f" % tot[0])
        print("  -> coverage %.1f%%, risk %.1f%% (%d tra loi, %d sai)"
              % (tot[1], tot[2], tot[3], tot[4]))
    else:
        print()
        print("  KHONG co nguong nao cho risk = 0 voi coverage > 0.")
        print("  Nghia la moi muc nguong deu con cau tra loi sai lot qua,")
        print("  hoac chua du du lieu de ket luan.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ket-qua")
    a = ap.parse_args()

    version = freeze.phien_ban_dang_dung()
    if a.ket_qua:
        f = Path(a.ket_qua)
    else:
        ds = sorted((BASE / "evaluation" / "results").glob(
            "c2_" + version + "_*.jsonl"))
        if not ds:
            raise SystemExit("Chua co ket qua C2.")
        f = ds[-1]

    rs = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()
          if x.strip()]
    cases = nap_case(version)
    print("Doc " + str(len(rs)) + " ket qua tu " + f.name)

    thieu = [t for t in ("diem_cao_nhat", "intent_do_tin_cay")
             if all(r.get(t) is None for r in rs)]
    if thieu:
        print()
        print("THIEU TRUONG: " + ", ".join(thieu))
        print()
        print("Ket qua nay chay TRUOC khi run_c2.py ghi cac truong do. Phai")
        print("chay lai C2 thi moi dung duoc duong risk-coverage:")
        print("    make c2")
        print()
        print("KHONG ve duong cong tu du lieu khong co.")

    ve(quet(rs, cases, "diem_cao_nhat"), "Diem truy xuat (RRF cao nhat)")
    ve(quet(rs, cases, "intent_do_tin_cay"), "Do tin cay Intent Router")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
