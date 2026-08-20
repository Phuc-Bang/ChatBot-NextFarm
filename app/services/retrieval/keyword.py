#!/usr/bin/env python3
"""
keyword.py - Tim kiem tu khoa tieng Viet (quy chuan v2.0 muc 14.2).

VAN DE KY THUAT PHAI GIAI

    PostgreSQL KHONG co cau hinh full-text search cho tieng Viet.
    Khong co to_tsvector('vietnamese', ...).

Nen keyword search o day dung hai kenh, ca hai chay tren cot text_unaccent:

    FTS 'simple'   tach token, khong stem. Bat cum tu chinh xac.
    trigram        pg_trgm word_similarity(). Chiu duoc loi chinh ta.

BAI TOAN KHONG DAU DUOC GIAI O DAY, KHONG PHAI O LLM

Nguoi dung go "ca chua can dat ph bao nhieu". Chunk trong kho ghi "Ca chua
thich hop voi dat co do pH tu...". Ban bo dau cua chunk la "ca chua thich hop
voi dat co do ph tu..." - khop truc tiep voi cau hoi, khong can doan dau mot
lan nao.

Doan dau la bia. Khop tren ban bo dau la tra cuu. Day la ly do cot
text_unaccent ton tai (muc 14.3).

VI SAO VAN CAN KEYWORD BEN CANH VECTOR

Vector search yeu chinh xac o: ten benh, ten giong, con so, ky hieu (pH, EC,
NPK), thuat ngu hiem. Day lai dung la nhung thu nong dan hoi nhieu nhat
(muc 14.4).

CHI DOC TU indexable_chunk

Moi truy van o file nay deu doc tu view indexable_chunk, khong bao gio doc
thang bang chunk. View do la cho DEC-005 duoc thuc thi: chunk cua tai lieu
chua duyet, va chunk rui ro cao chua duyet le, khong bao gio ra khoi day.

Doc thang bang chunk se lam lot chunk chua duyet vao cau tra loi ma khong co
gi bao loi. test_khong_doc_thang_bang_chunk canh giu dieu do.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE))

from contextlib import contextmanager  # noqa: E402

import yaml  # noqa: E402

from app.core.db import ket_noi  # noqa: E402
from app.core.text import bo_dau  # noqa: E402
from app.services.normalization.vietnamese import CauHoi  # noqa: E402

STOPWORDS_FILE = BASE / "knowledge" / "lexicon" / "stopwords.yaml"


def _nap_stopwords() -> set[str]:
    if not STOPWORDS_FILE.exists():
        return set()
    d = yaml.safe_load(STOPWORDS_FILE.read_text(encoding="utf-8")) or {}
    return {bo_dau(str(t)) for t in (d.get("stopwords") or [])}


STOPWORDS = _nap_stopwords()


def tsquery_or(khong_dau: str) -> str:
    """Sinh chuoi tsquery dang OR, da bo tu dung.

    VI SAO KHONG DUNG plainto_tsquery

    plainto_tsquery noi MOI token bang AND. Config 'simple' lai khong co danh
    sach tu dung cho ngon ngu nao, nen no giu ca "bao", "nhieu", "can". Ket
    qua do tren kho that (161 chunk):

        "ca chua can dat ph bao nhieu"
          -> 'ca' & 'chua' & 'can' & 'dat' & 'ph' & 'bao' & 'nhieu'
          -> 0 chunk

    Cung cau do bo tu dung roi noi bang OR: 82 chunk ung vien.

    Doi AND thanh OR khong lam ket qua loang, vi viec PHAN BIET la cua
    ts_rank va cua RRF - khong phai cua bo loc. Bo loc AND bien mot tu thua
    trong cau hoi thanh mot dieu kien bat buoc, va do la cach chac chan nhat
    de khong tra ve gi ca.
    """
    tu = [t for t in re.findall(r"\w+", khong_dau) if t not in STOPWORDS]
    return " | ".join(dict.fromkeys(tu))


@contextmanager
def _conn(conn=None):
    """Dung ket noi duoc truyen vao, hoac mo mot ket noi moi.

    Tham so conn ton tai de test chay duoc trong mot transaction roi rollback:
    neu ham nay luon tu mo ket noi rieng, du lieu fixture cua test se nam o
    transaction khac va truy van khong thay gi.
    """
    if conn is not None:
        yield conn
        return
    with ket_noi() as c:
        yield c

# DA CHOT 2026-08-20 bang so do - quet 72 to hop tren 22 case co ground
# truth, kho 185 chunk. Bang day du: docs/reports/P6_retrieval_tuning.md
#
#   TOP_K_MOI_KENH  10 -> 20 nang MRR 0.468 -> 0.562. Tu 20 tro len BAO HOA
#                   (30 va 50 deu cho 0.561). Lay 20: them chunk chi ton
#                   thoi gian ma khong duoc gi.
#   NGUONG_TRIGRAM  0.2 -> 0.4 lam MRR TUT 0.562 -> 0.492. Nguong cang chat
#                   cang mat chunh dung. Doi 0.3 -> 0.2.
#   K_RRF           gan nhu khong anh huong (0.559 / 0.561 / 0.562 cho
#                   10 / 30 / 60). Giu 60 - hang so RRF thong dung.
TOP_K_MOI_KENH = 20
K_RRF = 60                    # hang so RRF thong dung
NGUONG_TRIGRAM = 0.2          # word_similarity toi thieu


@dataclass
class ChunkTraVe:
    chunk_id: str
    document_id: str
    text: str
    section_title: str | None
    crop: str | None
    region: str | None
    url: str
    document_title: str | None
    publisher: str | None
    source_tier: int | None
    is_high_risk: bool
    diem: float = 0.0
    # Giu diem RRF truoc khi rerank ghi de `diem`. Mat no la mat kha nang so
    # sanh hai cach xep hang tren cung mot lan chay (xem rerank.py).
    diem_rrf: float = 0.0
    kenh: list[str] = field(default_factory=list)
    hang: dict[str, int] = field(default_factory=dict)


COT = """
    c.chunk_id, c.document_id, c.text, c.section_title, c.crop, c.region,
    c.url, c.document_title, c.publisher, c.source_tier, c.is_high_risk
