"""
Goi `app`.

CHO CACHE MODEL PHAI DAT O DAY, KHONG DAT CHO NAO KHAC

O C cua may nay day 99% (con 3,2 GB tren 189 GB). Cache HuggingFace mac dinh
nam trong thu muc nguoi dung tren o C va da chiem 1,7 GB - tuc chinh no la
mot phan cua cho day. Tai them mot model nua la het cho, va loi bao ra se la
mot loi giai nen kho hieu chu khong phai "het dia".

O D con 188 GB. Cache doi ve day.

Vi sao dat o day chu khong o config.nap_env(): huggingface_hub doc HF_HOME
LUC IMPORT. Nhieu file trong du an import sentence_transformers o dong dau
tien (bat buoc - xem chu thich ve segfault trong pipeline.py), tuc TRUOC khi
bat cu ham nao cua ta chay. Dat trong nap_env() la dat qua muon va cache van
roi ve o C.

`app/__init__.py` chay khi bat cu thu gi trong `app.` duoc import, nen no la
diem som nhat ta kiem soat duoc.

Van cho phep ghi de: dat HF_HOME san trong moi truong thi ta khong dung toi.
"""

from __future__ import annotations

import os
from pathlib import Path

_CACHE_MAC_DINH = Path(__file__).resolve().parents[1] / ".cache" / "huggingface"

if not os.environ.get("HF_HOME"):
    _CACHE_MAC_DINH.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(_CACHE_MAC_DINH)
