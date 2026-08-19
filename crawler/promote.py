#!/usr/bin/env python3
"""
promote.py - Dua ung vien tu discovered.json vao sources.yaml.

VI SAO LA MOT SCRIPT CHU KHONG PHAI SUA TAY

Sua tay 60-80 muc YAML thi vua lau vua de sai, va khong ai kiem lai duoc da
lam gi. Script nay lam viec do mot cach lap lai duoc, va chi lam DUNG mot
viec: chep URL + metadata tu de xuat sang danh sach nguon.

NO KHONG QUYET DINH TAI LIEU CO TOT HAY KHONG.

Viec loc tin tuc / quang cao ra khoi tai lieu ky thuat la viec cua buoc DUYET
TAI LIEU (knowledge/review/review_documents.py, cau hoi so 3 trong checklist
muc 27.2). Phan cong nhu vay la co y:

    crawler thu thap  ->  nguoi duyet loc  ->  chunk vao KB

Cho script tu doan "bai nay la tin tuc" roi loai truoc khi tai la sai nguyen
tac: no bo mat bang chung ma nguoi duyet chua he nhin thay.

CACH DUNG
    python promote.py --crop lua --limit 40
    python promote.py --all-crops --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import yaml

BASE = Path(__file__).parent
DISCOVERED = BASE / "data" / "discovered.json"
SOURCES = BASE / "sources.yaml"


def bo_dau(text: str) -> str:
    """Bo dau tieng Viet de sinh id ascii."""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def sinh_id(url: str, crop: str, da_dung: set[str]) -> str:
    """Sinh source_id on dinh tu duong dan URL."""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"\.(html?|aspx|php)$", "", slug, flags=re.I)
    slug = bo_dau(slug).lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")
    slug = "_".join(slug.split("_")[:6])[:52] or "nguon"

    base = crop + "__" + slug
    ma = base
    dem = 2
    while ma in da_dung:
        ma = base + "_" + str(dem)
        dem += 1
    return ma


def load_sources() -> dict:
    if not SOURCES.exists():
        return {"sources": []}
    return yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {"sources": []}


def main() -> None:
    ap = argparse.ArgumentParser(description="Dua ung vien vao sources.yaml")
    ap.add_argument("--crop", nargs="*", help="Chi lay cac cay nay")
    ap.add_argument("--all-crops", action="store_true",
                    help="Lay moi ung vien doan duoc cay trong")
    ap.add_argument("--limit", type=int, help="Toi da N ung vien moi cay")
    ap.add_argument("--dry-run", action="store_true", help="Chi in ra, khong ghi file")
    args = ap.parse_args()

    if not DISCOVERED.exists():
        raise SystemExit("Chua co " + str(DISCOVERED) + " - chay discover.py truoc")

    data = json.loads(DISCOVERED.read_text(encoding="utf-8"))
    cfg = load_sources()
    hien_co = {s["url"] for s in cfg["sources"]}
    da_dung = {s["id"] for s in cfg["sources"]}

    muon = set(args.crop) if args.crop else None
    dem_theo_cay: dict[str, int] = {}
    them: list[dict] = []

    for c in data.get("candidates", []):
        crop = c.get("crop_guess")
        if crop is None:              # khong doan duoc cay -> khong tu gan
            continue
        if muon and crop not in muon:
            continue
        if not (args.all_crops or muon):
            continue
        if c["url"] in hien_co:
            continue
        if args.limit and dem_theo_cay.get(crop, 0) >= args.limit:
            continue

        sid = sinh_id(c["url"], crop, da_dung)
        da_dung.add(sid)
        hien_co.add(c["url"])
        dem_theo_cay[crop] = dem_theo_cay.get(crop, 0) + 1

        them.append({
            "id": sid,
            "crop": crop,
            "region": c.get("region_hint"),
            "publisher": c.get("publisher"),
            "source_tier": c.get("source_tier") or 1,
            "url": c["url"],
            # Ghi lai xuat xu de truy nguoc duoc de xuat nay den tu dau
            "discovered_from": c.get("seed_id"),
            "discovered_anchor": (c.get("anchor") or "")[:150],
        })

    if not them:
        print("Khong co ung vien moi nao phu hop.")
        return

    print("Se them " + str(len(them)) + " nguon:")
    for crop, n in sorted(dem_theo_cay.items()):
        print("  " + crop.ljust(12) + str(n))

    if args.dry_run:
        print("\n(dry-run - khong ghi file)")
        for t in them[:10]:
            print("  " + t["id"][:46].ljust(48) + t["url"][:64])
        return

    cfg["sources"].extend(them)

    # Giu nguyen phan dau file (chu thich quy uoc) roi ghi lai toan bo danh sach
    goc = SOURCES.read_text(encoding="utf-8")
    dau = goc.split("sources:")[0] if "sources:" in goc else ""
    SOURCES.write_text(
        dau + yaml.safe_dump({"sources": cfg["sources"]}, allow_unicode=True,
                             sort_keys=False, width=120),
        encoding="utf-8")

    print("\nDa ghi " + str(SOURCES) + " - tong " + str(len(cfg["sources"])) + " nguon.")
    print("Chay 'python crawl.py' de tai. Nguon loi thi de nguyen la loi.")


if __name__ == "__main__":
    main()
