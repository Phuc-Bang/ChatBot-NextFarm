"""
Kenh truy xuat vector.

CHUA DUNG pgvector - VA DAY LA CO Y

Luoc do co bang `embedding` va extension pgvector da cai. Nhung kho tri thuc
hien chi co 161 chunk index duoc. Voi co do do:

    nhan ma tran 161 x 768 trong RAM   ~0,5 MB, mat vai mili giay
    dung chi muc HNSW cua pgvector     nhanh hon khong dang ke, va them mot
                                       buoc dong bo phai bao tri

Nap san vao RAM khi khoi dong, tim bang numpy. Khi kho lon len (vai chuc
nghin chunk) thi doi sang pgvector - luc do interface o day khong doi, chi
doi phan trong.

Ghi ro o day de nguoi doc sau khong tuong la quen lam.
"""

from __future__ import annotations

import numpy as np

from app.services.retrieval.keyword import COT, ChunkTraVe, _conn, _thanh_chunk

# Cache theo tien trinh: model va ma tran chi nap MOT lan.
_MODEL = None
_IDS: list[str] = []
_V: "np.ndarray | None" = None
_CHUNK: dict[str, ChunkTraVe] = {}


def _nap(conn=None, ten_model: str | None = None) -> None:
    """Nap model va embed toan bo kho. Chay mot lan cho ca tien trinh."""
    global _MODEL, _IDS, _V, _CHUNK
    if _V is not None:
        return

    from app.services.embedding.local import LocalEmbedding
    from app.core.config import lay

    _MODEL = LocalEmbedding(ten_model or lay("EMBEDDING_MODEL") or "halong")

    with _conn(conn) as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT " + COT + " FROM indexable_chunk c ORDER BY c.chunk_id")
            rows = cur.fetchall()

    ds = [_thanh_chunk(r) for r in rows]
    _CHUNK = {c.chunk_id: c for c in ds}
    _IDS = [c.chunk_id for c in ds]
    _V = _MODEL.ma_hoa([c.text for c in ds], la_cau_hoi=False)


def tim_vector(cau, crop: str | None = None, top_k: int = 20,
               conn=None) -> list[ChunkTraVe]:
    """Tim theo do tuong dong ngu nghia.

    `cau` la CauHoi da chuan hoa. Dung `cau.chuan` (co dau) chu khong dung
    ban bo dau: model embedding duoc huan luyen tren tieng Viet CO DAU, dua
    ban bo dau vao la tu lam mat thong tin.
    """
    _nap(conn)
    assert _V is not None and _MODEL is not None

    q = _MODEL.ma_hoa([getattr(cau, "chuan", str(cau))], la_cau_hoi=True)[0]
    diem = _V @ q                                   # da chuan hoa L2

    thu_tu = np.argsort(-diem)
    ra: list[ChunkTraVe] = []
    for j in thu_tu:
        c = _CHUNK[_IDS[j]]
        # Loc cay o day chu khong o SQL: ma tran da nap san, loc trong Python
        # re hon truy van lai. Chunk khong ghi cay (crop=None) van giu - do
        # la tai lieu chung, khong phai tai lieu sai cay.
        if crop and c.crop and c.crop != crop:
            continue
        c.diem = float(diem[j])
        ra.append(c)
        if len(ra) >= top_k:
            break
    return ra
