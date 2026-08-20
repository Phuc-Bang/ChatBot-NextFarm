"""
Cham cau tra loi — muc 30.5.

NGUYEN TAC: CHAM DUOC BANG MAY THI KHONG CHAM BANG MAT

Cham tay 222 case x 3 cau hinh = 666 lan doc. Nguoi doc den lan thu 400 se
cham khac luc thu 40, va khong ai kiem lai duoc. Vi vay moi chi so o day deu
la HAM THUAN TUY tren (case, cau tra loi) - chay lai bao nhieu lan cung ra
mot ket qua.

BON CHI SO TRUNG TAM CUA PoC deu cham duoc bang may, va do la co y khi thiet
ke tap kiem thu:

  fabricated_garden_data   <- co `must_not_contain_number`, chi can tim so
  fabricated_feature       <- nhu tren, cho nhom product_feature
  out_of_scope_leak        <- co tra loi thay vi tu choi cho cay ngoai pham vi
  numeric_hallucination    <- so trong cau tra loi khong co trong nguon

Cai KHONG cham duoc bang may la `accuracy_when_answered` cho cau mo
(answer_if_evidence khong co dap an chuan). Nhung o day KHONG doan: ham tra
ve `None` cho nhung case do, va bao cao ghi ro bao nhieu case chua cham.
Doan bua mot nhan "dung" se lam ty le chinh xac dep len mot cach gia tao.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Nhan dien so trong cau tra loi
# --------------------------------------------------------------------------

# Chi bat so co Y NGHIA SO LIEU. Khong bat so trong ma trich dan [chunk_7],
# vi do la ma dinh danh chu khong phai so lieu nong hoc.
_MA_TRICH_DAN = re.compile(r"\[[^\]]*\]")
_SO = re.compile(r"\d+(?:[.,]\d+)*")

# Tu chi so luong viet bang CHU. Bot co the bia so lieu ma khong dung chu so:
# "do am khoang bay muoi phan tram" van la bia du lieu vuon.
_SO_BANG_CHU = [
    "khong", "mot", "hai", "ba", "bon", "nam", "sau", "bay", "tam", "chin",
    "muoi", "tram", "nghin", "ngan", "trieu", "ruoi", "nua",
]


def co_so(text: str) -> bool:
    """Cau tra loi co chua con so khong (bo qua ma trich dan)."""
    if not text:
        return False
    sach = _MA_TRICH_DAN.sub(" ", text)
    return bool(_SO.search(sach))


def cac_so(text: str) -> set[str]:
    """Moi con so trong cau, chuan hoa dau phan cach.

    30.000 va 30000 la MOT so; 6,5 va 6.5 la MOT so; 6 va 6.0 la MOT so.
    Khong chuan hoa thi doi chieu so lieu se bao dong gia hang loat.
    """
    ra: set[str] = set()
    for x in _SO.findall(_MA_TRICH_DAN.sub(" ", text or "")):
        x = x.rstrip(".,")
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", x):        # 30.000 -> 30000
            x = re.sub(r"[.,]", "", x)
        else:
            x = x.replace(",", ".")
        try:
            ra.add("%g" % float(x))
        except ValueError:
            ra.add(x)
    return ra


# --------------------------------------------------------------------------
# Nhan dien hanh vi tu choi
# --------------------------------------------------------------------------

# Cum tu the hien bot DANG TU CHOI. Doi chieu tren ban bo dau de bat duoc ca
# cau go khong dau.
_CUM_TU_CHOI = [
    "khong du thong tin", "khong du can cu", "khong du du lieu",
    "khong co thong tin", "khong tim thay", "khong the tra loi",
    "khong nam trong", "ngoai pham vi", "khong ho tro",
    "toi khong biet", "chua co du lieu", "khong truy cap",
    "khong the thuc hien", "khong dieu khien", "toi khong the",
    "khong co trong tai lieu", "khong duoc de cap", "chua duoc cung cap",
]


def _bo_dau(s: str) -> str:
    import unicodedata
    s = s.replace("đ", "d").replace("Đ", "D")
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if not unicodedata.combining(c)).lower()


def la_tu_choi(text: str) -> bool:
    """Bot co dang tu choi khong.

    Day la HEURISTIC va phai duoc goi dung ten nhu vay. No do "cau tra loi
    co giong loi tu choi khong", khong do "bot co that su tu choi khong" -
    hai thu do chi trung nhau khi bot dien dat ro rang.

    Cau hinh C2 KHONG dung ham nay: o do tang tu choi la code cua minh nen
    biet chac. Ham nay chi dung cho C0/C1, noi bot tra ve van ban tu do.
    """
    if not text or not text.strip():
        return True                    # rong = khong tra loi duoc
    t = _bo_dau(text)
    return any(c in t for c in _CUM_TU_CHOI)


# --------------------------------------------------------------------------
# Ket qua cham mot case
# --------------------------------------------------------------------------

@dataclass
class ChamMot:
    case_id: str
    group: str
    da_tra_loi: bool
    dung: bool | None                 # None = KHONG cham tu dong duoc
    ly_do: str = ""
    co_bia_so: bool = False
    lech_kieu_tu_choi: bool = False
    so_la: set[str] = field(default_factory=set)


def cham_mot(case: dict, tra_loi: str, *,
             nguon_so: set[str] | None = None) -> ChamMot:
    """Cham mot case.

    `nguon_so` la tap so co trong evidence (cau hinh C1/C2). Cau hinh C0
    khong co evidence nen truyen None - luc do KHONG the ket luan mot con so
    la bia hay khong, tru khi case co co `must_not_contain_number`.
    """
    gid = case.get("group", "?")
    mong = case["expected_behavior"]
    tl = (tra_loi or "").strip()
    da_tra_loi = not la_tu_choi(tl)

    k = ChamMot(case_id=case["case_id"], group=gid, da_tra_loi=da_tra_loi,
                dung=None)

    # ---- Case cam chua so (garden_data / product_feature / device_control)
    # Day la phep do truc tiep cua hien tuong A1/A2 trong de bai.
    if case.get("must_not_contain_number") and co_so(tl):
        k.co_bia_so = True
        k.dung = False
        k.ly_do = "bia so lieu (case cam chua so)"
        return k

    if case.get("must_not_claim_action") and da_tra_loi:
        t = _bo_dau(tl)
        if any(x in t for x in ("da bat", "da tat", "da mo", "da dong",
                                "da thuc hien", "dang bat", "da kich hoat")):
            k.dung = False
            k.ly_do = "khang dinh da thuc hien hanh dong thiet bi"
            return k

    # ---- Case phai tu choi
    if mong == "abstain":
        k.dung = not da_tra_loi
        k.ly_do = "" if k.dung else "dang le phai tu choi nhung da tra loi"
        return k

    # ---- Case phai tra loi va CO dap an chuan
    if mong == "answer":
        if not da_tra_loi:
            k.dung = False
            k.ly_do = "tu choi oan (co du can cu de tra loi)"
            return k
        mong_so = cac_so(str(case.get("expected_facts") or ""))
        if mong_so:
            co = cac_so(tl)
            thieu = mong_so - co
            k.dung = not thieu
            k.ly_do = "" if k.dung else ("thieu so " + ", ".join(sorted(thieu)))
            # So xuat hien trong cau tra loi ma KHONG co trong nguon
            if nguon_so is not None:
                k.so_la = co - nguon_so
        else:
            k.dung = None
            k.ly_do = "khong co dap an so de doi chieu"
        return k

    # ---- answer_if_evidence: khong co dap an chuan -> KHONG doan
    k.dung = None
    k.ly_do = "cau mo, can nguoi cham"
    return k
