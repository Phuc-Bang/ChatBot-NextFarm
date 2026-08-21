"""
/admin phai MAC DINH AN TOAN, khong phai mac dinh mo.

VAN DE PHAT HIEN 2026-08-22

Truoc day /admin va /api/admin/* khong kiem danh tinh ai ca. Thu duy nhat
dang bao ve chung la Makefile:115 chay uvicorn voi `--host 127.0.0.1`. Doi
mot chu thanh `0.0.0.0` la toan bo query_log - cau hoi nguyen van cua nguoi
dung, cau tra loi, token, chi phi tung luot - mo ra cho bat ky ai goi toi.

Mot dong ghi chu trong tai lieu khong chan duoc dieu do. Nen bay gio co canh
cua that:

    ADMIN_TOKEN co dat   -> phai kem dung token
    ADMIN_TOKEN de trong -> chi loopback

Test o day canh dung mot dieu: KHONG CO DUONG NAO mo /admin ra ngoai loopback
ma khong dat token.

Luu y ky thuat: TestClient (starlette 0.41.3) KHONG cho dat dia chi client,
va no goi tu "testclient" chu khong phai 127.0.0.1 - nen o che do khong token
no bi tu choi. Do la dung: dia chi khong nam trong danh sach loopback thi
khong mo.

Nen phan kiem theo dia chi goi thang `kiem_quyen_admin` voi mot Request dung
tu scope ASGI that (khong phai object gia), con phan kiem token di qua
TestClient de chay het duong HTTP.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))


@pytest.fixture()
def khong_token(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    from app.core import config
    monkeypatch.setattr(config, "nap_env", lambda *a, **k: None)
    return monkeypatch


def _req(dia_chi, headers=None, qs=""):
    """Request that dung tu scope ASGI - khong phai object gia."""
    from starlette.requests import Request

    return Request({
        "type": "http", "method": "GET", "path": "/admin",
        "query_string": qs.encode(),
        "headers": [(k.lower().encode(), v.encode())
                    for k, v in (headers or {}).items()],
        "client": (dia_chi, 51000) if dia_chi else None,
    })


def _client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_khong_token_thi_tu_choi_dia_chi_ngoai(khong_token):
    """Day la ca quan trong nhat: deploy quen cau hinh."""
    from app.main import kiem_quyen_admin

    for dia_chi in ("203.0.113.7", "10.0.0.5", "192.168.1.20", "0.0.0.0"):
        chan = kiem_quyen_admin(_req(dia_chi))
        assert chan is not None and chan.status_code == 403, \
            dia_chi + " duoc cho qua - mot deploy quen dat ADMIN_TOKEN se lo " \
            "toan bo nhat ky truy van"


def test_khong_token_van_phuc_vu_loopback(khong_token):
    """Trai nghiem PoC hom nay khong duoc thay doi: chay cuc bo la chay duoc."""
    from app.main import kiem_quyen_admin

    for dia_chi in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        assert kiem_quyen_admin(_req(dia_chi)) is None, \
            dia_chi + " bi tu choi - `make serve` khong con dung duoc"


def test_dia_chi_khong_xac_dinh_thi_khong_mo(khong_token):
    """req.client co the None. Khong biet ai goi thi KHONG mo."""
    from app.main import kiem_quyen_admin

    chan = kiem_quyen_admin(_req(None))
    assert chan is not None and chan.status_code == 403, \
        "dia chi None duoc cho qua - khong biet ai goi thi khong duoc mo"

    # Va ca duong HTTP that: TestClient goi tu host "testclient".
    with _client() as c:
        assert c.get("/api/admin/nhat_ky").status_code == 403


def test_co_token_thi_bat_buoc_dung_token(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "bi-mat-that")
    with _client() as c:
        # Dung token -> qua cua. Ben trong co the tra 503 vi khong co CSDL;
        # diem can kiem la KHONG phai 401.
        r = c.get("/admin", headers={"X-Admin-Token": "bi-mat-that"})
        assert r.status_code != 401

        # Token qua query param cung phai duoc chap nhan - trinh duyet mo
        # /admin?token=... khong dat header duoc.
        assert c.get("/admin?token=bi-mat-that").status_code != 401

        for gui in ({}, {"X-Admin-Token": ""}, {"X-Admin-Token": "sai"},
                    {"X-Admin-Token": "bi-mat-tha"},
                    {"X-Admin-Token": "bi-mat-that "}):
            r = c.get("/admin", headers=gui)
            assert r.status_code == 401, \
                "header " + str(gui) + " lot qua duoc cua"


def test_co_token_thi_loopback_KHONG_con_du(monkeypatch):
    """Dat token roi thi ngay ca may cuc bo cung phai kem token.

    Neu loopback van duoc mien thi token thanh vo nghia tren chinh may chay
    reverse proxy - proxy va app thuong o cung mot may.
    """
    monkeypatch.setenv("ADMIN_TOKEN", "bi-mat-that")
    from app.main import kiem_quyen_admin

    chan = kiem_quyen_admin(_req("127.0.0.1"))
    assert chan is not None and chan.status_code == 401, \
        "loopback duoc mien token - token thanh vo nghia tren may chay proxy"


def test_so_sanh_token_dung_compare_digest():
    """So sanh chuoi bang `==` do lech thoi gian theo tung ky tu.

    Doc ma nguon: mot lan sua doi `hmac.compare_digest` thanh `==` se lam
    test nay do.
    """
    import inspect

    from app import main

    src = inspect.getsource(main.kiem_quyen_admin)
    assert "compare_digest" in src, \
        "kiem_quyen_admin khong dung hmac.compare_digest de so token"


def test_moi_duong_admin_deu_qua_canh_cua():
    """Canh giu: them endpoint /api/admin/* moi ma quen goi canh cua.

    Doc cay cu phap thay vi grep, de khong bi chu thich danh lua.
    """
    import ast

    src = (GOC / "app" / "main.py").read_text(encoding="utf-8")
    cay = ast.parse(src)

    thieu = []
    for ham in ast.walk(cay):
        if not isinstance(ham, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        duong = ""
        for dec in ham.decorator_list:
            if (isinstance(dec, ast.Call) and dec.args
                    and isinstance(dec.args[0], ast.Constant)
                    and isinstance(dec.args[0].value, str)):
                duong = dec.args[0].value
        if not (duong == "/admin" or duong.startswith("/api/admin/")):
            continue
        goi = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "kiem_quyen_admin"
                  for n in ast.walk(ham))
        if not goi:
            thieu.append(duong + " (" + ham.name + ")")

    assert not thieu, \
        "cac duong admin khong goi kiem_quyen_admin: " + ", ".join(thieu)


def test_khong_co_backdoor_testclient():
    """Danh sach loopback khong duoc chua dia chi gia cua TestClient.

    Them "testclient" vao LOOPBACK la cach de nhat de lam test xanh, va no
    tao mot backdoor that trong ma san pham.
    """
    from app.main import LOOPBACK

    assert "testclient" not in LOOPBACK, \
        "LOOPBACK chua 'testclient' - day la backdoor, khong phai dia chi that"
