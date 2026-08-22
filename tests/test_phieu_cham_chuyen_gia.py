"""
Bo tach phieu cham phai doc dung ca hai dang ban ghi.

SU CO THAT 2026-08-22

Phieu co hai dang dau moc:

    **Trả lời:**                                     <- ca CO tra loi
    **Hệ thống TỪ CHỐI** (lý do máy ghi: `...`)      <- ca TU CHOI

Ban dau bo tach chi biet dau moc thu nhat. Hau qua tren 50 cau that:

    21/50 ca co `tra_loi` RONG, va chu "TỪ CHỐI" bi nuot vao `cau_hoi`
    21 ca tu choi that chi nhan ra 7 (phan loai suy ra tu len(nguon)==0
    cong vai cum tu trong `tra_loi` - ca hai deu truot)

Khong chi la loi hien thi. Mot script cham diem tu dong da cho 4/5 diem kem
ghi chu "trich dan chuan" cho nhung o tra loi TRONG, vi no doc `so_nguon`
va tuong chung la cau tra loi co nguon.

Va neu de nguyen, mot chuyen gia NGUOI ngoi cham cung se cham 21/50 cau tren
mot o trong - nghia la cham diem that cung khong dung duoc.

Con so 29/21 lay tu chinh docs/PHIEU_CHAM_CHUYEN_GIA.md:
    grep -c "^## Câu "              -> 50
    grep -c "Hệ thống TỪ CHỐI"      -> 21
    grep -c "^\*\*Trả lời:\*\*"     -> 29
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

PHIEU = GOC / "docs" / "PHIEU_CHAM_CHUYEN_GIA.md"


def _cases():
    from app.services.evaluation.expert_parser import doc_phieu_cham
    return doc_phieu_cham()


def _dem_trong_phieu():
    van = PHIEU.read_text(encoding="utf-8")
    return (len(re.findall(r"^## Câu ", van, re.M)),
            len(re.findall(r"\*\*Hệ thống TỪ CHỐI\*\*", van)),
            len(re.findall(r"^\*\*Trả lời:\*\*", van, re.M)))


def test_so_ca_khop_phieu_goc():
    tong, tu_choi, tra_loi = _dem_trong_phieu()
    cs = _cases()
    assert len(cs) == tong, f"tach duoc {len(cs)} ca, phieu co {tong}"
    assert sum(1 for c in cs if c["da_tu_choi"]) == tu_choi, \
        "so ca tu choi khong khop phieu goc - phan loai dang doan chu khong doc"
    assert sum(1 for c in cs if not c["da_tu_choi"]) == tra_loi


def test_khong_ca_nao_co_o_noi_dung_rong():
    """O trong nghia la nguoi cham khong co gi de cham."""
    rong = [c["id"] for c in _cases() if not c["tra_loi"].strip()]
    assert not rong, "ca co noi dung rong: " + ", ".join(rong[:8])


def test_cau_hoi_khong_dinh_khoi_tu_choi():
    ban = [c["id"] for c in _cases() if "TỪ CHỐI" in c["cau_hoi"]]
    assert not ban, \
        "cau hoi bi dinh khoi TU CHOI: " + ", ".join(ban[:8]) + \
        " - regex cau hoi khong dung lai o dau moc tu choi"
    trong = [c["id"] for c in _cases() if not c["cau_hoi"].strip()]
    assert not trong, "cau hoi rong: " + ", ".join(trong[:8])


def test_ca_tu_choi_co_ly_do_may_ghi():
    thieu = [c["id"] for c in _cases()
             if c["da_tu_choi"] and not c.get("ly_do_tu_choi")]
    assert not thieu, "ca tu choi thieu ly do: " + ", ".join(thieu[:8])


def test_phan_loai_khong_dua_vao_so_nguon():
    """Ca TU CHOI van dan nguon - do la ly do cach suy luan cu that bai.

    Neu co ca tu choi nao co nguon ma bi xep thanh "co tra loi" thi cach
    phan loai da quay ve doan mo.
    """
    cs = _cases()
    tu_choi_co_nguon = [c for c in cs if c["da_tu_choi"] and c["nguon"]]
    assert tu_choi_co_nguon, \
        "khong ca tu choi nao co nguon - gia dinh cua test nay da doi, doc lai"
    for c in tu_choi_co_nguon:
        assert c["loai"] == "tu_choi", c["id"] + " bi doi nhan thanh co tra loi"
