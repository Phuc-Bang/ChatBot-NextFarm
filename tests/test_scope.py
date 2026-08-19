"""
Kiem thu Scope Check (quy chuan v2.0 muc 12).

Rang buoc kien truc quan trong nhat cua module nay khong phai "nhan dung ten
cay" ma la: DANH SACH CAY NGOAI PHAM VI KHONG DUOC THAM GIA QUYET DINH co
tra loi hay khong. Danh sach do khong bao gio day du duoc; neu quyet dinh
phu thuoc vao no thi moi cay thieu la mot lo ro.

test_thieu_cay_trong_danh_sach_van_khong_lot canh giu dieu do.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.abstention import templates as tpl  # noqa: E402
from app.services.intent import scope  # noqa: E402
from app.services.normalization.vietnamese import chuan_hoa  # noqa: E402


def kl(q, ctx=None):
    return scope.kiem_tra(q, ctx).ket_luan


# ----------------------------------------------------------------------
# Ba nhanh
# ----------------------------------------------------------------------
def test_cay_trong_pham_vi_di_tiep():
    for q in ["cà chua cần đất pH bao nhiêu", "lúa bón đạm bao nhiêu",
              "dưa chuột trồng vụ nào", "dưa leo làm giàn cao bao nhiêu",
              "ca chua can dat ph bao nhieu"]:
        assert kl(q) == scope.TRONG_PHAM_VI, q


def test_cay_ngoai_pham_vi_bi_chan():
    for q in ["cà phê cần pH bao nhiêu", "thanh long chiếu đèn bao lâu",
              "cà tím trồng khoảng cách bao nhiêu", "dưa hấu tưới mấy lần",
              "ca phe can dat ph bao nhieu"]:
        assert kl(q) == scope.NGOAI_PHAM_VI, q


def test_khong_ro_cay_thi_hoi_lai_chu_khong_tra_loi():
    assert kl("bón phân bao nhiêu là đủ") == scope.CAN_LAM_RO


def test_lay_cay_tu_ngu_canh():
    assert kl("thế còn bệnh xoăn lá thì sao",
              ["cà chua trồng vụ nào"]) == scope.TRONG_PHAM_VI


def test_hoi_ca_hai_thi_van_chan():
    """"trong xen ca chua voi ca phe" - tra loi nua nay nua kia ma khong bao
    nguoi dung biet phan nao khong co tai lieu la mot dang noi thieu."""
    r = scope.kiem_tra("trồng xen cà chua với cà phê có được không")
    assert r.ket_luan == scope.NGOAI_PHAM_VI
    assert r.cay_trong_pham_vi and r.cay_ngoai_nhan_duoc


# ----------------------------------------------------------------------
# RANG BUOC KIEN TRUC
# ----------------------------------------------------------------------
def test_thieu_cay_trong_danh_sach_van_khong_lot():
    """Cay khong co trong out_of_scope_crops.yaml van khong duoc tra loi.

    Danh sach cay trong o Viet Nam khong liet ke het duoc. Neu quyet dinh
    "co tra loi khong" phu thuoc vao danh sach do thi moi cay thieu la mot
    lo ro: bot gap cay la, khong thay trong danh sach cam, roi tra loi bang
    kien thuc nen cua LLM - dung thu muc 12 cam.
    """
    la = "cây sachi trồng ở độ cao bao nhiêu"
    assert not scope.tim_cay_ngoai_pham_vi(chuan_hoa(la))
    assert kl(la) == scope.CAN_LAM_RO      # khong lot, chi kem cu the


def test_danh_sach_chi_lam_cau_tu_choi_cu_the_hon():
    co_ten = scope.kiem_tra("cà phê cần pH bao nhiêu")
    khong_ten = scope.kiem_tra("cây sachi trồng ở độ cao bao nhiêu")
    assert not co_ten.duoc_di_tiep and not khong_ten.duoc_di_tiep
    assert "cà phê" in tpl.out_of_scope(co_ten.cay_ngoai_nhan_duoc[0])


# ----------------------------------------------------------------------
# Va cham do bo dau (DEC-031, muc 13.4)
# ----------------------------------------------------------------------
def test_khop_tren_ban_co_dau_khi_cau_hoi_co_dau():
    """Cac cap nay chi khac nhau dau thanh. Bo dau roi moi khop thi ca bon
    cau duoi day deu bi nhan nham thanh cau hoi ve cay ngoai pham vi."""
    assert kl("ruộng lúa nhà tôi bị ngộ độc phèn xử lý sao") == scope.TRONG_PHAM_VI
    assert kl("vườn tôi trồng cà chua có cần làm giàn không") == scope.TRONG_PHAM_VI
    assert kl("tưới nhỏ giọt cho cà chua thế nào") == scope.TRONG_PHAM_VI
    assert kl("điều kiện thời tiết nào lúa dễ đổ") == scope.TRONG_PHAM_VI


def test_ten_cay_khong_co_dau_van_phai_dung():
    """"lan", "na", "cam", "nho" von khong mang dau nao.

    Neu quyet dinh dung ban nao lai dua vao "tu can tim co dau khong" thay vi
    "cau hoi co dau khong", nhung ten nay luon roi ve nhanh bo dau va "lan"
    se khop trong "LAN truoc anh bao...".
    """
    assert kl("lần trước anh bảo độ ẩm 70% mà, giờ sao lại khác") == scope.CAN_LAM_RO
    assert kl("hoa lan tưới mấy lần") == scope.NGOAI_PHAM_VI


def test_dong_am_that_su_can_tu_lan_can():
    """Co cap khong dau nao cuu duoc: "dieu" trong "dieu kien" va "dieu"
    trong "cay dieu" viet giong het nhau. Chi tu lan can phan biet duoc."""
    assert "điều" not in scope.tim_cay_ngoai_pham_vi(
        chuan_hoa("điều kiện thời tiết nào lúa dễ đổ"))
    assert kl("dưa chuột trồng bò lan thì mật độ bao nhiêu") == scope.TRONG_PHAM_VI


def test_cau_khong_dau_doi_tu_chi_loai_cho_ten_mot_am_tiet():
    """Cau khong dau khong con thong tin dau thanh, nen ten mot am tiet phai
    co tu chi loai dung truoc moi duoc tinh."""
    assert kl("cay toi trong vu nao") == scope.NGOAI_PHAM_VI
    assert kl("vuon toi trong ca chua co can lam gian khong") == scope.TRONG_PHAM_VI


def test_ca_tim_va_ca_phao_khong_phai_ca_chua():
    for q in ["cà tím trồng khoảng cách bao nhiêu", "cà pháo muối bao lâu thì ăn được"]:
        r = scope.kiem_tra(q)
        assert r.ket_luan == scope.NGOAI_PHAM_VI, q
        assert "ca_chua" not in r.cay_trong_pham_vi


def test_dua_hau_va_dua_luoi_khong_phai_dua_chuot():
    for q in ["dưa hấu tưới mấy lần một ngày", "dưa lưới trồng nhà màng thế nào"]:
        r = scope.kiem_tra(q)
        assert r.ket_luan == scope.NGOAI_PHAM_VI, q
        assert "dua_chuot" not in r.cay_trong_pham_vi
