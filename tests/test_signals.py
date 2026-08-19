"""
Kiem thu signals.py.

Rang buoc quan trong nhat cua module nay khong phai "do chinh xac" ma la
"khong bao gio tu quyet". No do va canh bao; nguoi duyet ket luan.
Test cuoi cung trong file nay canh giu dung dieu do.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "knowledge" / "review"))

import signals  # noqa: E402


TAI_LIEU_KY_THUAT = """
Kỹ thuật trồng cà chua
1. Thời vụ. Vụ đông xuân gieo hạt trong khoảng thời gian thích hợp của địa phương.
2. Làm đất. Đất trồng cà chua cần được cày bừa kỹ, lên luống cao, mặt luống bằng phẳng.
3. Chọn giống. Chọn giống có khả năng kháng bệnh, xử lý hạt trước khi gieo.
4. Mật độ và khoảng cách. Trồng theo hàng, giữ khoảng cách giữa các cây.
5. Bón phân. Bón lót toàn bộ phân hữu cơ. Bón thúc chia làm nhiều lần.
6. Chăm sóc. Tưới nước đủ ẩm, làm giàn khi cây cao, tỉa cành cho thông thoáng.
7. Phòng trừ sâu bệnh theo nguyên tắc bốn đúng.
8. Thu hoạch khi quả chín đều.
"""

TIN_HOAT_DONG = """
Hội nghị tổng kết sản xuất vụ đông xuân
Sáng nay, Sở đã tổ chức hội nghị tổng kết. Đồng chí Giám đốc Sở phát biểu khai mạc.
Tham dự hội nghị có đoàn công tác của các huyện. Hội nghị đã triển khai quyết định số
123 về chỉ đạo sản xuất. Các đại biểu trao đổi với phóng viên và chia sẻ kinh nghiệm
xây dựng mô hình điểm. Hội nghị bế mạc trong buổi chiều cùng ngày.
"""


# ----------------------------------------------------------------------
# Phan biet tai lieu ky thuat va tin hoat dong
# ----------------------------------------------------------------------
def test_tai_lieu_ky_thuat_nhieu_tu_ky_thuat_hon():
    th = signals.do(TAI_LIEU_KY_THUAT)
    assert th.dem_ky_thuat > th.dem_tin_tuc


def test_tin_hoat_dong_nhieu_tu_tin_tuc_hon():
    th = signals.do(TIN_HOAT_DONG)
    assert th.dem_tin_tuc > th.dem_ky_thuat


def test_dem_duoc_ten_cay():
    th = signals.do(TAI_LIEU_KY_THUAT)
    assert th.dem_ten_cay.get("ca_chua", 0) >= 2
    assert "lua" not in th.dem_ten_cay


# ----------------------------------------------------------------------
# Canh bao
# ----------------------------------------------------------------------
def test_canh_bao_khi_khong_thay_ten_cay_khai_bao():
    th = signals.do(TAI_LIEU_KY_THUAT)
    cb = signals.canh_bao(th, "lua")
    assert any("khong tim thay ten cay" in c.lower() for c in cb)


def test_khong_canh_bao_khi_ten_cay_khop():
    th = signals.do(TAI_LIEU_KY_THUAT)
    cb = signals.canh_bao(th, "ca_chua")
    assert not any("khong tim thay ten cay" in c.lower() for c in cb)


def test_canh_bao_khi_giong_tin_hoat_dong():
    th = signals.do(TIN_HOAT_DONG)
    cb = signals.canh_bao(th, None)
    assert any("tin hoat dong" in c.lower() for c in cb)


def test_canh_bao_khi_ten_mien_khong_phai_gov_vn():
    th = signals.do(TAI_LIEU_KY_THUAT, "https://blog-nong-nghiep.com/bai-viet")
    assert any("gov.vn" in c for c in signals.canh_bao(th, "ca_chua"))


def test_khong_canh_bao_ten_mien_voi_gov_vn():
    th = signals.do(TAI_LIEU_KY_THUAT, "https://khuyennong.tinh.gov.vn/bai")
    assert not any("gov.vn" in c for c in signals.canh_bao(th, "ca_chua"))
    assert th.la_gov_vn is True


def test_canh_bao_van_ban_qua_ngan():
    th = signals.do("Cà chua. Thời vụ. Làm đất.")
    assert any("ngan" in c.lower() for c in signals.canh_bao(th, "ca_chua"))


def test_canh_bao_nhieu_dong_ngan_nghi_dinh_menu():
    rac = "\n".join(["Trang chu", "Gioi thieu", "Lien he", "Tin tuc"] * 20)
    th = signals.do(rac + "\n" + TAI_LIEU_KY_THUAT)
    assert any("dong rat ngan" in c.lower() for c in signals.canh_bao(th, None))


# ----------------------------------------------------------------------
# Rang buoc quan trong nhat
# ----------------------------------------------------------------------
def test_signals_khong_bao_gio_tu_quyet_duyet():
    """Module nay DO, khong PHAN.

    Cong duyet la cong cua nguoi (DEC-005, DEC-029). De may tu duyet chinh la
    kieu tat ma ca kien truc chong bia nay sinh ra de ngan. Test nay chan viec
    ai do lang le them mot truong 'approved' vao ket qua do.
    """
    th = signals.do(TAI_LIEU_KY_THUAT, "https://a.gov.vn/b")
    cam = {"approved", "verified", "accept", "reject", "decision", "score"}
    assert not (set(vars(th)) & cam), "signals.py khong duoc tra ve ket luan duyet"

    nguon = Path(signals.__file__).read_text(encoding="utf-8")
    assert "approved = True" not in nguon
    assert "approved=True" not in nguon
