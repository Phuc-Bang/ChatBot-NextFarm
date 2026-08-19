#!/usr/bin/env python3
"""
chunker.py - Cat tai lieu thanh chunk de truy xuat.

Quy chuan v2.0 muc 26.

NGUYEN TAC

  1. Cat theo CAU TRUC tai lieu truoc, theo do dai sau.
     Tai lieu quy trinh ky thuat tieng Viet gan nhu luon co muc danh so:
     "1. Thoi vu", "II. Lam dat", "a) Bon lot". Cat theo do giu duoc y nghia;
     cat theo do dai thuan tuy se xe doi quy trinh.

  2. Giu section_title vao chunk.
     Mot chunk noi "pH thich hop la ..." ma tach khoi tieu de muc thi khong
     con biet la pH dat hay pH nuoc tuoi. Day chinh la ly do quy chuan chon
     duyet o muc tai lieu thay vi muc cau (DEC-020).

  3. Tha chunk dai hon con hon chunk mat nua quy trinh.
     Khong cat ngang mot bang so lieu hay mot danh sach buoc ky thuat.

  4. Danh co is_high_risk theo tu dien viet tay.
     Chunk trung tu khoa rui ro cao phai duyet le tung chunk (muc 24.4), nen
     nap vao voi approved=False. Rang buoc trong lucoc do se chan neu quen.

  5. Sinh san ban BO DAU cho moi chunk.
     Day la co che giai bai toan cau hoi khong dau o TANG DU LIEU (muc 14.3),
     khong phai bang cach de LLM doan dau. Doan dau la bia; khop tren ban bo
     dau la tra cuu.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent.parent))

# bo_dau dinh nghia MOT LAN o app/core/text.py va dung chung cho ca phia nap
# du lieu (file nay) lan phia cau hoi (app/services/normalization). Hai phia
# bo dau khac nhau thi keyword search truot lang le - xem giai thich trong
# app/core/text.py.
from app.core.text import bo_dau  # noqa: E402
LEXICON = BASE.parent / "lexicon" / "high_risk_terms.yaml"

# Kich thuoc muc tieu tinh bang KY TU (khong phai token).
# [TODO] Chot lai sau khi do Recall@K o P6 - quy chuan muc 26 khong cho phep
# chot con so nay tren giay.
KICH_THUOC_MUC_TIEU = 1200
KICH_THUOC_TOI_DA = 2200
CHONG_LAN = 150
CHUNK_TOI_THIEU = 120

# Cac dang tieu de muc thuong gap trong tai lieu ky thuat tieng Viet
TIEU_DE = [
    re.compile(r"^\s*(\d{1,2})\s*[.)]\s+(\S.{0,90})$"),          # 1. Thoi vu
    re.compile(r"^\s*([IVX]{1,5})\s*[.)]\s+(\S.{0,90})$"),       # II. Lam dat
    re.compile(r"^\s*([a-z])\s*[.)]\s+(\S.{0,90})$"),            # a) Bon lot
    re.compile(r"^\s*[-*+•]\s*(\S.{0,60}):\s*$"),                # - Bon phan:
    re.compile(r"^\s*(\S.{0,60}):\s*$"),                         # Thoi vu:
]


def tai_tu_khoa_rui_ro() -> tuple[list[str], list[str]]:
    """Tra ve (high_risk_terms, caution_terms).

    Hai muc, hai he qua khac nhau - xem knowledge/lexicon/high_risk_terms.yaml:
      high_risk -> chunk PHAI duyet le tung chunk truoc khi index (muc 24.4)
      caution   -> chunk duyet gop nhu binh thuong, nhung cau tra loi dung
                   chunk nay bat buoc kem canh bao (muc 19 case C4)
    """
    if not LEXICON.exists():
        return [], []
    data = yaml.safe_load(LEXICON.read_text(encoding="utf-8")) or {}
    return ([str(t).lower() for t in (data.get("high_risk_terms") or [])],
            [str(t).lower() for t in (data.get("caution_terms") or [])])


def la_tieu_de(dong: str) -> str | None:
    """Tra ve tieu de neu dong nay trong nhu mot tieu de muc, nguoc lai None."""
    d = dong.strip()
    if not d or len(d) > 100:
        return None
    if d.endswith((".", "!", "?")) and not d.endswith(("...",)):
        return None            # cau van hoan chinh, khong phai tieu de
    for rx in TIEU_DE:
        m = rx.match(d)
        if m:
            return d
    # Dong VIET HOA toan bo cung thuong la tieu de
    chu = [c for c in d if c.isalpha()]
    if len(chu) >= 6 and all(c.isupper() for c in chu):
        return d
    return None


@dataclass
class Chunk:
    ordinal: int
    text: str
    section_title: str | None
    is_high_risk: bool
    needs_caution: bool = False
    text_unaccent: str = ""
    tu_khoa_rui_ro: list[str] = field(default_factory=list)
    tu_khoa_canh_bao: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.text_unaccent:
            self.text_unaccent = bo_dau(self.text)


def tach_muc(text: str) -> list[tuple[str | None, list[str]]]:
    """Tach van ban thanh cac muc theo tieu de. Tra ve [(tieu_de, [dong])]."""
    muc: list[tuple[str | None, list[str]]] = []
    tieu_de_hien_tai: str | None = None
    dong_hien_tai: list[str] = []

    for dong in text.splitlines():
        if not dong.strip():
            continue
        td = la_tieu_de(dong)
        if td is not None:
            if dong_hien_tai:
                muc.append((tieu_de_hien_tai, dong_hien_tai))
            tieu_de_hien_tai = td
            dong_hien_tai = []
        else:
            dong_hien_tai.append(dong.strip())

    if dong_hien_tai or tieu_de_hien_tai:
        muc.append((tieu_de_hien_tai, dong_hien_tai))
    return muc


def cat_theo_do_dai(dong: list[str]) -> list[str]:
    """Cat mot muc qua dai thanh nhieu manh, cat o ranh gioi DONG.

    Khong bao gio cat giua dong: mot dong trong tai lieu ky thuat thuong la
    mot buoc hoac mot hang bang: cat doi la mat nghia.
    """
    manh: list[str] = []
    hien_tai: list[str] = []
    do_dai = 0

    for d in dong:
        them = len(d) + 1
        qua_dai = do_dai + them > KICH_THUOC_MUC_TIEU
        # Dong ket thuc bang dau hai cham dang mo dau mot danh sach -> khong
        # cat ngay sau no
        mo_danh_sach = hien_tai and hien_tai[-1].rstrip().endswith(":")

        if hien_tai and qua_dai and not mo_danh_sach:
            manh.append("\n".join(hien_tai))
            # chong lan: giu vai dong cuoi de khong mat ngu canh
            giu, n = [], 0
            for truoc in reversed(hien_tai):
                if n + len(truoc) > CHONG_LAN:
                    break
                giu.insert(0, truoc)
                n += len(truoc)
            hien_tai = giu
            do_dai = n

        hien_tai.append(d)
        do_dai += them

        if do_dai > KICH_THUOC_TOI_DA:      # cung phai cat, du dang mo danh sach
            manh.append("\n".join(hien_tai))
            hien_tai, do_dai = [], 0

    if hien_tai:
        manh.append("\n".join(hien_tai))
    return [m for m in manh if m.strip()]


def cat(text: str, tu_khoa_rui_ro: list[str] | None = None,
        tu_khoa_canh_bao: list[str] | None = None) -> list[Chunk]:
    """Cat toan bo mot tai lieu thanh chunk."""
    if tu_khoa_rui_ro is None or tu_khoa_canh_bao is None:
        mac_dinh_rui_ro, mac_dinh_canh_bao = tai_tu_khoa_rui_ro()
        tu_khoa = mac_dinh_rui_ro if tu_khoa_rui_ro is None else tu_khoa_rui_ro
        canh_bao = mac_dinh_canh_bao if tu_khoa_canh_bao is None else tu_khoa_canh_bao
    else:
        tu_khoa, canh_bao = tu_khoa_rui_ro, tu_khoa_canh_bao
    ket_qua: list[Chunk] = []
    ordinal = 0

    for tieu_de, dong in tach_muc(text):
        if not dong:
            continue
        for manh in cat_theo_do_dai(dong):
            noi_dung = (tieu_de + "\n" + manh) if tieu_de else manh
            if len(noi_dung.strip()) < CHUNK_TOI_THIEU:
                # Manh qua ngan: gop vao chunk truoc thay vi tao chunk vun
                if ket_qua:
                    truoc = ket_qua[-1]
                    truoc.text = truoc.text + "\n" + manh
                    truoc.text_unaccent = bo_dau(truoc.text)
                    thap_truoc = truoc.text.lower()
                    trung = [t for t in tu_khoa if t in thap_truoc]
                    cb = [t for t in canh_bao if t in thap_truoc]
                    truoc.is_high_risk = bool(trung)
                    truoc.tu_khoa_rui_ro = trung
                    truoc.needs_caution = bool(trung or cb)
                    truoc.tu_khoa_canh_bao = cb
                    continue

            thap = noi_dung.lower()
            trung = [t for t in tu_khoa if t in thap]
            cb = [t for t in canh_bao if t in thap]
            ordinal += 1
            ket_qua.append(Chunk(
                ordinal=ordinal,
                text=noi_dung.strip(),
                section_title=tieu_de,
                is_high_risk=bool(trung),
                # Chunk rui ro cao thi duong nhien cung phai kem canh bao
                needs_caution=bool(trung or cb),
                tu_khoa_rui_ro=trung,
                tu_khoa_canh_bao=cb,
            ))

    return ket_qua
