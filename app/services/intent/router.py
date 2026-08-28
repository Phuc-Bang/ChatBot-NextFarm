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

import json
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
GREETING = "greeting"
THANKS = "thanks"

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
    # THEM 2026-08-28 cho cau_41 "lan truoc anh bao do am 70% ma...".
    # Cung ho voi "hom truoc"/"thang truoc" da co san.
    "lan truoc", "lan truoc do", "hom no",
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
    # THEM 2026-08-28: nguoi dung doi chieu so do cu voi hien tai.
    "sao lai khac", "sao gio khac", "gio sao lai", "sao lai doi",
    "co dung khong", "con dung khong",
    "co cao qua", "co thap qua", "dang dat",
]

# Cau hoi CHUAN MUC - khong bao gio la garden_data du co bao nhieu dau hieu
# khac. "ca chua khu A do am bao nhieu LA DUOC a" hoi nguong trong sach, phai
# tra loi; bo hai chu "la duoc" di thi thanh hoi so do that.
# Nhac THANG den kho du lieu vuon / cam bien. Mot minh nhom nay DA DU.
#
# THEM 2026-08-28 sau khi cham tay 50 cau. Hai ca bi danh dau KHUYET DIEM:
#
#   cau_41  "lan truoc anh bao do am 70% ma, gio sao lai khac"
#   cau_42  "anh co xem duoc du lieu vuon toi ma, dung choi"
#
# Ca hai deu nhan dung mot cau tra loi: "Ban dang hoi ve cay trong nao a?" -
# tuc may roi xuong `can_lam_ro` cua Scope Check. An toan (khong bia so), nhung
# TU CHOI SAI LY DO: nguoi dung hoi du lieu vuon, may lai hoi ho trong cay gi.
#
# Vi sao roi: luat garden_data doi IT NHAT HAI trong ba nhom (thoi diem / so
# huu / truy van trang thai). "du lieu vuon toi" chi cham nhom so huu, nen
# len(nhom) < 2 va luat bo qua. Nguong hai nhom la co ly cho cau nhu "ca chua
# khu A do am bao nhieu la duoc" - hoi NGUONG ky thuat, phai tra loi.
#
# Nhung nhac thang "du lieu vuon" / "cam bien" thi khong con mo ho nua: do
# khong the la cau hoi nguong. Nen nhom nay duoc tinh la du mot minh.
DAU_HIEU_KHO_VUON = [
    "du lieu vuon", "du lieu cua vuon", "so lieu vuon", "du lieu vuon toi",
    "du lieu vuon cua toi", "du lieu ruong", "so lieu ruong",
    "cam bien cua toi", "cam bien nha toi", "cam bien vuon",
    "du lieu cua toi", "so lieu cua toi", "lich su do", "nhat ky tuoi",
]
# KHONG dua "cam bien" / "thiet bi do" / "sensor" TRAN vao day. Da thu
# 2026-08-28 va hai test co san bat duoc ngay:
#
#     "cam bien do am dat nen chon sau bao nhieu"   <- hoi KY THUAT LAP DAT
#     "thiet bi do pH dat loai nao chinh xac"       <- hoi CHON THIET BI
#
# Ca hai la cau hoi nong hoc that, phai tra loi. "Cam bien" tran mo ho giua
# "cai cam bien cua toi dang bao gi" va "cam bien noi chung". Chi dang co so
# huu ro rang moi du chac de tu choi.
# KHONG dua "anh bao" / "em noi" / "lan truoc bao" vao day. Da thu 2026-08-28
# va no bat qua tay ngay: "anh bao toi cach trong ca chua voi" va "anh noi giup
# em quy trinh bon phan cho lua" deu bi day sang garden_data va TU CHOI OAN.
# Chung la tu dem hoi thoai, khong phai dau hieu du lieu. cau_41 duoc xu ly
# bang duong khac - qua THOI_DIEM "lan truoc" cong TRUY_VAN_TRANG_THAI, tuc
# van phai du hai nhom nhu moi cau khac.

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
    "cai dat": ["mat", "do", "khoang", "cach", "may", "khom"],  # cai dat mat do may cay

    # may (THIET BI) != may (tu de hoi "may")
    #
    # PHAT HIEN 2026-08-28. Hau qua nang nhat trong bang nay cho toi nay:
    # "Bat may bom khu A" bi phan loai thanh `agronomy_knowledge`.
    #
    # Duong di cua loi: TU_DE_HOI chua "may" (nghia "may kg", "may ngay").
    # Bo dau xong thi "may bom" cung thanh "may bom", nen luat device_control
    # thay co tu de hoi va TU BO ngay o dong 351:
    #     if _tim(kd, TU_DE_HOI) and not _tim(kd, TIEU_TU_YEU_CAU): return None
    # Chi thoat khi cau tinh co kem tieu tu yeu cau ("giup", "ho", "nhe").
    #
    # Do la mot unsafe_misroute - dung cai chi so §30.5 doi phai bang 0. Ca ho
    # bi anh huong: "Bat may bom khu A", "Tat may bom khu B", "Mo may bom ngay",
    # "Bat may quat nha kinh", "Tat may bom" - 5/5 deu lot.
    #
    # Tap v3 khong bat duoc vi khong case device_control nao dung chu "may":
    # tat ca deu viet "bom" / "van" / "tuoi" tran. Con so 0 la that voi tap da
    # dong bang, nhung tap khong phu cach noi tu nhien nhat trong tieng Viet -
    # "may bom" moi la tu thong dung cho cai bom nuoc.
    "may": ["bom", "quat", "suoi", "cay", "phun", "loc", "gat", "say",
            "bua", "xoi", "tuot", "nen", "thoi", "che"],
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

    # Nhom D: nhac thang kho du lieu vuon. Du MOT MINH - xem ghi chu o
    # DAU_HIEU_KHO_VUON. Dat truoc cac nhom kia vi no khong can cong don.
    d = _tim(kd, DAU_HIEU_KHO_VUON)
    if d:
        return 0.90, ["nhac kho du lieu vuon: " + d[0]]

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


