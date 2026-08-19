#!/usr/bin/env python3
"""
templates.py - Bon mau cau tu choi (quy chuan v2.0 muc 11.5).

QUY CHUAN VIET MAU TU CHOI

    neu ro VI SAO khong tra loi duoc
      -> chi NOI NAO co cau tra loi
        -> neu co, CHUYEN HUONG sang thu minh that su co

Tu choi cut lun ("em khong biet") va tu choi bia ("do am khu A la 65%") la
hai dau cua cung mot that bai: ca hai deu khien nguoi dung khong lam duoc gi
tiep. Khac nhau la cai thu hai con lam ho tin nham.

HAI QUY TAC KHONG DUOC PHA

  1. Mau tu choi khong duoc tu sinh ra MOT CON SO NAO.
     Duoc phep nhac lai nguyen van thong tin nguoi dung vua go (ten khu, ten
     chi so) - do la nhac lai, khong phai bia. Nhung khong duoc them mot gia
     tri do nao. test_mau_khong_tu_sinh_con_so canh giu dieu nay.

     He qua cho tang do: chi so "khong duoc chua so" (muc 30.5) phai so voi
     so CO TRONG CAU HOI, khong phai voi moi chu so trong cau tra loi. Nguoi
     dung go "khu 3" thi cau tu choi nhac "khu 3" la dung.

  2. Khong duoc hua thu minh khong co.
     Cau chuyen huong "em co tai lieu ve nguong nen duy tri" chi duoc noi khi
     kho tri thuc THAT SU co tai lieu cho cay do. Tham so co_tai_lieu ton tai
     de goi ben ngoai truyen su that vao, chu khong phai de trang tri.

CHO TRONG KHONG BIET THI NOI CHUNG CHUNG, KHONG DIEN BUA

Router tra ve khu=None khi khong tim thay ten khu trong cau hoi. Mau phai
chiu duoc None bang cach noi "vuon cua anh/chi", tuyet doi khong duoc chon
dai mot ten khu.
"""

from __future__ import annotations

REFUSE_GARDEN_DATA = "REFUSE_GARDEN_DATA"
REFUSE_PRODUCT_FEATURE = "REFUSE_PRODUCT_FEATURE"
REFUSE_DEVICE_CONTROL = "REFUSE_DEVICE_CONTROL"
REFUSE_OUT_OF_SCOPE = "REFUSE_OUT_OF_SCOPE"

TEN_CAY = {
    "lua": "lúa",
    "ca_chua": "cà chua",
    "dua_chuot": "dưa chuột",
}


def _ten_cay(cay: list[str] | None) -> str | None:
    """Ten cay de hien thi, hoac None neu khong xac dinh duoc DUY NHAT mot cay."""
    if not cay or len(cay) != 1:
        return None
    return TEN_CAY.get(cay[0])


def garden_data(khu: str | None = None,
                chi_so: str | None = None,
                cay: list[str] | None = None,
                co_tai_lieu: bool = True) -> str:
    """Tu choi cau hoi so lieu vuon - hien tuong A1 cua de bai.

    Day la mau quan trong nhat trong bon mau. Cau hoi "khu A gio do am bao
    nhieu" ma duoc tra loi bang nguong trong sach, kem trich dan dang hoang,
    la loai sai nguy hiem nhat cua ca he thong: no trong rat dang tin.
    """
    noi = khu or "vườn của anh/chị"

    dau = ("Hiện em chưa được kết nối với dữ liệu cảm biến vườn của anh/chị "
           "nên không xem được số đo thực tế ở " + noi + ". Anh/chị xem trực "
           "tiếp trong app NextFarm nhé.")

    if not co_tai_lieu:
        return dau

    ten = _ten_cay(cay)
    if chi_so and ten:
        sau = ("Còn về mức " + chi_so + " nên duy trì cho " + ten + " thì em "
               "có tài liệu — anh/chị muốn em nói không ạ?")
    elif chi_so:
        sau = ("Còn về mức " + chi_so + " nên duy trì thì em có tài liệu — "
               "anh/chị đang trồng cây gì để em tra đúng ạ?")
    elif ten:
        sau = ("Còn về các ngưỡng kỹ thuật nên duy trì cho " + ten + " thì em "
               "có tài liệu — anh/chị muốn hỏi chỉ số nào ạ?")
    else:
        sau = ("Còn về ngưỡng kỹ thuật nên duy trì thì em có tài liệu — "
               "anh/chị cho em biết cây trồng và chỉ số cần tra giúp em ạ.")

    return dau + "\n" + sau


def product_feature() -> str:
    """Tu choi cau hoi ve tinh nang app - hien tuong A2 cua de bai.

    Khong co tham so: mau nay khong duoc thay doi theo cau hoi. Cang tuy bien
    theo cau hoi thi cang de truot sang viec mo ta mot tinh nang khong ton tai
    - ma do dung la hien tuong A2.
    """
    return ("Câu này về tính năng của app NextFarm, em chưa có tài liệu hướng "
            "dẫn sử dụng nên không dám trả lời để tránh nói sai. Anh/chị liên "
            "hệ bộ phận hỗ trợ NextFarm giúp em ạ.")


def device_control() -> str:
    """Tu choi lenh dieu khien thiet bi."""
    return ("Em không thực hiện được lệnh điều khiển thiết bị. Việc bật/tắt "
            "van, bơm cần thao tác trực tiếp trong app để đảm bảo an toàn cho "
            "thiết bị và cây trồng ạ.")


def out_of_scope(cay_khac: str | None = None) -> str:
    """Tu choi cau hoi ngoai pham vi - dung chung cho Scope Check (muc 12)."""
    doi_tuong = "về " + cay_khac if cay_khac else "câu này"
    return ("Hiện em mới có tài liệu kỹ thuật cho lúa, cà chua và dưa chuột "
            "nên chưa trả lời được " + doi_tuong + ". Em không muốn đoán rồi "
            "nói sai ạ.")


def theo_nhan(nhan: str, **kw) -> str:
    """Chon mau theo nhan cua Intent Router.

    Khong co nhanh mac dinh tra ve chuoi rong: mot nhan la khong duoc lang le
    bien thanh cau tra loi trong. Vao day ma khong khop nhan nao la loi lap
    trinh, phai no ra.
    """
    from app.services.intent.router import (
        DEVICE_CONTROL, GARDEN_DATA, PRODUCT_FEATURE,
    )

    if nhan == GARDEN_DATA:
        return garden_data(**kw)
    if nhan == PRODUCT_FEATURE:
        return product_feature()
    if nhan == DEVICE_CONTROL:
        return device_control()
    raise ValueError("khong co mau tu choi cho nhan: " + repr(nhan))
