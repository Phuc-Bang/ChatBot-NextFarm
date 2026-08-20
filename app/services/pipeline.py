"""
Chuoi xu ly mot cau hoi, tu dau den cuoi (muc 10).

    chuan hoa -> Intent Router -> Scope Check -> truy xuat lai
              -> Evidence Pack -> LLM -> Grounding -> tra loi / tu choi

MOI CHANG DEU DO THOI GIAN RIENG

Muc 21.2 doi p50/p95 theo TUNG CHANG chu khong phai mot con so tong. Ly do
o muc 21.3: khi vuot ngan sach phai biet CAT CHANG NAO. Mot con so tong noi
"cham" nhung khong noi cat gi.

TU CHOI SOM LA TU CHOI RE

Ba chang dau (chuan hoa, router, scope) khong goi model nao. Cau bi chan o
day ton ~0ms va 0 dong. Do la ly do Intent Router dat TRUOC Scope Check va
ca hai dat truoc truy xuat.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.services.abstention import templates as tpl
from app.services.intent import scope
from app.services.intent.router import (
    AGRONOMY, DEVICE_CONTROL, GARDEN_DATA, PRODUCT_FEATURE, phan_loai)
from app.services.normalization.vietnamese import chuan_hoa


@dataclass
class ChunkNguon:
    """Mot nguon duoc trich dan - du de nguoi dung bam ve tai lieu goc."""

    chunk_id: str
    document_title: str | None
    publisher: str | None
    url: str
    text: str
    source_tier: int | None = None


@dataclass
class KetQuaHoi:
    cau_hoi: str
    tra_loi: str
    da_tu_choi: bool
    ly_do_tu_choi: str | None = None      # garden_data / product_feature / ...
    intent: str | None = None
    intent_do_tin_cay: float = 0.0
    intent_nguon: str | None = None
    cay: list[str] = field(default_factory=list)
    nguon: list[ChunkNguon] = field(default_factory=list)
    latency_ms: dict[str, int] = field(default_factory=dict)
    token_vao: int = 0
    token_ra: int = 0
    canh_bao: list[str] = field(default_factory=list)
    loi: str | None = None

    @property
    def tong_latency_ms(self) -> int:
        return sum(self.latency_ms.values())


class _Dong_ho:
    """Do thoi gian tung chang."""

    def __init__(self):
        self.moc: dict[str, int] = {}
        self._t = time.time()

    def cham(self, ten: str) -> None:
        gio = time.time()
        self.moc[ten] = int((gio - self._t) * 1000)
        self._t = gio


def tra_loi_cau_hoi(cau_hoi: str,
                    context_turns: list[str] | None = None,
                    *, dung_llm: bool = True,
                    top_k: int = 5) -> KetQuaHoi:
    """Xu ly mot cau hoi.

    `dung_llm=False` dung lai sau khi truy xuat - dung de do rieng tang tu
    choi ma khong ton quota.
    """
    dh = _Dong_ho()
    kq = KetQuaHoi(cau_hoi=cau_hoi, tra_loi="", da_tu_choi=False)

    # ---- 1. Chuan hoa (khong goi model) -----------------------------
    cau = chuan_hoa(cau_hoi)
    kq.canh_bao = list(cau.canh_bao)
    dh.cham("chuan_hoa")

    # ---- 2. Intent Router (khong goi model) -------------------------
    it = phan_loai(cau_hoi, context_turns)
    kq.intent = it.nhan
    kq.intent_do_tin_cay = it.do_tin_cay
    kq.intent_nguon = it.nguon
    dh.cham("intent")

    if it.phai_tu_choi:
        kq.da_tu_choi = True
        kq.ly_do_tu_choi = it.nhan
        if it.nhan == GARDEN_DATA:
            kq.tra_loi = tpl.garden_data(khu=it.khu, chi_so=it.chi_so,
                                         cay=it.cay or None)
        else:
            kq.tra_loi = tpl.theo_nhan(it.nhan)
        kq.latency_ms = dh.moc
        return kq

    # ---- 3. Scope Check (khong goi model) ---------------------------
    sc = scope.kiem_tra(cau_hoi, context_turns)
    kq.cay = list(sc.cay_trong_pham_vi)
    dh.cham("scope")

    if not sc.duoc_di_tiep:
        kq.da_tu_choi = True
        if sc.ket_luan == scope.NGOAI_PHAM_VI:
            kq.ly_do_tu_choi = "out_of_scope"
            kq.tra_loi = tpl.out_of_scope(
                (sc.cay_ngoai_nhan_duoc or [None])[0])
        else:
            # Khong ro cay - HOI LAI chu khong tu choi han. Hoi lai la hanh
            # vi dung khi that su khong biet nguoi dung hoi cay nao.
            kq.ly_do_tu_choi = "can_lam_ro"
            kq.tra_loi = (
                "Bạn đang hỏi về cây trồng nào ạ? Hiện tôi có tài liệu cho "
                "lúa, cà chua và dưa chuột.")
        kq.latency_ms = dh.moc
        return kq

    # ---- 4. Truy xuat lai -------------------------------------------
    try:
        from app.services.retrieval.hybrid import tim_kiem
        chunks = tim_kiem(cau, crop=(kq.cay or [None])[0], top_k=top_k)
    except Exception as e:                                 # noqa: BLE001
        kq.loi = "truy xuat loi: " + str(e)[:200]
        chunks = []
    dh.cham("truy_xuat")

    if not chunks:
        # KHONG co bang chung -> tu choi. Day la case C1 cua muc 19: thieu
        # can cu thi noi thieu can cu, khong duoc de LLM tu bia ra.
        kq.da_tu_choi = True
        kq.ly_do_tu_choi = "insufficient_evidence"
        kq.tra_loi = tpl.insufficient_evidence() \
            if hasattr(tpl, "insufficient_evidence") else (
                "Tôi chưa tìm thấy tài liệu nào trong kho tri thức để trả lời "
                "câu hỏi này. Tôi không đoán khi không có căn cứ.")
        kq.latency_ms = dh.moc
        return kq

    kq.nguon = [ChunkNguon(c.chunk_id, c.document_title, c.publisher,
                           c.url, c.text, c.source_tier) for c in chunks]

    if not dung_llm:
        kq.tra_loi = "(dung truoc buoc goi model)"
        kq.latency_ms = dh.moc
        return kq

    # ---- 5. LLM + Grounding -----------------------------------------
    from app.services.rag.sinh_cau_tra_loi import sinh_va_kiem
    r = sinh_va_kiem(cau_hoi, chunks)
    dh.cham("llm")

    kq.tra_loi = r.tra_loi
    kq.da_tu_choi = r.da_tu_choi
    kq.ly_do_tu_choi = r.ly_do
    kq.token_vao = r.token_vao
    kq.token_ra = r.token_ra
    if r.chunk_da_dung:
        kq.nguon = [n for n in kq.nguon if n.chunk_id in r.chunk_da_dung]
    kq.latency_ms = dh.moc
    return kq
