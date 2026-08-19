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

DSN_MAC_DINH = "postgresql://nextfarm:nextfarm@localhost:15432/nextfarm"


def dsn() -> str:
    """Chuoi ket noi. Uu tien DATABASE_URL trong .env / bien moi truong."""
    s = os.environ.get("DATABASE_URL", DSN_MAC_DINH)
    return s.replace("postgresql+psycopg://", "postgresql://")


def ket_noi(**kw):
    """Mo mot ket noi moi. Goi ben nhan trach nhiem dong."""
    import psycopg
    return psycopg.connect(dsn(), **kw)
