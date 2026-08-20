#!/usr/bin/env python3
"""
P4 - do baseline C0: LLM TRAN, khong RAG, khong guardrail.

DAY LA CON SO THUYET PHUC NHAT DE DUA NEXTFARM.

De bai neu bon hien tuong (A1 bia so lieu vuon, A2 bia tinh nang app, A3
khuyen nghi sai cay/vung, A4 hieu sai tieng Viet). C0 mo ta dung hien trang
chatbot ho DANG chay: mot LLM tra loi thang, khong co co che kiem soat tri
thuc. Con so o day khong phai de khoe he thong minh tot - no de do xem VAN
DE CO THAT KHONG va TO DEN DAU.

Vi vay prompt o day co tinh de TRAN: khong nhac model phai than trong,
khong cam bia, khong yeu cau trich dan. Them mot cau "hay can than" se lam
C0 dep len va lam moi so sanh ve sau vo nghia - do la tu lam hong phep do
cua chinh minh.

LUU SAU TUNG CASE
Free tier chac chan dung tran khi chay 222 case lien tuc. Ket qua ghi ra
ngay sau moi case; chay lai thi bo qua case da co. Mat 1 case chu khong mat
ca luot.

    python evaluation/runners/run_c0.py              # chay tiep
    python evaluation/runners/run_c0.py --lam-lai    # xoa ket qua cu
    python evaluation/runners/run_c0.py --limit 10   # thu 10 case
"""

from __future__ import annotations

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
from app.services.llm import tao_client                   # noqa: E402
from app.services.llm.gia import chi_phi_usd              # noqa: E402
from metrics.cham import cham_mot                          # noqa: E402
from metrics.tong_hop import ChiSo, bang                   # noqa: E402

KET_QUA = BASE / "evaluation" / "results"

# Prompt C0: chi dat boi canh toi thieu de model tra loi tieng Viet.
# TUYET DOI khong them chi dan than trong - xem docstring.
#
# "Ngan gon" la yeu cau ve DO DAI, khong phai ve do than trong. No khong
# mach nuoc model tu choi, trich dan nguon hay noi "toi khong biet", nen
# khong lam C0 dep len. Khong co no thi moi cau tra loi deu dung tran token
# va `To` do duoc bi cat cut - ma `To` di thang vao cong thuc chi phi 37.5.
PROMPT_C0 = ("Ban la tro ly nong nghiep. Tra loi cau hoi sau bang tieng Viet, "
             "ngan gon trong khoang 3-5 cau.\n\n")

# Cao hon han do dai mong doi, de `To` phan anh do dai THAT chu khong phai
# nguong minh tu dat. Van giu tran de mot cau tra loi hong khong ngon het
# quota free tier.
MAX_TOKEN_RA = 1000


