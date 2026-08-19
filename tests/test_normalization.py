"""
Kiem thu chuan hoa cau hoi tieng Viet (quy chuan v2.0 muc 13).

Chuan hoa la buoc de lam hong ca chuoi phia sau ma khong bao loi mot tieng
nao: cau hoi bi doi sai thi retrieval truot, LLM nhan evidence lech, va ket
qua eval xau di ma khong ai biet nguyen nhan nam o day. Vi vay file nay
kiem hai thu, theo thu tu quan trong:

  1. Chuan hoa khong BIA THEM NOI DUNG  (bon test cuoi file)
  2. Chuan hoa lam dung viec no phai lam (phan con lai)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "knowledge" / "chunking"))

import chunker  # noqa: E402
from app.core import text as core_text  # noqa: E402
from app.services.normalization import vietnamese as vn  # noqa: E402


# ----------------------------------------------------------------------
# Lop 1 - chuan hoa hinh thuc
# ----------------------------------------------------------------------
def test_gop_khoang_trang_va_ha_chu_thuong():
    c = vn.chuan_hoa("CÀ  CHUA\n\n  trồng   vụ nào")
    assert c.chuan == "cà chua trồng vụ nào"


def test_giu_nguyen_ban_goc():
    goc = "CÀ  CHUA   trồng vụ nào"
    assert vn.chuan_hoa(goc).goc == goc


def test_sinh_ban_bo_dau():
    c = vn.chuan_hoa("Cà chua cần đất pH bao nhiêu")
    assert c.khong_dau == "ca chua can dat ph bao nhieu"


def test_chuan_hoa_nfc_gop_hai_cach_go_cung_mot_chu():
    """Cung chu "ế" go tren Windows va tren web ra hai chuoi byte khac nhau.

    Khong chuan hoa NFC thi khop tu dien truot ma khong bao loi.
    """
    nfc = "ế"                    # ế dang 1 code point
    nfd = "ế"             # ế dang 3 code point
    assert nfc != nfd
    assert vn.chuan_hoa(nfc).chuan == vn.chuan_hoa(nfd).chuan


# ----------------------------------------------------------------------
# Hai phia cua retrieval phai bo dau giong het nhau
# ----------------------------------------------------------------------
def test_hai_phia_dung_chung_mot_ham():
    """Phia nap du lieu va phia cau hoi phai la CUNG MOT ham bo_dau.

    Neu hai ben bo dau khac nhau du chi mot ky tu, keyword search khong bao
    loi - no chi tra ve it ket qua hon, lang le, mai mai. Test nay chan viec
    ai do sao chep them mot ban bo_dau thu hai.
    """
    assert chunker.bo_dau is core_text.bo_dau
    assert vn.bo_dau is core_text.bo_dau


def test_cau_hoi_khong_dau_khop_ban_bo_dau_cua_chunk():
    """Day la co che giai bai toan khong dau o TANG DU LIEU (muc 14.3)."""
    chunk_text = "Cà chua thích hợp với đất có độ pH từ 6,0 đến 6,5."
    cau = vn.chuan_hoa("ca chua can dat ph bao nhieu")
    assert "ca chua" in core_text.bo_dau(chunk_text)
    assert "ca chua" in cau.khong_dau
    assert "ph" in core_text.bo_dau(chunk_text)


# ----------------------------------------------------------------------
# Lop 2 - tu dien viet tat
# ----------------------------------------------------------------------
def test_mo_rong_viet_tat_thuong_gap():
    c = vn.chuan_hoa("ca chua can dat ph bn")
    assert "bao nhiêu" in c.chuan


def test_chi_khop_tron_tu():
    """Loi da gap hai lan trong du an nay: "ph" khop trong "cát pha",
    "ma" khop trong "manh". Viet tat cung phai khop tron tu."""
    c = vn.chuan_hoa("khu vuon nha bac")
    assert "không" not in c.chuan          # "k" trong "khu" khong duoc no ra
    c2 = vn.chuan_hoa("bón lót cho lúa")
    assert c2.chuan == "bón lót cho lúa"


def test_cum_dai_duoc_uu_tien_hon_tu_le():
    c = vn.chuan_hoa("thuoc bvtv phun may lan")
    assert "thuốc bảo vệ thực vật" in c.chuan


# ----------------------------------------------------------------------
# Bay "kg" - vua la viet tat cua "khong" vua la ki-lo-gam
# ----------------------------------------------------------------------
def test_kg_canh_so_giu_nguyen_la_don_vi():
    c = vn.chuan_hoa("bon 50 kg/ha dam cho lua")
    assert "50 kg/ha" in c.chuan
    assert "không" not in c.chuan


def test_kg_khong_canh_so_hieu_la_khong():
    c = vn.chuan_hoa("kg biet trong lua vu nao")
    assert c.chuan.startswith("không biet")


def test_ly_do_chan_duoc_ghi_lai():
    """Moi lan tu choi mo rong deu phai ghi ly do - de doc lai duoc."""
    c = vn.chuan_hoa("bon 50 kg/ha dam")
    ly_do = [d[2] for d in c.da_thay]
    assert any("ki-lo-gam" in x for x in ly_do)


# ----------------------------------------------------------------------
# Bay ky hieu hoa hoc
# ----------------------------------------------------------------------
def test_k_canh_tu_phan_bon_khong_bi_hieu_la_khong():
    c = vn.chuan_hoa("phan k bon bao nhieu")
    assert "không" not in c.chuan


def test_k_cuoi_cau_hieu_la_khong():
    c = vn.chuan_hoa("lua bi sau phun thuoc k")
    assert c.chuan.endswith("không")


def test_chan_ngu_canh_chi_ap_cho_viet_tat_la_ky_hieu_hoa_hoc():
    """"bn" dung canh "ph" van phai no ra - "bn" khong bao gio la ky hieu."""
    c = vn.chuan_hoa("dat ph bn")
    assert "bao nhiêu" in c.chuan


# ----------------------------------------------------------------------
# Mo rong truy van - CONG THEM, khong THAY THE
# ----------------------------------------------------------------------
def test_dua_leo_mo_rong_sang_dua_chuot():
    c = vn.chuan_hoa("dua leo bi vang la")
    assert "dưa chuột" in c.mo_rong


def test_mo_rong_khong_duoc_sua_cau_hoi():
    """Nguoi mien Nam go "dua leo" thi cau hoi van phai la "dua leo".

    Bien the chi duoc noi them tu khoa cho retrieval. Thay the trong cau hoi
    la sua loi nguoi dung noi - va voi cap "ure"/"phan dam" thi con sai nghia
    (xem ghi chu trong local_terms.yaml).
    """
    c = vn.chuan_hoa("dua leo bi vang la")
    assert "dua leo" in c.chuan
    assert "dưa chuột" not in c.chuan


# ----------------------------------------------------------------------
# Lop 4 - lam ro thay vi doan
# ----------------------------------------------------------------------
def test_nhan_ra_cay_trong():
    assert vn.phat_hien_cay(vn.chuan_hoa("ca chua trong vu nao")) == ["ca_chua"]
    assert vn.phat_hien_cay(vn.chuan_hoa("dua leo tuoi may lan")) == ["dua_chuot"]


def test_khong_ro_cay_thi_hoi_lai_chu_khong_doan():
    can, cau = vn.can_lam_ro(vn.chuan_hoa("bon phan bao nhieu la du"))
    assert can and "lua, ca chua hay dua chuot" in cau


def test_nhieu_cay_cung_phai_hoi_lai():
    can, _ = vn.can_lam_ro(vn.chuan_hoa("lua va ca chua khac nhau the nao"))
    assert can


def test_ro_mot_cay_thi_di_tiep():
    can, _ = vn.can_lam_ro(vn.chuan_hoa("ca chua can dat ph bao nhieu"))
    assert not can


# ----------------------------------------------------------------------
# RANG BUOC KIEN TRUC - quan trong hon moi test o tren
# ----------------------------------------------------------------------
def test_moi_thay_doi_deu_truy_nguoc_duoc_ve_tu_dien():
    """Khong duoc co mot tu nao xuat hien trong cau chuan ma khong den tu
    tu dien viet tay.

    Day la ranh gioi giua "chuan hoa" va "bia": neu mot chuoi bien doi tao
    ra tu khong co trong tu dien, nghia la o dau do co suy dien noi dung.
    """
    tu_dien = {full for _, full in vn.VIET_TAT}
    for q in ["ca chua can dat ph bn", "dua leo bi vang la ntn",
              "thuoc bvtv phun may lan hnay", "lua sx vu dx dc k"]:
        c = vn.chuan_hoa(q)
        for cu, moi, _ in c.da_thay:
            assert cu == moi or moi in tu_dien, (
                "chuan hoa sinh ra '" + moi + "' khong co trong tu dien")


def test_khong_them_tu_ngoai_tu_dien_vao_cau():
    """Do so tu: cau chuan chi duoc dai them dung phan tu dien them vao."""
    c = vn.chuan_hoa("ca chua can dat ph bn")
    them = sum(len(moi.split()) - len(cu.split())
               for cu, moi, _ in c.da_thay if cu != moi)
    assert len(c.chuan.split()) == len("ca chua can dat ph bn".split()) + them


def test_module_khong_goi_llm():
    """Muc 13.3: cho LLM viet lai cau hoi la con duong ngan nhat de bia.

    Test nay chan viec ai do lang le them mot loi goi model vao day.
    """
    nguon = Path(vn.__file__).read_text(encoding="utf-8")
    for cam in ["openai", "anthropic", "requests.", "httpx", "urllib.request",
                "transformers", "generate(", "completion"]:
        assert cam not in nguon.lower(), "chuan hoa khong duoc goi model: " + cam


def test_deterministic():
    """Chay hai lan phai ra ket qua giong het nhau."""
    q = "lua sx vu dx bon 50 kg/ha dam dc k"
    a, b = vn.chuan_hoa(q), vn.chuan_hoa(q)
    assert (a.chuan, a.khong_dau, a.mo_rong) == (b.chuan, b.khong_dau, b.mo_rong)


def test_tu_dien_nap_duoc_va_khong_rong():
    assert len(vn.VIET_TAT) >= 20
    assert len(vn.TU_DIA_PHUONG) >= 5
    assert all(re.fullmatch(r"[\w ]+", s) for s, _ in vn.VIET_TAT)
