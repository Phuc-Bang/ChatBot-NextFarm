#!/usr/bin/env python3
"""
signals.py - Do cac tin hieu khach quan cua mot tai lieu, de nguoi duyet
quyet dinh nhanh hon.

RANH GIOI QUAN TRONG

File nay ĐO, khong PHAN. No khong bao gio dat approved=true hay false. Cong
duyet van la cong cua nguoi (DEC-005, DEC-029) - de may tu duyet chinh la
kieu tat ma ca kien truc chong bia nay sinh ra de ngan.

Cai no lam la thay nguoi doc 900 ky tu dau roi doan mo, bang cach dua ra so
dem cu the: tu khoa cay trong xuat hien bao nhieu lan, van ban co bao nhieu
tu ngu quy trinh ky thuat so voi tu ngu tin hoat dong, ty le dong ngan la
bao nhieu. Nguoi duyet nhin so roi tu ket luan.

Moi tin hieu deu kem BANG CHUNG (tu nao, dem bao nhieu) chu khong chi cho ra
mot diem so - de nguoi duyet kiem lai duoc ket luan cua may.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

# Tu ngu dac trung cua TAI LIEU QUY TRINH KY THUAT
TU_KY_THUAT = [
    "thời vụ", "làm đất", "lên luống", "bón lót", "bón thúc", "mật độ",
    "khoảng cách", "gieo hạt", "ngâm ủ", "chăm sóc", "tưới nước", "làm giàn",
    "tỉa cành", "thu hoạch", "quy trình", "kỹ thuật trồng", "chuẩn bị đất",
    "chọn giống", "xử lý hạt", "phòng trừ", "liều lượng", "giai đoạn",
]

# Tu ngu dac trung cua TIN HOAT DONG
TU_TIN_TUC = [
    "hội nghị", "hội thảo", "tập huấn", "đồng chí", "phát biểu", "tham dự",
    "triển khai", "chỉ đạo", "ban hành", "quyết định số", "nghị quyết",
    "ký kết", "tham quan", "đoàn công tác", "khai mạc", "bế mạc",
    "phóng viên", "trao đổi với", "cho biết", "chia sẻ", "mô hình điểm",
]

TEN_CAY = {
    "lua": ["lúa", "mạ", "gieo sạ", "thóc"],
    "ca_chua": ["cà chua"],
    "dua_chuot": ["dưa chuột", "dưa leo"],
}

SO = re.compile(r"\d+([.,]\d+)?")


@dataclass
class TinHieu:
    """Ket qua do. Khong co truong nao mang y nghia 'nen duyet'."""

    do_dai: int
    so_dong: int
    ty_le_dong_ngan: float
    dem_ky_thuat: int
    dem_tin_tuc: int
    tu_ky_thuat: list[str] = field(default_factory=list)
    tu_tin_tuc: list[str] = field(default_factory=list)
    dem_ten_cay: dict[str, int] = field(default_factory=dict)
    mat_do_so: float = 0.0
    ten_mien: str = ""
    la_gov_vn: bool = False

    def tom_tat(self) -> str:
        """Mot dong tom tat cho nguoi duyet doc luot."""
        cay = " ".join(k + "=" + str(v) for k, v in self.dem_ten_cay.items() if v)
        return (
            "kt=" + str(self.dem_ky_thuat)
            + " tin=" + str(self.dem_tin_tuc)
            + " | " + (cay or "khong thay ten cay")
            + " | so/1000tu=" + str(round(self.mat_do_so, 1))
            + " | dong ngan=" + str(round(self.ty_le_dong_ngan * 100)) + "%"
        )


def do(text: str, url: str = "") -> TinHieu:
    low = text.lower()
    dong = [d for d in text.splitlines() if d.strip()]
    ngan = [d for d in dong if len(d.strip()) < 25]

    tu_kt = [t for t in TU_KY_THUAT if t in low]
    tu_tt = [t for t in TU_TIN_TUC if t in low]

    dem_cay = {}
    for crop, kws in TEN_CAY.items():
        n = sum(low.count(kw) for kw in kws)
        if n:
            dem_cay[crop] = n

    so_tu = max(1, len(low.split()))
    host = urlsplit(url).netloc if url else ""

    return TinHieu(
        do_dai=len(text),
        so_dong=len(dong),
        ty_le_dong_ngan=len(ngan) / max(1, len(dong)),
        dem_ky_thuat=sum(low.count(t) for t in TU_KY_THUAT),
        dem_tin_tuc=sum(low.count(t) for t in TU_TIN_TUC),
        tu_ky_thuat=tu_kt[:8],
        tu_tin_tuc=tu_tt[:8],
        dem_ten_cay=dem_cay,
        mat_do_so=1000.0 * len(SO.findall(low)) / so_tu,
        ten_mien=host,
        la_gov_vn=host.endswith(".gov.vn"),
    )


def canh_bao(th: TinHieu, crop_khai_bao: str | None) -> list[str]:
    """Nhung diem NGUOI DUYET nen nhin ky. Khong phai ket luan.

    Moi canh bao deu doc duoc thanh mot cau hoi cu the, khong phai mot diem so.
    """
    ra = []

    if crop_khai_bao and not th.dem_ten_cay.get(crop_khai_bao):
        ra.append("Khong tim thay ten cay '" + crop_khai_bao + "' trong toan bo "
                  "van ban - kiem tra cau 2 cua checklist")

    if th.dem_tin_tuc > th.dem_ky_thuat:
        ra.append("Tu ngu tin hoat dong (" + str(th.dem_tin_tuc) + ") nhieu hon tu "
                  "ngu quy trinh ky thuat (" + str(th.dem_ky_thuat) + ") - kiem tra cau 3")

    if th.dem_ky_thuat == 0:
        ra.append("Khong co tu ngu quy trinh ky thuat nao - kiem tra cau 3")

    if th.ty_le_dong_ngan > 0.6:
        ra.append("Hon 60% so dong rat ngan - co the con dinh menu/banner, "
                  "kiem tra cau 4")

    if th.do_dai < 1500:
        ra.append("Van ban ngan (" + str(th.do_dai) + " ky tu) - co the chi la "
                  "tom tat hoac trang bi cat")

    if not th.la_gov_vn and th.ten_mien:
        ra.append("Ten mien khong phai .gov.vn (" + th.ten_mien + ") - xac dinh "
                  "lai tier o cau 1")

    return ra
