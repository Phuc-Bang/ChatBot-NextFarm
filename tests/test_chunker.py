"""
Kiem thu chunker.

Trong tam: chunk khong duoc mat NGU CANH, va noi dung rui ro cao khong duoc
lot qua ma khong bi danh dau.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "knowledge" / "chunking"))

import chunker  # noqa: E402


TAI_LIEU = """Kỹ thuật trồng cà chua
1. Thời vụ
Vụ đông xuân gieo hạt vào thời điểm thích hợp của địa phương.
Vụ hè thu gieo muộn hơn tuỳ điều kiện thời tiết.
2. Làm đất
Đất cần được cày bừa kỹ, lên luống cao, mặt luống bằng phẳng.
Chọn đất thoát nước tốt, không trồng liên tục nhiều vụ trên cùng chân đất.
3. Phòng trừ sâu bệnh
Khi phát hiện sâu bệnh cần phun thuốc bảo vệ thực vật theo liều lượng khuyến cáo.
Tuân thủ thời gian cách ly trước khi thu hoạch.
"""


# ----------------------------------------------------------------------
# Bo dau
# ----------------------------------------------------------------------
def test_bo_dau_giu_duoc_chu_va_so():
    assert chunker.bo_dau("Cà chua cần đất pH 6,5") == "ca chua can dat ph 6,5"


def test_bo_dau_xu_ly_chu_d_gach_ngang():
    assert chunker.bo_dau("Độ ẩm đất") == "do am dat"


def test_bo_dau_khop_voi_cau_hoi_khong_dau_cua_nong_dan():
    """Day la co che giai bai toan A4 o tang du lieu (muc 14.3)."""
    chunk = chunker.bo_dau("Cà chua thích hợp đất có độ pH trung tính")
    assert "ca chua" in chunk
    assert "do ph" in chunk


# ----------------------------------------------------------------------
# Nhan dien tieu de muc
# ----------------------------------------------------------------------
def test_nhan_tieu_de_danh_so():
    assert chunker.la_tieu_de("1. Thời vụ") == "1. Thời vụ"
    assert chunker.la_tieu_de("II. Làm đất") == "II. Làm đất"
    assert chunker.la_tieu_de("a) Bón lót") == "a) Bón lót"


def test_nhan_tieu_de_ket_thuc_bang_hai_cham():
    assert chunker.la_tieu_de("Bón phân:") == "Bón phân:"


def test_nhan_tieu_de_viet_hoa_toan_bo():
    assert chunker.la_tieu_de("HƯỚNG DẪN PHÒNG TRỪ DỊCH HẠI") is not None


def test_cau_van_hoan_chinh_khong_phai_tieu_de():
    assert chunker.la_tieu_de(
        "Đất cần được cày bừa kỹ trước khi lên luống.") is None


def test_dong_qua_dai_khong_phai_tieu_de():
    assert chunker.la_tieu_de("1. " + "x" * 200) is None


# ----------------------------------------------------------------------
# Cat chunk
# ----------------------------------------------------------------------
def test_cat_ra_nhieu_chunk():
    cs = chunker.cat(TAI_LIEU, tu_khoa_rui_ro=["thuốc", "liều lượng", "cách ly"])
    assert len(cs) >= 2


def test_chunk_giu_tieu_de_muc():
    """Chunk mat tieu de muc thi so lieu trong do mat luon dieu kien ap dung."""
    cs = chunker.cat(TAI_LIEU, tu_khoa_rui_ro=[])
    co_tieu_de = [c for c in cs if c.section_title]
    assert co_tieu_de, "khong chunk nao giu duoc tieu de muc"
    for c in co_tieu_de:
        assert c.section_title in c.text


def test_ordinal_lien_tuc_tu_mot():
    cs = chunker.cat(TAI_LIEU, tu_khoa_rui_ro=[])
    assert [c.ordinal for c in cs] == list(range(1, len(cs) + 1))


def test_moi_chunk_deu_co_ban_bo_dau():
    cs = chunker.cat(TAI_LIEU, tu_khoa_rui_ro=[])
    for c in cs:
        assert c.text_unaccent
        assert c.text_unaccent == chunker.bo_dau(c.text)


# ----------------------------------------------------------------------
# Noi dung rui ro cao - muc 24.4
# ----------------------------------------------------------------------
def test_danh_dau_chunk_co_tu_khoa_rui_ro():
    cs = chunker.cat(TAI_LIEU, tu_khoa_rui_ro=["thuốc", "liều lượng", "cách ly"])
    rui_ro = [c for c in cs if c.is_high_risk]
    assert rui_ro, "khong bat duoc chunk noi ve thuoc bao ve thuc vat"
    assert any("thuốc" in c.text.lower() for c in rui_ro)


def test_ghi_lai_tu_khoa_nao_lam_chunk_thanh_rui_ro():
    """Nguoi duyet can biet VI SAO chunk bi danh dau, khong chi biet la co."""
    cs = chunker.cat(TAI_LIEU, tu_khoa_rui_ro=["thuốc", "cách ly"])
    for c in cs:
        if c.is_high_risk:
            assert c.tu_khoa_rui_ro


def test_chunk_khong_co_tu_khoa_thi_khong_bi_danh_dau():
    text = "1. Thời vụ\nVụ đông xuân gieo hạt vào thời điểm thích hợp của địa phương."
    cs = chunker.cat(text, tu_khoa_rui_ro=["thuốc", "liều lượng"])
    assert all(not c.is_high_risk for c in cs)


def test_tu_dien_rui_ro_that_bat_duoc_noi_dung_thuoc():
    """Doc tu knowledge/lexicon/high_risk_terms.yaml, khong phai danh sach test."""
    tu_khoa = chunker.tai_tu_khoa_rui_ro()
    assert tu_khoa, "khong doc duoc tu dien rui ro cao"
    cs = chunker.cat(TAI_LIEU)
    assert any(c.is_high_risk for c in cs)


# ----------------------------------------------------------------------
# Khong xe doi noi dung
# ----------------------------------------------------------------------
def test_khong_cat_ngay_sau_dong_mo_danh_sach():
    """Dong ket thuc bang dau hai cham dang mo mot danh sach buoc ky thuat."""
    dong = ["Bón phân gồm các bước sau:"] + ["- Bước " + str(i) for i in range(1, 40)]
    manh = chunker.cat_theo_do_dai(dong)
    assert not manh[0].rstrip().endswith(":"), "cat ngay sau dau hai cham -> mat danh sach"


def test_khong_cat_giua_mot_dong():
    dong = ["Dòng số " + str(i) + " " + "x" * 100 for i in range(40)]
    manh = chunker.cat_theo_do_dai(dong)
    ghep = "\n".join(manh)
    for d in dong:
        assert d in ghep, "mot dong bi xe doi"


def test_van_ban_rong_khong_sinh_chunk():
    assert chunker.cat("", tu_khoa_rui_ro=[]) == []
    assert chunker.cat("   \n\n  ", tu_khoa_rui_ro=[]) == []


# ----------------------------------------------------------------------
# Hai muc rui ro - muc 19 case C4 va muc 24.4
# ----------------------------------------------------------------------
def test_tu_dien_tra_ve_hai_danh_sach():
    hep, rong = chunker.tai_tu_khoa_rui_ro()
    assert hep and rong
    assert "liều lượng" in hep
    assert "sâu bệnh" in rong
    # "sau benh" la tu chi CHU DE, khong duoc nam o muc bat duyet le
    assert "sâu bệnh" not in hep


def test_chunk_noi_ve_lieu_luong_phai_duyet_le():
    text = ("1. Phòng trừ\n"
            "Khi phát hiện sâu bệnh cần phun thuốc theo liều lượng khuyến cáo "
            "và tuân thủ thời gian cách ly trước khi thu hoạch.")
    cs = chunker.cat(text, ["liều lượng", "cách ly"], ["sâu bệnh"])
    assert any(c.is_high_risk for c in cs)


def test_chunk_chi_noi_chu_de_sau_benh_thi_chi_can_canh_bao():
    """Chunk noi 'can phong tru sau benh kip thoi' khong chua con so nao de bia.

    Bat duyet le nhung chunk nhu vay tieu mat ngan sach duyet ~10 gio ma khong
    doi lai an toan tuong xung - do la ly do tach hai muc.
    """
    text = ("1. Chăm sóc\n"
            "Thường xuyên thăm đồng, phát hiện sâu bệnh kịp thời để phòng trừ.")
    cs = chunker.cat(text, ["liều lượng", "nồng độ"], ["sâu bệnh", "phòng trừ"])
    assert cs
    assert all(not c.is_high_risk for c in cs)
    assert any(c.needs_caution for c in cs)


def test_chunk_rui_ro_cao_thi_luon_can_canh_bao():
    text = "1. Phòng trừ\nPha thuốc theo đúng liều lượng ghi trên nhãn trước khi phun."
    cs = chunker.cat(text, ["liều lượng"], [])
    for c in cs:
        if c.is_high_risk:
            assert c.needs_caution, "rui ro cao thi duong nhien phai kem canh bao"


def test_chunk_thuan_ky_thuat_khong_dinh_co_nao():
    text = "1. Thời vụ\nVụ đông xuân gieo hạt vào thời điểm thích hợp của địa phương."
    cs = chunker.cat(text, ["liều lượng"], ["sâu bệnh"])
    assert all(not c.is_high_risk and not c.needs_caution for c in cs)


# ---------------------------------------------------------------------------
# Day BAY, khong phai test chuc nang.
#
# PHAT HIEN 2026-08-22
#
# chunk_id dung theo THU TU trong tai lieu (knowledge/ingestion/load.py:153):
#
#     cid = rec["id"] + "#" + str(c.ordinal)
#
# Con knowledge/review/chunks.yaml khoa ket qua duyet le vao dung chuoi id do -
# 31 ban ghi, 24 duyet 7 loai, moi ban kem ly do va ten nguoi duyet.
#
# Doi bat ky hang so cat chunk nao la moi ordinal xe dich. Chunk
# `hatinh_dua_chuot_vietgap#1` sau khi cat lai la MOT DOAN VAN KHAC, nhung van
# mang quyet dinh duyet cu. KHONG CO GI BAO LOI. Mot chunk tung bi loai vi
# "tieu de tin tuc" co the duoc cap phep vao kho, hoac mot doan lieu luong da
# duyet bi chan.
#
# Do chinh la cong DEC-005 - thu dang giu numeric_hallucination = 0.
#
# Test nay khong ngan duoc viec doi hang so. No chi bat nguoi doi phai DOC cai
# gia truoc khi doi.
# ---------------------------------------------------------------------------

HANG_SO_DA_CHOT = {
    "KICH_THUOC_MUC_TIEU": 1200,
    "KICH_THUOC_TOI_DA": 2200,
    "CHONG_LAN": 150,
    "CHUNK_TOI_THIEU": 120,
}


def test_doi_hang_so_cat_chunk_phai_duyet_lai_chunk_rui_ro_cao():
    from knowledge.chunking import chunker

    lech = {ten: (mong, getattr(chunker, ten))
            for ten, mong in HANG_SO_DA_CHOT.items()
            if getattr(chunker, ten) != mong}

    assert not lech, (
        "Hang so cat chunk da doi: "
        + "; ".join(f"{k} {a} -> {b}" for k, (a, b) in lech.items())
        + ".\n\n"
        "Doi hang so nay lam moi chunk_id xe dich, trong khi "
        "knowledge/review/chunks.yaml khoa 31 quyet dinh duyet le vao chuoi "
        "id cu. Chung se de len nhung doan van KHAC ma khong bao loi.\n\n"
        "Truoc khi doi, phai lam mot trong hai:\n"
        "  (a) Khoa quyet dinh duyet vao sha256 van ban chunk (hoac offset) "
        "thay vi thu tu, roi duyet lai file chunks.yaml; hoac\n"
        "  (b) Duyet lai 31 chunk rui ro cao bang tay: "
        "python knowledge/review/review_chunks.py\n\n"
        "Lam xong thi cap nhat HANG_SO_DA_CHOT trong test nay."
    )


def test_chunk_id_van_dung_theo_thu_tu():
    """Neu cach dung chunk_id doi, cai bay o tren khong con y nghia.

    Doc ma nguon: bay gio la `rec["id"] + "#" + str(c.ordinal)`. Doi sang
    sha256 la mot cai tien THAT - luc do xoa test nay va test o tren.
    """
    from pathlib import Path

    goc = Path(__file__).resolve().parents[1]
    src = (goc / "knowledge" / "ingestion" / "load.py").read_text(encoding="utf-8")
    assert 'str(c.ordinal)' in src, (
        "load.py khong con dung ordinal de dung chunk_id. Neu da chuyen sang "
        "sha256 hoac offset thi cai bay o test truoc khong con can - xoa ca hai."
    )
