"""
Kiem thu cho co che cong diem vung mien (§14.5 & §40.2 Muc 11).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.retrieval.keyword import ChunkTraVe, cong_diem_vung


def _tao_chunk(chunk_id: str, region: str | None, diem_goc: float) -> ChunkTraVe:
    return ChunkTraVe(
        chunk_id=chunk_id,
        document_id="doc_1",
        text="noi dung kiem thu",
        section_title="Tieu de",
        crop="lua",
        region=region,
        url="https://khuyennong.gov.vn",
        document_title="Tai lieu",
        publisher="Khuyen nong",
        source_tier=1,
        is_high_risk=False,
        diem=diem_goc,
    )


def test_khong_truyen_region_thi_giu_nguyen():
    """Khi region la None hoac rong, danh sach va diem giu nguyen."""
    ds = [
        _tao_chunk("c1", "dong_bang_song_hong", 0.8),
        _tao_chunk("c2", "bac_trung_bo", 0.6),
    ]
    kq = cong_diem_vung(ds, None)
    assert len(kq) == 2
    assert kq[0].chunk_id == "c1"
    assert kq[0].diem == 0.8
    assert kq[1].chunk_id == "c2"
    assert kq[1].diem == 0.6


def test_cong_diem_vung_uu_tien_dung_vung():
    """Chunk cung vung duoc cong diem he_so va vuot len top khi diem goc gan nhau."""
    c_mien_bac = _tao_chunk("c_bac", "dong_bang_song_hong", 0.50)
    c_ha_tinh = _tao_chunk("c_hatinh", "bac_trung_bo", 0.55)

    # Chua cong vung: c_ha_tinh dung dau vi 0.55 > 0.50
    ds = [c_ha_tinh, c_mien_bac]

    # Nguoi dung o mien Bac: cong he_so 0.10 -> c_mien_bac len 0.60 > 0.55
    kq = cong_diem_vung(ds, "dong_bang_song_hong", he_so=0.10)
    assert kq[0].chunk_id == "c_bac"
    assert kq[0].diem == pytest.approx(0.60)
    assert "vung" in kq[0].kenh
    assert kq[1].chunk_id == "c_hatinh"
    assert kq[1].diem == pytest.approx(0.55)


def test_khong_lam_mat_tai_lieu_khac_vung():
    """Tai lieu khac vung chi bi giam uu tien tuong doi, KHONG bao gio bi loai bo."""
    c_nam_bo = _tao_chunk("c_nam", "dong_bang_song_cuu_long", 0.90)
    c_mien_bac = _tao_chunk("c_bac", "dong_bang_song_hong", 0.30)

    ds = [c_nam_bo, c_mien_bac]
    # Nguoi dung o mien Bac nhung tai lieu Nam Bo co diem noi dung vuot troi (0.90 vs 0.30 + 0.10 = 0.40)
    kq = cong_diem_vung(ds, "dong_bang_song_hong", he_so=0.10)
    assert len(kq) == 2
    assert kq[0].chunk_id == "c_nam"
    assert kq[1].chunk_id == "c_bac"
