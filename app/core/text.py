#!/usr/bin/env python3
"""
text.py - Ham xu ly van ban dung chung cho CA hai phia cua retrieval.

VI SAO FILE NAY PHAI TON TAI RIENG

Keyword search cua he thong nay khop ban BO DAU cua cau hoi voi ban BO DAU
cua chunk (muc 14.2, 14.3 quy chuan v2.0):

    cau hoi "ca chua can dat ph bao nhieu"
        -> bo_dau -> "ca chua can dat ph bao nhieu"
    chunk    "Ca chua thich hop voi dat co do pH..."
        -> bo_dau -> "ca chua thich hop voi dat co do ph..."
                     ^^^^^^^^ khop truc tiep

Neu hai phia bo dau theo hai cach khac nhau - du chi lech mot ky tu, vi du
mot ben doi "d" gach ngang con ben kia khong - thi keyword search KHONG bao
loi. No chi tra ve it ket qua hon, lang le, mai mai. Do la kieu loi te nhat:
he thong van chay, so lieu van co, chi la sai.

Vi vay bo_dau chi duoc dinh nghia DUNG MOT LAN, o day. Ca chunker (phia nap
du lieu) va normalization (phia cau hoi) deu import tu day. Test
tests/test_normalization.py::test_hai_phia_dung_chung_mot_ham canh giu dieu do.
"""

from __future__ import annotations

import re
import unicodedata

KHOANG_TRANG = re.compile(r"\s+")


def bo_dau(text: str) -> str:
    """Bo dau tieng Viet, giu nguyen chu va so, tra ve chu thuong.

    Khop voi hanh vi cua unaccent trong PostgreSQL cho tieng Viet: d gach
    ngang -> d, va cac dau thanh/dau mu bi loai.

    Buoc thay "d" gach ngang phai lam TRUOC khi tach NFD, vi "d" gach ngang
    la mot ky tu doc lap trong Unicode chu khong phai "d" + dau ket hop -
    tach NFD khong dung toi no.
    """
    text = text.replace("đ", "d").replace("Đ", "D")
    nfd = unicodedata.normalize("NFD", text)
    khong_dau = "".join(c for c in nfd if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", khong_dau).lower()


def gon_khoang_trang(text: str) -> str:
    """Gop moi chuoi khoang trang (ke ca xuong dong, tab) thanh mot dau cach."""
    return KHOANG_TRANG.sub(" ", text).strip()


def chuan_hoa_nfc(text: str) -> str:
    """Chuan hoa Unicode ve NFC.

    Tieng Viet go tren Windows, macOS va web thuong ra ba dang byte khac nhau
    cho cung mot chu ("ế" co the la 1, 2 hoac 3 code point). Khong chuan hoa
    thi so sanh chuoi va khop tu dien deu truot ma khong bao loi.
    """
    return unicodedata.normalize("NFC", text)
