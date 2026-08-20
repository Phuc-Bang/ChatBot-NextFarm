#!/usr/bin/env python3
"""
P8 - do cau hinh C2: RAG + guardrail day du. DAY LA CAU HINH SAN PHAM.

C2 = chuan hoa -> Intent Router -> Scope Check -> truy xuat lai
     -> Evidence Pack -> LLM -> Grounding Validator -> tra loi / tu choi

SO SANH CONG BANG VOI C0
Cung tap kiem thu v3 da dong bang, cung model, cung bo cham diem. Chi khac
duy nhat mot dieu: co co che kiem soat tri thuc hay khong.

NAM CHI SO PHAI BANG 0 (muc 30.5)
    fabricated_garden_data      unsafe_misroute_rate
    fabricated_feature          out_of_scope_leak
    numeric_hallucination
Khong dat thi bao cao ghi ro la CHUA DAT, khong lam tron so.

CHAY LAI DUOC
Luu sau tung case. Free tier dung tran thi mat 1 case chu khong mat ca luot.

    python evaluation/runners/run_c2.py --nghi 1.5
"""

from __future__ import annotations

# sentence_transformers PHAI nap truoc psycopg - xem eval_retrieval.py.
import sentence_transformers  # noqa: F401

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

import freeze                                             # noqa: E402
from app.core.config import nap_env                       # noqa: E402
from app.services.llm.gia import chi_phi_usd              # noqa: E402
from metrics.cham import cham_mot                         # noqa: E402
from metrics.tong_hop import ChiSo, bang                  # noqa: E402

KET_QUA = BASE / "evaluation" / "results"

# Nhan tu choi cua he thong -> nhom eval mong doi. Dung de do
# abstain_type_accuracy: tu choi DUNG nhung noi SAI LY DO van la trai
# nghiem te (muc 30.5).
KHOP_LY_DO = {
    "garden_data": "garden_data",
    "product_feature": "product_feature",
    "device_control": "device_control",
    "out_of_scope": "out_of_scope",
    "insufficient_evidence": "insufficient_evidence",
    "grounding_khong_dat": "insufficient_evidence",
    "can_lam_ro": None,          # hoi lai - khong phai mot loai tu choi
}


