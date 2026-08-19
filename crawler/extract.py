#!/usr/bin/env python3
"""
extract.py - Tim cac cau chua so lieu trong van ban da crawl.

DAY LA LUONG 2 CUA DEC-020, KHONG PHAI NGUON CHO RETRIEVAL.

Quy chuan v2.0 muc 24 chot hai luong duyet tach roi:

  Luong 1 (retrieval): duyet o muc TAI LIEU -> chunk -> embedding -> pgvector
  Luong 2 (fact):      duyet o muc CAU      -> bang verified_facts

File nay phuc vu luong 2. Cau duoc duyet o day KHONG di vao vector DB. No
duoc dung cho ba viec khac:

  a) Kiem so lieu deterministic o Grounding Validator tang 2 (muc 18.2)
  b) Lam ground truth cho tap kiem thu (muc 29.1)
  c) Phat hien mau thuan giua cac nguon

Ban goc trong CRAWLER_GUIDE muc 6 viet "chi nhung dong verified:true moi
duoc nap vao vector DB". Cau do da bi thay the - lam dung nguyen van thi kho
tri thuc chi con cac cau roi rac chua so, mat het thoi vu, chon giong, lam
dat, sau benh.

Dau ra la DE XUAT. Moi dong verified=false cho den khi nguoi duyet doi.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BASE = Path(__file__).parent
TEXT = BASE / "data" / "text"
MANIFEST = BASE / "data" / "manifest.json"
OUT = BASE / "data" / "candidates.json"

# Tu khoa CHI SO - dung de LOC cau, khong dung de gan gia tri.
# Day la ten chi so, khong phai gia tri chi so: khong vi pham nguyen tac 1
# cua muc 23.1 (khong hard-code so lieu nong hoc).
KEYWORDS = {
    "do_am": ["độ ẩm", "ẩm độ"],
    "nhiet_do": ["nhiệt độ"],
    "ph": ["pH", "độ ph", "độ pH"],
    "ec": ["EC", "độ dẫn điện"],
    "nang_suat": ["năng suất", "tạ/ha", "tấn/ha"],
    # Bo sung so voi ban goc: day la nhung chi so nong dan hoi nhieu nhat
    # ma bo tu khoa cu bo sot hoan toan.
    "mat_do_gieo": ["mật độ", "khoảng cách trồng", "lượng giống", "kg giống"],
    "luong_phan": ["lượng phân", "bón lót", "bón thúc", "kg/ha", "npk", "đạm", "kali", "lân"],
    "thoi_vu": ["thời vụ", "gieo từ", "trồng từ", "vụ xuân", "vụ đông", "vụ hè thu",
                "vụ mùa", "đông xuân"],
    "khoang_cach": ["hàng cách hàng", "cây cách cây", "lên luống", "luống cao",
                    "rộng luống", "mặt luống"],
}

NUMBER = re.compile(r"\d+([.,]\d+)?")
MAX_SENTENCE_LEN = 400

# Tu khoa phai khop theo BIEN TU, khong phai so khop chuoi con.
#
# Ban goc trong CRAWLER_GUIDE so khop chuoi con nen "ph" khop ben trong
# "cat pha", "phat trien", "phan bon", "phu nilon" -> 73/129 cau bi gan nham
# nhan pH, trong khi thuc te chi vai cau noi ve pH.
KEYWORD_REGEX = {
    metric: [(kw, re.compile(r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)"))
             for kw in kws]
    for metric, kws in KEYWORDS.items()
}

# Tu khoa noi dung rui ro cao - cau trung phai duyet ky hon (muc 24.4).
# Day chi la co canh bao cho nguoi duyet, khong phai bo loc.
HIGH_RISK_HINTS = [
    "thuốc", "hoạt chất", "liều lượng", "nồng độ", "phun", "cách ly",
    "trừ sâu", "trừ bệnh", "diệt cỏ", "bvtv",
]


def sentences(text: str) -> list[str]:
    out = []
    for raw in re.split(r"(?<=[.!?;])\s+|\n", text):
        s = raw.strip()
        if s:
            out.append(s)
    return out


def is_high_risk(sentence: str) -> bool:
    low = sentence.lower()
    return any(hint in low for hint in HIGH_RISK_HINTS)


def context_hint(sents: list[str], idx: int, radius: int = 1) -> str:
    """Vai cau xung quanh, de nguoi duyet thay ngu canh.

    Mot cau roi mat ngu canh thi khong duyet duoc: "pH thich hop la ..." tach
    khoi doan thi khong con biet la pH dat hay pH nuoc tuoi, giai doan nao.
    """
    lo = max(0, idx - radius)
    hi = min(len(sents), idx + radius + 1)
    return " ".join(sents[lo:hi])


def match_metric(sentence: str) -> str | None:
    """Tra ve chi so phu hop nhat, hoac None.

    Khi mot cau trung nhieu chi so thi chon tu khoa DAI NHAT, khong chon theo
    thu tu khai bao. Ban goc chon theo thu tu dict nen cau "Bon lot: ... kg
    lan supe" bi gan nhan ph chi vi ph duoc khai bao truoc luong_phan.
    """
    low = sentence.lower()
    trung: list[tuple[int, str]] = []
    for metric, cap in KEYWORD_REGEX.items():
        for kw, rx in cap:
            if rx.search(low):
                trung.append((len(kw), metric))
    if not trung:
        return None
    trung.sort(key=lambda x: -x[0])
    return trung[0][1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Trich cau chua so lieu tu van ban da crawl")
    ap.add_argument("--crop", nargs="*", help="Chi xu ly cac cay nay")
    args = ap.parse_args()

    if not MANIFEST.exists():
        raise SystemExit("Chua co " + str(MANIFEST) + " - chay crawl.py truoc")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out: list[dict] = []

    for rec in manifest["records"]:
        if rec.get("status") != "ok":
            continue
        if args.crop and rec.get("crop") not in set(args.crop):
            continue

        path = TEXT / (rec["id"] + ".txt")
        if not path.exists():
            print("[!] thieu file van ban: " + str(path))
            continue

        sents = sentences(path.read_text(encoding="utf-8"))
        for idx, sent in enumerate(sents):
            if len(sent) > MAX_SENTENCE_LEN:
                continue
            if not NUMBER.search(sent):
                continue
            metric = match_metric(sent)
            if metric is None:
                continue

            out.append({
                "source_id": rec["id"],
                "crop": rec.get("crop"),
                "region": rec.get("region"),
                "publisher": rec.get("publisher"),
                "url": rec.get("url"),
                "source_tier": rec.get("source_tier"),
                "metric": metric,
                "sentence_index": idx,
                "sentence": sent,
                "context_hint": context_hint(sents, idx),
                "high_risk": is_high_risk(sent),
                # Nguoi duyet dien cac truong duoi day, tu NGUYEN VAN cau tren.
                # Khong suy dien, khong quy doi don vi.
                "verified": False,
                "value_min": None,
                "value_max": None,
                "unit": None,
                "stage": None,
                "reviewer": None,
                "note": None,
            })

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    theo_metric: dict[str, int] = {}
    theo_crop: dict[str, int] = {}
    for c in out:
        theo_metric[c["metric"]] = theo_metric.get(c["metric"], 0) + 1
        key = c["crop"] or "?"
        theo_crop[key] = theo_crop.get(key, 0) + 1

    print("Tim duoc " + str(len(out)) + " cau ung vien.")
    print("\nTheo chi so:")
    for m, n in sorted(theo_metric.items(), key=lambda x: -x[1]):
        print("  " + m.ljust(14) + str(n))
    print("\nTheo cay:")
    for c, n in sorted(theo_crop.items()):
        print("  " + c.ljust(14) + str(n))
    rui_ro = sum(1 for c in out if c["high_risk"])
    print("\nCau co dau hieu rui ro cao: " + str(rui_ro) + " (phai duyet ky hon)")
    print("\nGhi ra " + str(OUT) + ". Tat ca verified=false.")
    print("Duyet bang: python ../knowledge/review/review_facts.py")


if __name__ == "__main__":
    main()
