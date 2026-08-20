#!/usr/bin/env python3
"""
Tinh lai chi so C2 khi CO Grounding tang 3, tu ket qua da luu.

VI SAO KHONG CHAY LAI 222 CASE

Tang 3 (mac dinh) thuan quy tac: no doc cau hoi, cau tra loi va evidence -
KHONG goi model nao. Vi vay ap duoc len ket qua da luu, khong ton quota va
khong phai doi model tra loi lai (moi lan goi lai la mot cau tra loi khac,
lam mat kha nang so sanh).

Cai NAY KHONG lam duoc: do lai latency va token. Tang 3 khong goi mang nen
token khong doi; latency co doi nhung phan them la ~1ms, duoi nguong nhieu
cua phep do.

    python evaluation/runners/c2_them_tang3.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

import app                                                 # noqa: E402,F401
import yaml                                                # noqa: E402

import freeze                                              # noqa: E402
from app.core.db import ket_noi                            # noqa: E402
from app.services.grounding.ngu_nghia import kiem_ngu_nghia  # noqa: E402


class _Chunk:
    def __init__(self, chunk_id: str, text: str):
        self.chunk_id = chunk_id
        self.text = text


def nap_case(version: str) -> dict[str, dict]:
    ra = {}
    for f in sorted((BASE / "evaluation" / "datasets" / version).glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in d.get("cases") or []:
            c["group"] = d.get("group", f.stem)
            ra[c["case_id"]] = c
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ket-qua", help="File .jsonl cua lan chay C2")
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
    print()

    tra_loi = [r for r in rs if not r.get("da_tu_choi") and not r.get("loi")]
    chan_them = []

    with ket_noi() as con, con.cursor() as cur:
        for r in tra_loi:
            ng = r.get("nguon") or []
            cur.execute("SELECT chunk_id, text FROM chunk WHERE chunk_id = ANY(%s)",
                        (list(ng),))
            chunks = [_Chunk(x, y) for x, y in cur.fetchall()]
            cs = cases.get(r["case_id"], {})
            loi = kiem_ngu_nghia(r["question"], r["answer"], chunks,
                                 cs.get("context_turns"))
            if loi:
                chan_them.append((r["case_id"], cs.get("expected_behavior"),
                                  cs.get("group"), loi[0]))

    print("C2 truoc tang 3 : " + str(len(tra_loi)) + " ca co tra loi / "
          + str(len(rs)) + " case")
    print("Tang 3 chan them: " + str(len(chan_them)) + " ca")
    print()
    for cid, mong, g, ly in chan_them:
        print("  " + cid.ljust(9) + " nhom=" + str(g).ljust(22)
              + " mong doi=" + str(mong))
        print("    " + ly)
    print()

    # Phan loai: chan DUNG hay chan NHAM
    dung = [x for x in chan_them if x[1] == "abstain"]
    khac = [x for x in chan_them if x[1] != "abstain"]
    print("  trong do mong doi `abstain` (chan DUNG) : " + str(len(dung)))
    print("  con lai (can nguoi phan)                : " + str(len(khac)))
    print()

    n = len(rs)
    print("answer_rate : " + str(round(100.0 * len(tra_loi) / n, 1))
          + "%  ->  " + str(round(100.0 * (len(tra_loi) - len(chan_them)) / n, 1))
          + "%")
    print()
    print("LUU Y: bang so chinh thuc trong BAO_CAO_SO_SANH.md van la bang")
    print("KHONG co tang 3, vi C0 cung khong co. So o day de biet tang 3")
    print("them duoc gi, khong phai de thay bang do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
