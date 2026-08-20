"""
Kiem thu reranker.

Khong nap model that (540 MB, cham tren CPU). Test o day kiem HANH VI cua
lop bao boc: tat/bat, nuot loi, dem loi, giu diem RRF.

Vi sao dem loi quan trong den muc co test rieng: lan do dau tien reranker
loi o CA 22 case, moi lan lui ve thu tu cu, va ket qua hien ra la "chenh
lech +0.000". No trong y het mot ket luan ("reranker khong giup gi") chu
khong trong nhu mot loi.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.retrieval import rerank                  # noqa: E402
from app.services.retrieval.keyword import ChunkTraVe      # noqa: E402


def chunk(cid: str, text: str, diem: float = 0.0) -> ChunkTraVe:
    c = ChunkTraVe(cid, "d", text, None, None, None, "", None, None, None,
                   False)
    c.diem = diem
    return c


class CauGia:
    def __init__(self, chuan: str):
        self.chuan = chuan


def test_tat_thi_tra_ve_thu_tu_cu(monkeypatch):
    """RERANKER_MODEL rong -> khong dung toi model nao."""
    monkeypatch.setattr(rerank, "_nap",
                        lambda t: (_ for _ in ()).throw(
                            AssertionError("khong duoc nap model khi TAT")))
    cs = [chunk("a", "x"), chunk("b", "y"), chunk("c", "z")]
    ra = rerank.xep_lai(CauGia("hoi"), cs, top_k=2, ten_model="")
    assert [c.chunk_id for c in ra] == ["a", "b"]


def test_xep_lai_theo_diem_cross_encoder(monkeypatch):
    class ModelGia:
        @staticmethod
        def predict(cap):
            # Cham cao cho chunk chua "dung"
            return [0.9 if "dung" in t else 0.1 for _, t in cap]

    monkeypatch.setattr(rerank, "_nap", lambda t: ModelGia)
    cs = [chunk("a", "sai"), chunk("b", "dung"), chunk("c", "sai")]
    ra = rerank.xep_lai(CauGia("hoi"), cs, top_k=2, ten_model="gia")
    assert ra[0].chunk_id == "b"


def test_giu_diem_rrf_khong_ghi_de(monkeypatch):
    """Mat diem RRF la mat kha nang so sanh hai cach xep hang."""
    class ModelGia:
        @staticmethod
        def predict(cap):
            return [0.5] * len(cap)

    monkeypatch.setattr(rerank, "_nap", lambda t: ModelGia)
    c = chunk("a", "x", diem=0.0164)
    ra = rerank.xep_lai(CauGia("hoi"), [c], top_k=1, ten_model="gia")
    assert ra[0].diem_rrf == 0.0164
    assert ra[0].diem == 0.5


def test_loi_thi_lui_ve_thu_tu_cu_va_DEM(monkeypatch):
    """Nuot loi la dung, nhung phai dem - neu khong loi trong nhu ket luan."""
    def no(_):
        raise RuntimeError("index 258 is out of bounds")

    monkeypatch.setattr(rerank, "_nap", no)
    truoc = rerank.so_lan_loi()
    cs = [chunk("a", "x"), chunk("b", "y")]
    ra = rerank.xep_lai(CauGia("hoi"), cs, top_k=2, ten_model="gia")

    assert [c.chunk_id for c in ra] == ["a", "b"], "phai lui ve thu tu cu"
    assert rerank.so_lan_loi() == truoc + 1, \
        "phai dem lan that bai - xem docstring dau file"


def test_danh_sach_rong():
    assert rerank.xep_lai(CauGia("hoi"), [], top_k=5, ten_model="gia") == []
