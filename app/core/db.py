#!/usr/bin/env python3
"""
db.py - Ket noi PostgreSQL.

Khong dung ORM o tang truy xuat. Ly do: cac truy van retrieval dung
to_tsvector('simple', ...), word_similarity() va RRF - deu la thu ma ORM
phai vong qua raw SQL moi viet duoc, va vong qua ORM lam kho doc dung cho
can doc ky nhat.
"""

from __future__ import annotations

import os

# 127.0.0.1 chu KHONG PHAI localhost. Do duoc 2026-08-20:
#
#     127.0.0.1   ket noi trong 0,01s
#     localhost   ket noi trong 10,05s   <- bang dung connect_timeout
#
# `localhost` phan giai ra ca ::1 (IPv6) lan 127.0.0.1, va libpq thu IPv6
# TRUOC. Docker Desktop chi bind IPv4, nen moi ket noi phai cho het
# connect_timeout roi moi thu IPv4 va thanh cong.
#
# Day la nguyen nhan goc cua ca chuoi su co: request /api/chat "treo",
# pytest treo, cong cu do cham (xem docs/reports/P10_su_co_treo_api.md).
# Doi lai thanh localhost la lam song lai toan bo.
DSN_MAC_DINH = "postgresql://nextfarm:nextfarm@127.0.0.1:15432/nextfarm"


def dsn() -> str:
    """Chuoi ket noi. Uu tien DATABASE_URL trong .env / bien moi truong."""
    s = os.environ.get("DATABASE_URL", DSN_MAC_DINH)
    return s.replace("postgresql+psycopg://", "postgresql://")


# Do duoc 2026-08-20: mo ket noi toi Postgres qua Docker Desktop tren Windows
# ton ~3,2s. Dat 15s de con cho lan cham, nhung KHONG de vo han.
TIMEOUT_KET_NOI = int(os.environ.get("DB_CONNECT_TIMEOUT", "15"))
# Mili-giay. Truy van nang nhat do duoc (quet 185 chunk) mat < 1s.
TIMEOUT_CAU_LENH = int(os.environ.get("DB_STATEMENT_TIMEOUT_MS",
                                      "30000"))


def ket_noi(**kw):
    """Mo mot ket noi moi. Goi ben nhan trach nhiem dong.

    LUON co connect_timeout. Khong co no, psycopg.connect() cho VO HAN, va
    mot su co DB bien thanh treo im lang - da va phai that: ghi_query_log()
    treo o buoc nay lam MOI request /api/chat khong bao gio tra ve, du cau
    tra loi da san sang tu 0,01s. try/except khong cuu duoc vi treo khong
    phai exception.

    Ben goi van co the ghi de bang connect_timeout=... neu can.
    """
    import psycopg
    kw.setdefault("connect_timeout", TIMEOUT_KET_NOI)
    # statement_timeout chan truong hop KHAC: ket noi mo duoc nhung truy van
    # khong bao gio xong. Da va phai that - psycopg ket o cursor.execute()
    # trong khi pg_stat_activity KHONG thay ket noi nao, tuc ket noi da dut
    # ma client khong biet. connect_timeout khong cuu duoc truong hop nay.
    kw.setdefault("options", "-c statement_timeout=" + str(TIMEOUT_CAU_LENH))
    return psycopg.connect(dsn(), **kw)
