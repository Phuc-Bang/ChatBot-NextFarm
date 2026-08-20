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
             top_k_rerank: int = 12) -> list[ChunkTraVe]:
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
    # top_k_rerank = 12: CHOT BANG SO DO, quet N tren 22 case.
    #
    #   N=3   MRR 0.455   1.011 ms   <- TE HON ca khi TAT
    #   N=5   MRR 0.477   1.105 ms   <- van te hon khi TAT (0.562)
    #   N=8   MRR 0.575   1.630 ms
    #   N=12  MRR 0.605   2.362 ms   <- diem ngot
    #   N=20  MRR 0.605   4.208 ms   <- cung chat luong, gap doi thoi gian
    #
    # N nho lam TE DI chu khong phai "it cai thien hon": rerank it chunk thi
    # doi thu tu ma khong doi tap hop, trong khi chunk dung thuong nam ngoai
    # top_k (R@1 50% nhung R@10 95,5%). Xem docs/reports/P6_reranker.md.
    from app.services.retrieval import rerank
    if rerank.co_bat():
        return rerank.xep_lai(cau, gop[:top_k_rerank], top_k=top_k)
    return gop[:top_k]
