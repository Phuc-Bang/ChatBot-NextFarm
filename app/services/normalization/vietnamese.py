#!/usr/bin/env python3
"""
vietnamese.py - Chuan hoa cau hoi tieng Viet, bon lop (quy chuan v2.0 muc 13).

RANH GIOI CUA MODULE NAY

    Duoc phep sua HINH THUC cau hoi.
    Tuyet doi khong duoc suy dien NOI DUNG.

"ca chua can dat ph bn"  ->  "ca chua can dat ph bao nhieu"        DUOC
"ca chua can dat ph bn"  ->  "ca chua giai doan ra hoa can pH..."  KHONG

Su khac nhau giua hai dong tren la toan bo ly do module nay ton tai. Cho LLM
viet lai cau hoi truoc khi retrieval la con duong ngan nhat de bia: no se tu
them dau, tu them tu, tu them ngu canh - va tu do moi thu phia sau deu lech
ma khong ai biet (muc 13.3). Vi vay o day khong co mot loi goi LLM nao. Moi
phep bien doi deu deterministic va kiem duoc bang unit test.

BON LOP

  Lop 1  chuan hoa hinh thuc         NFC, gop khoang trang, sinh ban bo dau
  Lop 2  tu dien viet tat / dia phuong   tra tu dien viet tay, khop TRON TU
  Lop 3  chiu loi chinh ta           KHONG lam o day - lam bang pg_trgm o
                                     tang retrieval (muc 13.2 lop 3)
  Lop 4  lam ro khi mo ho            tra ve tin hieu, KHONG tu doan

DAU VET

Moi phep thay deu ghi lai trong CauHoi.da_thay. Chuan hoa la buoc co the lam
hong ca chuoi phia sau ma khong bao loi, nen no phai kiem lai duoc: khi mot
case eval that bai, phai tra loi duoc cau hoi "chuan hoa da doi nhung gi".
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE))

from app.core.text import bo_dau, chuan_hoa_nfc, gon_khoang_trang  # noqa: E402

LEXICON = BASE / "knowledge" / "lexicon"

# Nhung viet tat ngan khong duoc mo rong khi dung canh cac tu nay, vi trong
# ngu canh do chung la KY HIEU HOA HOC chu khong phai viet tat. Day la mot
# bang tra co dinh, khong phai suy dien ngu nghia.
KY_HIEU_HOA_HOC = {
    "n", "p", "k", "npk", "kali", "dam", "lan", "phan", "ure",
    "kcl", "k2o", "p2o5", "ca", "mg", "zn", "cu", "fe", "ph",
}

CO_SO = re.compile(r"\d")


@dataclass
class CauHoi:
    """Ket qua chuan hoa. Ban goc luon duoc giu nguyen."""

    goc: str
    chuan: str
    khong_dau: str
    mo_rong: list[str] = field(default_factory=list)
    da_thay: list[tuple[str, str, str]] = field(default_factory=list)
    canh_bao: list[str] = field(default_factory=list)

    def tom_tat(self) -> str:
        doi = [(a, b) for a, b, _ in self.da_thay if a != b]
        if not doi:
            return "khong doi gi"
        return "; ".join(a + " -> " + b for a, b in doi)


# ----------------------------------------------------------------------
# Nap tu dien (lop 2)
# ----------------------------------------------------------------------
def _nap_viet_tat() -> list[tuple[str, str]]:
    """Tra ve [(dang_bo_dau_cua_short, full)], cum dai truoc cum ngan.

    Sap theo do dai giam dan de cum nhieu tu ("thuoc bvtv") duoc thu truoc
    tung tu le ("bvtv"). Day dung la lop loi da gap o extract.py: chon theo
    thu tu tu dien thay vi chon cum dai nhat.
    """
    f = LEXICON / "abbreviations.yaml"
    if not f.exists():
        return []
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    ra = []
    for m in data.get("abbreviations") or []:
        short, full = str(m.get("short", "")), str(m.get("full", ""))
        if not short or not full:
            continue
        if bo_dau(short) == bo_dau(full):
            continue          # muc dong nhat, liet ke chi de khong bi sua nham
        ra.append((bo_dau(short), full))
    ra.sort(key=lambda x: -len(x[0]))
    return ra


def _nap_tu_dia_phuong() -> list[tuple[str, list[str]]]:
    """Tra ve [(canonical, [variants])] de MO RONG truy van.

    Luu y: bien the KHONG duoc dung de thay the trong cau tra loi. "ure" la
    mot loai phan dam cu the, khong dong nghia hoan toan voi "phan dam" -
    xem ghi chu trong local_terms.yaml. O day chung chi duoc dung de noi
    them tu khoa cho retrieval.
    """
    f = LEXICON / "local_terms.yaml"
    if not f.exists():
        return []
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    ra = []
    for m in data.get("terms") or []:
        canon = str(m.get("canonical", ""))
        vars_ = [str(v) for v in (m.get("variants") or [])]
        if canon:
            ra.append((canon, vars_))
    return ra


VIET_TAT = _nap_viet_tat()
TU_DIA_PHUONG = _nap_tu_dia_phuong()


# ----------------------------------------------------------------------
# Lop 2 - thay tron tu
# ----------------------------------------------------------------------
def _duoc_phep_thay(short: str, kd: str, dau: int, cuoi: int) -> tuple[bool, str]:
    """Cac ngoai le phai cai trong CODE, khong the ghi trong YAML.

    "kg" la vi du kinh dien va da duoc ghi ro ngay trong abbreviations.yaml:
    no vua la viet tat cua "khong" vua la ki-lo-gam. "bon 50 kg/ha" ma bi doi
    thanh "bon 50 khong/ha" la hong han cau hoi.
    """
    truoc = kd[max(0, dau - 12):dau]
    sau = kd[cuoi:cuoi + 12]

    if short == "kg":
        if CO_SO.search(truoc[-6:]) or CO_SO.search(sau[:6]):
            return False, "kg dung canh so -> la ki-lo-gam, khong phai 'khong'"

    # Chi nhung viet tat MA BAN THAN no cung la ky hieu hoa hoc moi bi soi
    # ngu canh. Ap quy tac nay cho moi viet tat ngan la chan nham: "bn" trong
    # "dat ph bn" bi chan chi vi dung canh "ph", mac du "bn" khong bao gio la
    # ky hieu hoa hoc.
    if short in KY_HIEU_HOA_HOC:
        lan_can = re.findall(r"\w+", truoc)[-1:] + re.findall(r"\w+", sau)[:1]
        for t in lan_can:
            if t.lower() in KY_HIEU_HOA_HOC:
                return False, short + " dung canh '" + t + "' -> ky hieu hoa hoc"
        if CO_SO.search(truoc[-3:]) or CO_SO.search(sau[:3]):
            return False, short + " dung canh so -> ky hieu hoa hoc"

    return True, ""


def _mo_rong_viet_tat(s: str) -> tuple[str, list[tuple[str, str, str]], list[str]]:
    """Thay viet tat tron tu tren chuoi CO DAU, dinh vi bang ban bo dau.

    bo_dau() giu nguyen do dai chuoi (moi ky tu ra dung mot ky tu), nen chi so
    tim duoc tren ban bo dau ap thang duoc vao ban co dau. Neu vi ly do nao do
    do dai lech, bo qua ca lop 2 va ghi canh bao - tha khong mo rong con hon
    thay nham vi tri.
    """
    kd = bo_dau(s)
    if len(kd) != len(s):
        return s, [], ["Bo qua lop 2: ban bo dau lech do dai so voi ban goc"]

    thay: list[tuple[int, int, str, str, str]] = []
    da_chiem = [False] * len(s)

    for short, full in VIET_TAT:
        for m in re.finditer(r"(?<!\w)" + re.escape(short) + r"(?!\w)", kd):
            a, b = m.start(), m.end()
            if any(da_chiem[a:b]):
                continue
            for i in range(a, b):
                da_chiem[i] = True
            ok, ly_do = _duoc_phep_thay(short, kd, a, b)
            if ok:
                thay.append((a, b, s[a:b], full, "viet tat"))
            else:
                thay.append((a, b, s[a:b], s[a:b], ly_do))

    thay.sort(key=lambda x: -x[0])
    ra = s
    dau_vet: list[tuple[str, str, str]] = []
    for a, b, cu, moi, ly_do in thay:
        if cu != moi:
            ra = ra[:a] + moi + ra[b:]
        dau_vet.append((cu, moi, ly_do))
    dau_vet.reverse()
    return ra, dau_vet, []


# ----------------------------------------------------------------------
# API chinh
# ----------------------------------------------------------------------
def chuan_hoa(text: str) -> CauHoi:
    """Lop 1 + lop 2. Ban goc luon giu nguyen trong CauHoi.goc."""
    goc = text
    s = gon_khoang_trang(chuan_hoa_nfc(text)).lower()
    s, dau_vet, canh_bao = _mo_rong_viet_tat(s)
    s = gon_khoang_trang(s)

    return CauHoi(
        goc=goc,
        chuan=s,
        khong_dau=bo_dau(s),
        mo_rong=mo_rong_truy_van(s),
        da_thay=dau_vet,
        canh_bao=canh_bao,
    )


def mo_rong_truy_van(s: str) -> list[str]:
    """Tu khoa NOI THEM cho retrieval - khong thay the gi trong cau hoi.

    Nguoi mien Nam go "dua leo", tai lieu Bo NN viet "dua chuot". Khong noi
    them thi keyword search truot hoan toan. Nhung "dua leo" van phai duoc
    giu trong cau hoi goc, va cau tra loi van trich nguyen van tai lieu.
    """
    kd = bo_dau(s)
    ra: list[str] = []
    for canon, variants in TU_DIA_PHUONG:
        moi_dang = [canon] + variants
        co_mat = [
            d for d in moi_dang
            if re.search(r"(?<!\w)" + re.escape(bo_dau(d)) + r"(?!\w)", kd)
        ]
        if not co_mat:
            continue
        for d in moi_dang:
            if d not in co_mat and d not in ra:
                ra.append(d)
    return ra


CAY_TRONG = {
    "lua": ["lua", "cay lua", "gieo sa", "cay ma"],
    "ca_chua": ["ca chua"],
    "dua_chuot": ["dua chuot", "dua leo"],
}


def phat_hien_cay(cau: CauHoi) -> list[str]:
    """Tra ve DANH SACH cay nhan ra duoc, co the rong hoac nhieu hon mot.

    Co y tra ve danh sach chu khong phai mot gia tri: cau "lua va ca chua
    khac nhau the nao" that su hoi hai cay, con cau "cay nay tuoi bao nhieu"
    khong hoi cay nao ca. Ep ve mot gia tri o day chinh la doan - viec quyet
    dinh co phai lam ro hay khong thuoc ve lop 4, xem can_lam_ro().
    """
    kd = cau.khong_dau
    ra = []
    for crop, dang in CAY_TRONG.items():
        for d in dang:
            if re.search(r"(?<!\w)" + re.escape(d) + r"(?!\w)", kd):
                ra.append(crop)
                break
    return ra


def can_lam_ro(cau: CauHoi) -> tuple[bool, str]:
    """Lop 4 - hoi lai mot cau ngan thay vi doan (muc 13.2).

    Chi goi o nhanh agronomy_knowledge. Cac nhanh tu choi khong can biet cay
    trong la gi moi tu choi duoc.
    """
    cay = phat_hien_cay(cau)
    if not cay:
        return True, ("Chua xac dinh duoc cay trong. Hoi lai: anh/chi dang hoi "
                      "ve lua, ca chua hay dua chuot a?")
    if len(cay) > 1:
        return True, ("Cau hoi nhac toi nhieu cay (" + ", ".join(cay) + "). "
                      "Hoi lai de biet can tra cuu cay nao.")
    return False, ""
