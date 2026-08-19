#!/usr/bin/env python3
"""
discover.py - Tim URL bai viet that tu cac trang chuyen muc da biet.

VI SAO CAN FILE NAY

sources.yaml can 50-80 nguon (ASM-07) nhung khong ai duoc phep NGOI GO TAY
50-80 URL ra. Doan URL la mot dang bia dat: phan lon se 404, va nhung cai
song sot thi cung khong ai biet noi dung co dung khong.

Cach lam dung: xuat phat tu vai trang CHUYEN MUC da biet la that, thu thap
link bai viet tu do, loc theo tu khoa cay trong, roi de NGUOI DUYET quyet
dinh cai nao vao sources.yaml.

Dau ra la DE XUAT, chua phai nguon chinh thuc - giong het quan he giua
extract.py va verified_facts.

CACH DUNG

    python discover.py                    # chay tat ca seed
    python discover.py --seed ninhbinh_kht
    python discover.py --max-links 40

Ket qua ghi vao data/discovered.json. Doc file do, chon URL phu hop, them
vao sources.yaml kem crop/region/publisher/source_tier.
"""

from __future__ import annotations

import argparse
import json
import re
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
import yaml
from bs4 import BeautifulSoup

from crawl import DomainThrottle, fetch
from robots import RobotsCache

BASE = Path(__file__).parent
SEEDS = BASE / "seeds.yaml"
OUT = BASE / "data" / "discovered.json"
SOURCES = BASE / "sources.yaml"

TIMEOUT = 20
CONTACT = os.environ.get("CRAWLER_CONTACT_EMAIL", "").strip()
UA = "NextFarmBot/0.2 (nghien cuu hoc thuat; lien he: " + (CONTACT or "chua dien") + ")"

# Tu khoa nhan dien cay trong, ca dang co dau va khong dau.
# Day la tu khoa TEN CAY, khong phai so lieu nong hoc - khong vi pham
# nguyen tac 1 cua muc 23.1.
#
# Phai khop theo BIEN TU. Lan chay dau tien dung so khop chuoi thuong nen
# "ma" khop ben trong "manh" -> gan nham nhan lua cho mot bai ve nong thon
# moi. Doan sai o buoc de xuat khong nguy hiem bang doan sai o buoc tra loi,
# nhung van phai sua: nguoi duyet se tin vao nhan neu no thuong dung.
CROP_PATTERNS = {
    "lua": [r"lúa", r"lua", r"thóc", r"thoc", r"gieo sạ", r"gieo sa", r"mạ"],
    "ca_chua": [r"cà chua", r"ca chua"],
    "dua_chuot": [r"dưa chuột", r"dua chuot", r"dưa leo", r"dua leo"],
}
CROP_REGEX = {
    crop: [re.compile(r"(?<!\w)" + pat + r"(?!\w)") for pat in pats]
    for crop, pats in CROP_PATTERNS.items()
}

# Bai viet ky thuat thuong nam trong nhung chuyen muc nay
TECHNIQUE_HINTS = [
    "ky-thuat", "kỹ thuật", "quy-trinh", "quy trình", "huong-dan", "hướng dẫn",
    "cham-soc", "chăm sóc", "trong-", "trồng", "phong-tru", "phòng trừ",
    "san-xuat", "sản xuất", "canh-tac", "canh tác",
]


def normalize(text: str) -> str:
    return " " + " ".join(text.lower().split()) + " "


def guess_crop(text: str) -> str | None:
    """Doan cay trong tu tieu de/URL. Khong chac thi tra None - de nguoi duyet."""
    hay = normalize(text)
    hits = [crop for crop, regexes in CROP_REGEX.items()
            if any(rx.search(hay) for rx in regexes)]
    return hits[0] if len(hits) == 1 else None


def looks_like_article(url: str, anchor: str) -> bool:
    hay = normalize(url + " " + anchor)
    return any(hint in hay for hint in TECHNIQUE_HINTS)


def load_seeds() -> list[dict]:
    if not SEEDS.exists():
        sys.exit("Khong tim thay " + str(SEEDS))
    cfg = yaml.safe_load(SEEDS.read_text(encoding="utf-8")) or {}
    seeds = cfg.get("seeds") or []
    if not seeds:
        sys.exit("seeds.yaml khong co seed nao")
    return seeds


