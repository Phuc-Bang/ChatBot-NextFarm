"""
Giao dien chung cho moi nha cung cap LLM.

VI SAO PHAI CO TANG NAY THAY VI GOI THANG GEMINI

DEC-015 noi "khong chot model tren giay". Muon giu duoc loi do thi doi model
phai la doi mot dong .env, khong phai sua lai P4/P7/P8. Do dac biet dung o day
vi hai ly do da do duoc:

  1. Phan cung hien tai (RTX 2050, 4GB) khong chay noi model sinh cau tra loi:
     qwen3:4b tren CPU cho 11,4 token/giay, mot cau hoi RAG that mat 32,3 giay
     - qua nguong ASM-01 (p50 <= 5s) sau lan. Nhung neu NextFarm dau tu GPU
     lon hon thi phuong an self-host mo lai duoc, va luc do chi doi provider.

  2. Gia Gemini thay doi. gemini-1.5-flash da bi Google tat han (moi request
     tra ve 404), text-embedding-004 cung vay. Model nao cung co the la model
     tiep theo bi tat.

MOI LAN GOI DEU PHAI TRA VE SO TOKEN

Khong phai de lam dashboard cho dep. Muc 37.5 cua quy chuan co mot cong thuc
chi phi dang cho hai bien nay:

    Chi phi LLM/thang = C x T x (Ti x Pi + To x Po)

C va T la [EXT] - chi NextFarm co. Ti va To la thu PoC phai do. Khong ghi
token tu dau thi den luc viet bao cao khong co gi de dien, va con so chi phi
gui khach hang se thanh con so bia.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class KetQuaLLM:
    """Ket qua mot lan goi model.

    `text` co the rong khi model bi chan boi bo loc an toan hoac het token.
    Do KHONG phai loi cua lop nay - noi goi phai xu ly, va `finish_reason`
    cho biet vi sao. Tra ve chuoi rong lang le thi tang tren se tuong model
    "khong biet" trong khi that ra no bi chan.
    """

    text: str
    token_vao: int
    token_ra: int
    token_suy_nghi: int          # Gemini tinh tien phan nay NHU token ra
    latency_ms: int
    model: str
    provider: str
    finish_reason: str | None = None
    loi: str | None = None       # co gia tri => lan goi that bai
    raw_usage: dict = field(default_factory=dict)

    @property
    def token_ra_tinh_tien(self) -> int:
        """Token ra thuc su bi tinh tien.

        Gemini 2.5 tinh `thoughts_token_count` vao gia dau ra. Do tren key
        that: mot cau hoi hai chu sinh ra 1848 token suy nghi trong khi cau
        tra loi chi 3 token - tuc 99% hoa don den tu phan khong ai doc.

        Bo qua truong nay thi uoc luong chi phi sai hang chuc lan.
        """
        return self.token_ra + self.token_suy_nghi

    @property
    def thanh_cong(self) -> bool:
        return self.loi is None and bool(self.text)


class LLMClient(Protocol):
    """Moi provider phai cai dat dung mot ham nay."""

    ten_model: str
    ten_provider: str

    def sinh(self, prompt: str, *, json_mode: bool = False,
             max_token_ra: int | None = None) -> KetQuaLLM:
        ...