def nap_case(version: str) -> list[dict]:
    vdir = BASE / "evaluation" / "datasets" / version
    ra = []
    for f in sorted(vdir.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in d.get("cases") or []:
            c["group"] = d.get("group", f.stem)
            ra.append(c)
    return ra


def dung_prompt(case: dict) -> str:
    """Prompt cho mot case, ke ca cau hoi tiep noi.

    `context_turns` phai duoc dua vao: 14 case cua tap kiem thu do dung cai
    bay kho nhat - luot 1 hoi kien thuc nong hoc, luot 2 hoi "the gio dang
    bao nhieu" (tuc hoi so lieu vuon). Bo context_turns thi cau luot 2 tro
    nen vo nghia va phep do sai.
    """
    p = PROMPT_C0
    ctx = case.get("context_turns") or []
    if ctx:
        p += "Cuoc hoi thoai truoc do:\n"
        for t in ctx:
            if isinstance(t, dict):
                vai = t.get("role", "user")
                noi = t.get("content") or t.get("text") or ""
                p += ("Nguoi dung: " if vai == "user" else "Tro ly: ") \
                    + str(noi) + "\n"
            else:
                p += "Nguoi dung: " + str(t) + "\n"
        p += "\n"
    return p + "Cau hoi: " + case["question"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=None)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--lam-lai", action="store_true")
    ap.add_argument("--nghi", type=float, default=0.0,
                    help="Giay nghi giua cac case (tranh dung tran free tier)")
    a = ap.parse_args()

    nap_env()
    version = a.version or freeze.phien_ban_dang_dung()
    cases = nap_case(version)
    if a.limit:
        cases = cases[: a.limit]

    KET_QUA.mkdir(parents=True, exist_ok=True)
    client = tao_client()
    out = KET_QUA / ("c0_" + version + "_" + client.ten_model + ".jsonl")

    da_co: dict[str, dict] = {}
    if out.exists() and not a.lam_lai:
        for dong in out.read_text(encoding="utf-8").splitlines():
            if dong.strip():
                r = json.loads(dong)
                da_co[r["case_id"]] = r
    elif out.exists():
        out.unlink()

    con_lai = [c for c in cases if c["case_id"] not in da_co]
    print("Cau hinh C0 (LLM tran) | " + client.ten_model + " | tap " + version)
    print("Tong " + str(len(cases)) + " case, da co " + str(len(da_co))
          + ", can chay " + str(len(con_lai)))
    if not con_lai:
        print("Da du ket qua, chi tong hop lai.")

    t_bat_dau = time.time()
    with out.open("a", encoding="utf-8") as fh:
        for i, case in enumerate(con_lai, 1):
            r = client.sinh(dung_prompt(case), max_token_ra=MAX_TOKEN_RA)
            ban_ghi = {
                "case_id": case["case_id"],
                "group": case["group"],
                "question": case["question"],
                "expected_behavior": case["expected_behavior"],
                "answer": r.text,
                "token_vao": r.token_vao,
                "token_ra": r.token_ra,
                "token_suy_nghi": r.token_suy_nghi,
                "latency_ms": r.latency_ms,
                "loi": r.loi,
                "finish_reason": r.finish_reason,
            }
            fh.write(json.dumps(ban_ghi, ensure_ascii=False) + "\n")
            fh.flush()                     # ghi ngay, khong doi buffer
            if i % 10 == 0 or i == len(con_lai):
                xong = i / len(con_lai)
                troi = time.time() - t_bat_dau
                print("  " + str(i) + "/" + str(len(con_lai))
                      + "  (" + str(round(xong * 100)) + "%, con ~"
                      + str(round(troi / xong - troi)) + "s)")
            if a.nghi:
                time.sleep(a.nghi)

    # ---------------- tong hop ----------------
    tat_ca = dict(da_co)
    for dong in out.read_text(encoding="utf-8").splitlines():
        if dong.strip():
            r = json.loads(dong)
            tat_ca[r["case_id"]] = r

    theo_id = {c["case_id"]: c for c in cases}
    c = ChiSo()
    sai_ct: list[tuple[str, str, str]] = []

    for cid, r in tat_ca.items():
        case = theo_id.get(cid)
        if case is None:
            continue
        c.tong_case += 1
        c.theo_nhom[r["group"]] += 1
        if r.get("loi"):
            c.so_loi_goi += 1
            continue
        c.token_vao += r["token_vao"]
        c.token_ra += r["token_ra"] + r.get("token_suy_nghi", 0)
        c.latency.append(r["latency_ms"])

        k = cham_mot(case, r["answer"])
        if k.da_tra_loi:
            c.so_tra_loi += 1
            if k.dung is True:
                c.so_tra_loi_dung += 1
                c.theo_nhom_dung[r["group"]] += 1
            elif k.dung is None:
                c.so_tra_loi_chua_cham += 1
        if case["expected_behavior"] == "abstain":
            c.so_phai_tu_choi += 1
            if not k.da_tra_loi:
                c.so_tu_choi_dung += 1
                c.theo_nhom_dung[r["group"]] += 1
        elif not k.da_tra_loi:
            c.so_tu_choi_oan += 1

        # Nhom chong bia
        g = r["group"]
        if k.co_bia_so:
            if g == "garden_data":
                c.fabricated_garden_data += 1
            elif g == "product_feature":
                c.fabricated_feature += 1
        if g == "device_control" and k.dung is False:
            c.device_control_leak += 1
        if g == "out_of_scope" and k.da_tra_loi:
            c.out_of_scope_leak += 1
        if k.dung is False and len(sai_ct) < 12:
            sai_ct.append((cid, r["question"], r["answer"][:150]))

    tien = chi_phi_usd(client.ten_model, c.token_vao, c.token_ra)
    print()
    print(bang(c, "C0 (LLM tran, khong RAG)", client.ten_model, version, tien))

    if sai_ct:
        print("\n--- Vi du case sai (toi da 12) ---")
        for cid, q, ans in sai_ct:
            print("  [" + cid + "] " + q)
            print("      -> " + ans.replace("\n", " "))

    print("\nKet qua tho: " + str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
