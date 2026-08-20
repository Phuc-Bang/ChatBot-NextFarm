"""
Giao dien embedding.

VI SAO CHAY LOCAL CHU KHONG GOI API

Ba ly do, theo thu tu quan trong:

1. BAO MAT (muc 38). Embedding phai chay qua TOAN BO kho tri thuc va qua
   MOI cau hoi nguoi dung. Goi API nghia la ca hai thu do roi ha tang. Chay
   local thi ban ke luong du lieu doi tu:

       cau hoi nguoi dung -> Google        (neu dung API)
       cau hoi nguoi dung -> khong roi may (neu local)

   Voi NextFarm, cau "toan bo kho tri thuc va tang truy xuat chay tren ha
   tang cua cac anh, chi khau viet cau tra loi cuoi goi API" la mot luan
   diem that.

2. KHONG NAM TREN DUONG LATENCY THEO NGHIA DAT DO. Embed 161 chunk la viec
   chay MOT LAN. Chi con embed cau hoi moi luot, va do la mot cau ngan -
   encoder ~300M chay CPU van kip ngan sach ASM-01.

3. QUOTA. Free tier co han. De danh cho khau that su phai goi API.

CHUA CHOT MODEL - DEC-015

VN-MTEB (EACL 2026) cham halong_embedding 61,60 va multilingual-e5-small
60,66 tren 41 bo du lieu. Nhung do la diem TONG QUAT, khong phai tren tai
lieu nong nghiep tieng Viet cua minh. Vi vay khong chot tren giay: do
Recall@K tren 22 case co source_of_truth roi chon bang so.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class EmbeddingModel(Protocol):
    ten: str
    so_chieu: int

    def ma_hoa(self, texts: list[str], *, la_cau_hoi: bool = False):
        """Tra ve ma trận (len(texts), so_chieu), da chuan hoa L2.

        `la_cau_hoi` co that: mot so model (ho E5, bge) duoc huan luyen voi
        tien to khac nhau cho cau hoi va cho doan van. Dung sai tien to lam
        chat luong tut ro ret ma khong bao loi gi.
        """
        ...


def cosine(a: "np.ndarray", b: "np.ndarray") -> "np.ndarray":
    """Do tuong dong cosine giua (n,d) va (m,d) -> (n,m).

    Gia dinh ca hai da chuan hoa L2, luc do cosine chinh la tich vo huong.
    """
    return a @ b.T
