"""
review_chunks.py - luong 3 cua DEC-020, duyet le chunk rui ro cao.

Hai thu test o day canh giu:

  1. Ghi ra file phai giu nguyen tieng Viet co dau. yaml.safe_dump mac dinh
     escape non-ASCII thanh \\uXXXX, bien reject_reason thanh mot day ma
     khong doc duoc trong git diff - ma git diff CHINH LA cho nguoi khac
     xem lai quyet dinh duyet (muc 27).

  2. Truy van chi lay chunk cua tai lieu DA duyet o luong 1. Duyet le mot
     chunk thuoc tai lieu bi loai la cong vo ich: indexable_chunk doi
     d.approved AND c.approved, hong ve dau thi ve sau khong cuu duoc.
     Do duoc 2026-08-21: 20 trong 44 chunk rui ro cao roi vao dien nay.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import importlib.util

# knowledge/ khong phai package (khong co __init__.py) va khong nen bien
# thanh package chi de test nhap duoc - do la thu muc du lieu co script,
# khong phai thu vien. Nap thang theo duong dan.
_spec = importlib.util.spec_from_file_location(
    "review_chunks",
    Path(__file__).resolve().parents[1] / "knowledge" / "review" / "review_chunks.py",
)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)


def test_ghi_giu_tieng_viet_co_dau(tmp_path, monkeypatch):
    f = tmp_path / "chunks.yaml"
    monkeypatch.setattr(rc, "CHUNKS_YAML", f)
    rc.ghi({"chunks": [{"chunk_id": "x#1", "approved": False,
                        "reject_reason": "Tiêu đề tin tức, không có kỹ thuật"}]})
    raw = f.read_text(encoding="utf-8")
    assert "Tiêu đề" in raw, "yaml.safe_dump da escape tieng Viet -> git diff vo dung"
    assert "\\u" not in raw


def test_ghi_roi_doc_lai_khong_mat_gi(tmp_path, monkeypatch):
    f = tmp_path / "chunks.yaml"
    monkeypatch.setattr(rc, "CHUNKS_YAML", f)
    goc = {"chunks": [{"chunk_id": "a#1", "approved": True, "note": "Liều lượng bón thúc"}]}
    rc.ghi(goc)
    assert rc.nap() == goc


def test_nap_file_chua_ton_tai(tmp_path, monkeypatch):
    """Lan duyet dau tien chua co file - khong duoc nem loi."""
    monkeypatch.setattr(rc, "CHUNKS_YAML", tmp_path / "chua_co.yaml")
    assert rc.nap() == {"chunks": []}


def test_truy_van_loc_tai_lieu_da_duyet():
    """Chunk cua tai lieu bi loai khong duoc dua ra hoi.

    Kiem bang cach doc ma nguon: truy van phai co dieu kien d.approved.
    Mot lan sua vo y bo dieu kien nay se lam nguoi duyet ngoi duyet 20 chunk
    khong bao gio vao duoc kho.
    """
    import inspect

    src = inspect.getsource(rc.lay_chunk_rui_ro)
    assert "d.approved" in src
    assert "is_high_risk" in src


def test_da_quyet_dinh_lap_chi_muc_theo_chunk_id():
    data = {"chunks": [{"chunk_id": "a#1", "approved": True},
                       {"chunk_id": "b#2", "approved": False}]}
    d = rc.da_quyet_dinh(data)
    assert d["a#1"]["approved"] is True
    assert d["b#2"]["approved"] is False


def test_khong_co_co_duyet_het():
    """Khong duoc co duong tat duyet hang loat.

    Noi dung o day la lieu luong thuoc BVTV. DEC-005 doi NGUOI nhin tan mat
    tung cai. Mot co --duyet-het bien ca luong 3 thanh thu tuc.

    Doc DANH SACH THAM SO that bang cach phan tich cay cu phap, khong so
    chuoi tho tren ma nguon: docstring cua file co vi du "--limit 10" va
    moi phep so chuoi tren toan bo nguon deu bao dong gia vi no.
    """
    import ast

    cay = ast.parse(Path(rc.__file__).read_text(encoding="utf-8"))
    ten = [
        d.value
        for n in ast.walk(cay)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "add_argument"
        for d in n.args
        if isinstance(d, ast.Constant) and str(d.value).startswith("--")
    ]

    assert ten, "khong doc duoc tham so nao - test nay da mat tac dung"
    for co in ["--duyet-het", "--approve-all", "--tat-ca", "--yes", "--force"]:
        assert co not in ten, f"co {co} pha vo DEC-005"