"""


def _thanh_chunk(row) -> ChunkTraVe:
    return ChunkTraVe(*row[:11])


def _loc_cay(crop: str | None) -> tuple[str, list]:
    """Bo loc bat buoc theo cay trong (muc 14.5).

    Chunk khong ghi cay (crop IS NULL) van duoc lay: tai lieu chung ve dat,
    nuoc, phan bon khong gan voi mot cay cu the nhung van dung duoc.
    """
    if not crop:
        return "", []
    return " AND (c.crop = %s OR c.crop IS NULL)", [crop]


def tim_fts(cau: CauHoi, crop: str | None = None,
            top_k: int = TOP_K_MOI_KENH, conn=None) -> list[ChunkTraVe]:
    """Kenh 1 - full-text search cau hinh 'simple' tren ban bo dau."""
    truy_van = tsquery_or(cau.khong_dau)
    if not truy_van:
        return []          # cau hoi toan tu dung - khong con gi de tim

    loc, tham = _loc_cay(crop)
    sql = (
        "SELECT" + COT + ", ts_rank(to_tsvector('simple', c.text_unaccent), q) AS r "
        "FROM indexable_chunk c, to_tsquery('simple', %s) q "
        "WHERE to_tsvector('simple', c.text_unaccent) @@ q" + loc + " "
        "ORDER BY r DESC LIMIT %s"
    )
    with _conn(conn) as c, c.cursor() as cur:
        cur.execute(sql, [truy_van] + tham + [top_k])
        return [_thanh_chunk(r) for r in cur.fetchall()]


def tim_trigram(cau: CauHoi, crop: str | None = None,
                top_k: int = TOP_K_MOI_KENH,
                nguong: float = NGUONG_TRIGRAM, conn=None) -> list[ChunkTraVe]:
    """Kenh 2 - trigram, chiu duoc loi chinh ta va cach go khac nhau.

    Dung word_similarity(cau_hoi, van_ban) chu khong phai similarity():
    similarity() so hai chuoi TRON VEN, ma cau hoi thi ngan con chunk thi
    dai - diem se luon thap. word_similarity() do xem cau hoi khop tot den
    dau voi mot PHAN cua chunk, dung voi tinh huong o day.
    """
    loc, tham = _loc_cay(crop)
    sql = (
        "SELECT" + COT + ", word_similarity(%s, c.text_unaccent) AS s "
        "FROM indexable_chunk c "
        "WHERE word_similarity(%s, c.text_unaccent) >= %s" + loc + " "
        "ORDER BY s DESC LIMIT %s"
    )
    with _conn(conn) as c, c.cursor() as cur:
        cur.execute(sql, [cau.khong_dau, cau.khong_dau, nguong] + tham + [top_k])
        return [_thanh_chunk(r) for r in cur.fetchall()]


def hop_nhat_rrf(*ket_qua: tuple[str, list[ChunkTraVe]],
                 k: int = K_RRF) -> list[ChunkTraVe]:
    """Hop nhat nhieu kenh bang Reciprocal Rank Fusion.

    RRF cong 1/(k + hang) cua tung kenh. No dung HANG chu khong dung DIEM,
    nen khong can chuan hoa diem giua cac kenh - ts_rank va word_similarity
    o hai thang do hoan toan khac nhau, ep chung ve mot thang la tu bia ra
    mot phep quy doi khong co co so.
    """
    gop: dict[str, ChunkTraVe] = {}
    for ten_kenh, ds in ket_qua:
        for hang, c in enumerate(ds, start=1):
            cu = gop.get(c.chunk_id)
            if cu is None:
                gop[c.chunk_id] = cu = c
                cu.diem = 0.0
            cu.diem += 1.0 / (k + hang)
            cu.kenh.append(ten_kenh)
            cu.hang[ten_kenh] = hang
    return sorted(gop.values(), key=lambda c: -c.diem)


def cong_diem_vung(ds: list[ChunkTraVe], region: str | None,
                   he_so: float = 0.1) -> list[ChunkTraVe]:
    """Uu tien chunk cung vung voi nguoi dung (muc 14.5).

    Day la co che truc tiep chong hien tuong A3 - khuyen nghi khong phu hop
    vung mien. Thoi vu lua o dong bang song Cuu Long khac han mien Bac.

    CONG DIEM chu khong LOC: tai lieu mien khac van co the la tai lieu duy
    nhat noi ve dieu nguoi dung hoi. Loc bo se bien "khong dung vung" thanh
    "khong co gi de tra loi".

    [TODO] he_so phai den tu so do, chua chot (muc 14.6).
    """
    if not region:
        return ds
    for c in ds:
        if c.region and c.region == region:
            c.diem += he_so
            c.kenh.append("vung")
    return sorted(ds, key=lambda c: -c.diem)


def tim(cau: CauHoi, crop: str | None = None, region: str | None = None,
        top_k: int = TOP_K_MOI_KENH, conn=None) -> list[ChunkTraVe]:
    """Chay ca hai kenh roi hop nhat. Day la API duy nhat ben ngoai nen goi."""
    fts = tim_fts(cau, crop, top_k, conn=conn)
    tri = tim_trigram(cau, crop, top_k, conn=conn)
    return cong_diem_vung(hop_nhat_rrf(("fts", fts), ("trigram", tri)), region)
