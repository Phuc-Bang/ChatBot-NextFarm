"""
Kiem thu tim kiem tu khoa (quy chuan v2.0 muc 14.2).

Bo test nay tra loi hai cau hoi, theo thu tu quan trong:

  1. Chunk chua duyet co lot ra duoc khong?   (DEC-005 - cong chan)
  2. Cau hoi khong dau co tim duoc chunk co dau khong?  (muc 14.3)

Cau hoi thu hai la ca ly do cot text_unaccent ton tai. Neu no khong chay,
toan bo lap luan "giai bai toan khong dau o tang du lieu chu khong de LLM
doan dau" sup do, va he thong buoc phai quay lai cach doan dau - tuc la bia.

Test can PostgreSQL dang chay: make up && python db/migrate.py
"""

import os
import re
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

psycopg = pytest.importorskip("psycopg")

from app.core.text import bo_dau  # noqa: E402
from app.services.normalization.vietnamese import chuan_hoa  # noqa: E402
from app.services.retrieval import keyword as kw  # noqa: E402

DSN = os.environ.get(
    "DATABASE_URL", "postgresql://nextfarm:nextfarm@localhost:15432/nextfarm"
).replace("postgresql+psycopg://", "postgresql://")


def co_db() -> bool:
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not co_db(), reason="khong ket noi duoc PostgreSQL - chay 'make up' truoc")


@pytest.fixture()
def conn():
    """Transaction roi rollback - khong ban DB that."""
    with psycopg.connect(DSN) as c:
        c.autocommit = False
        yield c
        c.rollback()


def ma() -> str:
    return "t_" + uuid.uuid4().hex[:10]


def nap(cur, text, *, crop="ca_chua", approved_doc=True, approved_chunk=True,
        is_high_risk=False, reviewed_high_risk=False, region=None,
        section_title=None):
    """Nap mot chunk that vao DB, text_unaccent sinh bang dung ham cua he thong."""
    sid, did, cid = ma(), ma(), ma()
    cur.execute(
        "INSERT INTO source (source_id, publisher, base_url, source_tier) "
        "VALUES (%s, 'So NN kiem thu', 'https://a.gov.vn', 1)", (sid,))
    cur.execute(
        "INSERT INTO document (document_id, source_id, url, title, crop, region, "
        "crawled_at, approved, reviewer, reviewed_at) VALUES "
        "(%s, %s, 'https://a.gov.vn/x', 'Ky thuat trong', %s, %s, now(), %s, %s, %s)",
        (did, sid, crop, region, approved_doc,
         "kiem_thu" if approved_doc else None,
         "2026-01-01T00:00:00Z" if approved_doc else None))
    cur.execute(
        "INSERT INTO chunk (chunk_id, document_id, ordinal, text, text_unaccent, "
        "section_title, crop, region, is_high_risk, needs_caution, "
        "reviewed_high_risk, approved) "
        "VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (cid, did, text, bo_dau(text), section_title, crop, region,
         is_high_risk, is_high_risk, reviewed_high_risk, approved_chunk))
    return cid


CHUNK_CA_CHUA = ("Cà chua thích hợp với đất thịt nhẹ, tơi xốp, có độ pH từ "
                 "6,0 đến 6,5. Đất chua cần bón vôi trước khi trồng.")
CHUNK_LUA = ("Lúa vụ đông xuân gieo mạ khi nhiệt độ ổn định. Mật độ cấy tùy "
             "theo giống và chân đất.")


# ----------------------------------------------------------------------
# 1. Cong chan DEC-005 - quan trong hon moi test khac o day
# ----------------------------------------------------------------------
def test_chunk_cua_tai_lieu_chua_duyet_khong_bao_gio_tra_ve(conn):
    with conn.cursor() as cur:
        cid = nap(cur, CHUNK_CA_CHUA, approved_doc=False)
        cau = chuan_hoa("cà chua đất pH bao nhiêu")
        assert cid not in [c.chunk_id for c in kw.tim_fts(cau, "ca_chua", conn=conn)]
        assert cid not in [c.chunk_id for c in kw.tim_trigram(cau, "ca_chua", conn=conn)]
        assert cid not in [c.chunk_id for c in kw.tim(cau, "ca_chua", conn=conn)]


