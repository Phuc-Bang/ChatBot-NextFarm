#!/usr/bin/env python3
"""
router.py - Intent Router, lop rule (quy chuan v2.0 muc 11).

VIEC DUY NHAT CUA FILE NAY

Nhan ra cau hoi dang thuoc nhanh nao trong bon nhanh:

    agronomy_knowledge  -> di tiep vao Scope Check -> RAG
    garden_data         -> dung, tu choi (REFUSE_GARDEN_DATA)
    product_feature     -> dung, tu choi (REFUSE_PRODUCT_FEATURE)
    device_control      -> dung, tu choi (REFUSE_DEVICE_CONTROL)

Bot van khong co mot byte du lieu IoT nao. No chi duoc day de BIET MINH DANG
KHONG CO GI (muc 11.2). Day khong phai lam Bai toan B.

DAY MOI LA MOT NUA CUA ROUTER

Quy chuan muc 11.3 chot cach trien khai la "LLM phan loai few-shot (~40 vi
du) + mot lop rule chan truoc cho cac mau chac chan". File nay la lop rule.
Lop LLM chua lam duoc vi chua chot model (DEC-015).

Hau qua phai noi ro, khong duoc giau: khi khong luat nao khop, router tra ve
agronomy_knowledge voi nguon="mac_dinh" va do_tin_cay=0. Do KHONG phai mot
ket luan - do la "lop rule khong biet, nhuong cho lop sau". Quy tac thien
lech an toan cua muc 11.4 (khong chac thi nghieng ve TU CHOI) ap o lop LLM,
khong ap duoc o day: neu lop rule cu khong khop la tu choi thi bot se tu
choi gan nhu moi cau hoi nong hoc that.

Ai doc ket qua cua router deu phai doc ca truong `nguon`.

BA PHAN BIET KHO NHAT, VA CACH GIAI

  1. Hoi NGUONG hay hoi SO DO THUC TE
       "ca chua khu A do am bao nhieu LA DUOC"  -> nguong  -> tra loi
       "do am khu A bao nhieu"                  -> so do   -> tu choi
     Chi khac nhau o hai chu. Giai bang DAU_HIEU_CHUAN_MUC: cau nao co dau
     hieu hoi chuan muc thi khong bao gio la garden_data.

  2. RA LENH hay HOI TRANG THAI, khi ca hai deu nhac toi thiet bi
       "bat van 3"                  -> lenh    -> device_control
       "van so 3 co dang chay khong" -> hoi    -> garden_data
     Giai bang _la_cau_hoi_trang_thai(): cau hoi trang thai khong bao gio la
     menh lenh, tru khi kem tieu tu nho va ("giup", "ho", "duoc khong").

  3. Cau hoi tiep noi khong con chu ngu
       "the gio dang bao nhieu" / "xong chua em"
     Giai bang hai luot chay: luot mot tren cau hoi don, luot hai tren cau
     hoi gop toi da ba luot truoc do. Luot hai ha do tin cay.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE))

from app.services.normalization.vietnamese import (  # noqa: E402
    CauHoi, chuan_hoa, phat_hien_cay,
)

AGRONOMY = "agronomy_knowledge"
GARDEN_DATA = "garden_data"
PRODUCT_FEATURE = "product_feature"
DEVICE_CONTROL = "device_control"

NHAN_TU_CHOI = (GARDEN_DATA, PRODUCT_FEATURE, DEVICE_CONTROL)


# ======================================================================
# Tu dien dau hieu - viet tren ban BO DAU de chiu duoc ca cau khong dau
# ======================================================================

# --- garden_data: ba nhom, phai co it nhat HAI nhom (muc 11.3) ---
THOI_DIEM = [
    "gio", "bay gio", "dang", "hien tai", "hien nay", "hom qua", "hom nay",
    "sang nay", "chieu nay", "toi nay", "tuan nay", "thang nay", "vua nay",
    "luc nay", "may hom nay", "hom truoc", "dem qua", "thang truoc",
    "tuan truoc", "sang gio", "tu sang",
]

SO_HUU = [
    "khu a", "khu b", "khu c", "khu d", "khu e",
    "khu 1", "khu 2", "khu 3", "khu 4", "khu 5",
    "vuon toi", "vuon nha", "vuon cua toi", "vuon minh", "vuon em",
    "ruong nha", "ruong toi", "nha kinh", "nha luoi", "nha toi",
    "cua toi", "ben toi", "van so", "thiet bi so", "thiet bi",
    "khu vuon", "du lieu vuon", "trang trai",
]

TRUY_VAN_TRANG_THAI = [
    "dang bao nhieu", "dang la bao nhieu", "gio bao nhieu", "bao nhieu roi",
    "co chay khong", "dang chay khong", "dang chay", "co bat khong",
    "co hoat dong khong", "da tuoi chua", "tuoi chua", "may lan roi",
    "may lan", "do duoc bao nhieu", "chi so bao nhieu", "dang o muc",
    "len bao nhieu", "xuong bao nhieu", "the nao roi", "con bao nhieu",
    "da bat chua", "da tat chua", "con online khong", "co online khong",
    "mat ket noi", "co may", "co dat khong", "co du khong", "co on khong",
    "xong chua", "chay chua", "het bao nhieu", "tong bao nhieu",
    "co cao qua", "co thap qua", "dang dat",
]

# Cau hoi CHUAN MUC - khong bao gio la garden_data du co bao nhieu dau hieu
# khac. "ca chua khu A do am bao nhieu LA DUOC a" hoi nguong trong sach, phai
# tra loi; bo hai chu "la duoc" di thi thanh hoi so do that.
DAU_HIEU_CHUAN_MUC = [
    "la duoc", "la vua", "la tot", "la hop ly", "la dat", "la chuan",
    "thich hop", "phu hop", "nen duy tri", "nen o muc", "tieu chuan",
    "bao nhieu la", "the nao la", "can bao nhieu", "yeu cau bao nhieu",
    "bao nhieu thi", "ly tuong", "toi uu", "khuyen cao",
]

# Chi so do luong - dung cho luat "chi so + bao nhieu" o nhom C
CHI_SO = {
    "do am dat": "độ ẩm đất",
    "do am khong khi": "độ ẩm không khí",
    "do am": "độ ẩm",
    "am do": "độ ẩm",
    "nhiet do": "nhiệt độ",
    "ph": "pH",
    "ec": "EC",
    "anh sang": "ánh sáng",
    "dinh duong": "dinh dưỡng",
    "luong mua": "lượng mưa",
    "luong nuoc": "lượng nước",
}

# --- device_control: menh lenh tac dong vat ly ---
DONG_TU_DIEU_KHIEN = [
    "bat", "tat", "mo", "dong", "dung", "ngung", "chay", "khoi dong",
    "kich hoat", "hen gio", "cai lich", "dat lich", "tuoi", "ngat", "khoa",
    "van hanh",
]

DANH_TU_THIET_BI = [
    "bom", "may bom", "den", "quat", "he thong tuoi", "lich tuoi",
    "ca tuoi", "thiet bi", "cam bien", "cong tac", "relay", "may suoi",
    "mai che", "quat thong gio", "dan tuoi",
]

# Tieu tu bien mot cau hoi thanh mot YEU CAU: "tuoi ho anh khu B nhe"
TIEU_TU_YEU_CAU = [
    "giup", "ho", "nhe", "duoc khong", "di", "luon", "gium", "voi",
    "lam on", "cho toi", "cho anh", "cho em",
]

# --- product_feature: hoi ve chinh san pham va dich vu ---
TU_SAN_PHAM = [
    "app", "ung dung", "phan mem", "nextfarm", "next farm", "tinh nang",
    "man hinh", "giao dien", "nut", "cai dat", "dang nhap",
    "tai khoan", "thong bao", "phien ban", "cap nhat app", "menu",
    "dang ky tai khoan", "dang ky app",
    "goi cuoc", "phi dich vu", "ho tro ky thuat", "web", "website",
    # Ho tu vung san pham va dich vu - cung mot ho voi danh sach muc 11.3
    "mat khau", "dang xuat", "phan quyen", "chia quyen", "quyen",
    "lich su", "bao hanh", "gia bao nhieu", "bao nhieu tien", "mua o dau",
    "android", "ios", "iphone", "dien thoai", "may tinh", "sim", "wifi",
    "che do", "dong bo", "xuat bao cao", "xuat file", "cai dat lai",
    "ket noi lai", "huong dan su dung", "bo dieu khien", "goi dich vu",
]

# "tai sao he thong lam the nay" la cau hoi ve HANH VI SAN PHAM, khong phai
# ve cay trong - du no nhac ten thiet bi.
HOI_TAI_SAO = ["tai sao", "sao lai", "vi sao", "sao toi", "sao ma", "loi gi"]


# "van" bo dau trung voi "van" trong "cay VAN heo" (van = van) va "VAN de"
# (van = van). Bo dau xoa mat su khac nhau do, nen phai nhan dien van bang
# tu di kem thay vi bang chinh no.
VAN_RE = re.compile(r"(?<!\w)van\s+(so|khu|cham|dien|tuoi|chinh|xa|dong|\d)")

# Tu de hoi - mot cau hoi thong tin thi khong phai mot menh lenh.
# "dung may bom loai NAO" (dung) khac "DUNG ca tuoi dang chay" (dung), nhung
# bo dau roi thi ca hai deu la "dung". Tu de hoi la thu phan biet duoc.
TU_DE_HOI = ["nao", "gi", "the nao", "sao", "dau", "bao lau", "khi nao",
             "bao gio", "may", "kieu gi", "cach nao"]


# ----------------------------------------------------------------------
# Va cham do bo dau
# ----------------------------------------------------------------------
# Khop tron tu la dieu kien CAN nhung khong DU trong tieng Viet. Tieng Anh
# co "start" va "bat" la hai chuoi khac nhau; tieng Viet viet roi tung am
# tiet, nen sau khi bo dau:
#
#     bat  = bat (bat den)  = bat (bat dau, bat buoc)
#     gio  = gio (may gio)  = gio (thong gio, quat gio)
#     van  = van (van nuoc) = van (van heo) = van (van de)
#     dung = dung (dung lai) = dung (dung phan gi)
#
# Bo dau la thu bat buoc phai lam de chiu duoc cau hoi khong dau (muc 14.3),
# nhung no xoa mat dau thanh - va dau thanh la thu phan biet nhung tu tren.
#
# Bang duoi day ghi tung va cham DA GAP, kem tu di kem lam no vo hieu. Moi
# dong deu la mot cau hoi nong hoc that da bi tu choi oan trong luc do.
NGOAI_LE = {
    "gio": ["thong", "quat", "huong", "manh", "mua"],   # thong gio, quat gio
    "bat": ["dau", "buoc"],                              # bat dau, bat buoc
    "dong": ["xuan", "bang", "bao", "ruong"],            # vu dong xuan
    "mo": ["hinh", "ta", "dat"],                         # mo hinh, mo ta
    "tuoi": ["cay", "tho"],                              # tuoi cay (tuoi doi)
}


def _co(kd: str, tu: str) -> bool:
    """Khop TRON TU tren ban bo dau, tru cac va cham da biet.

    Khop chuoi con la lop loi da lam hong hai module trong du an nay: "ph"
    khop trong "cat pha", "ma" khop trong "manh". Khong lap lai lan thu ba.
    """
    loai_tru = NGOAI_LE.get(tu)
    for m in re.finditer(r"(?<!\w)" + re.escape(tu) + r"(?!\w)", kd):
        if not loai_tru:
            return True
        truoc = re.findall(r"\w+", kd[max(0, m.start() - 12):m.start()])[-1:]
        sau = re.findall(r"\w+", kd[m.end():m.end() + 12])[:1]
        if not any(t in loai_tru for t in truoc + sau):
            return True
    return False


def _tim(kd: str, ds: list[str]) -> list[str]:
    return [t for t in ds if _co(kd, t)]


# ======================================================================
@dataclass
class KetQua:
    """Ket qua phan loai.

    `nguon` quan trong khong kem `nhan`:
      "rule"       - mot luat da khop tren chinh cau hoi
      "rule_ngu_canh" - luat khop nho gop them luot truoc do
      "mac_dinh"   - khong luat nao khop, lop rule KHONG BIET va nhuong cho
                     lop LLM. Doc `nhan` ma bo qua `nguon` la hieu sai.
    """

    nhan: str
    do_tin_cay: float
    nguon: str
    bang_chung: list[str] = field(default_factory=list)
    khu: str | None = None
    chi_so: str | None = None
    cay: list[str] = field(default_factory=list)

    @property
    def phai_tu_choi(self) -> bool:
        return self.nhan in NHAN_TU_CHOI

    def __str__(self) -> str:
        bc = "[" + ", ".join(self.bang_chung) + "]" if self.bang_chung else ""
        return (self.nhan + " (" + self.nguon + ", tin cay="
                + str(round(self.do_tin_cay, 2)) + ") " + bc)


# ======================================================================
# Trich thong tin de dien vao mau tu choi - KHONG DOAN
# ======================================================================
KHU_RE = re.compile(r"(?<!\w)khu\s+([a-z0-9]{1,3})(?!\w)")


def trich_khu(kd: str) -> str | None:
    """Tra ve ten khu dung nhu nguoi dung go, hoac None.

    None nghia la khong biet. Mau tu choi phai chiu duoc None bang cach noi
    chung chung, chu khong duoc dien mot ten khu nao do vao cho trong.
    """
    m = KHU_RE.search(kd)
    if not m or m.group(1) == "vuc":
        return None
    return "khu " + m.group(1).upper()


def trich_chi_so(kd: str) -> str | None:
    """Tra ve chi so DAI NHAT khop duoc, hoac None.

    Chon cum dai nhat chu khong phai cum dau tien: "do am dat" phai thang
    "do am". Day dung la loi da sua trong extract.py - chon theo thu tu tu
    dien thay vi chon cum dai nhat.
    """
    khop = [(k, v) for k, v in CHI_SO.items() if _co(kd, k)]
    if not khop:
        return None
    return max(khop, key=lambda x: len(x[0]))[1]


def _co_so_huu(kd: str) -> list[str]:
    """Dau hieu vi tri thuoc so huu.

    "khu" tran cung tinh, tru "khu vuc" - "khu vuc mien Bac" la dia ly, khong
    phai mot khu vuon cua nguoi dung.
    """
    ra = _tim(kd, SO_HUU)
    if not ra and _co(kd, "khu") and not _co(kd, "khu vuc"):
        ra = ["khu"]
    return ra


KHUNG_TRANG_THAI = re.compile(
    r"(?<!\w)co\s+(du|cao|thap|on|dat|tot|nhieu|it|kip|day)\b.{0,30}?khong(?!\w)")


def _la_cau_hoi_trang_thai(kd: str) -> bool:
    """Cau dang HOI trang thai, khong phai dang RA LENH."""
    if re.search(r"(?<!\w)co\s+\S.{0,30}?\s+khong(?!\w)", kd):
        return True
    return any(_co(kd, t) for t in
               ("chua", "may gio", "bao nhieu", "the nao roi", "may lan"))


# ======================================================================
# Ba luat
# ======================================================================
def _luat_device_control(kd: str) -> tuple[float, list[str]] | None:
    """Menh lenh tac dong vat ly.

    Dieu kien tien quyet la mot dong tu dieu khien. Chi dong tu la khong du:
    "tuoi nuoc cho ca chua may lan mot ngay" la cau hoi ky thuat.
    """
    dt = _tim(kd, DONG_TU_DIEU_KHIEN)
    if not dt:
        return None

    tb = _tim(kd, DANH_TU_THIET_BI)
    if VAN_RE.search(kd):
        tb = ["van (" + VAN_RE.search(kd).group(0) + ")"] + tb
    sh = _co_so_huu(kd)
    yc = _tim(kd, TIEU_TU_YEU_CAU)

    # "app co tu dong bat van khong" hoi KHA NANG cua app, khong phai lenh.
    if _tim(kd, TU_SAN_PHAM):
        return None

    # "tai sao tat bom thi ca tuoi cung dung" hoi HANH VI he thong, khong
    # phai ra lenh. Khong co cau menh lenh nao bat dau bang "tai sao".
    if _tim(kd, HOI_TAI_SAO):
        return None

    # Cau co tu de hoi la cau hoi thong tin, khong phai menh lenh:
    # "dung may bom loai NAO cho ruong 5 sao" hoi chon may, khong bao he
    # thong tat bom. Tru khi kem tieu tu yeu cau ("tat bom giup toi voi").
    if _tim(kd, TU_DE_HOI) and not _tim(kd, TIEU_TU_YEU_CAU):
        return None

    # Menh lenh dat dau cau la dau hieu manh nhat: "bat van 3", "hen gio tuoi"
    mo_dau = kd.lstrip()
    bat_dau_bang_lenh = any(mo_dau.startswith(v + " ") for v in dt)

    # Cau hoi trang thai khong phai menh lenh - tru khi kem tieu tu yeu cau
    # ("cho vuon toi ngung tuoi hom nay duoc khong" van la mot yeu cau), hoac
    # tru khi chinh luot truoc do da la mot menh lenh ("bat van 3" -> "xong
    # chua em"). Truong hop sau chi gap o luot chay co ngu canh.
    if _la_cau_hoi_trang_thai(kd) and not yc and not bat_dau_bang_lenh:
        return None

    if tb and (bat_dau_bang_lenh or yc or not _la_cau_hoi_trang_thai(kd)):
        return 0.95, ["dong tu: " + dt[0], "thiet bi: " + tb[0]]

    # Khong nhac ten thiet bi nhung ra lenh len mot vi tri cu the:
    # "em tuoi ho anh khu B nhe"
    if sh and (yc or bat_dau_bang_lenh):
        return 0.85, ["dong tu: " + dt[0], "vi tri: " + sh[0],
                      "yeu cau: " + (yc[0] if yc else "menh lenh dau cau")]

    return None


def _luat_product_feature(kd: str) -> tuple[float, list[str]] | None:
    """Hoi ve chinh san pham hoac dich vu NextFarm."""
    sp = _tim(kd, TU_SAN_PHAM)
    if sp:
        return 0.9, ["tu san pham: " + sp[0]]

    # "tai sao tat bom thi ca tuoi cung dung theo" - hoi HANH VI cua he thong.
    ts = _tim(kd, HOI_TAI_SAO)
    tb = _tim(kd, DANH_TU_THIET_BI)
    if ts and tb:
        return 0.8, ["hoi hanh vi he thong: " + ts[0], "thiet bi: " + tb[0]]

    return None


def _luat_garden_data(kd: str) -> tuple[float, list[str]] | None:
    """Can it nhat HAI trong BA nhom dau hieu (muc 11.3).

    Mot nhom la khong du, va day khong phai su than trong thua: "ca chua khu
    A do am bao nhieu la duoc" chi co nhom so huu -> van la cau hoi nguong ky
    thuat, phai tra loi. "the gio dang bao nhieu" co ca thoi diem lan truy
    van trang thai -> hoi so do that.
    """
    if _tim(kd, DAU_HIEU_CHUAN_MUC):
        return None                    # hoi nguong, khong phai hoi so do

    a = _tim(kd, THOI_DIEM)
    b = _co_so_huu(kd)
    c = _tim(kd, TRUY_VAN_TRANG_THAI)

    # "do am khu A bao nhieu" - chi so do luong di voi "bao nhieu", khong kem
    # dau hieu chuan muc, la dang hoi so do thuc te.
    chi_so = trich_chi_so(kd)
    if chi_so and _co(kd, "bao nhieu") and not c:
        c = [chi_so + " + bao nhieu"]
    if not c and KHUNG_TRANG_THAI.search(kd):
        c = ["khung 'co ... khong': " + KHUNG_TRANG_THAI.search(kd).group(0)]

    nhom = [x for x in (a, b, c) if x]
    if len(nhom) < 2:
        return None

    bc = []
    if a:
        bc.append("thoi diem: " + a[0])
    if b:
        bc.append("so huu: " + b[0])
    if c:
        bc.append("truy van: " + c[0])
    return (0.95 if len(nhom) == 3 else 0.85), bc


LUAT = (
    (DEVICE_CONTROL, _luat_device_control),
    (PRODUCT_FEATURE, _luat_product_feature),
    (GARDEN_DATA, _luat_garden_data),
)


# ======================================================================
# API chinh
# ======================================================================
def _gop_ngu_canh(cau_hoi: str, context_turns: list[str] | None) -> str:
    """Gop toi da 3 luot gan nhat de bat cau hoi tiep noi (muc 11.3).

    "the gio dang bao nhieu" tach rieng thi thieu chu ngu; dat canh luot
    truoc "ca chua khu A do am bao nhieu la duoc a" thi ro la hoi so do thuc
    te cua khu A.

    Ngu canh chi dung de PHAN LOAI. No khong duoc dua vao retrieval hay vao
    cau tra loi - do la duong de ngu canh cu bien thanh noi dung moi.
    """
    truoc = (context_turns or [])[-3:]
    return " . ".join(truoc + [cau_hoi])


def phan_loai(cau_hoi: str, context_turns: list[str] | None = None) -> KetQua:
    """Phan loai mot cau hoi. Deterministic, khong goi model."""
    cau: CauHoi = chuan_hoa(cau_hoi)
    day_du: CauHoi = chuan_hoa(_gop_ngu_canh(cau_hoi, context_turns))

    chung = dict(
        khu=trich_khu(day_du.khong_dau),
        chi_so=trich_chi_so(day_du.khong_dau),
        cay=phat_hien_cay(day_du),
    )

    # Luot 1: chi cau hoi hien tai. Thu tu luat co y nghia - menh lenh dieu
    # khien la mau cu the nhat, roi den cau hoi ve san pham, cuoi cung moi
    # den so lieu vuon (mau rong nhat).
    for nhan, luat in LUAT:
        kq = luat(cau.khong_dau)
        if kq:
            return KetQua(nhan, kq[0], "rule", kq[1], **chung)

    # Luot 2: gop them luot truoc. Cau hoi tiep noi ("the gio dang bao nhieu",
    # "xong chua em") khong du chu de phan loai neu tach rieng. Ha do tin cay
    # vi ngu canh co the da cu.
    if context_turns:
        for nhan, luat in LUAT:
            kq = luat(day_du.khong_dau)
            if kq:
                return KetQua(nhan, kq[0] * 0.9, "rule_ngu_canh",
                              kq[1] + ["(nho ngu canh)"], **chung)

    # Khong luat nao khop. Day KHONG phai ket luan "cau nay la nong hoc" -
    # day la "lop rule khong biet". Lop LLM few-shot (muc 11.3) phai xu ly
    # phan nay, va chinh o do moi ap quy tac thien lech an toan muc 11.4.
    return KetQua(AGRONOMY, 0.0, "mac_dinh", ["khong luat nao khop"], **chung)
