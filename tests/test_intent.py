"""
Kiem thu Intent Router va bon mau tu choi (quy chuan v2.0 muc 11).

Router la thanh phan duy nhat dung giua nguoi dung va hien tuong A1 - bot tra
loi mot con so trong sach cho cau hoi "vuon toi dang bao nhieu". Mot loi o day
khong lam he thong bao loi; no lam he thong tra ve mot cau tra loi TRONG RAT
DANG TIN. Vi vay file nay kiem ky nhat ba cho:

  1. Cap cau hoi chi khac nhau vai chu ma khac han nhanh xu ly
  2. Cau hoi tiep noi - luot sau khong con chu ngu
  3. Mau tu choi khong tu sinh ra con so, khong hua thu minh khong co
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.abstention import templates as tpl  # noqa: E402
from app.services.intent import router as R  # noqa: E402


def nhan(q, ctx=None):
    return R.phan_loai(q, ctx).nhan


# ----------------------------------------------------------------------
# Bay quan trong nhat: hoi NGUONG hay hoi SO DO THUC TE
# ----------------------------------------------------------------------
def test_hoi_nguong_ky_thuat_thi_di_tiep():
    """Cau nay phai duoc TRA LOI. Chan no lai la bot vo dung."""
    assert nhan("cà chua khu A độ ẩm bao nhiêu là được ạ") == R.AGRONOMY


def test_bo_hai_chu_la_duoc_thi_thanh_hoi_so_do():
    """Cung cau tren, bo dau hieu chuan muc di, thanh hoi so do that."""
    assert nhan("độ ẩm khu A bao nhiêu") == R.GARDEN_DATA


def test_cac_dau_hieu_chuan_muc_khac_cung_chan_duoc():
    for q in ["ph thich hop cho lua o khu a la bao nhieu",
              "do am dat nen duy tri cho ca chua hien nay la bao nhieu",
              "nhiet do bao nhieu la tot cho dua chuot trong nha kinh"]:
        assert nhan(q) == R.AGRONOMY, q


# ----------------------------------------------------------------------
# Bay thu hai: cau hoi tiep noi
# ----------------------------------------------------------------------
def test_cau_tiep_noi_hoi_so_lieu_vuon():
    """Day la vi du mo dau muc 11.1 - lo hong lon nhat cua kien truc v1.0.

    Scope Check theo cay trong se cho lot: ngu canh la ca chua nen cau hoi
    "van thuoc pham vi". Chi Intent Router moi chan duoc.
    """
    ctx = ["cà chua khu A độ ẩm bao nhiêu là được ạ"]
    assert nhan("thế giờ đang bao nhiêu", ctx) == R.GARDEN_DATA


def test_cau_tiep_noi_xac_nhan_lenh_thiet_bi():
    ctx = ["bật van 3 trong 10 phút", "ừ đồng ý"]
    assert nhan("xong chưa em", ctx) == R.DEVICE_CONTROL


def test_khong_co_ngu_canh_thi_khong_bia_ra_ngu_canh():
    """"the gio dang bao nhieu" dung mot minh van phai chan - no co du hai
    nhom dau hieu. Nhung router khong duoc tu nghi ra mot khu nao ca."""
    kq = R.phan_loai("thế giờ đang bao nhiêu")
    assert kq.nhan == R.GARDEN_DATA
    assert kq.khu is None


def test_ngu_canh_lam_ha_do_tin_cay():
    ctx = ["bật van 3 trong 10 phút", "ừ đồng ý"]
    a = R.phan_loai("xong chưa em", ctx)
    b = R.phan_loai("bật van 3 trong 10 phút")
    assert a.nguon == "rule_ngu_canh" and b.nguon == "rule"
    assert a.do_tin_cay < b.do_tin_cay


# ----------------------------------------------------------------------
# Bay thu ba: RA LENH hay HOI TRANG THAI
# ----------------------------------------------------------------------
def test_menh_lenh_dieu_khien():
    for q in ["bật van 3 trong 10 phút", "tắt bơm khu B đi",
              "hẹn giờ tưới khu B lúc 5h sáng mai"]:
        assert nhan(q) == R.DEVICE_CONTROL, q


def test_hoi_trang_thai_thiet_bi_la_hoi_so_lieu_khong_phai_ra_lenh():
    for q in ["Van số 3 có đang chạy không?", "van so 3 co dang chay k"]:
        assert nhan(q) == R.GARDEN_DATA, q


def test_dong_tu_tuoi_mot_minh_khong_phai_lenh_dieu_khien():
    """"tuoi nuoc cho ca chua may lan mot ngay" la cau hoi ky thuat.

    Doi hoi ca dong tu lan danh tu thiet bi chinh la de chan nham lan nay.
    """
    assert nhan("tưới nước cho cà chua mấy lần một ngày") == R.AGRONOMY


def test_tai_sao_khong_bao_gio_mo_dau_mot_menh_lenh():
    assert nhan("tại sao tắt bơm thì cả ca tưới cũng dừng theo") == R.PRODUCT_FEATURE


# ----------------------------------------------------------------------
# product_feature
# ----------------------------------------------------------------------
def test_hoi_tinh_nang_app():
    for q in ["app có tự tưới theo dự báo thời tiết không",
              "tôi quên mật khẩu thì lấy lại kiểu gì",
              "bảo hành thiết bị mấy năm vậy"]:
        assert nhan(q) == R.PRODUCT_FEATURE, q


def test_hoi_kha_nang_cua_app_khong_bi_coi_la_menh_lenh():
    assert nhan("app có tự động bật van khi đất khô không") == R.PRODUCT_FEATURE


# ----------------------------------------------------------------------
# Khong duoc tu choi oan
# ----------------------------------------------------------------------
def test_cau_hoi_nong_hoc_thuong_di_tiep():
    for q in ["lúa bón đạm bao nhiêu kg/ha", "ca chua can dat ph bao nhieu",
              "dưa chuột trồng vụ nào", "cách làm đất trồng cà chua",
              "cà phê cần pH bao nhiêu"]:
        assert nhan(q) == R.AGRONOMY, q


def test_cau_hoi_ngoai_pham_vi_van_di_tiep():
    """Chan cau hoi ve ca phe la viec cua Scope Check (muc 12), chay SAU
    router. Chan o day la chan sai tang - va mau tu choi cung sai luon."""
    assert nhan("thanh long ra hoa trái vụ cần chiếu đèn bao lâu") == R.AGRONOMY


def test_khu_vuc_khong_phai_khu_vuon():
    """"khu vuc mien Bac" la dia ly, khong phai mot khu vuon cua nguoi dung."""
    assert nhan("khu vực miền Bắc hiện nay trồng giống lúa nào") == R.AGRONOMY
    assert R.trich_khu("khu vuc mien bac") is None


# ----------------------------------------------------------------------
# Trich thong tin de dien vao mau - khong duoc doan
# ----------------------------------------------------------------------
def test_trich_dung_ten_khu_va_chi_so():
    kq = R.phan_loai("thế giờ đang bao nhiêu",
                     ["cà chua khu A độ ẩm bao nhiêu là được ạ"])
    assert kq.khu == "khu A"
    assert kq.chi_so == "độ ẩm"
    assert kq.cay == ["ca_chua"]


def test_khong_tim_thay_thi_de_none_chu_khong_dien_bua():
    kq = R.phan_loai("giờ đang bao nhiêu vậy")
    assert kq.khu is None and kq.cay == []


def test_chon_chi_so_dai_nhat():
    """"do am dat" phai thang "do am" - loi da sua trong extract.py."""
    assert R.trich_chi_so("do am dat khu a bao nhieu") == "độ ẩm đất"


# ----------------------------------------------------------------------
# Bon mau tu choi
# ----------------------------------------------------------------------
def test_mau_khong_tu_sinh_con_so():
    """Mot cau tu choi co con so trong do la mot con so bia.

    Duoc phep nhac lai nguyen van thong tin nguoi dung vua go (vi du "khu 3"),
    nhung ban than mau khong duoc mang san chu so nao.
    """
    mau = [
        tpl.garden_data(), tpl.garden_data(chi_so="độ ẩm", cay=["ca_chua"]),
        tpl.garden_data(co_tai_lieu=False),
        tpl.product_feature(), tpl.device_control(),
        tpl.out_of_scope(), tpl.out_of_scope("cà phê"),
    ]
    for m in mau:
        assert not re.search(r"\d", m), "mau tu choi chua con so: " + m


def test_khong_biet_ten_khu_thi_noi_chung_chung():
    m = tpl.garden_data(khu=None)
    assert "vườn của anh/chị" in m


def test_biet_ten_khu_thi_nhac_lai_dung_ten_do():
    assert "khu A" in tpl.garden_data(khu="khu A")


def test_khong_co_tai_lieu_thi_khong_hua_co_tai_lieu():
    """Cau chuyen huong "em co tai lieu" chi duoc noi khi that su co.

    Kho tri thuc hien co 0 chunk index duoc (chua duyet xong), nen day khong
    phai gia dinh xa voi.
    """
    m = tpl.garden_data(chi_so="độ ẩm", cay=["ca_chua"], co_tai_lieu=False)
    assert "có tài liệu" not in m
    assert "chưa được kết nối" in m


def test_khong_ro_cay_thi_khong_chon_bua_mot_cay():
    m = tpl.garden_data(chi_so="độ ẩm", cay=["lua", "ca_chua"])
    assert "lúa" not in m and "cà chua" not in m


def test_moi_mau_deu_neu_ly_do_va_chi_duong():
    """Quy chuan viet mau: vi sao -> o dau co -> chuyen huong (muc 11.5)."""
    assert "app NextFarm" in tpl.garden_data()
    assert "hỗ trợ NextFarm" in tpl.product_feature()
    assert "trong app" in tpl.device_control()
    assert "lúa, cà chua và dưa chuột" in tpl.out_of_scope()


def test_nhan_la_khong_duoc_lang_le_thanh_cau_tra_loi_trong():
    with pytest.raises(ValueError):
        tpl.theo_nhan(R.AGRONOMY)


def test_theo_nhan_khop_du_ba_nhanh_tu_choi():
    assert tpl.theo_nhan(R.PRODUCT_FEATURE) == tpl.product_feature()
    assert tpl.theo_nhan(R.DEVICE_CONTROL) == tpl.device_control()
    assert "khu A" in tpl.theo_nhan(R.GARDEN_DATA, khu="khu A")


# ----------------------------------------------------------------------
# Rang buoc ky thuat
# ----------------------------------------------------------------------
def test_khop_tron_tu_khong_khop_chuoi_con():
    """Loi da lam hong hai module trong du an: "ph" khop trong "cat pha",
    "ma" khop trong "manh". Router khong duoc lap lai lan thu ba."""
    assert R._co("bat bom", "bat")
    assert not R._co("bat dau vu moi", "bat")
    assert not R._co("cat pha thi bon gi", "ph")


def test_bo_dau_lam_mat_su_khac_nhau_giua_van_va_van():
    """Khop tron tu KHONG du khi hai tu khac nhau bo dau ra giong nhau.

    "van" (thiet bi), "van" trong "cay VAN heo" va "VAN de nay" - ba tu khac
    nhau, bo dau xong deu la "van". Vi vay van phai duoc nhan bang tu di kem,
    khong phai bang chinh no.
    """
    assert R.VAN_RE.search("bat van 3 trong 10 phut")
    assert R.VAN_RE.search("mo van khu a di em")
    assert not R.VAN_RE.search("tuoi roi ma cay van heo")
    assert not R.VAN_RE.search("van de nay xu ly the nao")


def test_dung_va_dung_cung_bo_dau_ra_mot_chu():
    """"DUNG ca tuoi dang chay" (dung) la lenh; "DUNG may bom loai nao"
    (dung) la cau hoi chon may. Tu de hoi la thu phan biet duoc hai cau."""
    assert nhan("Dừng ca tưới đang chạy") == R.DEVICE_CONTROL
    assert nhan("dùng máy bơm loại nào cho ruộng 5 sào") == R.AGRONOMY


# Cau hoi nong hoc that, KHONG lay tu tap kiem thu da dong bang. Day la luoi
# an toan cho huong sai con lai: luat cang rong thi cang de tu choi oan, va
# tu choi oan khong hien ra trong con so cua tap kiem thu neu tap do chi toan
# case phai bi chan.
HOI_NONG_HOC_THAT = [
    "tưới rồi mà cây vẫn héo thì làm sao",
    "dùng máy bơm loại nào cho ruộng 5 sào",
    "vấn đề vàng lá ở dưa chuột xử lý thế nào",
    "cà chua vẫn chưa ra hoa có phải thiếu lân không",
    "bón lót vụ đông xuân cho lúa cần những gì",
    "mô hình tưới nhỏ giọt cho cà chua có tốt không",
    "lúa bị đạo ôn phun thuốc gì",
    "mật độ gieo sạ lúa bao nhiêu kg một sào",
    "dưa chuột làm giàn cao bao nhiêu",
    "đất chua thì bón vôi bao nhiêu",
    "cà chua trồng khoảng cách bao nhiêu là hợp lý",
    "thời vụ gieo mạ ở miền Bắc khi nào",
    "phân chuồng ủ bao lâu thì dùng được",
    "cách phòng trừ sâu đục quả cà chua",
    "lúa đẻ nhánh cần bón thúc gì",
    "dưa leo bị phấn trắng chữa thế nào",
    "nhiệt độ thích hợp cho cà chua là bao nhiêu",
    "trồng lúa cần bao nhiêu nước một vụ",
    "sao lá cà chua bị xoăn",
    "hệ thống tưới nhỏ giọt lắp thế nào cho vườn cà chua",
    # Nhom nay nham thang vao cac va cham do bo dau - xem NGOAI_LE trong
    # router.py. Moi cau o day da tung bi tu choi oan mot lan.
    "bắt đầu lắp hệ thống tưới cho vườn cà chua cần gì",
    "vụ đông xuân bón lót cho lúa thế nào",
    "đồng bằng sông Cửu Long gieo sạ lúa thời điểm nào",
    "mô hình nhà kính trồng cà chua chi phí ra sao",
    "cây cà chua tuổi bao nhiêu ngày thì ra hoa",
    "bắt buộc phải làm giàn cho dưa chuột không",
    "dùng để bón lót thì phân nào tốt",
    "máy bơm nước tưới lúa nên chọn công suất bao nhiêu",
    "đóng bao thóc sau thu hoạch bảo quản thế nào",
    "quạt thông gió trong nhà kính cà chua đặt ở đâu",
    "cảm biến độ ẩm đất nên chôn sâu bao nhiêu",
    "thiết bị đo pH đất loại nào chính xác",
]


def test_ngoai_le_khong_lam_hong_cau_phai_bi_chan():
    """Loai tru va cham khong duoc di qua xa den muc chan mat luat.

    "gio" bi loai tru khi di canh "thong" (thong gio), nhung "khu A gio bao
    nhieu" van phai la garden_data.
    """
    assert nhan("Độ ẩm đất khu A giờ bao nhiêu?") == R.GARDEN_DATA
    assert nhan("mở van khu A đi em") == R.DEVICE_CONTROL
    assert nhan("Dừng ca tưới đang chạy") == R.DEVICE_CONTROL


@pytest.mark.parametrize("q", HOI_NONG_HOC_THAT)
def test_khong_tu_choi_oan_cau_hoi_nong_hoc(q):
    assert nhan(q) == R.AGRONOMY


def test_nguon_mac_dinh_khong_phai_mot_ket_luan():
    """Khi khong luat nao khop, router tra ve agronomy voi do tin cay 0.

    Doc `nhan` ma bo qua `nguon` la hieu sai ket qua: do la "lop rule khong
    biet", khong phai "cau nay chac chan la nong hoc".
    """
    kq = R.phan_loai("thanh long ra hoa trái vụ cần chiếu đèn bao lâu")
    assert kq.nguon == "mac_dinh" and kq.do_tin_cay == 0.0


def test_router_khong_goi_llm():
    nguon = Path(R.__file__).read_text(encoding="utf-8")
    for cam in ["openai", "anthropic", "requests.", "httpx", "urllib.request",
                "transformers"]:
        assert cam not in nguon.lower(), "lop rule khong duoc goi model: " + cam


def test_ma_nguon_khong_chua_ky_tu_dieu_khien():
    """Da tung co mot ky tu backspace (\\x08) lot vao mot bieu thuc chinh quy
    o file nay thay cho \\b.

    grep khong thay no, mat khong thay no, va bieu thuc lang le khong khop gi
    ca - dung kieu loi im lang ma ca kien truc nay sinh ra de chan. Test nay
    lam no thanh loi bao duoc.
    """
    for f in [Path(R.__file__), Path(tpl.__file__)]:
        s = f.read_text(encoding="utf-8")
        xau = {c for c in s if ord(c) < 32 and c not in "\n\t\r"}
        assert not xau, f.name + " chua ky tu dieu khien: " + repr(xau)


def test_deterministic():
    q, ctx = "thế giờ đang bao nhiêu", ["cà chua khu A độ ẩm bao nhiêu là được ạ"]
    a, b = R.phan_loai(q, ctx), R.phan_loai(q, ctx)
    assert (a.nhan, a.do_tin_cay, a.khu, a.chi_so) == (b.nhan, b.do_tin_cay, b.khu, b.chi_so)
