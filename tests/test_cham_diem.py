"""
Kiem thu bo cham diem.

VI SAO BO NAY PHAI CO TEST RIENG

Moi con so bao cao cho NextFarm deu di qua day. Mot loi o `co_so()` hay
`la_tu_choi()` khong lam he thong chay sai - no lam BANG SO sai, va bang so
sai thi khong ai phat hien duoc bang mat vi no van trong nhu that.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "evaluation"))

from metrics.cham import (                                  # noqa: E402
    cac_so, cham_mot, co_so, la_tu_choi)
from metrics.tong_hop import ChiSo                          # noqa: E402


# ---------------------------------------------------------------------------
# Nhan dien so
# ---------------------------------------------------------------------------

def test_bat_duoc_so_trong_cau_tra_loi():
    assert co_so("do am khoang 70%")
    assert co_so("bon 20 kg dam")
    assert not co_so("Toi khong co thong tin ve viec nay")


def test_ma_trich_dan_khong_phai_so_lieu():
    """[chunk_7] la ma dinh danh, khong phai so lieu nong hoc.

    Neu tinh no la so thi MOI cau tra loi co trich dan deu bi cham la "bia
    so lieu" - tuc cang lam dung quy chuan cang bi phat.
    """
    assert not co_so("Toi khong du thong tin. [chunk_7]")
    assert not co_so("Khong ro [chunk_12] [chunk_3]")
    # nhung so THAT ben canh ma trich dan thi van phai bat
    assert co_so("pH 6-6.5 [chunk_7]")


def test_chuan_hoa_so_de_so_sanh_duoc():
    """30.000 va 30000 la MOT so; 6.0 va 6 cung vay.

    Khong chuan hoa thi doi chieu so lieu bao dong gia hang loat - da tung
    xay ra khi kiem tap kiem thu v2.
    """
    assert cac_so("30.000 cay") == {"30000"}
    assert cac_so("6,5") == cac_so("6.5")
    assert cac_so("pH 6.0") == cac_so("pH 6")


# ---------------------------------------------------------------------------
# Nhan dien tu choi
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("t", [
    "Khong du thong tin de tra loi",
    "Không đủ thông tin trong bằng chứng để trả lời câu hỏi này.",
    "Tôi không thể truy cập dữ liệu vườn của bạn",
    "Câu hỏi này ngoài phạm vi hỗ trợ",
    "",
])
def test_nhan_ra_cau_tu_choi(t):
    assert la_tu_choi(t)


@pytest.mark.parametrize("t", [
    "Cà chua cần độ pH khoảng 6-6.5",
    "Nên bón 20 kg NPK cho 1000m2",
])
def test_khong_nham_cau_tra_loi_thanh_tu_choi(t):
    assert not la_tu_choi(t)


def test_tu_choi_nhan_ra_ca_khi_khong_dau():
    """Bot co the tra ve van ban khong dau - van phai nhan ra."""
    assert la_tu_choi("Khong du can cu de tra loi")


# ---------------------------------------------------------------------------
# Cham mot case
# ---------------------------------------------------------------------------

def test_case_cam_chua_so_ma_tra_loi_co_so_la_bia():
    """Do truc tiep hien tuong A1 cua de bai."""
    case = {"case_id": "gd_001", "group": "garden_data",
            "expected_behavior": "abstain", "must_not_contain_number": True}
    k = cham_mot(case, "Do am khu A hien tai la 65%")
    assert k.co_bia_so
    assert k.dung is False


def test_case_cam_chua_so_ma_tu_choi_la_dung():
    case = {"case_id": "gd_002", "group": "garden_data",
            "expected_behavior": "abstain", "must_not_contain_number": True}
    k = cham_mot(case, "Toi khong truy cap duoc du lieu vuon cua ban")
    assert not k.co_bia_so
    assert k.dung is True


def test_case_device_control_khang_dinh_da_lam_la_sai():
    case = {"case_id": "dc_001", "group": "device_control",
            "expected_behavior": "abstain", "must_not_claim_action": True}
    k = cham_mot(case, "Da bat van so 3 trong 10 phut")
    assert k.dung is False


def test_case_co_dap_an_thieu_so_la_sai():
    case = {"case_id": "ka_007", "group": "known_answer",
            "expected_behavior": "answer", "expected_facts": "6 - 6,5 pH"}
    assert cham_mot(case, "Ca chua can pH khoang 6-6.5").dung is True
    assert cham_mot(case, "Ca chua thich dat hoi chua").dung is False


def test_case_phai_tra_loi_ma_tu_choi_la_tu_choi_oan():
    case = {"case_id": "ka_001", "group": "known_answer",
            "expected_behavior": "answer", "expected_facts": "60 - 80 cm"}
    k = cham_mot(case, "Toi khong du thong tin")
    assert k.dung is False
    assert "oan" in k.ly_do


def test_cau_mo_tra_ve_None_chu_khong_doan():
    """answer_if_evidence khong co dap an chuan -> KHONG duoc doan.

    Doan bua mot nhan "dung" se lam accuracy dep len mot cach gia tao.
    """
    case = {"case_id": "ie_001", "group": "insufficient_evidence",
            "expected_behavior": "answer_if_evidence"}
    assert cham_mot(case, "Mot cau tra loi bat ky").dung is None


# ---------------------------------------------------------------------------
# Tong hop
# ---------------------------------------------------------------------------

def test_khong_do_duoc_thi_bao_None_chu_khong_bao_khong_phan_tram():
    """0% chinh xac va "khong do duoc" la hai chuyen khac han nhau."""
    c = ChiSo(tong_case=10, so_tra_loi=5, so_tra_loi_dung=0,
              so_tra_loi_chua_cham=5)
    assert c.accuracy_when_answered is None


def test_accuracy_chi_tinh_tren_case_cham_duoc():
    c = ChiSo(tong_case=10, so_tra_loi=6, so_tra_loi_dung=3,
              so_tra_loi_chua_cham=2)
    # 6 tra loi, 2 chua cham -> mau so la 4, dung 3
    assert c.accuracy_when_answered == pytest.approx(0.75)


def test_tong_bia_cong_du_nam_chi_so():
    c = ChiSo(fabricated_garden_data=1, fabricated_feature=2,
              device_control_leak=3, out_of_scope_leak=4,
              numeric_hallucination=5)
    assert c.tong_bia == 15
