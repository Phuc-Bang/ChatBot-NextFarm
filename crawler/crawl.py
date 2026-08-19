#!/usr/bin/env python3
"""
crawl.py - Tai tai lieu tu sources.yaml, luu bang chung goc.

BON NGUYEN TAC BAT BUOC (quy chuan v2.0 muc 23.1):

  1. Khong hard-code so lieu nong hoc trong script. Moi con so phai den tu
     tai lieu tai ve, khong phai tu tay nguoi viet code.
  2. Luu bang chung goc: file tho + URL + HTTP status + thoi diem + hash.
  3. That bai phai la that bai. Trang loi -> status "failed", KHONG duoc thay
     bang du lieu mac dinh, KHONG duoc "cuu" bang du lieu tay.
  4. Crawl va trich xuat tach roi. File nay chi tai va tach van ban.

Vi pham bat ky diem nao -> crawler tro thanh nguon hallucination.

Bo sung so voi ban goc trong CRAWLER_GUIDE:
  - Kiem robots.txt truoc moi URL           (DEC-028a)
  - Doc duoc file PDF bang pypdf            (DEC-027)
  - Gian nhip request theo TUNG ten mien    (DEC-028b)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
import yaml
from bs4 import BeautifulSoup

from robots import RobotsCache

BASE = Path(__file__).parent
RAW = BASE / "data" / "raw"
TEXT = BASE / "data" / "text"
MANIFEST = BASE / "data" / "manifest.json"
SOURCES = BASE / "sources.yaml"

DELAY = 3.0         # giay toi thieu giua 2 request CUNG mot ten mien
TIMEOUT = 20
MIN_TEXT_LEN = 200  # ngan hon nguong nay -> coi nhu khong co noi dung

CONTACT = os.environ.get("CRAWLER_CONTACT_EMAIL", "").strip()
UA = "NextFarmBot/0.2 (nghien cuu hoc thuat; lien he: " + (CONTACT or "chua dien") + ")"

# Cac trang thai co the ghi ra manifest. Khong co trang thai nao mang y nghia
# "that bai nhung van dung tam du lieu khac".
STATUS_OK = "ok"
STATUS_EMPTY = "empty"
STATUS_FAILED = "failed"
STATUS_ROBOTS = "robots_disallowed"


# ----------------------------------------------------------------------
# Gian nhip theo ten mien
# ----------------------------------------------------------------------
class DomainThrottle:
    """Bao dam hai request cung mot ten mien cach nhau it nhat `delay` giay.

    Ban goc trong CRAWLER_GUIDE sleep sau MOI request bat ke ten mien nao,
    nen crawl 60 nguon mat it nhat 3 phut cho khong. Cach nay van lich su
    voi tung may chu ma tong thoi gian ngan hon nhieu.
    """

    def __init__(self, delay: float = DELAY) -> None:
        self.delay = delay
        self._last: dict[str, float] = {}

    def wait(self, url: str, override: float | None = None) -> None:
        host = urlsplit(url).netloc
        delay = max(self.delay, override or 0.0)
        last = self._last.get(host)
        if last is not None:
            remaining = delay - (time.monotonic() - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last[host] = time.monotonic()


# ----------------------------------------------------------------------
# Tai va tach van ban
# ----------------------------------------------------------------------
def fetch(url: str, session: requests.Session):
    """Tra ve (content_bytes, content_type, http_status, error).

    content_bytes = None neu that bai. Khong bao gio tra ve du lieu thay the.
    """
    try:
        resp = session.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return None, None, None, type(exc).__name__ + ": " + str(exc)

    if resp.status_code != 200:
        return None, None, resp.status_code, "HTTP " + str(resp.status_code)

    ctype = (resp.headers.get("Content-Type") or "").lower()
    return resp.content, ctype, resp.status_code, None


def is_pdf(url: str, content_type: str | None, content: bytes | None) -> bool:
    """Nhan dien PDF theo Content-Type, duoi file, hoac chu ky %PDF-."""
    if content_type and "application/pdf" in content_type:
        return True
    if urlsplit(url).path.lower().endswith(".pdf"):
        return True
    if content and content[:5] == b"%PDF-":
        return True
    return False


def html_to_text(content: bytes) -> str:
    """Tach van ban hien thi. Bo script/style/nav/footer/header/form."""
    soup = BeautifulSoup(content, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "noscript"]):
        tag.decompose()
    lines = [ln.strip() for ln in soup.get_text("\n").splitlines()]
    return "\n".join(ln for ln in lines if ln)


def html_title(content: bytes) -> str | None:
    """Lay title tu the <title> hoac <h1>. Khong co thi tra None - khong doan."""
    soup = BeautifulSoup(content, "lxml")
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        if title:
            return title
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
        if title:
            return title
    return None


def pdf_to_text(content: bytes) -> tuple[str, str | None]:
    """Tach van ban tu PDF. Tra ve (text, title). title=None neu PDF khong ghi."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # trang hong thi bo qua trang do, khong bo ca file
            pages.append("")
    joined = "\n".join(pages)
    text = "\n".join(ln.strip() for ln in joined.splitlines() if ln.strip())

    title = None
    try:
        meta = reader.metadata
        meta_title = meta.get("/Title") if meta else None
        if meta_title and str(meta_title).strip():
            title = str(meta_title).strip()
    except Exception:
        title = None
    return text, title