TU_CHAO_HOI = [
    "hello", "xin chao", "chao", "hi", "hey", "chao ban", "chao em", "chao ad",
    "chao bot", "he lo", "alo", "hi ban", "hello ban", "good morning", "chuc buoi sang",
    "ban la ai", "may la ai", "ai day", "gioi thieu", "gioi thieu ve ban",
    "ban co the lam gi", "ban lam duoc gi", "ban giup duoc gi", "tro giup", "huong dan",
]

TU_CAM_ON = [
    "cam on", "cam on ban", "cam on em", "cam on ad", "cam on nhe", "thanks",
    "thank you", "ok cam on", "da cam on", "tam biet", "bye", "bye bye",
]


def _luat_chao_hoi(kd: str) -> tuple[float, list[str]] | None:
    tu_khoa = _tim(kd, TU_CHAO_HOI)
    if tu_khoa:
        words = kd.strip().split()
        if len(words) <= 8:
            return 1.0, ["chao hoi / lam quen: " + tu_khoa[0]]
        if any(kd.startswith(p) for p in ("ban la ai", "gioi thieu", "ban co the", "ban lam duoc", "ban giup duoc")):
            return 1.0, ["hoi nang luc tro ly: " + tu_khoa[0]]
    return None


def _luat_cam_on(kd: str) -> tuple[float, list[str]] | None:
    tu_khoa = _tim(kd, TU_CAM_ON)
    if tu_khoa:
        words = kd.strip().split()
        if len(words) <= 6:
            return 1.0, ["cam on / tam biet: " + tu_khoa[0]]
    return None


