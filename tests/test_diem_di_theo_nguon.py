"""
Diem PHAI di theo chunk ra toi ChunkNguon.

SU CO THAT 2026-08-22

Duong risk-coverage (muc 30.4) quet nguong tau tren diem truy xuat. Chay
`make risk-coverage` lan dau ra mot duong cong THOAI HOA - dung mot diem:

    tau        coverage%   risk%   tra loi   sai
    -0.0000    43.2        2.9     35        1

Nguyen nhan: `ChunkNguon` khong co truong `diem`, con run_c2.py ghi

    "diem_cao_nhat": max(getattr(n, "diem", 0.0) or 0.0 for n in r.nguon)

`getattr` voi gia tri mac dinh KHONG BAO LOI khi thuoc tinh khong ton tai.
No lang le tra ve 0.0. Ket qua: 81/81 ban ghi deu co diem_cao_nhat = 0.0,
file ket qua trong nhu binh thuong, va cong cu ve duong cong bao "khong co
nguong nao cho risk = 0" - nghe nhu mot ket luan khoa hoc chu khong phai
mot loi.

Day la ly do test nay kiem CAU TRUC chu khong kiem gia tri: mot truong bi
thieu o day khong lam gi do do len, no lam mot phep do ra ket qua sai.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_chunknguon_co_truong_diem():
    """Thieu truong nay thi getattr im lang tra ve 0.0."""
    from app.services.pipeline import ChunkNguon

    ten = {f.name for f in ChunkNguon.__dataclass_fields__.values()}
    assert "diem" in ten, \
        "ChunkNguon thieu truong `diem` - duong risk-coverage se thoai hoa"
    assert "diem_rrf" in ten, \
        "ChunkNguon thieu `diem_rrf` - mat kha nang so sanh RRF voi rerank"


def test_dung_chunknguon_truyen_diem_vao():
    """Co truong thoi chua du - phai co ai do DIEN vao."""
    import inspect

    from app.services import pipeline

    src = inspect.getsource(pipeline)
    i = src.find("ChunkNguon(")
    assert i > 0, "khong tim thay cho dung ChunkNguon - test da mat tac dung"
    doan = src[i:i + 320]
    assert "diem" in doan, \
        "dung ChunkNguon ma khong truyen diem - moi chunk se mang diem 0.0"


def test_diem_giu_nguyen_gia_tri_truyen_vao():
    from app.services.pipeline import ChunkNguon

    n = ChunkNguon("a#1", "T", "P", "u", "text", 1, 0.9421, 0.0470)
    assert n.diem == 0.9421
    assert n.diem_rrf == 0.0470


def test_runner_c2_van_doc_dung_ten_truong():
    """run_c2.py va ChunkNguon phai khop ten truong.

    Hai file nay o hai tang khac nhau va khong co gi rang buoc chung. Doi ten
    truong o mot ben la du de phep do im lang tra ve 0 lan nua.
    """
    src = (Path(__file__).resolve().parents[1]
           / "evaluation" / "runners" / "run_c2.py").read_text(encoding="utf-8")
    assert 'getattr(n, "diem"' in src or "n.diem" in src, \
        "run_c2.py khong con doc truong `diem` - kiem lai ca hai ben"
