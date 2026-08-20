"""
Ghi query_log KHONG duoc chan cau tra loi.

SU CO THAT 2026-08-20

Moi request POST /api/chat khong bao gio tra ve. py-spy dump chi thang:

    ghi_query_log (app/core/nhat_ky.py)
      ket_noi (app/core/db.py)
        connect (psycopg/connection.py)
          wait_conn  <- TREO o day

Cau tra loi da san sang tu 0,01s (do bang cach goi thang tra_loi_cau_hoi).
Cau "bat van 3 trong 10 phut" dang le ton 6ms va 0 token vi bi Intent Router
chan ngay - nhung nguoi dung khong bao gio thay no.

try/except quanh ghi_query_log da co san va KHONG cuu duoc: treo khong phai
exception. psycopg.connect() khong co connect_timeout thi cho VO HAN.

Hai lop bao ve, test o day kiem ca hai.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_ket_noi_luon_co_connect_timeout(monkeypatch):
    """Lop 1: khong bao gio cho vo han."""
    from app.core import db

    da_goi = {}

    class GiaPsycopg:
        @staticmethod
        def connect(dsn, **kw):
            da_goi.update(kw)
            return object()

    monkeypatch.setitem(sys.modules, "psycopg", GiaPsycopg)
    db.ket_noi()
    assert "connect_timeout" in da_goi, \
        "ket_noi() phai dat connect_timeout, neu khong mot su co DB se " \
        "bien thanh treo im lang"
    assert da_goi["connect_timeout"] > 0


def test_ben_goi_ghi_de_duoc_timeout(monkeypatch):
    from app.core import db

    da_goi = {}

    class GiaPsycopg:
        @staticmethod
        def connect(dsn, **kw):
            da_goi.update(kw)
            return object()

    monkeypatch.setitem(sys.modules, "psycopg", GiaPsycopg)
    db.ket_noi(connect_timeout=3)
    assert da_goi["connect_timeout"] == 3


def test_ghi_log_an_toan_nuot_loi():
    """Lop 2: loi ghi log khong duoc noi len tang tren."""
    from app.main import _ghi_log_an_toan

    class KetQuaGia:
        pass

    # Doi tuong thieu moi thuoc tinh -> ghi_query_log chac chan nem loi.
    # Ham nay van phai tra ve binh thuong.
    _ghi_log_an_toan(KetQuaGia())


def test_chat_khong_goi_ghi_log_trong_than_ham():
    """Ghi log phai qua BackgroundTasks, khong nam tren duong tra loi.

    Kiem bang cach doc ma nguon: than ham chat() khong duoc goi thang
    ghi_query_log. Doc ma nguon nghe tho so, nhung no bat dung thu can bat -
    mot lan sua vo y dat lai ghi_query_log() vao than ham se lam test do.
    """
    import inspect

    from app import main

    # BO CHU THICH truoc khi kiem. Than ham co chu thich giai thich
    # chinh su co nay va no nhac ten ghi_query_log - kiem ca chu thich
    # se bao dong gia.
    src = chr(10).join(d.split("#", 1)[0]
                    for d in inspect.getsource(main.chat).splitlines())
    assert "ghi_query_log(" not in src, \
        "chat() goi thang ghi_query_log - no se chan cau tra loi khi DB treo"
    assert "add_task" in src, \
        "chat() phai day viec ghi log sang BackgroundTasks"