LUAT = (
    (GREETING, _luat_chao_hoi),
    (THANKS, _luat_cam_on),
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


# ======================================================================
# LLM Few-Shot Intent Router (§11.3 & §40.2 Mục 9)
# ======================================================================

FEW_SHOT_EXAMPLES = [
    # 1. agronomy_knowledge
    {"text": "Cà chua cần bón bao nhiêu lân khi làm đất", "intent": AGRONOMY},
    {"text": "Thời vụ gieo lúa vụ Đông Xuân ở miền Bắc khi nào", "intent": AGRONOMY},
    {"text": "Độ ẩm đất dưa chuột bao nhiêu là cần tưới", "intent": AGRONOMY},
    {"text": "Cách phòng trừ sâu đục quả trên cà chua", "intent": AGRONOMY},
    {"text": "Lúa đẻ nhánh bón phân gì cho cứng cây", "intent": AGRONOMY},
    {"text": "Dưa leo làm giàn cao khoảng mấy mét", "intent": AGRONOMY},
    {"text": "Đất trồng cà chua độ pH 6.2 có cần bón vôi không", "intent": AGRONOMY},
    {"text": "Mật độ trồng dưa chuột bao tử là bao nhiêu cây một ha", "intent": AGRONOMY},
    
    # 2. garden_data
    {"text": "Độ ẩm đất khu B của vườn tôi hiện tại là bao nhiêu", "intent": GARDEN_DATA},
    {"text": "Vườn nhà anh đang đo được nhiệt độ bao nhiêu độ", "intent": GARDEN_DATA},
    {"text": "Hôm nay khu A đã tưới nước mấy lần rồi", "intent": GARDEN_DATA},
    {"text": "Cảm biến pH khu 2 báo số mấy thế em", "intent": GARDEN_DATA},
    {"text": "Cho anh xem lịch sử độ ẩm đất tuần qua của ruộng lúa", "intent": GARDEN_DATA},
    {"text": "Trạm thời tiết vườn em có ghi nhận mưa sáng nay không", "intent": GARDEN_DATA},
    
    # 3. device_control
    {"text": "Bật máy bơm tưới khu A giúp tôi ngay", "intent": DEVICE_CONTROL},
    {"text": "Tắt van số 3 đi em ơi", "intent": DEVICE_CONTROL},
    {"text": "Mở quạt thông gió nhà kính số 1 lên", "intent": DEVICE_CONTROL},
    {"text": "Dừng ca tưới tự động lúc 5 giờ chiều", "intent": DEVICE_CONTROL},
    {"text": "Kích hoạt hệ thống phun thuốc sâu khu B", "intent": DEVICE_CONTROL},
    {"text": "Ngắt điện toàn bộ máy bơm trạm 2", "intent": DEVICE_CONTROL},
    
    # 4. product_feature
    {"text": "NextFarm có hỗ trợ kết nối cảm biến EC không", "intent": PRODUCT_FEATURE},
    {"text": "Giá bộ điều khiển tưới NextFarm bao nhiêu tiền", "intent": PRODUCT_FEATURE},
    {"text": "App NextFarm có cài được trên iPhone không", "intent": PRODUCT_FEATURE},
    {"text": "Bảo hành thiết bị NextFarm trong thời gian bao lâu", "intent": PRODUCT_FEATURE},
    {"text": "Làm thế nào để mua thêm van điều khiển từ xa của bên bạn", "intent": PRODUCT_FEATURE},
    
    # 5. greeting
    {"text": "Chào bạn, mình là nông dân mới bắt đầu trồng cà chua", "intent": GREETING},
    {"text": "Xin chào bot NextFarm", "intent": GREETING},
    {"text": "Hello em, có rảnh tư vấn anh chút không", "intent": GREETING},
    
    # 6. thanks
    {"text": "Cảm ơn bạn nhiều nhé, thông tin rất hữu ích", "intent": THANKS},
    {"text": "Cảm ơn chuyên gia, tôi đã hiểu", "intent": THANKS},
    {"text": "Ok cảm ơn em nhiều nha", "intent": THANKS},
    
    # 7. out_of_scope
    {"text": "Giá vàng hôm nay tăng hay giảm thế em", "intent": "out_of_scope"},
    {"text": "Viết giúp tôi bài thơ về mùa gặt lúa", "intent": "out_of_scope"},
    {"text": "Cách sửa xe máy bị chết máy giữa đường", "intent": "out_of_scope"},
    {"text": "Dự báo thời tiết New York ngày mai", "intent": "out_of_scope"},
]


NHAN_HOP_LE = frozenset({AGRONOMY, GARDEN_DATA, PRODUCT_FEATURE, DEVICE_CONTROL,
                         GREETING, THANKS})


def _go_rao_json(t: str) -> str:
    """Go rao ```json ... ``` quanh cau tra loi cua model.

    Viet rieng vi `.strip("```json")` KHONG lam viec nay - str.strip nhan mot
    tap ky tu chu khong phai tien to.
    """
    t = (t or "").strip()
    if t.startswith("```"):
        t = t[3:]
        if t[:4].lower() == "json":
            t = t[4:]
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


class LLMFewShotRouter:
    """Tầng phân loại Intent Few-Shot bằng LLM (§11.3).
    
    Được kích hoạt khi tầng Rule-based siêu nhanh không phát hiện mẫu rõ ràng
    (do_tin_cay == 0.0 hoặc nguon == 'mac_dinh').
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.examples = FEW_SHOT_EXAMPLES

    def tao_prompt_fewshot(self, cau_hoi: str, context_turns: list[str] | None = None) -> str:
        """Sinh prompt phân loại kèm 35+ ví dụ mẫu."""
        lines = [
            "Bạn là bộ định tuyến ý định (Intent Router) chuyên dụng cho hệ thống Nextfarm AI.",
            "Nhiệm vụ: Phân loại câu hỏi của người dùng vào ĐÚNG 1 trong các nhóm ý định sau:",
            f"1. {AGRONOMY}: Hỏi kiến thức kỹ thuật nông nghiệp chuẩn (làm đất, bón phân, sâu bệnh, thời vụ, giống).",
            f"2. {GARDEN_DATA}: Hỏi dữ liệu cảm biến đo đạc thực tế, số liệu thời gian thực của vườn/trang trại.",
            f"3. {DEVICE_CONTROL}: Yêu cầu ra lệnh bật/tắt thiết bị, điều khiển van, máy bơm, quạt thông gió.",
            f"4. {PRODUCT_FEATURE}: Hỏi về tính năng sản phẩm, báo giá thiết bị hoặc phần mềm của NextFarm.",
            f"5. {GREETING}: Chào hỏi xã giao ban đầu.",
            f"6. {THANKS}: Cảm ơn, tạm biệt hoặc kết thúc hội thoại.",
            "7. out_of_scope: Câu hỏi hoàn toàn ngoài lề nông nghiệp và Nextfarm.",
            "",
            "QUY TẮC THIÊN LỆCH AN TOÀN (§11.4):",
            "- Nếu câu hỏi có dấu hiệu yêu cầu bật/tắt hoặc điều khiển, BẮT BUỘC gán device_control.",
            "- Nếu câu hỏi phân vân giữa hỏi chuẩn mực kỹ thuật và hỏi dữ liệu vườn riêng, ưu tiên an toàn.",
            "",
            "VÍ DỤ MẪU (FEW-SHOT EXAMPLES):"
        ]

        for ex in self.examples:
            lines.append(f"- Câu hỏi: \"{ex['text']}\" -> Intent: {ex['intent']}")

        if context_turns:
            lines.append(f"\nNgữ cảnh các lượt trước: {' | '.join(context_turns[-3:])}")

        lines.append(f"\nCâu hỏi cần phân loại: \"{cau_hoi}\"")
        lines.append("Trả về định dạng JSON: {\"intent\": \"...\", \"confidence\": 0.95, \"reason\": \"...\"}")
        return "\n".join(lines)

    def phan_loai(self, cau_hoi: str, context_turns: list[str] | None = None) -> KetQua:
        """Phân loại kết hợp: Rule trước, nếu không rõ thì gọi Few-Shot."""
        kq_rule = phan_loai(cau_hoi, context_turns)
        if kq_rule.nguon != "mac_dinh" and kq_rule.do_tin_cay > 0.0:
            return kq_rule

        # Nếu không có LLM client kết nối sẵn, fallback sang heuristic ngữ nghĩa có độ tin cậy ước lượng
        day_du: CauHoi = chuan_hoa(_gop_ngu_canh(cau_hoi, context_turns))
        chung = dict(
            khu=trich_khu(day_du.khong_dau),
            chi_so=trich_chi_so(day_du.khong_dau),
            cay=phat_hien_cay(day_du),
        )

        if self.llm_client is not None:
            # SUA 2026-08-28 - bon loi khien nhanh nay khong the chay voi client
            # that. Ca bon deu song sot vi 6 test chi dua mock tu che.
            #
            #  1. Goi `self.llm_client.goi(prompt)`. KHONG client nao co method
            #     do: giao uoc LLMClient (llm/base.py:81) va ca GeminiClient
            #     (llm/gemini.py:119) deu la `sinh(prompt, *, json_mode=...)`.
            #     Dua client that vao la AttributeError ngay dong dau.
            #  2. Doc `res.van_ban`. KetQuaLLM khong co truong do - la `text`
            #     (llm/base.py:47).
            #  3. `.strip("```json")` khong go tien to. str.strip nhan mot TAP
            #     KY TU, nen no go bat ky ky tu nao thuoc {`,j,s,o,n} o hai dau.
            #     "```json{...}" thi may man dung lai o `{`, nhung mot cau tra
            #     loi bat dau bang "n" hay ket thuc bang "s" se bi an mat chu.
            #  4. `except Exception: pass` nuot moi loi. Hong thi tut xuong
            #     heuristic ma khong ai biet - dung kieu suy giam im lang ma
            #     hybrid.py:70 co y tranh.
            try:
                prompt = self.tao_prompt_fewshot(cau_hoi, context_turns)
                res = self.llm_client.sinh(prompt, json_mode=True,
                                           max_token_ra=200)
                if getattr(res, "loi", None) or not (res.text or "").strip():
                    raise RuntimeError(
                        "model khong tra ve gi: " + str(getattr(res, "loi", "")
                                                        or res.finish_reason))
                parsed = json.loads(_go_rao_json(res.text))
                intent = parsed.get("intent", AGRONOMY)
                if intent not in NHAN_HOP_LE:
                    raise ValueError("nhan la: " + str(intent))
                conf = float(parsed.get("confidence", 0.85))
                reason = parsed.get("reason", "few_shot_llm_decision")
                return KetQua(intent, conf, "few_shot_llm", [reason], **chung)
            except Exception as e:                         # noqa: BLE001
                # Khong chan luong - nhung PHAI noi ra. Im lang o day nghia la
                # tang LLM chet ma he thong van bao cao nhu dang chay du hai tang.
                print("  (canh bao: tang few-shot LLM hong, dung heuristic - "
                      + str(e)[:120] + ")")

        # Heuristic ngữ nghĩa chuẩn: nếu có từ khóa nông học -> gán độ tin cậy 0.85 thay vì 0.0
        kd = day_du.khong_dau
        tu_nong_hoc = ["trong", "bon", "phan", "sau", "benh", "dat", "tuoi", "giong", "vu", "ph", "do am"]
        co_nong_hoc = any(t in kd for t in tu_nong_hoc) or (chung["cay"] is not None)

        if co_nong_hoc:
            return KetQua(AGRONOMY, 0.85, "few_shot_heuristic", ["khop_tu_khoa_nong_hoc_chuan"], **chung)
        
        return KetQua(AGRONOMY, 0.60, "few_shot_default", ["mac_dinh_thap"], **chung)


def dinh_tuyen_fewshot(cau_hoi: str, context_turns: list[str] | None = None, llm_client=None) -> KetQua:
    """Hàm tiện ích chạy bộ định tuyến kết hợp Rule + Few-shot (§40.2 Mục 9)."""
    router = LLMFewShotRouter(llm_client=llm_client)
    return router.phan_loai(cau_hoi, context_turns)



# ---------------------------------------------------------------------------
# Cong vao DUY NHAT cua dinh tuyen y dinh cho duong song.
#
# Vi sao mac dinh TAT tang few-shot:
#
# Moi con so C0/C1/C2 hien co - ke ca "0 ca bia" cua C2 - deu do tren router
# THUAN RULE. Bat tang LLM len la doi hanh vi dinh tuyen, va luc do bo so lieu
# dang giao cho NextFarm khong con mo ta he thong dang chay nua. Doi mot tham
# so roi giu nguyen bao cao cu la cach nhanh nhat de bien mot bo do that thanh
# mot bo do sai.
#
# Nen: tang few-shot da xay, da sua het loi giao dien, da co test - nhung chi
# vao duong song khi CO Y bat, va khi bat thi PHAI do lai 222 case.
#
# Bat:  INTENT_FEWSHOT=1 trong .env
# Do:   python evaluation/runners/run_config.py --config c2
# ---------------------------------------------------------------------------

_BAT = {"1", "true", "yes", "on", "bat"}


def dung_fewshot() -> bool:
    from app.core.config import lay
    return (lay("INTENT_FEWSHOT") or "").strip().lower() in _BAT


def dinh_tuyen(cau_hoi: str, context_turns: list[str] | None = None) -> KetQua:
    """Phan loai y dinh cho pipeline. Doc co INTENT_FEWSHOT de chon tang."""
    if not dung_fewshot():
        return phan_loai(cau_hoi, context_turns)

    try:
        from app.services.llm import tao_client
        client = tao_client()
    except Exception as e:                                 # noqa: BLE001
        # Khong co client thi chay rule, nhung phai noi ra: nguoi van hanh da
        # BAT co nay, im lang la de ho tuong tang LLM dang chay.
        print("  (canh bao: INTENT_FEWSHOT bat nhung khong tao duoc client - "
              + str(e)[:120] + ")")
        return phan_loai(cau_hoi, context_turns)

    return LLMFewShotRouter(llm_client=client).phan_loai(cau_hoi, context_turns)
