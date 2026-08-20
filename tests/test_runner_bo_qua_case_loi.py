"""
Case tung LOI khong duoc tinh la "da chay".

SU CO THAT 2026-08-20

Ba trinh chay (C0/C1/C2) luu ket qua sau TUNG case de chay lai duoc khi dut
giua chung. Lan chay sau doc file cu va bo qua nhung case da co.

Nhung case LOI cung duoc ghi vao file do - kem truong `loi`. Hau qua: quota
free tier can giua chung, 35 case nhan 429 va duoc ghi lai, roi moi lan chay
sau deu BO QUA ca 35 case do vinh vien.

Do duoc: truoc ban sua, run_c1 bao "can chay 18"; sau ban sua, "can chay 53"
(222 - 169 thanh cong). 35 case da bien mat khoi phep do ma khong bao gi.

Bang so thieu 35/222 case trong khi van in ra day du va trong nhu that - do
la kieu hong nguy hiem nhat.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

RUNNER = ["run_c0", "run_c1", "run_c2"]


def _ma_nguon(ten: str) -> str:
    return (BASE / "evaluation" / "runners" / (ten + ".py")).read_text(
        encoding="utf-8")


@pytest.mark.parametrize("ten", RUNNER)
def test_bo_qua_case_da_loi(ten):
    """Vong doc file cu phai co nhanh loai bo case co truong `loi`."""
    src = _ma_nguon(ten)
    assert 'if r.get("loi"):' in src, (
        ten + ".py doc lai ket qua cu ma KHONG loai case da loi. "
        "Case 429 se bi coi la da chay va bo qua vinh vien - "
        "xem docstring dau file nay.")


@pytest.mark.parametrize("ten", RUNNER)
def test_nhanh_loai_bo_nam_TRUOC_khi_ghi_vao_da_co(ten):
    """`continue` phai dung truoc `da_co[...] = r`, khong phai sau."""
    src = _ma_nguon(ten)
    i_loi = src.index('if r.get("loi"):')
    i_ghi = src.index('da_co[r["case_id"]] = r')
    assert i_loi < i_ghi, (
        ten + ".py kiem `loi` SAU khi da ghi vao da_co - vo tac dung")


def test_logic_loc_dung():
    """Kiem chinh phep loc, khong chi kiem ma nguon."""
    ban_ghi = [
        {"case_id": "a", "answer": "x"},
        {"case_id": "b", "loi": "ClientError: 429 RESOURCE_EXHAUSTED"},
        {"case_id": "c", "answer": "y"},
        {"case_id": "d", "loi": None},          # loi=None la THANH CONG
    ]
    da_co = {}
    for r in ban_ghi:
        if r.get("loi"):
            continue
        da_co[r["case_id"]] = r

    assert set(da_co) == {"a", "c", "d"}, \
        "loi=None phai duoc tinh la thanh cong; chi loi THAT moi bi loai"
