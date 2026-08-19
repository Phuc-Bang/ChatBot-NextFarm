"""
Kiem thu luoc do va cac RANG BUOC o tang du lieu.

Bo test nay canh giu dung mot y: nguyen tac cua quy chuan phai la rang buoc
ky thuat, khong phai loi hua trong tai lieu.

  - Chunk cua tai lieu chua duyet KHONG duoc lot vao indexable_chunk (DEC-005)
  - Chunk rui ro cao chua duyet le KHONG duoc index (muc 24.4)
  - Da duyet thi phai biet AI duyet va KHI NAO (dieu kien de audit duoc)

Test can PostgreSQL dang chay. Khong ket noi duoc thi bo qua, khong bao do -
de nguoi chay test tren may chua dung docker khong bi chan.
Chay truoc: make up && python db/migrate.py
"""

import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")

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
    """Moi test chay trong mot transaction roi rollback - khong ban DB that."""
    with psycopg.connect(DSN) as c:
        c.autocommit = False
        yield c
        c.rollback()


def ma() -> str:
    return "t_" + uuid.uuid4().hex[:10]


def them_source(cur, tier=1):
    sid = ma()
    cur.execute(
        "INSERT INTO source (source_id, publisher, base_url, source_tier) "
        "VALUES (%s, 'Kiem thu', 'https://a.gov.vn', %s)", (sid, tier))
    return sid


def them_document(cur, sid, approved, crop="ca_chua"):
    did = ma()
    cur.execute(
        "INSERT INTO document (document_id, source_id, url, crop, crawled_at, "
        "approved, reviewer, reviewed_at) "
        "VALUES (%s, %s, 'https://a.gov.vn/x', %s, now(), %s, %s, %s)",
        (did, sid, crop, approved,
         "kiem_thu" if approved else None,
         "now()" and (None if not approved else "2026-01-01T00:00:00Z")))
    return did


def them_chunk(cur, did, **kw):
    cid = ma()
    cur.execute(
        "INSERT INTO chunk (chunk_id, document_id, ordinal, text, text_unaccent, "
        "is_high_risk, reviewed_high_risk, approved) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (cid, did, kw.get("ordinal", 1), kw.get("text", "Cà chua cần đất tơi xốp"),
         kw.get("text_unaccent", "ca chua can dat toi xop"),
         kw.get("is_high_risk", False), kw.get("reviewed_high_risk", False),
         kw.get("approved", True)))
    return cid


def trong_view(cur, cid) -> bool:
    cur.execute("SELECT 1 FROM indexable_chunk WHERE chunk_id = %s", (cid,))
    return cur.fetchone() is not None


# ----------------------------------------------------------------------
# Cong chan chinh - DEC-005
# ----------------------------------------------------------------------
def test_chunk_cua_tai_lieu_da_duyet_thi_index_duoc(conn):
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=True)
        cid = them_chunk(cur, did)
        assert trong_view(cur, cid) is True


def test_chunk_cua_tai_lieu_CHUA_duyet_khong_duoc_index(conn):
    """Day la rang buoc quan trong nhat cua ca luoc do."""
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=False)
        cid = them_chunk(cur, did)
        assert trong_view(cur, cid) is False


def test_chunk_bi_danh_dau_loai_khong_duoc_index(conn):
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=True)
        cid = them_chunk(cur, did, approved=False)
        assert trong_view(cur, cid) is False


# ----------------------------------------------------------------------
# Noi dung rui ro cao - muc 24.4
# ----------------------------------------------------------------------
def test_chunk_rui_ro_cao_chua_duyet_le_bi_chan_ngay_luc_ghi(conn):
    """Quen duyet le phai la LOI GHI DU LIEU, khong phai so suat im lang."""
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=True)
        with pytest.raises(psycopg.errors.CheckViolation):
            them_chunk(cur, did, is_high_risk=True, reviewed_high_risk=False,
                       approved=True)


def test_chunk_rui_ro_cao_da_duyet_le_thi_index_duoc(conn):
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=True)
        cid = them_chunk(cur, did, is_high_risk=True, reviewed_high_risk=True,
                         approved=True)
        assert trong_view(cur, cid) is True


def test_chunk_rui_ro_cao_chua_duyet_nhung_khong_approved_thi_ghi_duoc(conn):
    """Duong di binh thuong: nap vao voi approved=false, cho duyet le sau."""
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=True)
        cid = them_chunk(cur, did, is_high_risk=True, reviewed_high_risk=False,
                         approved=False)
        assert trong_view(cur, cid) is False


# ----------------------------------------------------------------------
# Dieu kien de audit duoc
# ----------------------------------------------------------------------
def test_da_duyet_ma_khong_ghi_nguoi_duyet_thi_bi_chan(conn):
    with conn.cursor() as cur:
        sid = them_source(cur)
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                "INSERT INTO document (document_id, source_id, url, crop, "
                "crawled_at, approved) VALUES (%s, %s, 'https://a.gov.vn/y', "
                "'lua', now(), TRUE)", (ma(), sid))


def test_khong_nhan_nguon_tier_3(conn):
    """Tier 3 bi cam o PoC nay - muc 22.1."""
    with conn.cursor() as cur:
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                "INSERT INTO source (source_id, publisher, source_tier) "
                "VALUES (%s, 'Blog nao do', 3)", (ma(),))


def test_khong_nhan_cay_ngoai_pham_vi(conn):
    """Pham vi khoa o ba cay - DEC-002."""
    with conn.cursor() as cur:
        sid = them_source(cur)
        with pytest.raises(psycopg.errors.CheckViolation):
            them_document(cur, sid, approved=False, crop="ca_phe")


def test_fact_khoang_gia_tri_nguoc_bi_chan(conn):
    """min > max lot vao tang kiem so se chan nham hang loat cau tra loi dung."""
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=True)
        with pytest.raises(psycopg.errors.CheckViolation):
            cur.execute(
                "INSERT INTO fact (document_id, sentence_index, sentence, metric, "
                "value_min, value_max) VALUES (%s, 1, 'cau nao do', 'ph', 7, 6)",
                (did,))


# ----------------------------------------------------------------------
# Ha tang tim kiem tieng Viet - DEC-021
# ----------------------------------------------------------------------
def test_co_du_ba_extension(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension")
        co = {r[0] for r in cur.fetchall()}
    assert {"vector", "unaccent", "pg_trgm"} <= co


def test_co_chi_muc_fts_va_trigram(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'chunk'")
        idx = {r[0] for r in cur.fetchall()}
    assert "chunk_fts_simple_idx" in idx
    assert "chunk_trgm_idx" in idx


def test_truy_van_khong_dau_khop_duoc_chunk_co_dau(conn):
    """Bai toan A4 duoc giai o TANG DU LIEU, khong phai bang cach doan dau."""
    with conn.cursor() as cur:
        sid = them_source(cur)
        did = them_document(cur, sid, approved=True)
        them_chunk(cur, did,
                   text="Cà chua thích hợp với đất tơi xốp, độ pH trung tính",
                   text_unaccent="ca chua thich hop voi dat toi xop, do ph trung tinh")

        cur.execute(
            "SELECT count(*) FROM indexable_chunk "
            "WHERE text_unaccent LIKE %s", ("%ca chua%",))
        assert cur.fetchone()[0] >= 1


def test_immutable_unaccent_bo_dau_dung(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT immutable_unaccent(%s)", ("Cà chua cần đất pH bao nhiêu",))
        assert cur.fetchone()[0] == "Ca chua can dat pH bao nhieu"