def test_chunk_rui_ro_cao_chua_duyet_le_khong_tra_ve(conn):
    """Chunk rui ro cao chua duyet le duoc nap voi approved=False (muc 24.4)."""
    with conn.cursor() as cur:
        cid = nap(cur, "Phun thuốc bảo vệ thực vật cho cà chua theo liều lượng ghi trên bao bì",
            is_high_risk=True, reviewed_high_risk=False, approved_chunk=False)
        cau = chuan_hoa("cà chua phun thuốc bảo vệ thực vật")
        assert cid not in [c.chunk_id for c in kw.tim(cau, "ca_chua", conn=conn)]


def test_trang_thai_nguy_hiem_bi_chan_ngay_o_luoc_do(conn):
    """View indexable_chunk loc "rui ro cao ma chua duyet le", nhung trang
    thai do con KHONG GHI VAO DB DUOC.

    Rang buoc high_risk_phai_duyet_le bien viec quen duyet thanh mot loi ghi
    du lieu, chu khong phai mot so suat im lang o tang truy van.
    """
    with conn.cursor() as cur:
        with pytest.raises(psycopg.errors.CheckViolation):
            nap(cur, "Phun thuốc trừ sâu cho cà chua",
                is_high_risk=True, reviewed_high_risk=False, approved_chunk=True)


def test_chunk_rui_ro_cao_da_duyet_le_thi_tra_ve(conn):
    with conn.cursor() as cur:
        cid = nap(cur, "Phun thuốc bảo vệ thực vật cho cà chua theo liều lượng ghi trên bao bì",
            is_high_risk=True, reviewed_high_risk=True)
        cau = chuan_hoa("cà chua phun thuốc bảo vệ thực vật")
        ra = kw.tim(cau, "ca_chua", conn=conn)
        assert cid in [c.chunk_id for c in ra]
        matched = next(c for c in ra if c.chunk_id == cid)
        assert matched.is_high_risk


def test_khong_doc_thang_bang_chunk():
    """Moi truy van phai di qua view indexable_chunk.

    Doc thang bang chunk lam lot chunk chua duyet vao cau tra loi ma khong co
    gi bao loi - dung kieu that bai im lang ma DEC-005 sinh ra de chan.
    """
    nguon = Path(kw.__file__).read_text(encoding="utf-8")
    # SQL trong file nay viet tu khoa bang CHU HOA, nen "FROM " phan biet
    # duoc voi "from __future__ import ..." cua Python.
    bang = re.findall(r"FROM\s+(\w+)", nguon)
    assert bang, "khong tim thay truy van nao"
    assert set(bang) == {"indexable_chunk"}, "truy van doc tu bang khac: " + str(set(bang))


# ----------------------------------------------------------------------
# 2. Cau hoi khong dau - ly do cot text_unaccent ton tai
# ----------------------------------------------------------------------
def test_cau_hoi_khong_dau_tim_duoc_chunk_co_dau(conn):
    """Day la test quan trong nhat cua muc 14.3.

    Khong co no thi lap luan "giai bai toan khong dau o tang du lieu" chi la
    lap luan tren giay.
    """
    with conn.cursor() as cur:
        cid = nap(cur, CHUNK_CA_CHUA)
        ra = kw.tim(chuan_hoa("ca chua can dat ph bao nhieu"), "ca_chua", conn=conn)
        assert cid in [c.chunk_id for c in ra]


def test_cau_hoi_co_dau_cung_tim_duoc(conn):
    with conn.cursor() as cur:
        cid = nap(cur, CHUNK_CA_CHUA)
        ra = kw.tim(chuan_hoa("cà chua cần đất pH bao nhiêu"), "ca_chua", conn=conn)
        assert cid in [c.chunk_id for c in ra]


def test_viet_tat_duoc_mo_rong_truoc_khi_tim(conn):
    """"bn" -> "bao nhieu" o tang chuan hoa, roi moi den retrieval."""
    with conn.cursor() as cur:
        cid = nap(cur, CHUNK_CA_CHUA)
        ra = kw.tim(chuan_hoa("ca chua dat ph bn"), "ca_chua", conn=conn)
        assert cid in [c.chunk_id for c in ra]


def test_trigram_chiu_duoc_loi_chinh_ta(conn):
    """Loi chinh ta xu ly o tang retrieval bang pg_trgm, KHONG bang cach bao
    LLM doan xem nguoi dung dinh viet gi (muc 13.2 lop 3)."""
    with conn.cursor() as cur:
        cid = nap(cur, CHUNK_CA_CHUA)
        ra = kw.tim_trigram(chuan_hoa("ca chuaa thich hop dat"), "ca_chua",
                            conn=conn)
        assert cid in [c.chunk_id for c in ra]


