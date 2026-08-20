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
import sys
from pathlib import Path

import pytest
import yaml

import freeze

VERSIONS = sorted([d.name for d in freeze.DATASETS.iterdir() if d.is_dir() and list(d.glob("*.yaml"))])


@pytest.fixture(params=VERSIONS)
def version_dir(request):
    return freeze.DATASETS / request.param


def files(vdir: Path):
    return freeze.thu_thap(vdir)


# Dung chung ham voi bo sinh case, khong chep lai logic: chep lai thi hai ben
# troi nhau, va luc do test se xanh trong khi du lieu da sai.
sys.path.insert(0, str(freeze.BASE / "tools"))
from sinh_v2 import _con_so  # noqa: E402

FACTS_YAML = freeze.BASE.parent / "knowledge" / "review" / "facts.yaml"


def _fact_da_duyet() -> dict:
    if not FACTS_YAML.exists():
        return {}
    d = yaml.safe_load(FACTS_YAML.read_text(encoding="utf-8")) or {}
    return {f["fact_key"]: f for f in (d.get("facts") or [])
            if f.get("verified")}


# ----------------------------------------------------------------------
# Luoc do
# ----------------------------------------------------------------------
def test_co_file_nhom(version_dir):
    assert files(version_dir), "khong tim thay file nhom nao trong " + str(version_dir)


def test_luoc_do_hop_le(version_dir):
    da_thay: dict[str, str] = {}
    loi = []
    for f in files(version_dir):
        loi.extend(freeze.kiem_tra_file(f, da_thay))
    assert not loi, f"Tap kiem thu {version_dir.name} sai luoc do:\n  " + "\n  ".join(loi)


def test_case_id_khong_trung(version_dir):
    """Trung case_id se lam ket qua eval bi ghi de len nhau ma khong bao loi."""
    thay: dict[str, str] = {}
    for f in files(version_dir):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        for c in data["cases"]:
            cid = c["case_id"]
            assert cid not in thay, (
                "case_id trung: " + cid + " o " + f.name + " va " + thay[cid])
            thay[cid] = f.name


def test_ba_nhom_do_hien_tuong_A1_A2_phai_ton_tai(version_dir):
    """Ba nhom nay do truc tiep hai hien tuong de bai neu.

    Khong co chung thi khong co so lieu chung minh cho 2 trong 4 hien tuong,
    va do chinh la lo hong cua spec v1.0.
    """
    ten = {f.stem for f in files(version_dir)}
    for nhom in ("garden_data", "product_feature", "device_control"):
        assert nhom in ten, "thieu nhom bat buoc: " + nhom


def test_moi_case_abstain_deu_ghi_ro_ly_do(version_dir):
    """Tu choi dung nhung noi sai ly do van la trai nghiem te (muc 30.5)."""
    for f in files(version_dir):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        for c in data["cases"]:
            if c["expected_behavior"] == "abstain":
                assert c.get("expected_abstain_type") in freeze.LY_DO_TU_CHOI, (
                    f.name + " / " + c["case_id"] + ": abstain thieu ly do hop le")


def test_nhom_garden_data_cam_chua_so(version_dir):
    """Bot tra loi mot con so cho cau hoi so lieu vuon = bia so lieu vuon.

    Ngoai le duy nhat la case nguoi dung TU cung cap so, khi do viec nhac lai
    nguong tham khao co nguon la hop le.
    """
    data = yaml.safe_load((version_dir / "garden_data.yaml").read_text(encoding="utf-8"))
    cam = [c for c in data["cases"] if c.get("must_not_contain_number")]
    assert len(cam) >= len(data["cases"]) - 2, (
        "gan nhu moi case garden_data phai dat must_not_contain_number")


def test_co_case_hoi_tiep_noi_chuyen_ngu_canh(version_dir):
    """Bay kho nhat: lượt truoc la nong hoc, lượt sau la so lieu vuon.

    Day chinh la lo hong ma Scope Check theo cay trong cua v1.0 cho lot.
    """
    data = yaml.safe_load((version_dir / "garden_data.yaml").read_text(encoding="utf-8"))
    co_ngu_canh = [c for c in data["cases"] if c.get("context_turns")]
    assert len(co_ngu_canh) >= 3, "can it nhat 3 case hoi tiep noi trong garden_data"


