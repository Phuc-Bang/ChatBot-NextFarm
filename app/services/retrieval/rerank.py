"""
Xep hang lai bang cross-encoder (muc 14.2).

VI SAO CAN

Do duoc tren 22 case co ground truth, kho 185 chunk (P6_retrieval_tuning.md):

    R@10 = 95,5%     hau nhu MOI cau deu tim duoc chunk dung trong top-10
    R@1  = 50,0%     nhung mot nua bi xep sai hang

Van de con lai la XEP HANG, khong phai TIM KIEM. Do dung la viec cua
cross-encoder: bi-encoder (embedding) ma hoa cau hoi va chunk RIENG roi so
vector, con cross-encoder doc CA HAI cung luc nen bat duoc quan he ma phep
so vector bo qua. Doi lai no cham hon nhieu, vi vay chi chay tren top-N da
loc chu khong chay tren ca kho.

CHON MODEL: PhoRanker

    itdainb/PhoRanker              540 MB   tieng Viet
    BAAI/bge-reranker-base       2.224 MB
    BAAI/bge-reranker-v2-m3      2.271 MB
    namdp-ptit/ViRanker          2.271 MB
    cross-encoder/ms-marco-...     296 MB   chi tieng Anh

PhoRanker duoc chon vi no la model tieng Viet nho nhat trong nhom - xem
app/__init__.py ve chuyen dung luong dia.

TAT DUOC, VA MAC DINH LA TAT

`RERANKER_MODEL` de trong thi khong rerank. Quy chuan muc 14.6 doi do rieng
dong gop cua reranker (bat/tat), va mot thanh phan khong tat duoc thi khong
do rieng duoc.
"""

from __future__ import annotations

from app.services.retrieval.keyword import ChunkTraVe

_MODEL = None
_TEN_DANG_NAP: str | None = None
_SO_LAN_LOI = 0          # xem chu thich trong xep_lai()


def _nap(ten_model: str):
    """Nap cross-encoder. CHAY CPU, khong chay GPU.

    Do duoc: GPU cua may nay chi co 4 GB. Model embedding (~300M) da chiem
    cho o do. Nap them cross-encoder len cung GPU thi vo:

        RuntimeError: CUDA error: device-side assert triggered

    Loi nay bao o mot loi goi API khac voi cho gay ra no (CUDA bao bat dong
    bo), nen no rat kho truy. Ep CPU la cach chac chan.

    Ghi de duoc bang RERANKER_DEVICE neu may khac co GPU du lon.
    """
    global _MODEL, _TEN_DANG_NAP
    if _MODEL is not None and _TEN_DANG_NAP == ten_model:
        return _MODEL
    from sentence_transformers import CrossEncoder

    from app.core.config import lay
    device = (lay("RERANKER_DEVICE") or "cpu").strip() or "cpu"
    # max_length=256, KHONG phai 512. PhoRanker khai
    # max_position_embeddings = 258 trong config.json; dat 512 thi vo:
    #     index 258 is out of bounds for dimension 1 with size 258
    # Loi nay bi ham xep_lai() nuot (dung theo thiet ke - khong duoc sap cau
    # tra loi), nen no hien ra thanh "reranker khong cai thien gi" thay vi
    # thanh mot loi. Da va phai that: lan do dau cho "chenh lech +0.000" o
    # ca 22 case.
    _MODEL = CrossEncoder(ten_model, max_length=256, device=device)
    _TEN_DANG_NAP = ten_model
    return _MODEL


def co_bat() -> bool:
    """Reranker co duoc cau hinh khong."""
    from app.core.config import lay
    return bool((lay("RERANKER_MODEL") or "").strip())


def xep_lai(cau, chunks: list[ChunkTraVe], top_k: int = 5,
            ten_model: str | None = None) -> list[ChunkTraVe]:
    """Xep lai `chunks` theo diem cross-encoder, tra ve top_k.

    KHONG bao gio nem loi len tren: neu nap model that bai thi tra ve thu tu
    cu. Mat mot phan chat luong con hon sap ca cau tra loi. Nhung phai IN RA
    - im lang thi chat luong tut ma khong ai biet.
    """
    from app.core.config import lay

    ten = (ten_model or lay("RERANKER_MODEL") or "").strip()
    if not ten or not chunks:
        return chunks[:top_k]

    cau_hoi = getattr(cau, "chuan", None) or str(cau)
    try:
        m = _nap(ten)
        diem = m.predict([(cau_hoi, c.text) for c in chunks])
    except Exception as e:                                 # noqa: BLE001
        # Nuot loi la DUNG (khong duoc sap cau tra loi), nhung phai DEM.
        #
        # Da va phai that: reranker loi o ca 22 case, moi lan deu tra ve thu
        # tu cu, va ket qua do hien ra thanh "chenh lech +0.000" - trong nhu
        # mot ket luan ("reranker khong giup gi") chu khong nhu mot loi. Bo
        # dem nay de bat cu ai doc ket qua cung thay ngay.
        global _SO_LAN_LOI
        _SO_LAN_LOI += 1
        print("  (canh bao: khong rerank duoc - " + str(e)[:120] + ")")
        return chunks[:top_k]

    # Ghi diem vao chunk de con truy nguoc duoc khi phan tich loi. Giu diem
    # RRF cu o `diem_rrf` chu khong ghi de - mat no la mat kha nang so sanh
    # hai cach xep hang tren cung mot lan chay.
    for c, d in zip(chunks, diem):
        c.diem_rrf = c.diem
        c.diem = float(d)
    return sorted(chunks, key=lambda c: c.diem, reverse=True)[:top_k]


def so_lan_loi() -> int:
    """So lan rerank that bai va phai lui ve thu tu cu.

    Cong cu do PHAI goi ham nay va bao ra. Mot bang so "reranker khong cai
    thien gi" khi thuc ra no chua chay lan nao la mot ket luan sai, va no
    trong y het mot ket luan dung.
    """
    return _SO_LAN_LOI
