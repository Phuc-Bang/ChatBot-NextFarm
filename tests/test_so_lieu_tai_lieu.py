"""
Con so trong tai lieu phai khop voi thuc te chay duoc.

SU CO THAT 2026-08-22

Bay cho trong README.md, docs/GIAO_HANG_NEXTFARM.md va
docs/BAO_CAO_TONG_KET_NEXTFARM.md ghi bo kiem thu co 310 test. Chay that ra
318. Khong ai sua vi khong co gi bao.

Lech 8 test khong gay hai ky thuat. No gay hai theo cach khac: du an nay ban
mot loi hua "moi con so deu kiem chung duoc". Con so DE KIEM NHAT - chay mot
lenh la biet - ma lai sai, thi moi con so kho kiem hon trong cung tai lieu
cung mat trong luong.

Test nay canh CAI GI:
  - so test ghi trong ba tai lieu phai giong nhau
  - va phai bang so test pytest that su thu thap duoc

Test nay KHONG canh:
  - cac con so khac trong tai lieu (so chunk, so case, chi phi). Chung den tu
    ket qua do va co bang chung rieng trong evaluation/results/.
  - so test trong docs/reports/. Bao cao la ban ghi tai thoi diem do - sua so
    trong bao cao cu la lam hong ban ghi lich su.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

# Chi bat con so dang noi ve SO LUONG TEST, khong bat so tien hay so dong.
#
# `(?!\s*case)` la bat buoc: "222 test case" la kich thuoc TAP KIEM THU, mot
# con so hoan toan khac. Lan chay dau khong co no va test do vi bat nham 222.
MAU = re.compile(r"(\d{3})\s*(?:/\s*\d{3}\s*)?"
                 r"(?:unit\s+)?(?:[Tt]ests?(?!\s*case)|test tự động|xanh)")

TAI_LIEU = (
    "README.md",
    "docs/GIAO_HANG_NEXTFARM.md",
    "docs/BAO_CAO_TONG_KET_NEXTFARM.md",
)


def _so_trong(ten: str) -> list[int]:
    van = (GOC / ten).read_text(encoding="utf-8")
    return [int(m.group(1)) for m in MAU.finditer(van)]


def test_ba_tai_lieu_ghi_cung_mot_con_so():
    """Loi pho bien nhat: sua mot cho, quen sau cho."""
    thay = {}
    for ten in TAI_LIEU:
        so = set(_so_trong(ten))
        assert so, ten + " khong ghi so test o dau ca - mau regex hong hoac " \
                         "tai lieu da bo con so nay"
        thay[ten] = so

    hop = set().union(*thay.values())
    assert len(hop) == 1, \
        "ba tai lieu ghi so test khac nhau: " + \
        "; ".join(k + "=" + str(sorted(v)) for k, v in thay.items())


def test_so_trong_tai_lieu_bang_so_chay_that():
    """So ghi trong tai lieu phai la so pytest thu thap duoc.

    Bo qua khi chay le mot file: luc do pytest thu thap 2 test chu khong
    phai ca bo, so sanh se do oan.
    """
    import conftest

    if not getattr(conftest, "THU_THAP_DAY_DU", False):
        pytest.skip("chay le mot phan bo test - khong doi chieu duoc tong so")

    that = conftest.SO_TEST_THU_THAP
    assert that, "conftest khong ghi lai so test thu thap duoc"

    ghi = set().union(*(set(_so_trong(t)) for t in TAI_LIEU))
    assert ghi == {that}, (
        "tai lieu ghi " + str(sorted(ghi)) + " test nhung pytest thu thap "
        + str(that) + ". Sua ba tai lieu: " + ", ".join(TAI_LIEU)
    )
