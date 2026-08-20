"""
Bang gia token — dau vao cho mo hinh chi phi muc 37.5.

MOI DONG O DAY LA MOT CON SO TRA TU TRANG GIA CHINH THUC, KEM NGAY TRA.

Gia khong phai hang so. Trong mot lan tra cuu duy nhat (2026-08-20) da thay:

  - gemini-1.5-flash        : Google DA TAT, moi request tra ve 404
  - text-embedding-004      : DA TAT tu 2026-01-14
  - gemini-2.0-flash-lite   : DA TAT tu 2026-06-01
    (day chinh la model co gia 0.075/0.30 - con so nay van con troi noi trong
     nhieu tai lieu va rat de chep nham vao bao cao)
  - gemini-3.6-flash        : 0.75 vao / 3.75 ra, nhung TANG GAP DOI tu
    2027-01-01 len 1.50 / 7.50

Bao cao chi phi gui NextFarm ma dung gia cua model da tat la bao cao sai tu
goc. Vi vay:

  - moi muc gia deu ghi NGAY TRA CUU va NGUON
  - model khong co trong bang -> NEM LOI, khong doan, khong lay gia gan dung
  - muc 37.5 phai in kem ngay tra cuu, de nguoi doc biet con so cu den dau

Nguon: https://ai.google.dev/gemini-api/docs/pricing
"""

from __future__ import annotations

from dataclasses import dataclass

NGAY_TRA_CUU = "2026-08-20"
NGUON_GIA = "https://ai.google.dev/gemini-api/docs/pricing"


@dataclass(frozen=True)
class Gia:
    """Don gia USD cho 1 TRIEU token."""

    vao: float
    ra: float
    ghi_chu: str = ""


# Chi ghi model DANG SONG tai ngay tra cuu.
BANG_GIA: dict[str, Gia] = {
    "gemini-2.5-flash": Gia(
        0.30, 2.50,
        "Chua co ngay tat cong bo. Gia van/audio khac - PoC chi dung van ban."),
    "gemini-2.5-flash-lite": Gia(
        0.10, 0.40, "Re nhat con song; chat luong thap hon 2.5-flash."),
    "gemini-2.5-pro": Gia(
        1.25, 10.00, "Gia bac <=200k token; tren nguong do la 2.50/15.00."),
    "gemini-3.1-flash-lite": Gia(
        0.25, 1.50, "CO ngay tat: 2027-05-07."),
    "gemini-3.5-flash": Gia(1.50, 9.00, "Chua co ngay tat cong bo."),
    "gemini-3.6-flash": Gia(
        0.75, 3.75, "TANG len 1.50/7.50 tu 2027-01-01."),
    "gemini-embedding-2": Gia(
        0.20, 0.0, "Embedding chi tinh dau vao."),
}


class ThieuGia(KeyError):
    """Model khong co trong bang gia."""


def tra_gia(model: str) -> Gia:
    """Don gia cua mot model.

    NEM LOI khi khong biet, thay vi tra ve gia mac dinh. Mot gia mac dinh
    lang le se chay suot den bang chi phi cuoi cung ma khong ai phat hien.
    """
    if model not in BANG_GIA:
        raise ThieuGia(
            "Khong co gia cho '" + model + "'. Tra tai " + NGUON_GIA
            + " roi them vao BANG_GIA kem ngay tra. Model dang biet: "
            + ", ".join(sorted(BANG_GIA)))
    return BANG_GIA[model]


def chi_phi_usd(model: str, token_vao: int, token_ra: int) -> float:
    """Chi phi mot lan goi.

    `token_ra` phai la token_ra_tinh_tien (da cong token suy nghi) - xem
    KetQuaLLM.token_ra_tinh_tien.
    """
    g = tra_gia(model)
    return token_vao / 1e6 * g.vao + token_ra / 1e6 * g.ra
