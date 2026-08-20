#!/usr/bin/env python3
"""
Do dong gop rieng cua reranker (muc 14.6).

VI SAO PHAI DO RIENG

Quy chuan doi "do duoc dong gop rieng cua reranker (bat/tat)". Them mot
thanh phan roi bao "he thong tot len" ma khong tach duoc phan nao la cua no
thi khong biet co nen giu no khong - reranker ton them thoi gian moi luot,
va thoi gian do nam trong ngan sach ASM-01.

Chay:
    python evaluation/runners/eval_rerank.py
    python evaluation/runners/eval_rerank.py --model itdainb/PhoRanker
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

import app                                                 # noqa: E402,F401
import sentence_transformers                               # noqa: E402,F401

from app.core.db import ket_noi                            # noqa: E402
from app.services.normalization.vietnamese import (        # noqa: E402
    chuan_hoa, phat_hien_cay)
from app.services.retrieval.keyword import (               # noqa: E402
    hop_nhat_rrf, tim_fts, tim_trigram)
from app.services.retrieval.vector import tim_vector       # noqa: E402


def _nap_eval():
    spec = importlib.util.spec_from_file_location(
        "er", str(BASE / "evaluation" / "runners" / "eval_retrieval.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def do(cases, gt, con, ten_model: str | None, top_k_rerank: int = 20):
    """Tra ve (R@1, R@3, R@5, MRR, ms_moi_cau)."""
    from app.services.retrieval import rerank

    r1 = r3 = r5 = 0
    mrr = 0.0
    tong_ms = 0.0
    for c in cases:
        dung = gt[c["case_id"]]
        if not dung:
            continue
        cau = chuan_hoa(c["question"])
        crop = (phat_hien_cay(cau) or [None])[0]
        gop = hop_nhat_rrf(
            ("fts", tim_fts(cau, crop, 20, conn=con)),
            ("trigram", tim_trigram(cau, crop, 20, conn=con)),
            ("vector", tim_vector(cau, crop, 20, conn=con)))

        t = time.time()
        if ten_model:
            ds = rerank.xep_lai(cau, gop[:top_k_rerank], top_k=10,
                                ten_model=ten_model)
        else:
            ds = gop[:10]
        tong_ms += (time.time() - t) * 1000

        ids = [x.chunk_id for x in ds]
        h = next((i + 1 for i, x in enumerate(ids) if x in dung), None)
        if h:
            mrr += 1.0 / h
            if h <= 1:
                r1 += 1
            if h <= 3:
                r3 += 1
            if h <= 5:
                r5 += 1
    n = len(cases)
    return (100.0 * r1 / n, 100.0 * r3 / n, 100.0 * r5 / n,
            mrr / n, tong_ms / n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="itdainb/PhoRanker")
    ap.add_argument("--version", default=None)
    a = ap.parse_args()

    import freeze
    version = a.version or freeze.phien_ban_dang_dung()

    from app.services.retrieval import rerank

    m = _nap_eval()
    cases = m.nap_case_co_nguon(version)
    with ket_noi() as con:
        gt = {c["case_id"]: m.chunk_dung(con, c["source_of_truth"])[0]
              for c in cases}
        do_duoc = sum(1 for c in cases if gt[c["case_id"]])
        print("Tap " + version + " | " + str(do_duoc) + "/" + str(len(cases))
              + " case do duoc")
        print()

        ket = []
        for ten, mo in [("TAT rerank", None), ("BAT rerank", a.model)]:
            r = do(cases, gt, con, mo)
            ket.append((ten, r))
            print("%-12s R@1 %5.1f  R@3 %5.1f  R@5 %5.1f  MRR %.3f  %6.1f ms/cau"
                  % (ten, r[0], r[1], r[2], r[3], r[4]))

        # Bao so lan rerank that bai. Neu no > 0 thi bang tren KHONG do
        # duoc dong gop cua reranker - no do chinh cau hinh TAT hai lan.
        n_loi = rerank.so_lan_loi()
        if n_loi:
            print()
            print("!!! rerank THAT BAI " + str(n_loi) + " lan - moi lan lui")
            print("!!! ve thu tu cu. Bang tren KHONG do duoc reranker.")

        print()
        (_, a0), (_, a1) = ket
        print("Chenh lech: R@1 %+.1f  R@3 %+.1f  R@5 %+.1f  MRR %+.3f"
              % (a1[0] - a0[0], a1[1] - a0[1], a1[2] - a0[2], a1[3] - a0[3]))
        print("Chi phi   : +%.1f ms moi luot hoi" % (a1[4] - a0[4]))
        print()
        print("Ngan sach ASM-01: p50 <= 5000 ms tong. So tren la phan rerank")
        print("them vao, chua ke truy xuat va goi model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
