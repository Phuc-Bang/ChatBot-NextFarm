#!/usr/bin/env python3
"""
migrate.py - Ap dung cac file SQL trong db/migrations theo thu tu.

VI SAO KHONG DUNG ALEMBIC

Luoc do nay khong lon va thay doi cham, nhung co nhieu RANG BUOC quan trong
can doc duoc bang mat (CHECK cua high-risk, view indexable_chunk). SQL thuan
giu duoc chung nguyen ven va co the doc nhu tai lieu; alembic se bien chung
thanh loi goi ham Python kho doi chieu voi quy chuan.

VI SAO KHONG DUNG db/init/

Script trong db/init chi chay MOT LAN, luc volume con rong. Sua luoc do sau
do se khong duoc ap dung ma khong co canh bao nao.

CACH DUNG
    python db/migrate.py               # ap dung cac migration chua chay
    python db/migrate.py --status      # xem da chay nhung gi
    python db/migrate.py --dry-run     # xem se chay gi
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
MIGRATIONS = BASE / "migrations"

DEFAULT_DSN = "postgresql://nextfarm:nextfarm@localhost:15432/nextfarm"

BANG_THEO_DOI = """
CREATE TABLE IF NOT EXISTS schema_migration (
    filename    TEXT PRIMARY KEY,
    sha256      TEXT NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def dsn() -> str:
    """Lay DSN tu bien moi truong, khong hard-code mat khau that vao code."""
    raw = os.environ.get("DATABASE_URL", DEFAULT_DSN)
    # SQLAlchemy dung tien to postgresql+psycopg://, psycopg thi khong hieu
    return raw.replace("postgresql+psycopg://", "postgresql://")


def bam(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def danh_sach() -> list[Path]:
    return sorted(MIGRATIONS.glob("*.sql"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Ap dung migration SQL")
    ap.add_argument("--status", action="store_true", help="Xem da chay nhung gi")
    ap.add_argument("--dry-run", action="store_true", help="Xem se chay gi")
    args = ap.parse_args()

    try:
        import psycopg
    except ImportError:
        sys.exit("Thieu psycopg. Chay: pip install -r requirements.txt")

    files = danh_sach()
    if not files:
        sys.exit("Khong co file migration nao trong " + str(MIGRATIONS))

    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(BANG_THEO_DOI)
            conn.commit()

            cur.execute("SELECT filename, sha256 FROM schema_migration")
            da_chay = dict(cur.fetchall())

        if args.status:
            print("Migration da chay:")
            for name, h in sorted(da_chay.items()):
                print("  " + name.ljust(34) + h[:12])
            con_lai = [f.name for f in files if f.name not in da_chay]
            print("\nChua chay: " + (", ".join(con_lai) if con_lai else "(khong con)"))
            return

        for path in files:
            h = bam(path)

            if path.name in da_chay:
                if da_chay[path.name] != h:
                    # File da chay ma noi dung doi -> nguy hiem, dung lai.
                    # Sua migration cu se lam DB cua moi nguoi lech nhau ma
                    # khong ai biet. Muon doi thi them file moi.
                    sys.exit(
                        "LOI: " + path.name + " da chay nhung noi dung da thay doi.\n"
                        "Sua migration cu se lam DB cua moi nguoi lech nhau.\n"
                        "Muon doi luoc do -> them file migration MOI.")
                continue

            if args.dry_run:
                print("[se chay] " + path.name)
                continue

            print("[chay] " + path.name)
            sql = path.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migration (filename, sha256) VALUES (%s, %s)",
                    (path.name, h))
            conn.commit()

        if not args.dry_run:
            print("\nXong.")


if __name__ == "__main__":
    main()
