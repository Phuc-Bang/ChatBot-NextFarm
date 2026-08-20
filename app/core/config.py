"""
Doc .env. Khong dung thu vien ngoai de script chay duoc ngay ca khi chua
cai du phu thuoc.

.env KHONG bao gio duoc commit (.gitignore). Moi gia tri that song o do.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"

_da_nap = False


def nap_env(force: bool = False) -> None:
    """Nap .env vao os.environ.

    Bien moi truong CO SAN duoc uu tien: cho phep ghi de tam thoi khi chay
    thu nghiem ma khong phai sua file.
    """
    global _da_nap
    if _da_nap and not force:
        return
    _da_nap = True
    if not ENV_FILE.exists():
        return
    for dong in ENV_FILE.read_text(encoding="utf-8").splitlines():
        dong = dong.strip()
        if not dong or dong.startswith("#") or "=" not in dong:
            continue
        k, v = dong.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def lay(ten: str, mac_dinh: str | None = None) -> str | None:
    nap_env()
    return os.environ.get(ten, mac_dinh)


def bat_buoc(ten: str) -> str:
    v = lay(ten)
    if not v:
        raise RuntimeError(
            "Thieu " + ten + " trong .env. Xem .env.example de biet dinh dang.")
    return v