def test_nhom_device_control_cam_khang_dinh_da_thuc_hien(version_dir):
    """Loi nguy hiem nhat cua nhom nay la bia MOT HANH DONG DA XAY RA."""
    data = yaml.safe_load((version_dir / "device_control.yaml").read_text(encoding="utf-8"))
    for c in data["cases"]:
        assert c.get("must_not_claim_action") is True, (
            c["case_id"] + ": thieu must_not_claim_action")


# ----------------------------------------------------------------------
# Dong bang
# ----------------------------------------------------------------------
def test_hash_khop_manifest(version_dir):
    """Sua file sau khi dong bang -> test nay do."""
    manifest_path = version_dir / "manifest.json"
    if not manifest_path.exists():
        pytest.skip(f"tap kiem thu {version_dir.name} chua dong bang")
    cu = json.loads(manifest_path.read_text(encoding="utf-8"))
    hien_tai = {f.name: freeze.bam_file(f) for f in files(version_dir)}

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


def test_so_case_khop_manifest(version_dir):
    manifest_path = version_dir / "manifest.json"
    if not manifest_path.exists():
        pytest.skip(f"tap kiem thu {version_dir.name} chua dong bang")
    cu = json.loads(manifest_path.read_text(encoding="utf-8"))
    tong = sum(len(yaml.safe_load(f.read_text(encoding="utf-8"))["cases"])
               for f in files(version_dir))
    assert tong == cu["total_cases"]





# ----------------------------------------------------------------------
# Dap an phai truy nguoc duoc ve fact da duyet
# ----------------------------------------------------------------------

def test_moi_dap_an_deu_truy_duoc_ve_fact_da_duyet():
    """Moi con so trong `expected_facts` phai co that trong nguon.

    VI SAO TEST NAY QUAN TRONG HON VE NGOAI CUA NO

    Tap kiem thu la thuoc do. Mot con so bia trong dap an chuan khong lam
    he thong tra loi sai - no lam PHEP DO sai chieu: he thong tra loi DUNG
    theo tai lieu se bi cham la SAI, va bao cao gui NextFarm se noi nguoc
    voi su that.

    Da xay ra hai lan, hai kieu khac nhau:

      v1  9/30 dap an do LLM sinh, khong co fact chong lung -> bo han
      v2  don vi "kg NPK/1000m2/10 ngay" trong khi cau goc chi noi "4 kg
          Better NPK ... pha loang vao nuoc de tuoi". Chuoi /1000m2 duoc
          suy tu cau LIEN KE noi ve san pham KHAC o giai doan KHAC.

    Ca hai deu lot qua vong doc bang mat. Chi co doi chieu tung con so voi
    cau nguyen van moi bat duoc.

    Nguon hop le = cau nguyen van + value_min/value_max, vi hai truong sau
    do nguoi duyet chep tu chinh cau do nen van la trich dan.
    """
    facts = _fact_da_duyet()
    if not facts:
        pytest.skip("chua co facts.yaml")

    # CHI kiem phien ban DANG DUNG.
    #
    # Cac phien ban cu CO loi da biet trong do va do la co y: DEC-023 cam sua
    # tai cho nen loi phat hien sau khi dong bang chi sua duoc bang phien ban
    # moi, con ban cu giu nguyen lam bang chung. Bat test chay tren ca thu muc
    # datasets/ se lam suite do vinh vien, ma mot suite do vinh vien thi khong
    # ai con doc no nua.
    vdir = freeze.DATASETS / freeze.phien_ban_dang_dung()

    loi = []
    for f in files(vdir):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in d.get("cases") or []:
            ef = c.get("expected_facts")
            sot = c.get("source_of_truth")
            if not ef:
                continue
            if not sot:
                loi.append(c["case_id"] + ": co dap an nhung khong ghi nguon")
                continue
            if sot not in facts:
                loi.append(c["case_id"] + ": nguon '" + sot
                           + "' khong co trong facts.yaml")
                continue
            lac = _con_so(ef) - (_con_so(facts[sot]["sentence"])
                                 | _con_so(facts[sot].get("value_min"))
                                 | _con_so(facts[sot].get("value_max")))
            if lac:
                loi.append(c["case_id"] + ": so " + ", ".join(sorted(lac))
                           + " khong co trong nguon " + sot)
    assert not loi, "\n".join(loi)