# ----------------------------------------------------------------------
# 3. Bo loc va uu tien
# ----------------------------------------------------------------------
def test_loc_theo_cay_trong(conn):
    with conn.cursor() as cur:
        nap(cur, CHUNK_LUA, crop="lua")
        cid_cc = nap(cur, CHUNK_CA_CHUA, crop="ca_chua")
        ra = kw.tim(chuan_hoa("dat toi xop gieo trong"), "ca_chua", conn=conn)
        assert all(c.crop in (None, "ca_chua") for c in ra)
        assert cid_cc in [c.chunk_id for c in ra]


def test_chunk_khong_ghi_cay_van_duoc_lay(conn):
    """Tai lieu chung ve dat, nuoc, phan bon khong gan voi cay cu the nao."""
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        sid, did, cid = ma(), ma(), ma()
        cur.execute("INSERT INTO source (source_id, publisher, source_tier) "
                    "VALUES (%s, 'X', 1)", (sid,))
        cur.execute(
            "INSERT INTO document (document_id, source_id, url, crop, crawled_at, "
            "approved, reviewer, reviewed_at) VALUES "
            "(%s, %s, 'https://a.gov.vn/y', 'ca_chua', now(), true, 'kt', now())",
            (did, sid))
        t = "Đất chua có độ pH dưới 5,5 cần bón vôi cải tạo trước khi gieo trồng."
        cur.execute(
            "INSERT INTO chunk (chunk_id, document_id, ordinal, text, "
            "text_unaccent, crop) VALUES (%s, %s, 1, %s, %s, NULL)",
            (cid, did, t, bo_dau(t)))
        ra = kw.tim(chuan_hoa("dat chua bon voi"), "ca_chua", conn=conn)
        assert cid in [c.chunk_id for c in ra]


def test_cung_vung_duoc_cong_diem_chu_khong_loc_bo(conn):
    """Chong hien tuong A3 bang CONG DIEM, khong bang LOC BO.

    Tai lieu vung khac van co the la tai lieu duy nhat noi ve dieu nguoi dung
    hoi. Loc bo bien "khong dung vung" thanh "khong co gi de tra loi".
    """
    with conn.cursor() as cur:
        cid_bac = nap(cur, CHUNK_CA_CHUA, region="mien_bac")
        cid_nam = nap(cur, CHUNK_CA_CHUA + " Chú ý thoát nước.", region="mien_nam")
        ra = kw.tim(chuan_hoa("ca chua dat ph"), "ca_chua",
                    region="mien_nam", conn=conn)
        ids = [c.chunk_id for c in ra]
        assert cid_bac in ids and cid_nam in ids     # khong loc bo ai
        assert ids[0] == cid_nam                     # nhung dung vung len truoc


# ----------------------------------------------------------------------
# 4. Hop nhat RRF
# ----------------------------------------------------------------------
def test_rrf_cong_diem_theo_hang_khong_theo_diem_goc():
    """ts_rank va word_similarity o hai thang do khac han nhau. Ep chung ve
    mot thang la tu bia ra mot phep quy doi khong co co so."""
    a = kw.ChunkTraVe("a", "d", "t", None, None, None, "u", None, None, 1, False)
    b = kw.ChunkTraVe("b", "d", "t", None, None, None, "u", None, None, 1, False)
    ra = kw.hop_nhat_rrf(("fts", [a, b]), ("trigram", [b, a]))
    assert {c.chunk_id for c in ra} == {"a", "b"}
    assert abs(ra[0].diem - ra[1].diem) < 1e-9      # doi xung thi bang diem


def test_rrf_uu_tien_chunk_hai_kenh_cung_tra_ve():
    a = kw.ChunkTraVe("a", "d", "t", None, None, None, "u", None, None, 1, False)
    b = kw.ChunkTraVe("b", "d", "t", None, None, None, "u", None, None, 1, False)
    c = kw.ChunkTraVe("c", "d", "t", None, None, None, "u", None, None, 1, False)
    ra = kw.hop_nhat_rrf(("fts", [b, a]), ("trigram", [c, a]))
    assert ra[0].chunk_id == "a"                    # a co mat o ca hai kenh
    assert set(ra[0].kenh) == {"fts", "trigram"}


def test_tham_so_chua_chot_duoc_danh_dau_todo():
    """Top-K, trong so RRF, nguong deu la [TODO] cho den khi do Recall@K
    (muc 14.6). Khong duoc chot tren giay."""
    nguon = Path(kw.__file__).read_text(encoding="utf-8")
    assert "[TODO]" in nguon
