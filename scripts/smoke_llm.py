#!/usr/bin/env python3
"""
Kiem tra nhanh: key co chay khong, model co ton tai khong, token co doc duoc
khong. CHAY CAI NAY TRUOC khi chay 222 case.

Ly do ton tai: gemini-1.5-flash da bi Google TAT han, moi request tra ve 404.
Phat hien dieu do o cau thu 1 ton 3 giay; phat hien o cau thu 200 ton ca buoi.

    python scripts/smoke_llm.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import nap_env                      # noqa: E402
from app.services.llm import tao_client                   # noqa: E402
from app.services.llm.gia import (                        # noqa: E402
    NGAY_TRA_CUU, NGUON_GIA, chi_phi_usd, tra_gia)

CAU_THU = [
    ("Tieng Viet co dau",
     "Tra loi dung mot cau ngan bang tieng Viet: cay lua can nuoc khong?"),
    ("Bam vao bang chung",
     "Ban CHI duoc dung thong tin trong BANG CHUNG.\n\n"
     "BANG CHUNG [chunk_7]: Do ph trung binh cua dat trong ca chua khoang "
     "6-6.5, neu dat chua hon phai bon them voi.\n\n"
     "CAU HOI: Ca chua can do pH bao nhieu?\n\n"
     "Tra loi ngan bang tieng Viet, kem [chunk_7]."),
    ("Biet noi khong du can cu",
     "Ban CHI duoc dung thong tin trong BANG CHUNG. Neu bang chung khong du "
     "de tra loi thi phai noi ro la khong du, TUYET DOI khong doan.\n\n"
     "BANG CHUNG [chunk_7]: Do ph trung binh cua dat trong ca chua khoang "
     "6-6.5.\n\n"
     "CAU HOI: Ca chua can bao nhieu kg dam mot hecta?\n\n"
     "Tra loi ngan bang tieng Viet."),
]


def main() -> int:
    nap_env()
    try:
        c = tao_client()
    except Exception as e:                                 # noqa: BLE001
        print("KHONG TAO DUOC CLIENT:", e)
        return 1

    print("=" * 70)
    print("SMOKE TEST  |  " + c.ten_provider + " / " + c.ten_model)
    print("=" * 70)

    try:
        g = tra_gia(c.ten_model)
        print("Gia (tra ngay " + NGAY_TRA_CUU + "): vao $" + str(g.vao)
              + " / ra $" + str(g.ra) + " moi 1 trieu token")
        if g.ghi_chu:
            print("  " + g.ghi_chu)
    except Exception as e:                                 # noqa: BLE001
        print("CANH BAO: " + str(e)[:200])
        print("  -> chay duoc nhung KHONG uoc luong duoc chi phi.")

    tong_vao = tong_ra = 0
    hong = 0
    print()
    for ten, p in CAU_THU:
        r = c.sinh(p, max_token_ra=200)
        if not r.thanh_cong:
            hong += 1
            print("[HONG] " + ten)
            print("       " + str(r.loi or ("rong, finish_reason="
                                            + str(r.finish_reason))))
            continue
        tong_vao += r.token_vao
        tong_ra += r.token_ra_tinh_tien
        print("[OK]   " + ten + "  (" + str(r.latency_ms) + "ms, vao="
              + str(r.token_vao) + " ra=" + str(r.token_ra)
              + " think=" + str(r.token_suy_nghi) + ")")
        print("       " + r.text.replace("\n", " ")[:160])

    print()
    print("-" * 70)
    if hong:
        print("CO " + str(hong) + "/" + str(len(CAU_THU)) + " CAU HONG.")
        return 1

    print("Tong: vao=" + str(tong_vao) + " ra=" + str(tong_ra) + " token")
    try:
        gia = chi_phi_usd(c.ten_model, tong_vao, tong_ra)
        print("Chi phi 3 cau nay: $" + format(gia, ".6f"))
        # Uoc luong tho cho mot luot do - KHONG phai con so bao cao.
        print("Uoc luong 222 case (theo trung binh 3 cau nay): $"
              + format(gia / len(CAU_THU) * 222, ".4f"))
        print("  (uoc luong tho de biet do lon; con so that lay tu lan chay "
              "C0 that)")
    except Exception:                                      # noqa: BLE001
        pass
    print("Nguon gia: " + NGUON_GIA)
    print("\nDAT. Chay duoc P4 (baseline C0).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
