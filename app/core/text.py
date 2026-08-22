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


def co_dau(s: str) -> bool:
    """Chuoi co mang dau tieng Viet khong."""
    return bo_dau(s) != s.lower()


def khop_cum(chuan: str, khong_dau: str, cum: str,
              co_dau_goc: bool | None = None) -> bool:
    """Khop mot cum tu, CO DAU khi cau hoi co dau.

    VI SAO KHONG KHOP THANG TREN BAN BO DAU

    Bo dau la thu bat buoc de chiu duoc cau hoi khong dau (muc 14.3), nhung
    no xoa mat dau thanh - va dau thanh la thu phan biet nhieu cap tu:

        "bi ngo doc phen"  <- "bi ngo" o day la "bi ngo", khong phai "bi ngo"
        "vai lua"          <- "lua" o day la "lua", khong phai "lua"
        "vuon toi"         <- "toi" o day la "toi", khong phai "toi"

    Khop tron tu khong cuu duoc nhung truong hop nay vi tieng Viet viet roi
    tung am tiet: moi am tiet deu la mot "tu tron" (DEC-031, muc 13.4).

    Nhung phan lon nguoi dung CO go dau. Khi ho go dau, thong tin phan biet
    van con nguyen - chi la ta da tu vut no di truoc khi khop. Ham nay giu
    lai: co dau thi khop tren ban co dau, khong dau moi khop tren ban bo dau.

    Nguoi go khong dau van duoc phuc vu, chi la chiu rui ro va cham cao hon -
    va do la rui ro cua chinh cach go, khong phai cua he thong.
    """
    # Quyet dinh dua vao CAU HOI co dau hay khong, KHONG dua vao tu can tim.
    # Nhieu ten cay von khong co dau ("lan", "na", "cam", "nho"); neu doi ca
    # hai phia deu co dau thi nhung tu do luon roi ve nhanh bo dau, va "lan"
    # se khop trong "LAN truoc anh bao...".
    #
    # co_dau_goc phai la dau cua cau hoi NGUOI DUNG GO, khong phai cua ban da
    # chuan hoa. Lop 2 co the THEM dau vao cau: "bao nhieu kg" -> "bao nhieu
    # khong" bien mot cau khong dau thanh co dau, roi tu do "dua chuot" khong
    # con khop voi "dua chuot" nua. Lan lam hong nay khong bao loi mot tieng.
    if co_dau_goc if co_dau_goc is not None else co_dau(chuan):
        ban, muc = chuan, cum.lower()
    else:
        ban, muc = khong_dau, bo_dau(cum)
    return re.search(r"(?<!\w)" + re.escape(muc) + r"(?!\w)", ban) is not None


def bam_chunk(text: str) -> str:
    """Van tay cua NOI DUNG mot chunk. Dung lam khoa cho quyet dinh duyet le.

    VI SAO CAN HAM NAY - phat hien 2026-08-22

    Truoc day quyet dinh duyet le (knowledge/review/chunks.yaml) khoa vao
    `chunk_id`, ma chunk_id dung theo THU TU trong tai lieu:

        cid = rec["id"] + "#" + str(c.ordinal)     # load.py:153

    Doi bat ky hang so cat chunk nao la moi ordinal xe dich. Chunk
    `hatinh_dua_chuot_vietgap#1` sau khi cat lai la MOT DOAN VAN KHAC, nhung
    van nhan quyet dinh duyet cu - va khong co gi bao loi. Mot chunk tung bi
    loai vi "tieu de tin tuc" co the duoc cap phep vao kho lieu luong.

    Khoa theo noi dung thi hong theo huong AN TOAN: van ban doi -> bam doi ->
    khong khop -> chunk rui ro cao khong duoc duyet -> DEC-005 chan. Nguoi
    duyet thay ngay bang `review_chunks.py --status`.

    Chuan hoa truoc khi bam: NFC + gon khoang trang. Hai thu nay khong doi
    NGHIA cua chunk, nen mot khac biet ve khoang trang khong duoc phep huy mot
    quyet dinh duyet that.
    """
    import hashlib

    chuan = gon_khoang_trang(chuan_hoa_nfc(text)).strip()
    return hashlib.sha256(chuan.encode("utf-8")).hexdigest()
