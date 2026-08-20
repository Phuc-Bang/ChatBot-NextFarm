"""
Kiem thu API va chuoi xu ly - KHONG goi model, KHONG can mang.

Test o day thay client LLM bang mot ban gia. Ly do khong phai chi de chay
nhanh: mot test goi model that se PHU THUOC VAO QUOTA va vao noi dung model
sinh ra hom do. Test do se do lung tung - hom nay xanh, mai do, ma khong ai
sua gi ca. Test phai kiem CO CHE cua minh, khong kiem model cua Google.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from app.services.rag.sinh_cau_tra_loi import (              # noqa: E402
    dung_evidence_pack, kiem_grounding, sinh_va_kiem)


@dataclass
class ChunkGia:
    chunk_id: str
    text: str
    document_title: str | None = "Tai lieu thu"
    publisher: str | None = "So NN"
    url: str = "https://vi.du/a"
    source_tier: int | None = 1
    crop: str | None = "ca_chua"
    region: str | None = None
    section_title: str | None = None
    document_id: str = "doc1"
    is_high_risk: bool = False
    diem: float = 0.0
    kenh: list = field(default_factory=list)


CHUNKS = [
    ChunkGia("c1", "Do pH trung binh cua dat trong ca chua khoang 6-6.5."),
    ChunkGia("c2", "Mat do trong 30.000 - 35.000 cay/ha."),
]


class LLMGia:
    """Client gia tra ve dung chuoi da dinh san."""

    ten_model = "gia"
    ten_provider = "gia"

    def __init__(self, tra_ve: str):
        self.tra_ve = tra_ve

    def sinh(self, prompt, **kw):
        from app.services.llm.base import KetQuaLLM
        return KetQuaLLM(text=self.tra_ve, token_vao=10, token_ra=5,
                         token_suy_nghi=0, latency_ms=1, model="gia",
                         provider="gia")


# ---------------------------------------------------------------------------
# Evidence Pack
# ---------------------------------------------------------------------------

def test_evidence_pack_giu_nguyen_van():
    """Khong tom tat: tom tat lam mat thong tin ma tang kiem so can den."""
    p = dung_evidence_pack(CHUNKS)
    assert "6-6.5" in p
    assert "30.000 - 35.000" in p
    assert "[c1]" in p and "[c2]" in p


# ---------------------------------------------------------------------------
# Grounding - tang 1
# ---------------------------------------------------------------------------

def test_chan_trich_dan_chunk_khong_co_that():
    loi = kiem_grounding("pH la 6-6.5 [c99]", CHUNKS, [])
    assert any("khong co trong Evidence Pack" in x for x in loi)


def test_chap_nhan_trich_dan_dung():
    assert kiem_grounding("pH la 6-6.5 [c1]", CHUNKS, ["c1"]) == []


# ---------------------------------------------------------------------------
# Grounding - tang 2 (quan trong nhat)
# ---------------------------------------------------------------------------

def test_chan_con_so_khong_co_trong_bang_chung():
    """Day la tang chan bia so lieu - chi so trung tam cua PoC."""
    loi = kiem_grounding("Ca chua can pH 7.5 [c1]", CHUNKS, ["c1"])
    assert any("khong co trong bang chung" in x for x in loi)


def test_khong_bao_dong_gia_voi_dau_phan_cach_nghin():
    """30.000 va 30000 la MOT so.

    Khong chuan hoa thi tang 2 bao dong gia lien tuc, va mot tang canh gac
    bao dong gia lien tuc se bi tat di - luc do mat han tang quan trong nhat.
    """
    assert kiem_grounding("Trong 30000 cay/ha [c2]", CHUNKS, ["c2"]) == []
    assert kiem_grounding("Trong 30.000 cay/ha [c2]", CHUNKS, ["c2"]) == []


def test_khong_bao_dong_gia_voi_so_thap_phan_viet():
    """6,5 (kieu Viet) va 6.5 la MOT so."""
    assert kiem_grounding("pH 6,5 [c1]", CHUNKS, ["c1"]) == []


def test_ma_trich_dan_khong_bi_coi_la_so_lieu():
    """[c1] chua chu 'c1' - khong duoc bat '1' trong do thanh so lieu."""
    assert kiem_grounding("Do pH 6-6.5 [c1]", CHUNKS, ["c1"]) == []


# ---------------------------------------------------------------------------
# sinh_va_kiem
# ---------------------------------------------------------------------------

def test_tu_choi_khi_model_khai_khong_du_can_cu():
    c = LLMGia('{"du_can_cu": false, "tra_loi": "khong du", "chunk_da_dung": []}')
    r = sinh_va_kiem("hoi gi do", CHUNKS, client=c)
    assert r.da_tu_choi
    assert r.ly_do == "insufficient_evidence"


def test_tu_choi_khi_json_hong():
    """Khong phan tich duoc thi khong kiem duoc; khong kiem duoc thi KHONG
    duoc hien ra."""
    r = sinh_va_kiem("hoi", CHUNKS, client=LLMGia("day khong phai JSON"))
    assert r.da_tu_choi
    assert r.ly_do == "loi_dinh_dang"


def test_chan_khi_model_bia_so_du_khai_du_can_cu():
    """Ca quan trong nhat: model NOI la co can cu nhung so lieu la bia.

    Prompt la loi de nghi, model co the khong nghe. Validator la co che.
    """
    c = LLMGia('{"du_can_cu": true, "tra_loi": "Ca chua can pH 8.9 [c1]",'
               ' "chunk_da_dung": ["c1"]}')
    r = sinh_va_kiem("hoi", CHUNKS, client=c)
    assert r.da_tu_choi
    assert r.ly_do == "grounding_khong_dat"
    assert r.canh_bao_grounding


def test_cho_qua_khi_dat_moi_tang():
    c = LLMGia('{"du_can_cu": true, "tra_loi": "Ca chua can pH 6-6.5 [c1]",'
               ' "chunk_da_dung": ["c1"]}')
    r = sinh_va_kiem("hoi", CHUNKS, client=c)
    assert not r.da_tu_choi
    assert "6-6.5" in r.tra_loi
    assert r.chunk_da_dung == ["c1"]


# ---------------------------------------------------------------------------
# Pipeline - tang tu choi som (khong goi model, khong cham DB)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cau,ly_do", [
    ("bật van 3 trong 10 phút", "device_control"),
    ("độ ẩm khu A giờ đang bao nhiêu", "garden_data"),
    ("app có tự tưới theo dự báo thời tiết không", "product_feature"),
])
def test_tu_choi_som_khong_goi_model(cau, ly_do):
    """Ba chang dau khong goi model nao - cau bi chan o day ton 0 dong.

    Do la ly do Intent Router dat TRUOC Scope Check va ca hai dat truoc
    truy xuat (muc 10).
    """
    from app.services.pipeline import tra_loi_cau_hoi
    r = tra_loi_cau_hoi(cau, dung_llm=False)
    assert r.da_tu_choi
    assert r.ly_do_tu_choi == ly_do
    assert r.token_vao == 0 and r.token_ra == 0
    assert "truy_xuat" not in r.latency_ms      # chua he cham den DB


def test_tu_choi_som_van_do_latency_tung_chang():
    """Muc 21.2 doi do TUNG chang, khong phai mot con so tong."""
    from app.services.pipeline import tra_loi_cau_hoi
    r = tra_loi_cau_hoi("bật van 3", dung_llm=False)
    assert "chuan_hoa" in r.latency_ms
    assert "intent" in r.latency_ms
