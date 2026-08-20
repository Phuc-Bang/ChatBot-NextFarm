"""
Truy xuat lai: hop nhat vector + FTS + trigram bang RRF (muc 14.4).

VI SAO PHAI CA BA KENH - DO DUOC, KHONG PHAI GIA DINH

Do tren 15 case co ground truth, 161 chunk (xem docs/reports/
P6_retrieval_tuning.md):

    cau hinh            R@1     R@3     MRR
    hybrid(halong)     60.0    73.3   0.687
    chi tu khoa        46.7    60.0   0.576
    chi vector         13.3    80.0   0.432

Vector MOT MINH kem nhat ve MRR - nhin cot do thi ket luan la bo vector di.
Nhung R@3 cua no la 80%, cao nhat bang: no TIM DUNG chunk, chi XEP SAI vi
tri. Hop nhat voi tu khoa thi R@1 nhay 13,3% -> 60%.

Hai kenh bu nhau:
    tu khoa  khop mat chu -> trung thi chinh xac, nhung dien dat khac la truot
    vector   hieu nghia   -> bat duoc dien dat khac, nhung khong biet chunk
                             nao chinh xac hon

HOP NHAT THEO HANG, KHONG THEO DIEM

cosine (0..1), ts_rank (khong chan tren) va word_similarity (0..1) o ba
thang do khac han nhau. Ep chung ve mot thang la tu bia ra mot phep quy doi
khong co co so. RRF chi dung THU HANG nen khong can chuan hoa.
"""

from __future__ import annotations

from app.services.retrieval.keyword import (
    TOP_K_MOI_KENH, ChunkTraVe, cong_diem_vung, hop_nhat_rrf, tim_fts,
    tim_trigram)
from app.services.retrieval.vector import tim_vector


def tim_kiem(cau, crop: str | None = None, region: str | None = None,
             top_k: int = 5, top_k_kenh: int = TOP_K_MOI_KENH,
             dung_vector: bool = True, conn=None,
             top_k_rerank: int = 20) -> list[ChunkTraVe]:
    """Tim top_k chunk lien quan nhat.

    `dung_vector=False` de do rieng dong gop cua vector, hoac de chay khi
    chua tai duoc model embedding.

    Moi truy van deu doc tu view `indexable_chunk` - chunk chua duyet khong
    bao gio vao duoc day (DEC-005). Cong chan nam o tang du lieu chu khong
    o loi hua trong code.
    """
    kenh: list[tuple[str, list[ChunkTraVe]]] = [
        ("fts", tim_fts(cau, crop, top_k_kenh, conn=conn)),
        ("trigram", tim_trigram(cau, crop, top_k_kenh, conn=conn)),
    ]
    if dung_vector:
        try:
            kenh.append(("vector", tim_vector(cau, crop, top_k_kenh, conn=conn)))
        except Exception as e:                             # noqa: BLE001
            # Khong nap duoc model thi VAN chay bang hai kenh tu khoa, nhung
            # phai noi ra. Im lang thi chat luong tut ma khong ai biet.
            print("  (canh bao: khong dung duoc kenh vector - " + str(e)[:120]
                  + ")")

    gop = hop_nhat_rrf(*kenh)
    if region:
        gop = cong_diem_vung(gop, region)

    # Rerank: chi chay khi RERANKER_MODEL duoc dat (mac dinh TAT).
    #
    # Dua cho no NHIEU hon top_k de no con gi de xep lai. Lay dung top_k roi
    # rerank la vo nghia: thu tu doi nhung tap hop khong doi, ma R@1 thap
    # trong khi R@10 cao (50% vs 95,5%) nghia la chunk dung THUONG nam ngoai
    # top_k. Xem app/services/retrieval/rerank.py.
    from app.services.retrieval import rerank
    if rerank.co_bat():
        return rerank.xep_lai(cau, gop[:top_k_rerank], top_k=top_k)
    return gop[:top_k]
