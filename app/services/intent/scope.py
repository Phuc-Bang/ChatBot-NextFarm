#!/usr/bin/env python3
"""
scope.py - Scope Check (quy chuan v2.0 muc 12).

Chay SAU Intent Router, va CHI cho nhanh agronomy_knowledge. Cau hoi so lieu
vuon da bi router chan tu truoc; dua no vao day chi lam ra mot cau tu choi
sai loai.

NGUYEN TAC QUYET DINH - doc ky, day la cho de lam sai

    Chi mot dieu quyet dinh co tra loi hay khong:
    CO NHAN RA CAY TRONG PHAM VI (lua / ca chua / dua chuot) HAY KHONG.

        nhan ra          -> di tiep
        khong nhan ra    -> KHONG tra loi, du the nao

    Danh sach cay ngoai pham vi (out_of_scope_crops.yaml) KHONG tham gia
    quyet dinh do. No chi lam cau tu choi cu the hon:
        khong co danh sach -> "em chua ro anh/chi hoi cay gi"
        co danh sach       -> "em chua co tai lieu ve ca phe"

VI SAO KHONG LAM NGUOC LAI

Cach lam truc quan hon la: liet ke cay ngoai pham vi, thay cay nao trong
danh sach thi tu choi. Cach do co mot lo ro khong bao gio va duoc: danh sach
cay trong o Viet Nam khong liet ke het duoc. Bot gap mot cay la, khong thay
trong danh sach cam, roi tra loi bang kien thuc nen cua LLM - dung thu muc
12 cam.

Voi cach hien tai, thieu sot trong danh sach chi lam cau tu choi chung chung
hon. No khong bao gio lam lot mot cau tra loi.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE))

from app.core.text import bo_dau, co_dau, khop_cum  # noqa: E402
from app.services.normalization.vietnamese import (  # noqa: E402
    CauHoi, chuan_hoa, phat_hien_cay,
)

LEXICON = BASE / "knowledge" / "lexicon" / "out_of_scope_crops.yaml"

TRONG_PHAM_VI = "trong_pham_vi"
NGOAI_PHAM_VI = "ngoai_pham_vi"
CAN_LAM_RO = "can_lam_ro"


def _nap_cay_ngoai() -> list[tuple[str, list[str]]]:
    if not LEXICON.exists():
        return []
    data = yaml.safe_load(LEXICON.read_text(encoding="utf-8")) or {}
    ra = []
    for m in data.get("crops") or []:
        canon = str(m.get("canonical", ""))
        if canon:
            ra.append((canon, [str(v) for v in (m.get("variants") or [])]))
    return ra


CAY_NGOAI = _nap_cay_ngoai()


@dataclass
class KetQuaScope:
    ket_luan: str
    cay_trong_pham_vi: list[str]
    cay_ngoai_nhan_duoc: list[str]
    ly_do: str

    @property
    def duoc_di_tiep(self) -> bool:
        return self.ket_luan == TRONG_PHAM_VI


# Tu chi loai dung truoc ten cay. Xem DEC-031 (muc 13.4 quy chuan).
#
# 32 trong so ten cay o out_of_scope_crops.yaml chi co MOT am tiet, va bo dau
# xong thi phan lon dam vao mot tu thong dung:
#
#     toi (toi)   dam vao "vuon TOI"
#     nho (nho)   dam vao "tuoi NHO giot"
#     bong (bong) dam vao "cay ua BONG"
#     dieu (dieu) dam vao "DIEU kien thoi tiet"
#     ngo (ngo)   dam vao "NGO doc"
#     lan (lan)   dam vao "may LAN mot ngay"
#     dua (dua)   dam vao "DUA chuot", "DUA hau"
#
# Nen ten mot am tiet chi duoc tinh khi co tu chi loai dung ngay truoc no.
# Ten tu hai am tiet tro len ("ca phe", "thanh long", "ca tim") du dac trung
# de nhan truc tiep.
#
# CAI GIA PHAI TRA CUA QUY TAC NAY LA RE, va do la co y: cau "ngo trong the
# nao" se khong nhan ra "ngo", roi roi vao nhanh can_lam_ro. Bot van KHONG
# tra loi - chi la cau hoi lai chung chung hon mot chut thay vi noi dich danh
# "em chua co tai lieu ve ngo". Quyet dinh khong doi, chi loi van doi.
#
# "vuon" va "ruong" CO Y khong nam trong danh sach nay, du chung dung truoc
# ten cay rat tu nhien ("vuon toi", "ruong lac"). Ly do: "vuon toi" (vuon toi)
# pho bien hon "vuon toi" (vuon toi) rat nhieu lan, va nham theo huong do lam
# tu choi oan mot cau hoi ve ca chua.
TU_CHI_LOAI = [
    "cay", "qua", "trai", "cu", "hoa", "rau", "hat",
    "trong", "gieo", "vu", "giong", "thu hoach",
    "canh tac", "bon cho", "tuoi cho",
]

# Ten cay mot am tiet trung voi mot tu thong dung NGAY CA KHI CO DAU.
# Bo dau khong lien quan o day - "dieu" trong "dieu kien" va "dieu" trong
# "cay dieu" viet giong het nhau. Chi ngu canh phia sau phan biet duoc.
#
# Bang nay chi can khi cau hoi CO dau; cau khong dau da bi TU_CHI_LOAI chan.
# Gia tri la (tu dung TRUOC lam no khong con la ten cay,
#             tu dung SAU lam no khong con la ten cay)
DONG_AM_CO_DAU = {
    "điều": ([], ["kiện", "khiển", "trị", "chỉnh", "hoà", "hòa", "tiết"]),
    "lạc": ([], ["hậu", "quan", "đề", "lối", "điệu"]),
    "vải": ([], ["địa", "bạt", "phủ", "che"]),
    "cam": ([], ["kết", "chịu", "đoan"]),
    "hành": ([], ["động", "chính", "vi", "trình", "nghề"]),
    "bông": ([], ["lúa", "hoa", "gòn"]),
    # "Bắc thơm", "gạo thơm", "lúa thơm" la ten giong lua, khong phai dua
    "thơm": (["bắc", "gạo", "lúa", "nếp", "mùi", "hoa"],
             ["ngon", "mùi", "quá", "hơn", "số"]),
    # "một khóm", "khóm lúa" la bui cay, khong phai dua
    "khóm": (["một", "mỗi", "từng", "các", "những"], ["lúa", "mạ"]),
    "tiêu": ([], ["chuẩn", "thụ", "diệt", "hao", "chí", "đề", "biểu", "cực"]),
    "lan": (["bò", "leo", "mọc"], ["rộng", "truyền", "toả", "tỏa", "nhanh"]),
    "nho": ([], ["nhỏ"]),
    "bơ": ([], ["vơ", "phờ"]),
    "na": (["hàng"], []),
}


def tim_cay_ngoai_pham_vi(cau: CauHoi) -> list[str]:
    """Ten cay ngoai pham vi nhan ra duoc trong cau hoi.

    Hai lop bao ve chong nhan nham, vi mot lop khong du:

      1. khop_cum() khop tren ban CO DAU khi cau hoi co dau. Nho vay
         "bi ngo doc phen" khong bi nhan la "bi ngo", va "vuon toi" khong bi
         nhan la "vuon toi".

      2. Ten cay MOT AM TIET con phai co tu chi loai dung truoc. Lop nay danh
         cho nguoi go khong dau - luc do lop 1 khong con thong tin de dung.

    Nhan nham theo huong nao cung dat: nhan nham "ca tim" thanh "ca chua" thi
    tra loi sai cay; nhan nham "vuon toi" thanh cay toi thi tu choi oan mot
    cau hoi ve ca chua.
    """
    ra = []
    for canon, variants in CAY_NGOAI:
        for dang in [canon] + variants:
            if not khop_cum(cau.chuan, cau.khong_dau, dang, cau.goc_co_dau):
                continue
            if len(bo_dau(dang).split()) > 1:
                ra.append(canon)
                break

            # Ten mot am tiet. Hai duong xu ly khac han nhau:
            if cau.goc_co_dau:
                # Cau hoi co dau -> khop_cum() da khop tren ban co dau, chi
                # con lo dong am that su ("dieu kien" vs "cay dieu").
                m = re.search(r"(?<!\w)" + re.escape(dang.lower()) + r"(?!\w)",
                              cau.chuan)
                if not m:
                    continue
                cam_truoc, cam_sau = DONG_AM_CO_DAU.get(dang, ([], []))
                truoc = cau.chuan[:m.start()].rstrip().split(" ")[-1]
                sau = (cau.chuan[m.end():].lstrip().split(" ") or [""])[0]
                sau = sau.strip(",.?!:;")
                if truoc not in cam_truoc and sau not in cam_sau:
                    ra.append(canon)
                    break
            else:
                # Cau hoi khong dau -> khong con thong tin dau thanh, doi tu
                # chi loai dung ngay truoc (DEC-031).
                m = re.search(r"(?<!\w)" + re.escape(bo_dau(dang)) + r"(?!\w)",
                              cau.khong_dau)
                truoc = cau.khong_dau[:m.start()].rstrip() if m else ""
                if any(truoc.endswith(t) for t in TU_CHI_LOAI):
                    ra.append(canon)
                    break
    return ra


def kiem_tra(cau_hoi: str, context_turns: list[str] | None = None) -> KetQuaScope:
    """Kiem tra pham vi cua mot cau hoi da duoc router xac dinh la nong hoc."""
    cau: CauHoi = chuan_hoa(cau_hoi)
    trong = phat_hien_cay(cau)

    # Cay trong pham vi co the nam o luot truoc: "ca chua trong vu nao" roi
    # "the con benh xoan la thi sao". Ngu canh chi dung de XAC DINH CAY, khong
    # duoc mang noi dung cua luot cu sang cau tra loi moi.
    if not trong and context_turns:
        gop = chuan_hoa(" . ".join(context_turns[-3:] + [cau_hoi]))
        trong = phat_hien_cay(gop)

    ngoai = tim_cay_ngoai_pham_vi(cau)

    if trong and ngoai:
        # "trong xen ca chua voi ca phe co duoc khong" - hoi ca hai. Tai lieu
        # da duyet khong noi gi ve ca phe, nen tra loi phan nao cung la tra
        # loi thieu mot nua ma khong bao cho nguoi dung biet.
        return KetQuaScope(
            NGOAI_PHAM_VI, trong, ngoai,
            "Cau hoi nhac ca cay trong pham vi (" + ", ".join(trong)
            + ") lan cay ngoai pham vi (" + ", ".join(ngoai) + ")")

    if trong:
        return KetQuaScope(TRONG_PHAM_VI, trong, [], "")

    if ngoai:
        return KetQuaScope(
            NGOAI_PHAM_VI, [], ngoai,
            "Chi nhac cay ngoai pham vi: " + ", ".join(ngoai))

    # Khong nhan ra cay nao. KHONG duoc tra loi - nhung cung khong duoc noi
    # "ngoai pham vi", vi biet dau nguoi dung dang hoi ve lua ma dung tu ma
    # tu dien chua co. Hoi lai la hanh vi dung.
    return KetQuaScope(
        CAN_LAM_RO, [], [],
        "Khong nhan ra cay trong nao trong cau hoi lan ngu canh")
