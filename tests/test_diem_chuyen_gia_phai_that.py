"""
Diem chuyen gia phai do NGUOI cham, khong duoc sinh bang script.

SU CO THAT 2026-08-22

Commit 59329b3 them evaluation/results/expert_scores.json kem
evaluation/scripts/danh_gia_chuyen_gia_auto.py, va thong bao "hoan thanh cham
diem chuyen gia 50 cau - Diem TB: 3.89/5.0".

Script do KHONG doc noi dung cau tra loi. No chay mot thang if/else theo SO
NGUON va loai cau hoi:

    if loai == "tu_choi":      c1..c5 = 4,4,3,4,4
    elif so_nguon >= 2:        c1..c5 = 4,4,4,4,4
    elif so_nguon == 1:        c1..c5 = 4,3,3,4,3
    else:                      c1..c5 = 3,3,3,3,3

Hau qua do duoc: 50 "danh gia chuyen gia" chi co DUNG 3 to hop diem khac
nhau, 36/50 ca giong het nhau. Va file ghi:

    "reviewer": "Chuyên gia Nông học Nextfarm AI"

- mot chuyen gia khong ton tai. Ghi chu di kem ("Noi dung phu hop quy trinh
khuyen nong") la mot khang dinh ve nong hoc, do doan ma chua bao gio doc
nong hoc.

VI SAO DIEU NAY NGHIEM TRONG HON MOI LOI KHAC TRONG DU AN

Toan bo du an ton tai de chung minh he thong KHONG BIA. Quy chuan ghi ro
diem chuyen gia la "thu duy nhat cho ra ty le chinh xac that", vi nguoi
duyet cua doi KHONG phai chuyen gia nong nghiep (DEC-029). Sinh diem bang
script roi gan ten chuyen gia vao la bia dung thu ma san pham hua se khong
bia - va no nam trong tai lieu giao cho khach hang, tren mot repo cong khai.

Cong cu /expert GIU LAI - no la mot cong cu cham diem tu te. Chi du lieu bia
bi go.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

DIEM = GOC / "evaluation" / "results" / "expert_scores.json"
TIEU_CHI = ("c1", "c2", "c3", "c4", "c5")

# Ten khong duoc phep dung lam nguoi cham: chung khong tro toi mot con nguoi.
TEN_GIA = ("nextfarm ai", "chuyên gia nông học nextfarm ai", "ai", "auto",
           "script", "he thong", "hệ thống", "chatbot", "gpt", "gemini",
           "claude", "bot")


def test_khong_co_script_sinh_diem_chuyen_gia():
    """Khong duoc ton tai bat ky script nao tu sinh diem chuyen gia."""
    nghi = []
    for f in (GOC / "evaluation").rglob("*.py"):
        van = f.read_text(encoding="utf-8", errors="ignore")
        if "expert_scores" in van and ('"c1"' in van or "'c1'" in van):
            nghi.append(str(f.relative_to(GOC)))
    assert not nghi, (
        "script tu sinh diem chuyen gia: " + ", ".join(nghi) + "\n"
        "Diem chuyen gia phai do nguoi cham qua /expert. Mot script khong doc "
        "duoc nong hoc thi khong cham duoc nong hoc."
    )


def test_neu_co_file_diem_thi_phai_do_nguoi_cham():
    """File diem chi hop le khi no mang dau vet cua mot NGUOI cham that.

    Bo qua khi chua co file - chua ai cham la trang thai binh thuong va
    trung thuc. Cai KHONG binh thuong la mot file day du diem ma khong ai
    cham.
    """
    if not DIEM.exists():
        return  # chua ai cham - dung, va la trang thai hien tai

    d = json.loads(DIEM.read_text(encoding="utf-8"))
    scores = d.get("scores") or {}
    if not scores:
        return

    nguoi = str(d.get("reviewer") or "").strip().lower()
    assert nguoi, "file diem khong ghi ai cham"
    assert nguoi not in TEN_GIA, (
        "nguoi cham la '" + str(d.get("reviewer")) + "' - khong tro toi mot "
        "con nguoi. Diem chuyen gia phai kem ten nguoi chiu trach nhiem."
    )
    assert not any(t in nguoi for t in ("ai)", " ai", "auto", "script")), \
        "ten nguoi cham co dau hieu la may sinh: " + str(d.get("reviewer"))

    # Phan bo diem: nguoi cham 50 cau nong hoc khong the chi ra vai to hop.
    to_hop = Counter(tuple(v.get(k) for k in TIEU_CHI) for v in scores.values())
    if len(scores) >= 20:
        assert len(to_hop) > 4, (
            str(len(scores)) + " ca cham nhung chi co " + str(len(to_hop))
            + " to hop diem khac nhau (nhieu nhat: " + str(to_hop.most_common(1))
            + "). Day la dau van tay cua mot thang if/else, khong phai cua mot "
            "nguoi doc tung cau."
        )


def test_endpoint_ghi_diem_di_qua_canh_cua():
    """POST /api/expert/save ghi de ban ghi nghiem thu - khong duoc de mo.

    Doc cay cu phap thay vi grep, de chu thich khong danh lua.
    """
    import ast

    cay = ast.parse((GOC / "app" / "main.py").read_text(encoding="utf-8"))
    for ham in ast.walk(cay):
        if not isinstance(ham, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        duong = ""
        for dec in ham.decorator_list:
            if (isinstance(dec, ast.Call) and dec.args
                    and isinstance(dec.args[0], ast.Constant)
                    and isinstance(dec.args[0].value, str)):
                duong = dec.args[0].value
        if duong != "/api/expert/save":
            continue
        goi = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "kiem_quyen_admin" for n in ast.walk(ham))
        assert goi, \
            "/api/expert/save khong goi kiem_quyen_admin - bat ky ai cung ghi " \
            "de duoc ket qua danh gia chuyen gia"
        return
    raise AssertionError("khong tim thay endpoint /api/expert/save")


def test_khong_ghi_de_ban_ghi_bang_phieu_rong():
    """POST rong khong duoc xoa cong cham cua chuyen gia.

    SU CO THAT trong luc kiem thu 2026-08-22: mot lenh
    `curl -X POST -d '{}' /api/expert/save` tra ve 200 va lam file diem con
    dung hai ky tu `{}`. Endpoint THAY THE toan bo ban ghi, nen mot than yeu
    cau sai la mat sach cong cham.
    """
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        h = {"X-Admin-Token": "t"}
        import os
        os.environ["ADMIN_TOKEN"] = "t"
        try:
            for than in ({}, {"reviewer": "Nguyen Van A"},
                         {"scores": {"cau_1": {"c1": 5}}},
                         {"reviewer": "  ", "scores": {"cau_1": {"c1": 5}}},
                         {"reviewer": "Nguyen Van A", "scores": {}}):
                r = c.post("/api/expert/save", json=than, headers=h)
                assert r.status_code == 400, \
                    "than " + str(than) + " duoc chap nhan (HTTP " \
                    + str(r.status_code) + ") - no se ghi de ban ghi danh gia"
                assert "loi" in r.json()
        finally:
            os.environ.pop("ADMIN_TOKEN", None)
