"""
Kiem thu loc ung vien theo ket qua duyet tai lieu (DEC-020 luong 1).

Rang buoc: cau trich tu tai lieu DA BI LOAI khong duoc dua ra cho nguoi duyet.
Tai lieu bi loai thi khong chunk nao cua no vao duoc kho tri thuc, nen mot
fact trich tu do khong bao gio dung de kiem so hay lam ground truth duoc -
duyet no la cong bo di.

Do tren du lieu that: 52/193 cau ung vien thuoc 13 tai lieu bi loai.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "knowledge" / "review"))

import review_facts as rf  # noqa: E402


def test_chi_lay_cau_thuoc_tai_lieu_da_duyet():
    import json
    duyet = rf.tai_lieu_da_duyet()
    assert duyet, "chua duyet tai lieu nao - test nay can documents.yaml that"

    cands = json.loads(rf.CANDIDATES.read_text(encoding="utf-8"))
    trong = [c for c in cands if c.get("source_id") in duyet]
    assert 0 < len(trong) < len(cands), "bo loc phai loai bot mot phan"
    assert all(c["source_id"] in duyet for c in trong)


def test_khong_duyet_tai_lieu_nao_thi_khong_loc_gi():
    """Loc theo mot tap rong se lam moi cau bien mat va nguoi dung tuong la
    het viec - im lang va sai."""
    import types
    goc = rf.DOCUMENTS
    try:
        rf.DOCUMENTS = Path("khong-ton-tai.yaml")
        assert rf.tai_lieu_da_duyet() is None
    finally:
        rf.DOCUMENTS = goc


def test_tai_lieu_bi_loai_van_duoc_giu_lai():
    """Tai lieu bi loai la BANG CHUNG cua quy trinh duyet (muc 27.2), khong
    phai rac - phai con trong file de xem lai duoc."""
    import yaml
    ds = yaml.safe_load(rf.DOCUMENTS.read_text(encoding="utf-8"))["documents"]
    assert any(not d.get("approved") for d in ds)
    assert all(d.get("reviewer") for d in ds if not d.get("approved"))