# ----------------------------------------------------------------------
def load_sources() -> list[dict]:
    if not SOURCES.exists():
        sys.exit("Khong tim thay " + str(SOURCES))
    cfg = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    sources = cfg.get("sources") or []
    if not sources:
        sys.exit("sources.yaml khong co nguon nao")
    return sources


def crawl_one(src: dict, session: requests.Session, robots: RobotsCache,
              throttle: DomainThrottle) -> dict:
    """Tai mot nguon. Luon tra ve mot ban ghi manifest, ke ca khi that bai."""
    sid = src["id"]
    url = src["url"]
    now = datetime.now(timezone.utc).isoformat()
    record = dict(src)
    record["fetched_at"] = now

    # 1. robots.txt
    decision = robots.check(url)
    if not decision.allowed:
        print("[--] " + sid + ": bi robots.txt chan - " + decision.reason)
        record.update(status=STATUS_ROBOTS, http_status=None, error=decision.reason)
        return record

    # 2. Tai
    throttle.wait(url, override=decision.crawl_delay)
    content, ctype, http_status, err = fetch(url, session)
    if content is None:
        print("[XX] " + sid + ": " + str(err))
        record.update(status=STATUS_FAILED, http_status=http_status, error=err)
        return record

    # 3. Tach van ban
    try:
        if is_pdf(url, ctype, content):
            doc_type = "pdf"
            text, title = pdf_to_text(content)
            raw_name = sid + ".pdf"
        else:
            doc_type = "html"
            text = html_to_text(content)
            title = html_title(content)
            raw_name = sid + ".html"
    except Exception as exc:
        msg = "parse: " + type(exc).__name__ + ": " + str(exc)
        print("[XX] " + sid + ": khong tach duoc van ban - " + msg)
        record.update(status=STATUS_FAILED, http_status=http_status, error=msg)
        return record

    # 4. Noi dung qua ngan -> coi nhu that bai, KHONG bu bang gi ca
    if len(text) < MIN_TEXT_LEN:
        print("[XX] " + sid + ": noi dung qua ngan (" + str(len(text)) + " ky tu)")
        record.update(status=STATUS_EMPTY, http_status=http_status,
                      doc_type=doc_type, text_length=len(text))
        return record

    # 5. Luu bang chung
    (RAW / raw_name).write_bytes(content)
    (TEXT / (sid + ".txt")).write_text(text, encoding="utf-8")

    print("[OK] " + sid + ": " + str(len(text)) + " ky tu (" + doc_type + ")")
    record.update(
        status=STATUS_OK,
        http_status=http_status,
        doc_type=doc_type,
        title=title,               # None neu trang khong ghi title - khong doan
        text_length=len(text),
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        raw_file="data/raw/" + raw_name,
        text_file="data/text/" + sid + ".txt",
    )
    return record


def main() -> None:
    ap = argparse.ArgumentParser(description="Tai tai lieu tu sources.yaml")
    ap.add_argument("--only", nargs="*", help="Chi tai cac source_id nay")
    ap.add_argument("--limit", type=int, help="Chi tai N nguon dau tien")
    args = ap.parse_args()

    if not CONTACT:
        print("[!] CRAWLER_CONTACT_EMAIL chua duoc dat - User-Agent se thieu "
              "dia chi lien he. Xem .env.example.", file=sys.stderr)

    RAW.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)

    sources = load_sources()
    if args.only:
        wanted = set(args.only)
        sources = [s for s in sources if s["id"] in wanted]
    if args.limit:
        sources = sources[: args.limit]

    session = requests.Session()
    robots = RobotsCache(user_agent=UA, timeout=TIMEOUT)
    throttle = DomainThrottle(DELAY)

    records = [crawl_one(src, session, robots, throttle) for src in sources]

    MANIFEST.write_text(
        json.dumps(
            {"crawled_at": datetime.now(timezone.utc).isoformat(),
             "user_agent": UA,
             "records": records},
            ensure_ascii=False, indent=2),
        encoding="utf-8")

    tally: dict[str, int] = {}
    for rec in records:
        tally[rec["status"]] = tally.get(rec["status"], 0) + 1

    print("\n--- Ket qua ---")
    for status in (STATUS_OK, STATUS_EMPTY, STATUS_FAILED, STATUS_ROBOTS):
        if status in tally:
            print("  " + status.ljust(20) + str(tally[status]))
    print("  " + "TONG".ljust(20) + str(len(records)))

    if tally.get(STATUS_OK, 0) == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