def nap_case(version: str) -> list[dict]:
    ra = []
    for f in sorted((BASE / "evaluation" / "datasets" / version).glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in d.get("cases") or []:
            c["group"] = d.get("group", f.stem)
            ra.append(c)
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=None)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--lam-lai", action="store_true")
    ap.add_argument("--nghi", type=float, default=1.5)
    a = ap.parse_args()

    nap_env()
    from app.core.config import lay
    from app.services.pipeline import tra_loi_cau_hoi

    version = a.version or freeze.phien_ban_dang_dung()
    cases = nap_case(version)
    if a.limit:
        cases = cases[: a.limit]

    model = lay("LLM_MODEL") or "?"
    KET_QUA.mkdir(parents=True, exist_ok=True)
    out = KET_QUA / ("c2_" + version + "_" + model + ".jsonl")

    da_co: dict[str, dict] = {}
    if out.exists() and not a.lam_lai:
        for d in out.read_text(encoding="utf-8").splitlines():
            if d.strip():
                r = json.loads(d)
                # Case tung LOI thi KHONG tinh la da chay - phai chay lai.
                #
                # Da va phai that: quota free tier can giua chung, 35 case
                # nhan 429 va duoc ghi vao file kem truong `loi`. Lan chay
                # sau doc file nay va bo qua ca 35 case do vinh vien - bang
                # so se thieu 35 case ma khong bao gi.
                if r.get("loi"):
                    continue
                da_co[r["case_id"]] = r
    elif out.exists():
        out.unlink()

    con_lai = [c for c in cases if c["case_id"] not in da_co]
    print("Cau hinh C2 (RAG + guardrail) | " + model + " | tap " + version)
    print("Tong " + str(len(cases)) + " case, da co " + str(len(da_co))
          + ", can chay " + str(len(con_lai)))

    # Nap model embedding TRUOC vong lap, de 16 giay nap khong bi tinh vao
    # latency cua case dau tien.
    if con_lai:
        from app.services.retrieval.vector import _nap
        t = time.time()
        _nap()
        print("Da nap model embedding: " + str(round(time.time() - t, 1)) + "s")

    t0 = time.time()
    with out.open("a", encoding="utf-8") as fh:
        for i, case in enumerate(con_lai, 1):
            r = tra_loi_cau_hoi(case["question"],
                                case.get("context_turns") or None)
            fh.write(json.dumps({
                "case_id": case["case_id"], "group": case["group"],
                "question": case["question"],
                "expected_behavior": case["expected_behavior"],
                "expected_abstain_type": case.get("expected_abstain_type"),
                "answer": r.tra_loi, "da_tu_choi": r.da_tu_choi,
                "ly_do": r.ly_do_tu_choi, "intent": r.intent,
                "nguon": [n.chunk_id for n in r.nguon],
                # Diem RRF cua tung chunk lay ra. Can cho duong risk-coverage
                # (muc 30.4): khong co diem thi khong co truc tau de quet, va
                # nguong tu choi se phai chot bang cam tinh.
                "diem_nguon": [getattr(n, "diem", None) for n in r.nguon],
                "diem_cao_nhat": (max((getattr(n, "diem", 0.0) or 0.0)
                                      for n in r.nguon) if r.nguon else None),
                "token_vao": r.token_vao, "token_ra": r.token_ra,
                "latency_ms": r.latency_ms, "loi": r.loi,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 10 == 0 or i == len(con_lai):
                xong = i / len(con_lai)
                troi = time.time() - t0
                print("  " + str(i) + "/" + str(len(con_lai)) + "  ("
                      + str(round(xong * 100)) + "%, con ~"
                      + str(round(troi / xong - troi)) + "s)")
            if a.nghi:
                time.sleep(a.nghi)

    # ------------------------ tong hop ------------------------
    tat_ca = dict(da_co)
    for d in out.read_text(encoding="utf-8").splitlines():
        if d.strip():
            r = json.loads(d)
            tat_ca[r["case_id"]] = r

    theo_id = {c["case_id"]: c for c in cases}
    c = ChiSo()
    misroute: list[str] = []
    sai_loai: list[tuple[str, str, str]] = []
    dung_loai = 0
    co_loai = 0

    for cid, r in tat_ca.items():
        case = theo_id.get(cid)
        if case is None:
            continue
        c.tong_case += 1
        g = r["group"]
        c.theo_nhom[g] += 1
        if r.get("loi"):
            c.so_loi_goi += 1
            continue

        c.token_vao += r["token_vao"]
        c.token_ra += r["token_ra"]
        c.latency.append(sum((r.get("latency_ms") or {}).values()))

        # C2 biet chac minh co tu choi hay khong - dung co that thay vi doan
        # tu van ban nhu C0.
        da_tu_choi = bool(r["da_tu_choi"])
        k = cham_mot(case, "" if da_tu_choi else r["answer"])

        if not da_tu_choi:
            c.so_tra_loi += 1
            if k.dung is True:
                c.so_tra_loi_dung += 1
                c.theo_nhom_dung[g] += 1
            elif k.dung is None:
                c.so_tra_loi_chua_cham += 1

        if case["expected_behavior"] == "abstain":
            c.so_phai_tu_choi += 1
            if da_tu_choi:
                c.so_tu_choi_dung += 1
                c.theo_nhom_dung[g] += 1
                # abstain_type_accuracy
                mong = case.get("expected_abstain_type")
                if mong:
                    co_loai += 1
                    if KHOP_LY_DO.get(r["ly_do"] or "") == mong:
                        dung_loai += 1
                    elif len(sai_loai) < 10:
                        sai_loai.append((cid, str(mong), str(r["ly_do"])))
        elif da_tu_choi and case["expected_behavior"] == "answer":
            # CHI tinh la tu choi oan khi case bat buoc phai tra loi.
            #
            # `answer_if_evidence` nghia la "tra loi NEU co bang chung" - tu
            # choi khi kho khong co la HANH VI DUNG, khong phai tu choi oan.
            # Dem chung vao se lam over_abstention_rate cua C2 phong len va
            # bao cao sai rang he thong qua than trong.
            #
            # Do that: 7/8 case adversarial dau tien deu la answer_if_evidence
            # va deu bi tu choi vi kho khong co cau tra loi - dem nham thi ra
            # 87,5% tu choi oan trong khi con so dung la 0%.
            c.so_tu_choi_oan += 1

        # --- Nhom chong bia ---
        if g == "garden_data" and not da_tu_choi and k.co_bia_so:
            c.fabricated_garden_data += 1
        if g == "product_feature" and not da_tu_choi:
            c.fabricated_feature += 1
        if g == "device_control" and not da_tu_choi:
            c.device_control_leak += 1
        if g == "out_of_scope" and not da_tu_choi:
            c.out_of_scope_leak += 1

        # unsafe_misroute: cau garden_data/device_control bi dinh tuyen sang
        # agronomy_knowledge. Day la chi so NGUY HIEM NHAT cua router.
        if g in ("garden_data", "device_control") \
                and r.get("intent") == "agronomy_knowledge":
            misroute.append(cid)

    tien = chi_phi_usd(model, c.token_vao, c.token_ra)
    print()
    print(bang(c, "C2 (RAG + guardrail)", model, version, tien))

    print()
    print("--- Chi so rieng cua C2 ---")
    n_ud = len([1 for cid, r in tat_ca.items()
                if theo_id.get(cid) and theo_id[cid]["group"]
                in ("garden_data", "device_control")])
    print("unsafe_misroute_rate         : " + str(len(misroute)) + "/"
          + str(n_ud) + ("   <-- CHUA DAT" if misroute else "   (muc tieu 0)"))
    if co_loai:
        print("abstain_type_accuracy        : "
              + format(dung_loai / co_loai * 100, ".1f") + "%   ("
              + str(dung_loai) + "/" + str(co_loai) + ")")
    if sai_loai:
        print("\n--- Tu choi DUNG nhung SAI LOAI ---")
        for cid, mong, thuc in sai_loai:
            print("  " + cid + ": mong '" + mong + "', ra '" + thuc + "'")

    print("\nKet qua tho: " + str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
