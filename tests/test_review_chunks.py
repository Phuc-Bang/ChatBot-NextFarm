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

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

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


def test_da_quyet_dinh_lap_chi_muc_theo_bam_noi_dung():
    """DOI 2026-08-22: khoa la sha256 noi dung, khong con la chunk_id.

    Ban cu cua test nay khang dinh chi muc theo chunk_id. Do dung voi ma luc
    ay va SAI voi cai can bao ve: chunk_id chua `ordinal` nen no doi khi doi
    hang so cat chunk, va mot quyet dinh duyet cu se de len doan van khac.
    Giu lai test o day thay vi xoa, de nguoi doc sau thay khoa da doi va vi sao.
    """
    data = {"chunks": [{"chunk_id": "a#1", "sha256": "a" * 64, "approved": True},
                       {"chunk_id": "b#2", "sha256": "b" * 64, "approved": False}]}
    d = rc.da_quyet_dinh(data)
    assert d["a" * 64]["approved"] is True
    assert d["b" * 64]["approved"] is False
    assert "a#1" not in d, "van con lap chi muc theo chunk_id"


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


# ---------------------------------------------------------------------------
# Quyet dinh duyet le phai khoa vao NOI DUNG, khong vao thu tu.
#
# LO HONG DA CO 2026-08-22
#
# chunk_id dung theo thu tu trong tai lieu (load.py:153):
#     cid = rec["id"] + "#" + str(c.ordinal)
#
# Doi hang so cat chunk -> moi ordinal xe dich -> `hatinh_dua_chuot_vietgap#1`
# tro thanh MOT DOAN VAN KHAC nhung van nhan quyet dinh duyet cu. Khong co gi
# bao loi. Mot chunk tung bi loai vi "tieu de tin tuc" co the duoc cap phep
# vao kho lieu luong thuoc BVTV.
#
# Da doi khoa sang sha256 noi dung. Tinh chat phai giu: van ban doi -> bam
# doi -> KHONG khop -> chunk rui ro cao khong duoc duyet -> DEC-005 chan.
# Hong theo huong AN TOAN.
# ---------------------------------------------------------------------------


def test_moi_ban_ghi_duyet_deu_co_sha256():
    import yaml

    d = yaml.safe_load((GOC / "knowledge" / "review" / "chunks.yaml")
                       .read_text(encoding="utf-8"))
    ds = d["chunks"]
    assert ds, "chunks.yaml rong"
    thieu = [c["chunk_id"] for c in ds if not c.get("sha256")]
    assert not thieu, \
        "ban ghi duyet thieu sha256: " + ", ".join(thieu[:5]) + \
        " - chung se bi bo qua khi nap, chunk se khong duoc duyet"


def test_khong_co_hai_ban_ghi_cung_bam():
    import yaml

    d = yaml.safe_load((GOC / "knowledge" / "review" / "chunks.yaml")
                       .read_text(encoding="utf-8"))
    bams = [c["sha256"] for c in d["chunks"] if c.get("sha256")]
    assert len(bams) == len(set(bams)), \
        "hai ban ghi duyet cung sha256 - mot quyet dinh dang de len quyet dinh kia"


def test_bam_doi_theo_noi_dung_khong_theo_khoang_trang():
    from app.core.text import bam_chunk

    a = bam_chunk("Phun 1,5 lit/ha, cach ly 7 ngay")
    assert bam_chunk("Phun 1,5 lit/ha,  cach ly 7 ngay\n") == a, \
        "khac biet khoang trang lam doi bam - mot quyet dinh duyet that se bi " \
        "huy oan chi vi dinh dang"
    assert bam_chunk("Phun 2,5 lit/ha, cach ly 7 ngay") != a, \
        "doi LIEU LUONG ma bam khong doi - quyet dinh duyet cu se de len " \
        "mot lieu luong khac"


def test_tra_cuu_khoa_theo_bam_chu_khong_theo_chunk_id():
    """Doc ma nguon ca hai phia: cong nap va cong duyet.

    Chi can mot phia tra theo chunk_id la lo hong quay lai.
    """
    load = (GOC / "knowledge" / "ingestion" / "load.py").read_text(encoding="utf-8")
    assert 'duyet_chunk.get(bam_chunk(' in load, \
        "load.py tra quyet dinh duyet khong theo bam noi dung"
    assert '{c["chunk_id"]: c for c in muc}' not in load, \
        "load.py van dung chunk_id lam khoa cho chunks.yaml"

    rv = (GOC / "knowledge" / "review" / "review_chunks.py").read_text(encoding="utf-8")
    assert '{c["sha256"]: c' in rv, \
        "review_chunks.py van khoa theo chunk_id"
    assert '"sha256": bam_chunk(' in rv, \
        "review_chunks.py khong ghi sha256 khi luu quyet dinh"


def test_ban_ghi_thieu_bam_bi_bo_qua_chu_khong_duoc_duyet_oan():
    """Hong theo huong an toan: tra cuu that bai = CHUA duyet, khong phai duyet."""
    import sys as _s

    _s.path.insert(0, str(GOC / "knowledge" / "ingestion"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_load_kt", GOC / "knowledge" / "ingestion" / "load.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    import tempfile
    import yaml
    from pathlib import Path as _P

    with tempfile.TemporaryDirectory() as d:
        f = _P(d) / "chunks.yaml"
        f.write_text(yaml.safe_dump({"chunks": [
            {"chunk_id": "co_bam#1", "sha256": "a" * 64, "approved": True},
            {"chunk_id": "thieu_bam#2", "approved": True},
        ]}, allow_unicode=True), encoding="utf-8")
        ra = mod.doc_yaml(f, "chunks")

    assert "a" * 64 in ra, "ban ghi co sha256 phai tra cuu duoc"
    assert len(ra) == 1, \
        "ban ghi thieu sha256 van lot vao bang tra cuu - no se duoc duyet oan"
