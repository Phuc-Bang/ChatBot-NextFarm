"""
API admin phai BAO LOI khi CSDL hong, khong duoc tra so lieu mac dinh.

SU CO PHAT HIEN 2026-08-22 (ra soat, chua kip xay ra khi demo)

Ba ham doc cua `app/core/nhat_ky.py` deu nuot exception roi tra ve gia tri
"binh thuong":

    doc_nhat_ky()   -> []
    tong_quan()     -> {"tong_luot": 222, "so_tu_choi": 147, ... }
    thong_ke_kho()  -> {"chunk_tong": 292, "chunk_index_duoc": 185, ... }

Bo so cua tong_quan() day du va khop nhau den muc khong the phan biet voi so
that. Demo cho NextFarm ma quen `docker compose up -d` thi trang /admin van
hien "222 luot hoi, 147 ca da chan, chi phi $0,0526" - va khong ai biet.

Day la mau thuan truc tiep voi dieu du an nay dang ban. Quy chuan cua chinh
du an: "That bai phai la that bai. Khong thay bang du lieu mac dinh."

Bon test dau kiem HANH VI. Test thu nam doc MA NGUON de canh giu - mot lan
"sua cho tien" dat lai so mac dinh se lam no do.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))


def _lam_hong_db(monkeypatch):
    """Bat `ket_noi` nem loi, giong luc Postgres khong chay."""
    from app.core import nhat_ky

    def ket_noi_hong(*a, **kw):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(nhat_ky, "ket_noi", ket_noi_hong)


def test_doc_nhat_ky_nem_loi_khi_db_hong(monkeypatch):
    """[] nghia la "chua ai hoi", khong phai "khong doc duoc"."""
    from app.core.nhat_ky import LoiDocNhatKy, doc_nhat_ky

    _lam_hong_db(monkeypatch)
    with pytest.raises(LoiDocNhatKy):
        doc_nhat_ky()


def test_tong_quan_nem_loi_khi_db_hong(monkeypatch):
    from app.core.nhat_ky import LoiDocNhatKy, tong_quan

    _lam_hong_db(monkeypatch)
    with pytest.raises(LoiDocNhatKy):
        tong_quan()


def test_thong_ke_kho_nem_loi_khi_db_hong(monkeypatch):
    from app.core.nhat_ky import LoiDocNhatKy, thong_ke_kho

    _lam_hong_db(monkeypatch)
    with pytest.raises(LoiDocNhatKy):
        thong_ke_kho()


def test_khong_con_so_cung_trong_nhat_ky():
    """Canh giu: khong con con so bia nao trong ma nguon.

    BO CHU THICH truoc khi kiem - chu thich giai thich su co nay co nhac
    lai chinh cac con so do va se bao dong gia. Cach lam giong
    tests/test_ghi_log_khong_chan.py:93.
    """
    src = (GOC / "app" / "core" / "nhat_ky.py").read_text(encoding="utf-8")
    ma = "\n".join(d.split("#", 1)[0] for d in src.splitlines())
    # Bo luon docstring cua lop/ham (chua chu tieng Viet, khong chua so).
    for so in ("222", "8084", "0.0526", "56862", "22680", "292", "185"):
        assert so not in ma, (
            "con so cung `" + so + "` con trong app/core/nhat_ky.py - "
            "mot gia tri mac dinh cho truong hop loi da quay lai"
        )
    assert "return []" not in ma, \
        "doc_nhat_ky() lai tra ve [] khi loi - loi im lang quay lai"


def test_endpoint_admin_tra_503(monkeypatch):
    """Loi phai noi len toi HTTP status, khong dung lai o tang service.

    Phai dat ADMIN_TOKEN: TestClient goi tu dia chi "testclient", khong phai
    loopback, nen canh cua /admin tu choi truoc khi cham toi CSDL. Do la hanh
    vi DUNG cua canh cua - dia chi khong xac dinh duoc thi khong mo - nen
    test phai di qua cua tu te chu khong duoc noi long cua.
    """
    from fastapi.testclient import TestClient

    from app.core import nhat_ky
    from app.main import app

    def ket_noi_hong(*a, **kw):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(nhat_ky, "ket_noi", ket_noi_hong)
    monkeypatch.setenv("ADMIN_TOKEN", "token-test")

    with TestClient(app) as c:
        for duong in ("/api/admin/tong_quan",
                      "/api/admin/nhat_ky",
                      "/api/admin/kho_tri_thuc"):
            r = c.get(duong, headers={"X-Admin-Token": "token-test"})
            assert r.status_code == 503, duong + " tra " + str(r.status_code)
            assert "loi" in r.json(), duong + " thieu khoa 'loi'"


def test_trang_admin_kiem_tra_r_ok():
    """Trang admin phai kiem `r.ok`, khong duoc goi thang `r.json()`.

    HTTP 503 van co body JSON hop le nen `.then(r => r.json())` KHONG nem
    loi. Thieu kiem tra nay thi 503 se duoc ve len bieu do nhu du lieu that.
    """
    html = (GOC / "frontend" / "admin.html").read_text(encoding="utf-8")
    assert 'fetch("/api/admin/kho_tri_thuc").then(r => r.json())' not in html, \
        "admin.html goi thang r.json() - 503 se lot qua nhu du lieu that"
    assert "r.ok" in html, "admin.html khong kiem tra r.ok o dau ca"
    assert 'id="bang-loi"' in html, \
        "admin.html khong co bang bao loi - nguoi xem khong phan biet duoc " \
        "'chua co du lieu' voi 'khong doc duoc du lieu'"
