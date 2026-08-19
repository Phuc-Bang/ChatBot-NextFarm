"""
Kiem thu discover.py - KHONG goi mang.

Trong tam: nhan cay trong phai khop theo BIEN TU. Lan chay dau tien dung
so khop chuoi thuong nen "ma" khop ben trong "manh", gan nham nhan lua cho
mot bai ve nong thon moi. Nguoi duyet se tin vao nhan neu no thuong dung,
nen nhan sai la mot dang bia dat o buoc de xuat.
"""

import discover


# ----------------------------------------------------------------------
# Nhan dien cay trong
# ----------------------------------------------------------------------
def test_nhan_dung_lua():
    assert discover.guess_crop("Kỹ thuật gieo mạ vụ xuân") == "lua"
    assert discover.guess_crop("Quy trình canh tác lúa chất lượng cao") == "lua"
    assert discover.guess_crop("ky thuat trong lua nuoc") == "lua"


def test_nhan_dung_ca_chua():
    assert discover.guess_crop("Kỹ thuật trồng cà chua") == "ca_chua"
    assert discover.guess_crop("ky thuat trong ca chua ghep") == "ca_chua"


def test_nhan_dung_dua_chuot():
    assert discover.guess_crop("Kỹ thuật trồng dưa chuột vụ đông") == "dua_chuot"
    assert discover.guess_crop("Trồng dưa leo trong nhà màng") == "dua_chuot"


def test_khong_khop_ben_trong_tu_khac():
    """Loi da gap that: 'mạ' khop trong 'mạnh'."""
    assert discover.guess_crop("Bước chuyển mạnh mẽ trong xây dựng NTM") is None
    assert discover.guess_crop("Phát triển kinh tế từ nghề trồng nấm") is None


def test_cay_ngoai_pham_vi_tra_none():
    for tieu_de in ("Trồng lạc trái vụ", "Chăm sóc bưởi Phúc Trạch",
                    "Kỹ thuật nuôi tôm nước lợ", "Trồng nho mẫu đơn"):
        assert discover.guess_crop(tieu_de) is None


def test_nhieu_cay_trong_mot_tieu_de_thi_tra_none():
    """Khong chac thi de nguoi duyet quyet, khong tu chon mot cai."""
    assert discover.guess_crop("So sánh hiệu quả trồng lúa và cà chua") is None


# ----------------------------------------------------------------------
# Loc bai viet ky thuat
# ----------------------------------------------------------------------
def test_nhan_ra_bai_ky_thuat():
    assert discover.looks_like_article(
        "https://vi.du/khoa-hoc-ky-thuat/trong-dua-chuot-781.html",
        "Kỹ thuật trồng và chăm sóc dưa chuột")


def test_bo_qua_lien_ket_dieu_huong():
    assert not discover.looks_like_article("https://vi.du/lien-he", "Liên hệ")
    assert not discover.looks_like_article("https://vi.du/gioi-thieu", "Giới thiệu")


# ----------------------------------------------------------------------
# Nguyen tac
# ----------------------------------------------------------------------
def test_khong_co_url_nao_hard_code_ngoai_seeds():
    """Moi URL nguon phai den tu seeds.yaml / sources.yaml, khong nam trong code."""
    from pathlib import Path

    ma = Path(discover.__file__).read_text(encoding="utf-8")
    dong_ma = [ln for ln in ma.splitlines()
               if not ln.strip().startswith("#") and "vi.du" not in ln]
    noi_dung = "\n".join(dong_ma)
    assert "gov.vn" not in noi_dung