def existing_urls() -> set[str]:
    """URL da co trong sources.yaml - khong de xuat lai."""
    if not SOURCES.exists():
        return set()
    cfg = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    return {s["url"] for s in (cfg.get("sources") or [])}


def harvest(seed: dict, session, robots: RobotsCache, throttle: DomainThrottle,
            max_links: int) -> tuple[list[dict], str | None]:
    """Tra ve (danh sach de xuat, loi). Loi != None nghia la seed that bai."""
    url = seed["url"]

    decision = robots.check(url)
    if not decision.allowed:
        return [], "robots: " + decision.reason

    throttle.wait(url, override=decision.crawl_delay)
    content, _ctype, http_status, err = fetch(url, session)
    if content is None:
        return [], err or ("HTTP " + str(http_status))

    soup = BeautifulSoup(content, "lxml")
    host = urlsplit(url).netloc
    seen: set[str] = set()
    found: list[dict] = []

    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"].strip())
        parts = urlsplit(href)

        if parts.scheme not in ("http", "https"):
            continue
        if parts.netloc != host:            # chi lay lien ket cung ten mien
            continue
        clean = parts._replace(fragment="").geturl()
        if clean in seen or clean == url:
            continue

        anchor = a.get_text(" ", strip=True)
        if len(anchor) < 12:                # link dieu huong, khong phai bai viet
            continue
        if not looks_like_article(clean, anchor):
            continue

        crop = guess_crop(anchor + " " + clean)
        seen.add(clean)
        found.append({
            "url": clean,
            "anchor": anchor,
            "crop_guess": crop,            # None = khong chac, nguoi duyet quyet
            "seed_id": seed["id"],
            "publisher": seed.get("publisher"),
            "region_hint": seed.get("region"),
            "source_tier": seed.get("source_tier"),
        })
        if len(found) >= max_links:
            break

    return found, None


def main() -> None:
    ap = argparse.ArgumentParser(description="Tim URL bai viet tu trang chuyen muc")
    ap.add_argument("--seed", nargs="*", help="Chi chay cac seed_id nay")
    ap.add_argument("--max-links", type=int, default=60,
                    help="So link toi da lay tu moi trang chuyen muc")
    args = ap.parse_args()

    seeds = load_seeds()
    if args.seed:
        wanted = set(args.seed)
        seeds = [s for s in seeds if s["id"] in wanted]

    session = requests.Session()
    robots = RobotsCache(user_agent=UA, timeout=TIMEOUT)
    throttle = DomainThrottle()
    already = existing_urls()

    all_found: list[dict] = []
    seed_status: list[dict] = []

    for seed in seeds:
        found, err = harvest(seed, session, robots, throttle, args.max_links)
        if err:
            print("[XX] " + seed["id"] + ": " + err)
            seed_status.append({"seed_id": seed["id"], "status": "failed", "error": err})
            continue

        moi = [f for f in found if f["url"] not in already]
        print("[OK] " + seed["id"] + ": " + str(len(found)) + " lien ket, "
              + str(len(moi)) + " chua co trong sources.yaml")
        seed_status.append({"seed_id": seed["id"], "status": "ok",
                            "found": len(found), "new": len(moi)})
        all_found.extend(moi)

    # Bo trung URL giua cac seed
    unique: dict[str, dict] = {}
    for item in all_found:
        unique.setdefault(item["url"], item)
    ket_qua = list(unique.values())

    OUT.write_text(
        json.dumps({"discovered_at": datetime.now(timezone.utc).isoformat(),
                    "seeds": seed_status,
                    "candidates": ket_qua},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")

    theo_cay: dict[str, int] = {}
    for item in ket_qua:
        key = item["crop_guess"] or "chua_ro"
        theo_cay[key] = theo_cay.get(key, 0) + 1

    print("\n--- De xuat ---")
    for crop, n in sorted(theo_cay.items()):
        print("  " + crop.ljust(12) + str(n))
    print("  " + "TONG".ljust(12) + str(len(ket_qua)))
    print("\nGhi ra " + str(OUT) + ". Day la DE XUAT - doc va chon truoc khi "
          "them vao sources.yaml.")


if __name__ == "__main__":
    main()
