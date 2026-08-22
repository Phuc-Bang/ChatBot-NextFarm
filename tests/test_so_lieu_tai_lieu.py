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
  - so test ghi trong BON noi (ba tai lieu + trang /report) phai giong nhau
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
                 r"(?:[Uu]nit\s+)?(?:[Tt]ests?(?!\s*case)|test tự động|xanh)")

TAI_LIEU = (
    "README.md",
    "docs/GIAO_HANG_NEXTFARM.md",
    "docs/BAO_CAO_TONG_KET_NEXTFARM.md",
    # Trang /report la thu NextFarm thuc su nhin. Them vao 2026-08-22 sau
    # khi phat hien no van ghi 310 trong khi ba file kia da sang 331.
    "frontend/report.html",
)


# Trong report.html co mot o KPI la con so TRAN, khong co tu "test" ben canh:
#     <div class="kpi-metric so">339 / 339</div>
# MAU o tren khong bat duoc no. Da kiem: doi o do thanh 888 / 888 ma bo test
# van xanh. Nen phai bat rieng bang mau markup.
MAU_KPI = re.compile(r'class="kpi-metric so">\s*(\d{3})\s*/\s*(\d{3})\s*<')


def _so_trong(ten: str) -> list[int]:
    van = (GOC / ten).read_text(encoding="utf-8")
    so = [int(m.group(1)) for m in MAU.finditer(van)]
    for m in MAU_KPI.finditer(van):
        a, b = int(m.group(1)), int(m.group(2))
        assert a == b, (ten + ": o KPI ghi " + str(a) + " / " + str(b)
                        + " - hai nua phai bang nhau")
        so.append(a)
    return so


def test_moi_noi_ghi_cung_mot_con_so():
    """Loi pho bien nhat: sua mot cho, quen sau cho."""
    thay = {}
    for ten in TAI_LIEU:
        so = set(_so_trong(ten))
        assert so, ten + " khong ghi so test o dau ca - mau regex hong hoac " \
                         "tai lieu da bo con so nay"
        thay[ten] = so

    hop = set().union(*thay.values())
    assert len(hop) == 1, \
        "cac noi ghi so test khac nhau: " + \
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

    try:
        import psycopg  # noqa: F401
    except ImportError:
        # Khi khong co psycopg tren moi truong cuc bo, 2 file DB test (36 tests)
        # bi importorskip bo qua nen chi thu thap 322 thay vi 358 nhu tren CI.
        if (that + 36) in ghi:
            return

    assert ghi == {that}, (
        "tai lieu ghi " + str(sorted(ghi)) + " test nhung pytest thu thap "
        + str(that) + ". Sua cac file: " + ", ".join(TAI_LIEU)
    )

