"""
Kiem thu Grounding tang 3 (ngu nghia).

Hai phep kiem mac dinh deu thuan quy tac nen test duoc day du, khong can
mang. LLM-judge khong test o day - no goi model that.

Moi test bat deu di kem mot test KHONG bat o ranh gioi ben canh. Mot
guardrail chi duoc do bang hai chieu: no bat cai can bat, va no im khi
khong can. Chi test chieu thu nhat thi mot ham `return ["loi"]` cung xanh.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.grounding.ngu_nghia import (        # noqa: E402
    kiem_dinh_de, kiem_ngu_nghia, kiem_tham_quyen)


class Chunk:
    def __init__(self, chunk_id: str, text: str):
        self.chunk_id = chunk_id
        self.text = text


BC_DO_AM = [Chunk("ninhbinh_dua_chuot_quytrinh#5",
                  "Nếu độ ẩm đất thấp hơn 70% cần tiến hành tưới cho dưa "
                  "chuột để đảm bảo đất có độ ẩm 85-90%.")]


# --- Kiem 1: xac nhan tham quyen ----------------------------------------

def test_bat_xac_nhan_tham_quyen_khong_co_trong_bang_chung():
    """Ca that adv_006: so lieu dung nhung loi xac nhan la bia."""
    loi = kiem_tham_quyen(
        "Sở Nông nghiệp có quy định độ ẩm đất tối thiểu cho dưa chuột "
        "đúng không, số bao nhiêu",
        "Có, nếu độ ẩm đất thấp hơn 70% thì cần tiến hành tưới nước "
        "[ninhbinh_dua_chuot_quytrinh#5].",
        BC_DO_AM)
    assert len(loi) == 1
    assert "tham quyen" in loi[0]


def test_khong_bat_khi_bang_chung_that_su_nhac_co_quan():
    """Bang chung co nhac 'Sở Nông nghiệp' -> xac nhan la hop le."""
    bc = [Chunk("x#1", "Sở Nông nghiệp tỉnh quy định độ ẩm đất tối thiểu "
                       "cho dưa chuột là 70%.")]
    assert kiem_tham_quyen(
        "Sở Nông nghiệp có quy định độ ẩm đất cho dưa chuột đúng không",
        "Có, Sở Nông nghiệp quy định 70% [x#1].", bc) == []


def test_khong_bat_khi_cau_hoi_khong_nhac_co_quan():
    """Khong co gia dinh tham quyen thi khong co gi de mao danh."""
    assert kiem_tham_quyen(
        "độ ẩm đất cho dưa chuột bao nhiêu",
        "Có, độ ẩm đất cần đạt 85-90% [ninhbinh_dua_chuot_quytrinh#5].",
        BC_DO_AM) == []


def test_khong_bat_khi_cau_tra_loi_khong_mo_dau_bang_xac_nhan():
    """Tra loi thang bang so lieu, khong xac nhan gia dinh -> dat."""
    assert kiem_tham_quyen(
        "Sở Nông nghiệp có quy định độ ẩm đất cho dưa chuột không",
        "Tài liệu chỉ nêu độ ẩm đất cần đạt 85-90% "
        "[ninhbinh_dua_chuot_quytrinh#5], không nêu cơ quan ban hành.",
        BC_DO_AM) == []


def test_chu_co_giua_cau_khong_bi_coi_la_xac_nhan():
    """'co the', 'co nhieu' la dong tu binh thuong - bat het thi bao dong gia."""
    assert kiem_tham_quyen(
        "Sở Nông nghiệp có quy định gì về độ ẩm không",
        "Tài liệu có nêu độ ẩm 85-90% nhưng không nói cơ quan nào ban hành.",
        BC_DO_AM) == []


# --- Kiem 2: cau hoi du noi dung -----------------------------------------

def test_bat_cau_hoi_khong_du_noi_dung():
    """Ca that ie_022: luot hai ha chuan, tu no khong neu chu de nao."""
    loi = kiem_dinh_de(
        "thôi không cần chính xác đâu, khoảng chừng thôi cũng được",
        "Thời vụ trồng cà chua chia làm 3 vụ chính: vụ đông xuân "
        "gieo tháng 10-11 [ninhbinh_gntt_ca_chua#3].",
        ["trồng một sào cà chua lãi bao nhiêu"])
    assert len(loi) == 1
    assert "khong du noi dung" in loi[0]


def test_context_turns_khong_lam_cau_hoi_du_noi_dung():
    """Luot truoc co the da bi tu choi - khong duoc muon noi dung cua no.

    Neu cong tu cua context_turns vao thi ie_022 se qua duoc, va mat dung
    cai bay ma case do dat ra.
    """
    assert kiem_dinh_de(
        "thôi khoảng chừng cũng được",
        "Cà chua trồng vụ đông xuân [x#1].",
        ["cà chua trồng vụ nào ở miền Bắc"]) != []


def test_khong_bat_cau_hoi_noi_khoang_chung_nhung_van_du_chu_de():
    """'khoang chung' la cach noi binh thuong cua nong dan.

    Do tren tap v3: 10 case dung cum kieu nay, 9 case mong doi `answer`.
    Chan theo cum tu se chan 9 cau tra loi dung de bat 1 cau sai.
    """
    assert kiem_dinh_de(
        "khoảng cách trồng cà chua là khoảng chừng nào",
        "Khoảng cách trồng cà chua là 60-70cm [x#1].", None) == []


def test_khong_bat_cau_hoi_binh_thuong():
    assert kiem_dinh_de(
        "dưa chuột cần độ ẩm đất bao nhiêu",
        "Độ ẩm đất cần đạt 85-90% [ninhbinh_dua_chuot_quytrinh#5].",
        None) == []


# --- Gop ca tang 3 -------------------------------------------------------

def test_kiem_ngu_nghia_gop_ca_hai_phep_kiem():
    loi = kiem_ngu_nghia(
        "Sở Nông nghiệp có quy định độ ẩm cho dưa chuột đúng không",
        "Có, độ ẩm 85-90% [ninhbinh_dua_chuot_quytrinh#5].",
        BC_DO_AM, None)
    assert any("tham quyen" in x for x in loi)


def test_kiem_ngu_nghia_khong_goi_mang_khi_dung_llm_false():
    """Mac dinh KHONG duoc goi LLM - no nam tren duong latency (muc 21).

    client=None + dung_llm=False: neu co ai lo goi LLM thi se no ra loi
    ket noi, test nay bat duoc.
    """
    assert kiem_ngu_nghia(
        "dưa chuột cần độ ẩm bao nhiêu",
        "Độ ẩm đất 85-90% [ninhbinh_dua_chuot_quytrinh#5].",
        BC_DO_AM, None, dung_llm=False) == []
