#!/usr/bin/env python3
"""
Do Recall@K va MRR de CHON MODEL EMBEDDING bang so (DEC-015, muc 26).

GROUND TRUTH O DAU RA

22 case cua tap kiem thu co truong `source_of_truth` tro thang ve mot fact
da duoc NGUOI duyet, va fact do biet no den tu cau nao cua tai lieu nao.
Tu do suy ra duoc chunk nao la chunk DUNG cho cau hoi do.

Day la ly do muc 24.5 bat duyet fact TRUOC khi do retrieval: khong co fact
da duyet thi khong co ground truth, va khong co ground truth thi moi con so
Recall deu la tu cham diem cho minh.

DO CA BA KENH

    keyword  - FTS + trigram (da co tu P6)
    vector   - embedding (dang chon model)
    hybrid   - hop nhat bang RRF

Do rieng tung kenh moi biet kenh nao dong gop gi. Chi do hybrid thi khong
tra loi duoc cau "co can vector khong" - ma do la cau phai tra loi truoc khi
them mot phu thuoc moi vao he thong.

    python evaluation/runners/eval_retrieval.py --models halong e5-small
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# THU TU IMPORT O DAY LA BAT BUOC, KHONG PHAI NGAU NHIEN
#
# Tren may nay (Windows, torch 2.5.1+cu121, psycopg 3.2.3), nap
# `sentence_transformers` SAU khi psycopg da mo ket noi lam tien trinh
# SEGFAULT - thoat im lang, khong traceback, khong ghi duoc dong log nao.
#
#     psycopg -> sentence_transformers   : segfault (exit 139)
#     sentence_transformers -> psycopg   : chay binh thuong
#
# Nap truoc o day de moi module ve sau import theo thu tu nao cung an toan.
# Bo dong nay di thi script chet lang le va rat kho lan ra nguyen nhan.
# ---------------------------------------------------------------------------
import sentence_transformers  # noqa: F401,E402  (phai nap TRUOC psycopg)

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

import freeze                                             # noqa: E402
from app.core.config import nap_env                       # noqa: E402
from app.core.db import ket_noi                           # noqa: E402

K_DO = (1, 3, 5, 10)


def nap_case_co_nguon(version: str) -> list[dict]:
    """Case co `source_of_truth` - tuc co ground truth de do."""
    ra = []
    for f in sorted((BASE / "evaluation" / "datasets" / version).glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in d.get("cases") or []:
            if c.get("source_of_truth"):
                c["group"] = d.get("group", f.stem)
                ra.append(c)
    return ra


def _chuan(s: str) -> str:
    """Chuan hoa khoang trang truoc khi doi chieu.

    Cau trong bang `fact` chua ky tu NBSP (\\xa0) den tu HTML goc, con text
    chunk da qua mot buoc lam sach khac. Doi chieu thang thi khong bao gio
    khop, va ham nay se lang le tra ve rong -> Recall = 0 cho MOI model, tuc
    phep do chet ma khong bao loi.
    """
    return " ".join((s or "").replace("\xa0", " ").split())


def chunk_dung(con, source_of_truth: str) -> tuple[set[str], set[str]]:
    """(chunk index duoc, chunk bi chan) chua cau nguon cua mot fact.

    Cot `fact.chunk_id` co trong luoc do nhung TOAN BO la NULL - buoc nap
    chua dien. Vi vay phai doi chieu bang noi dung.

    TRA VE CA HAI TAP, khong gop lam mot. Ly do: mot fact co the nam trong
    chunk `is_high_risk` chua duyet le, va DEC-005 chan chunk do khoi kho
    truy xuat. Luc do KHONG he thong nao tim ra duoc - do la hanh vi DUNG,
    khong phai loi cua retrieval. Gop chung vao ground truth se lam Recall
    tut xuong va do nham cho model, trong khi nguyen nhan that la "chua
    duyet xong".
    """
    doc_id = source_of_truth.rsplit("#", 1)[0]
    with con.cursor() as cur:
        cur.execute(
            "SELECT sentence FROM fact WHERE document_id = %s "
            "AND sentence_index = %s",
            (doc_id, int(source_of_truth.rsplit("#", 1)[1])))
        r = cur.fetchone()
        if not r:
            return set(), set()
        cau = _chuan(r[0])[:60]
        cur.execute(
            "SELECT chunk_id, text, approved FROM chunk WHERE document_id = %s",
            (doc_id,))
        mo, chan = set(), set()
        for cid, text, approved in cur.fetchall():
            if cau and cau in _chuan(text):
                (mo if approved else chan).add(cid)
        return mo, chan


def nap_chunk(con) -> tuple[list[int], list[str]]:
    with con.cursor() as cur:
        cur.execute("SELECT chunk_id, text FROM indexable_chunk ORDER BY chunk_id")
        rs = cur.fetchall()
    return [r[0] for r in rs], [r[1] for r in rs]


def do_mot_model(ten_model: str, cases: list[dict],
                 dap_an: dict[str, set[int]],
                 ids: list[int], texts: list[str]) -> dict:
    from app.services.embedding.local import LocalEmbedding

    t0 = time.time()
    m = LocalEmbedding(ten_model)
    t_nap = time.time() - t0

    t0 = time.time()
    V = m.ma_hoa(texts, la_cau_hoi=False)
    t_kho = time.time() - t0

    hoi = [c["question"] for c in cases]
    t0 = time.time()
    Q = m.ma_hoa(hoi, la_cau_hoi=True)
    t_hoi = (time.time() - t0) / max(len(hoi), 1)

    sim = Q @ V.T                                  # da chuan hoa L2
    thu_tu = np.argsort(-sim, axis=1)

    hit = {k: 0 for k in K_DO}
    mrr = 0.0
    do_duoc = 0
    for i, c in enumerate(cases):
        dung = dap_an.get(c["case_id"])
        if not dung:
            continue     # bi chan hoac khong doi chieu duoc - da bao o main()
        do_duoc += 1
        xep = [ids[j] for j in thu_tu[i]]
        vi_tri = next((r for r, cid in enumerate(xep, 1) if cid in dung), None)
        if vi_tri:
            mrr += 1.0 / vi_tri
            for k in K_DO:
                if vi_tri <= k:
                    hit[k] += 1

    return {
        "model": ten_model, "so_chieu": m.so_chieu, "do_duoc": do_duoc,
        "recall": {k: (hit[k] / do_duoc if do_duoc else 0.0) for k in K_DO},
        "mrr": mrr / do_duoc if do_duoc else 0.0,
        "giay_nap": t_nap, "giay_kho": t_kho, "giay_moi_cau_hoi": t_hoi,
    }


def do_keyword(cases: list[dict], dap_an: dict[str, set[str]],
               con) -> dict:
    """Do kenh tu khoa da co tu P6 (FTS + trigram, hop nhat RRF).

    VI SAO PHAI DO KENH NAY

    Neu tu khoa mot minh da du thi them vector la them mot phu thuoc (model
    ~300MB, thoi gian nap, RAM) ma khong doi lai gi. Cau "co can vector
    khong" phai tra loi bang so truoc khi cam no vao he thong.
    """
    from app.services.normalization.vietnamese import chuan_hoa
    from app.services.retrieval.keyword import (
        hop_nhat_rrf, tim_fts, tim_trigram)

    hit = {k: 0 for k in K_DO}
    mrr = 0.0
    do_duoc = 0
    t_tong = 0.0
    for c in cases:
        dung = dap_an.get(c["case_id"])
        if not dung:
            continue
        do_duoc += 1
        t0 = time.time()
        cau = chuan_hoa(c["question"])
        fts = tim_fts(cau, conn=con)
        tri = tim_trigram(cau, conn=con)
        gop = hop_nhat_rrf(("fts", fts), ("trigram", tri))
        t_tong += time.time() - t0
        vi_tri = next((r for r, ch in enumerate(gop, 1)
                       if ch.chunk_id in dung), None)
        if vi_tri:
            mrr += 1.0 / vi_tri
            for k in K_DO:
                if vi_tri <= k:
                    hit[k] += 1

    return {
        "model": "keyword", "so_chieu": 0, "do_duoc": do_duoc,
        "recall": {k: (hit[k] / do_duoc if do_duoc else 0.0) for k in K_DO},
        "mrr": mrr / do_duoc if do_duoc else 0.0,
        "giay_nap": 0.0, "giay_kho": 0.0,
        "giay_moi_cau_hoi": t_tong / max(do_duoc, 1),
    }


def do_hybrid(ten_model: str, cases: list[dict], dap_an: dict[str, set[str]],
              ids: list[str], texts: list[str], con, top_k: int = 20) -> dict:
    """Hop nhat vector + tu khoa bang RRF (muc 14.4).

    Hop nhat theo HANG chu khong theo DIEM: cosine, ts_rank va
    word_similarity o ba thang do khac han nhau, ep ve mot thang la tu bia
    ra mot phep quy doi khong co co so. Dung lai ham hop_nhat_rrf da co.
    """
    from app.services.normalization.vietnamese import chuan_hoa
    from app.services.retrieval.keyword import (
        ChunkTraVe, hop_nhat_rrf, tim_fts, tim_trigram)
    from app.services.embedding.local import LocalEmbedding

    m = LocalEmbedding(ten_model)
    V = m.ma_hoa(texts, la_cau_hoi=False)

    hit = {k: 0 for k in K_DO}
    mrr = 0.0
    do_duoc = 0
    t_tong = 0.0
    for c in cases:
        dung = dap_an.get(c["case_id"])
        if not dung:
            continue
        do_duoc += 1
        t0 = time.time()
        q = m.ma_hoa([c["question"]], la_cau_hoi=True)[0]
        thu_tu = np.argsort(-(V @ q))[:top_k]
        # Boc thanh ChunkTraVe rong de dung chung ham RRF - chi can chunk_id.
        vec = [ChunkTraVe(ids[j], "", "", None, None, None, "", None, None,
                          None, False) for j in thu_tu]
        cau = chuan_hoa(c["question"])
        gop = hop_nhat_rrf(("vector", vec),
                           ("fts", tim_fts(cau, conn=con)),
                           ("trigram", tim_trigram(cau, conn=con)))
        t_tong += time.time() - t0
        vi_tri = next((r for r, ch in enumerate(gop, 1)
                       if ch.chunk_id in dung), None)
        if vi_tri:
            mrr += 1.0 / vi_tri
            for k in K_DO:
                if vi_tri <= k:
                    hit[k] += 1

    return {
        "model": "hybrid(" + ten_model + ")", "so_chieu": m.so_chieu,
        "do_duoc": do_duoc,
        "recall": {k: (hit[k] / do_duoc if do_duoc else 0.0) for k in K_DO},
        "mrr": mrr / do_duoc if do_duoc else 0.0,
        "giay_nap": 0.0, "giay_kho": 0.0,
        "giay_moi_cau_hoi": t_tong / max(do_duoc, 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=None)
    ap.add_argument("--models", nargs="*", default=["halong", "e5-small"])
    ap.add_argument("--bo-keyword", action="store_true",
                    help="Bo qua kenh tu khoa (mac dinh CO do de so sanh)")
    ap.add_argument("--hybrid", nargs="*", default=[],
                    help="Do them cau hinh hybrid cho cac model nay")
    a = ap.parse_args()

    nap_env()
    version = a.version or freeze.phien_ban_dang_dung()
    cases = nap_case_co_nguon(version)

    con = ket_noi()
    ids, texts = nap_chunk(con)

    dap_an: dict[str, set[str]] = {}
    bi_chan: list[str] = []
    khong_thay: list[str] = []
    for c in cases:
        mo, chan = chunk_dung(con, c["source_of_truth"])
        if mo:
            dap_an[c["case_id"]] = mo
        elif chan:
            bi_chan.append(c["case_id"])
        else:
            khong_thay.append(c["case_id"])
    co_ga = len(dap_an)

    print("Tap kiem thu " + version + " | " + str(len(cases))
          + " case co source_of_truth")
    print("  do duoc                 : " + str(co_ga))
    if bi_chan:
        print("  KHONG do duoc (bi chan) : " + str(len(bi_chan)))
        print("      Chunk nguon la noi dung RUI RO CAO chua duyet le nen")
        print("      DEC-005 chan khoi kho truy xuat. Khong he thong nao tim")
        print("      ra duoc - day la hanh vi DUNG, khong phai loi retrieval.")
        print("      Duyet 44 chunk rui ro cao se mo lai cac case nay.")
    if khong_thay:
        print("  khong doi chieu duoc    : " + str(len(khong_thay))
              + "   " + ", ".join(khong_thay[:5]))
    print("Kho tri thuc: " + str(len(ids)) + " chunk index duoc")
    if co_ga == 0:
        print("\nKHONG CO GROUND TRUTH - khong do duoc.")
        return 1

    print()
    kq = []
    if not a.bo_keyword:
        print("Dang do keyword (FTS + trigram) ...")
        try:
            kq.append(do_keyword(cases, dap_an, con))
        except Exception as e:                             # noqa: BLE001
            print("  BO QUA keyword: " + str(e)[:200])
    for ten in a.models:
        print("Dang do " + ten + " ...")
        try:
            kq.append(do_mot_model(ten, cases, dap_an, ids, texts))
        except Exception as e:                             # noqa: BLE001
            print("  BO QUA " + ten + ": " + str(e)[:200])

    for ten in a.hybrid:
        print("Dang do hybrid(" + ten + ") ...")
        try:
            kq.append(do_hybrid(ten, cases, dap_an, ids, texts, con))
        except Exception as e:                             # noqa: BLE001
            print("  BO QUA hybrid(" + ten + "): " + str(e)[:200])

    if not kq:
        return 1

    print()
    print("=" * 78)
    print("RECALL@K  |  " + str(co_ga) + " case co ground truth  |  "
          + str(len(ids)) + " chunk")
    print("=" * 78)
    dau = "model".ljust(18) + "chieu".rjust(6)
    for k in K_DO:
        dau += ("R@" + str(k)).rjust(8)
    dau += "MRR".rjust(8) + "nap(s)".rjust(9) + "kho(s)".rjust(9) \
        + "hoi(ms)".rjust(9)
    print(dau)
    print("-" * 78)
    for r in sorted(kq, key=lambda x: -x["mrr"]):
        d = r["model"].ljust(18) + str(r["so_chieu"]).rjust(6)
        for k in K_DO:
            d += format(r["recall"][k] * 100, ".1f").rjust(8)
        d += format(r["mrr"], ".3f").rjust(8)
        d += format(r["giay_nap"], ".1f").rjust(9)
        d += format(r["giay_kho"], ".1f").rjust(9)
        d += format(r["giay_moi_cau_hoi"] * 1000, ".0f").rjust(9)
        print(d)
    print()
    print("hoi(ms) = thoi gian embed MOT cau hoi - day la phan nam tren")
    print("duong latency moi luot (ngan sach ASM-01: p50 <= 5s tong).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
