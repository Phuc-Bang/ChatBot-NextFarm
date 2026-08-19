"""
Hang rao ky thuat cho DEC-023: tap kiem thu khong duoc sua sau khi dong bang.

Quy chuan v2.0 muc 28: neu vua sua he thong vua sua de thi thi moi con so
"cai thien" deu vo nghia. Loi hua trong tai lieu la khong du - phai co test
lam cho viec sua len bi phat hien ngay.

Test o day chia hai loai:
  - Luoc do: luon chay, bat loi ngay khi viet case moi
  - Hash   : chi chay khi da co manifest.json (tuc la da dong bang)
"""

import json
from pathlib import Path

import pytest
import yaml

import freeze

VERSION = "v1"
VDIR = freeze.DATASETS / VERSION
MANIFEST = VDIR / "manifest.json"


def files():
    return freeze.thu_thap(VDIR)


# ----------------------------------------------------------------------
# Luoc do
# ----------------------------------------------------------------------
def test_co_file_nhom():
    assert files(), "khong tim thay file nhom nao trong " + str(VDIR)


def test_luoc_do_hop_le():
    da_thay: dict[str, str] = {}
    loi = []
    for f in files():
        loi.extend(freeze.kiem_tra_file(f, da_thay))
    assert not loi, "Tap kiem thu sai luoc do:\n  " + "\n  ".join(loi)


def test_case_id_khong_trung():
    """Trung case_id se lam ket qua eval bi ghi de len nhau ma khong bao loi."""
    thay: dict[str, str] = {}
    for f in files():
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        for c in data["cases"]:
            cid = c["case_id"]
            assert cid not in thay, (
                "case_id trung: " + cid + " o " + f.name + " va " + thay[cid])
            thay[cid] = f.name


def test_ba_nhom_do_hien_tuong_A1_A2_phai_ton_tai():
    """Ba nhom nay do truc tiep hai hien tuong de bai neu.

    Khong co chung thi khong co so lieu chung minh cho 2 trong 4 hien tuong,
    va do chinh la lo hong cua spec v1.0.
    """
    ten = {f.stem for f in files()}
    for nhom in ("garden_data", "product_feature", "device_control"):
        assert nhom in ten, "thieu nhom bat buoc: " + nhom


def test_moi_case_abstain_deu_ghi_ro_ly_do():
    """Tu choi dung nhung noi sai ly do van la trai nghiem te (muc 30.5)."""
    for f in files():
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        for c in data["cases"]:
            if c["expected_behavior"] == "abstain":
                assert c.get("expected_abstain_type") in freeze.LY_DO_TU_CHOI, (
                    f.name + " / " + c["case_id"] + ": abstain thieu ly do hop le")


def test_nhom_garden_data_cam_chua_so():
    """Bot tra loi mot con so cho cau hoi so lieu vuon = bia so lieu vuon.

    Ngoai le duy nhat la case nguoi dung TU cung cap so, khi do viec nhac lai
    nguong tham khao co nguon la hop le.
    """
    data = yaml.safe_load((VDIR / "garden_data.yaml").read_text(encoding="utf-8"))
    cam = [c for c in data["cases"] if c.get("must_not_contain_number")]
    assert len(cam) >= len(data["cases"]) - 2, (
        "gan nhu moi case garden_data phai dat must_not_contain_number")


def test_co_case_hoi_tiep_noi_chuyen_ngu_canh():
    """Bay kho nhat: lượt truoc la nong hoc, lượt sau la so lieu vuon.

    Day chinh la lo hong ma Scope Check theo cay trong cua v1.0 cho lot.
    """
    data = yaml.safe_load((VDIR / "garden_data.yaml").read_text(encoding="utf-8"))
    co_ngu_canh = [c for c in data["cases"] if c.get("context_turns")]
    assert len(co_ngu_canh) >= 3, "can it nhat 3 case hoi tiep noi trong garden_data"


def test_nhom_device_control_cam_khang_dinh_da_thuc_hien():
    """Loi nguy hiem nhat cua nhom nay la bia MOT HANH DONG DA XAY RA."""
    data = yaml.safe_load((VDIR / "device_control.yaml").read_text(encoding="utf-8"))
    for c in data["cases"]:
        assert c.get("must_not_claim_action") is True, (
            c["case_id"] + ": thieu must_not_claim_action")


# ----------------------------------------------------------------------
# Dong bang
# ----------------------------------------------------------------------
@pytest.mark.skipif(not MANIFEST.exists(),
                    reason="tap kiem thu chua dong bang (chua co manifest.json)")
def test_hash_khop_manifest():
    """Sua file sau khi dong bang -> test nay do."""
    cu = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hien_tai = {f.name: freeze.bam_file(f) for f in files()}

    thieu = set(cu["files"]) - set(hien_tai)
    assert not thieu, "file da bi xoa sau khi dong bang: " + ", ".join(sorted(thieu))

    them = set(hien_tai) - set(cu["files"])
    assert not them, (
        "file moi duoc them vao phien ban da dong bang: " + ", ".join(sorted(them))
        + "\nMuon them case -> tao thu muc phien ban moi, khong sua tai cho.")

    khac = [n for n, h in hien_tai.items() if cu["files"].get(n) != h]
    assert not khac, (
        "file da bi sua sau khi dong bang: " + ", ".join(sorted(khac))
        + "\nMuon doi -> tao phien ban moi va chay lai toan bo cau hinh cu.")


@pytest.mark.skipif(not MANIFEST.exists(), reason="chua dong bang")
def test_so_case_khop_manifest():
    cu = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tong = sum(len(yaml.safe_load(f.read_text(encoding="utf-8"))["cases"])
               for f in files())
    assert tong == cu["total_cases"]
