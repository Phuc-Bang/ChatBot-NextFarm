#!/usr/bin/env python3
"""
sinh_bien_the.py - Sinh nhom no_diacritic va typo tu cac case da co.

    python evaluation/tools/sinh_bien_the.py --xem       # in ra, khong ghi
    python evaluation/tools/sinh_bien_the.py --ghi

VI SAO SINH TU CASE DA CO CHU KHONG VIET MOI

Hai nhom nay khong do "bot co biet cau tra loi khong". Chung do MOT thu duy
nhat: HANH VI CO GIU NGUYEN khi cau hoi bi lam bien dang khong.

    "Độ ẩm đất khu A giờ bao nhiêu?"  -> phai tu choi (garden_data)
    "Do am dat khu A gio bao nhieu?"  -> van phai tu choi, y het
    "Do am dat khu A gio bao nhieuu?" -> van phai tu choi, y het

Vi vay ky vong cua case bien the phai BANG DUNG ky vong cua case goc. Viet
tay lai se lam trooi ky vong mot cach vo tinh, va khi do khong con biet
"khac nhau" den tu bien dang hay den tu cach dat cau hoi.

Truong `note` cua moi case ghi ro case goc, de doc lai duoc.

DAY LA CONG CU, KHONG PHAI NGUON SU THAT

Quy chuan muc 29 doi cac case sinh bang script phai duoc SOAT TAY tung cau
truoc khi dong bang. Script chi lam phan co khi; nguoi doc lai xem cau sinh
ra co phai kieu go that cua nguoi Viet khong.

Cac phep bien doi deu deterministic (khong dung random khong seed), nen chay
lai hai lan ra ket qua giong het nhau - dieu kien de soat tay co y nghia.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

from app.core.text import bo_dau, co_dau  # noqa: E402

DATASET = BASE / "evaluation" / "datasets" / "v1"

# Case goc duoc chon tay de phu deu cac nhom, khong lay may moc theo thu tu.
NGUON_KHONG_DAU = [
    "gd_001", "gd_002", "gd_003", "gd_004", "gd_006", "gd_008", "gd_012",
    "gd_017", "gd_020",
    "pf_001", "pf_003", "pf_005", "pf_007", "pf_009", "pf_012",
    "dc_001", "dc_004", "dc_007", "dc_009", "dc_012",
    "oos_001", "oos_003", "oos_006", "oos_010", "oos_013", "oos_018",
    "adv_001", "adv_004", "adv_009",
]

NGUON_TYPO = [
    "gd_001", "gd_003", "gd_005", "gd_009", "gd_018", "gd_019", "gd_022",
    "pf_002", "pf_004", "pf_008", "pf_014", "pf_016",
    "dc_002", "dc_006", "dc_010", "dc_013",
    "oos_002", "oos_005", "oos_012", "oos_016", "oos_019", "oos_021",
    "adv_003", "adv_007", "adv_012",
]


# ----------------------------------------------------------------------
# Phep bien doi
# ----------------------------------------------------------------------
def khong_dau(s: str) -> str:
    """Bo dau bang DUNG ham ma he thong dung, khong viet ban thu hai.

    Neu cong cu sinh de thi bo dau kieu khac voi tang chuan hoa, de thi se do
    mot thu ma he thong khong bao gio gap.
    """
    return bo_dau(s)


# Bon kieu go sai hay gap khi go tieng Viet tren dien thoai. Moi kieu deu
# deterministic: chon vi tri theo do dai tu, khong dung random.
def _lap_chu_cuoi(tu: str) -> str:
    """"nhieu" -> "nhieuu". Go tren dien thoai bi giu phim."""
    return tu + tu[-1] if len(tu) >= 3 else tu


def _thieu_mot_chu(tu: str) -> str:
    """"khong" -> "khng". Bo chu nguyen am o giua."""
    if len(tu) < 4:
        return tu
    i = len(tu) // 2
    return tu[:i] + tu[i + 1:]


def _doi_cho_hai_chu(tu: str) -> str:
    """"chua" -> "cuha". Go nhanh nen dao thu tu."""
    if len(tu) < 4:
        return tu
    i = len(tu) // 2
    return tu[:i - 1] + tu[i] + tu[i - 1] + tu[i + 1:]


# Am tiet tieng Viet chi dai toi da 7 chu cai khi da bo dau ("nghieng"), va
# chi dung bang chu cai duoi day. "nextfarm", "vietgap", "excel" khong phai
# am tiet tieng Viet nen khong ai go telex cho chung.
CHU_CAI_VIET = set("abcdefghiklmnopqrstuvxy")


def _la_am_tiet_viet(tu: str) -> bool:
    return 2 <= len(tu) <= 7 and all(c in CHU_CAI_VIET for c in tu)


def _sot_telex(tu: str) -> str:
    """"dung" -> "dungf". Go telex nhung dau khong an, con lai ky tu dieu khien.

    Day la kieu sai rieng cua tieng Viet, khong co trong tieng Anh: nguoi go
    "af" de ra "a", he thong khong nhan, con lai chu "f" tho.

    Chi ap cho am tiet tieng Viet. "nextfarmf" khong phai loi go co that -
    khong ai go telex cho mot ten rieng tieng Anh.
    """
    return tu + "f" if _la_am_tiet_viet(tu) else tu


KIEU_SAI = [_lap_chu_cuoi, _thieu_mot_chu, _doi_cho_hai_chu, _sot_telex]


def chen_loi(s: str, thu_tu: int) -> str:
    """Chen dung MOT loi vao mot tu dai nhat cua cau.

    Mot loi moi cau, khong phai nhieu: cau hoi that hiem khi sai ba cho cung
    luc, va sai nhieu qua thi de thi do mot thu khac han - do la kha nang doc
    van ban hong, khong phai chiu loi go.
    """
    kd = bo_dau(s)
    tu = kd.split()
    if not tu:
        return kd

    kieu = KIEU_SAI[thu_tu % len(KIEU_SAI)]

    # Chon tu dai nhat, va chi xet tu KHONG dinh dau cau: chen loi vao
    # "khong?" se ra "khong?f" - khong ai go nhu vay. Dau cau nam ngoai vung
    # go sai.
    ung_vien = [j for j, t in enumerate(tu) if t.isalpha()]
    if not ung_vien:
        return kd
    ung_vien.sort(key=lambda j: (-len(tu[j]), j))

    # Kieu duoc chon co the khong ap duoc vao cau nao (vi du _thieu_mot_chu
    # doi tu tu 4 chu tro len, ma ca cau toan tu 3 chu). Khi do phai doi kieu
    # khac chu khong duoc tra ve cau NGUYEN VEN - mot case "typo" khong co
    # loi go nao la mot case do nham nhom.
    thu_tu_kieu = [kieu] + [k for k in KIEU_SAI if k is not kieu]
    for k in thu_tu_kieu:
        for j in ung_vien:
            moi = k(tu[j])
            if moi != tu[j]:
                tu[j] = moi
                return " ".join(tu)
    raise ValueError("khong chen duoc loi go nao vao: " + kd)


# ----------------------------------------------------------------------
def nap_tat_ca() -> dict[str, dict]:
    ra = {}
    for f in sorted(DATASET.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in data.get("cases") or []:
            c["_group"] = data.get("group", f.stem)
            ra[c["case_id"]] = c
    return ra


def sinh(nguon: list[str], tien_to: str, bien_doi, tat_ca: dict) -> list[dict]:
    ra = []
    n = 0
    for thu_tu, cid in enumerate(nguon, start=1):
        goc = tat_ca.get(cid)
        if goc is None:
            print("  BO QUA: khong tim thay case goc " + cid, file=sys.stderr)
            continue
        if not co_dau(goc["question"]):
            print("  BO QUA: " + cid + " von da khong dau", file=sys.stderr)
            continue

        n += 1
        moi = {
            "case_id": tien_to + "_" + str(n).zfill(3),
            "derived_from": cid,
            "question": bien_doi(goc["question"], thu_tu),
            "expected_behavior": goc["expected_behavior"],
        }
        if goc.get("context_turns"):
            moi["context_turns"] = [bien_doi(t, thu_tu) for t in goc["context_turns"]]
        if goc.get("expected_abstain_type"):
            moi["expected_abstain_type"] = goc["expected_abstain_type"]
        if goc.get("must_not_contain_number") is not None:
            moi["must_not_contain_number"] = goc["must_not_contain_number"]
        moi["note"] = ("Bien the cua " + cid + " (" + goc["_group"] + "). "
                       "Cau goc: " + goc["question"])
        ra.append(moi)
    return ra


DAU_FILE = {
    "no_diacritic": """# Nhóm no_diacritic — câu hỏi gõ không dấu
#
# ĐO CÁI GÌ
#
# Nhóm này KHÔNG đo "bot có biết câu trả lời không". Nó đo đúng một thứ:
# HÀNH VI CÓ GIỮ NGUYÊN khi người dùng gõ không dấu hay không.
#
# Kỳ vọng của mỗi case ở đây BẰNG ĐÚNG kỳ vọng của case gốc. Lệch một case
# nghĩa là bỏ dấu đã làm hệ thống đổi hành vi — và đó là lỗi cần sửa, không
# phải giới hạn cần chấp nhận.
#
# VÌ SAO NHÓM NÀY QUAN TRỌNG HƠN VẺ NGOÀI CỦA NÓ
#
# Toàn bộ tầng từ chối (Intent Router, Scope Check) khớp từ khoá trên bản bỏ
# dấu. DEC-031 (§13.4) đo được rằng bỏ dấu làm sập khớp trọn từ: "bật" và
# "bắt", "giờ" và "gió", "van" và "vẫn" thành cùng một chuỗi. Câu hỏi có dấu
# còn cứu được bằng cách khớp trên bản có dấu; câu hỏi không dấu thì không.
#
# Nghĩa là nhóm này chạy đúng vào đường rủi ro cao nhất của kiến trúc hiện
# tại. Nó là bộ đo trực tiếp của DEC-031.
#
# CÁCH SINH
#
# Sinh bằng evaluation/tools/sinh_bien_the.py từ các case đã có, rồi SOÁT TAY
# từng câu (§29). Bỏ dấu bằng đúng hàm app/core/text.py::bo_dau mà hệ thống
# dùng — viết bản bỏ dấu thứ hai sẽ làm đề thi đo một thứ hệ thống không gặp.
""",
    "typo": """# Nhóm typo — câu hỏi có lỗi gõ
#
# ĐO CÁI GÌ
#
# Giống no_diacritic: đo HÀNH VI CÓ GIỮ NGUYÊN khi câu hỏi có lỗi gõ hay
# không. Kỳ vọng mỗi case bằng đúng kỳ vọng case gốc.
#
# XỬ LÝ LỖI CHÍNH TẢ Ở ĐÂU
#
# §13.2 lớp 3 chốt rõ: xử lý ở tầng retrieval bằng pg_trgm, KHÔNG bằng cách
# bảo LLM "đoán xem người dùng định viết gì". Đoán là đường bịa đi thẳng vào
# lớp hiểu câu hỏi — câu "bon dam cho lua bao nhieu" có thể bị viết lại thành
# "bón đạm cho lúa giai đoạn đẻ nhánh bao nhiêu kg/ha", và từ đó mọi thứ phía
# sau đều lệch mà không ai biết.
#
# Nhóm này vì vậy cũng là bộ đo gián tiếp cho ràng buộc đó.
#
# BỐN KIỂU GÕ SAI
#
#   lặp chữ cuối    nhieu  -> nhieuu     giữ phím trên điện thoại
#   thiếu một chữ   khong  -> khng       gõ nhanh, sót nguyên âm
#   đổi chỗ hai chữ chua   -> cuha       gõ nhanh, đảo thứ tự
#   sót telex       ca     -> caf        gõ telex nhưng dấu không ăn
#
# Kiểu thứ tư là lỗi riêng của tiếng Việt, không có trong tiếng Anh.
#
# MỘT LỖI MỖI CÂU, không phải nhiều: câu hỏi thật hiếm khi sai ba chỗ cùng
# lúc, và sai nhiều quá thì đề thi đo một thứ khác hẳn — khả năng đọc văn bản
# hỏng, chứ không phải chịu lỗi gõ.
""",
}


def ghi(ten: str, cases: list[dict]) -> None:
    f = DATASET / (ten + ".yaml")
    noi_dung = DAU_FILE[ten] + "\n" + yaml.safe_dump(
        {"group": ten, "version": "v1", "cases": cases},
        allow_unicode=True, sort_keys=False, width=100)
    f.write_text(noi_dung, encoding="utf-8")
    print("Da ghi " + str(f) + " (" + str(len(cases)) + " case)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ghi", action="store_true")
    a = ap.parse_args()

    tat_ca = nap_tat_ca()
    nd = sinh(NGUON_KHONG_DAU, "nd", lambda s, n: khong_dau(s), tat_ca)
    tp = sinh(NGUON_TYPO, "tp", chen_loi, tat_ca)

    for ten, ds in (("no_diacritic", nd), ("typo", tp)):
        print("\n=== " + ten + " (" + str(len(ds)) + " case) ===")
        for c in ds:
            print("  " + c["case_id"] + ": " + c["question"])
        if a.ghi:
            ghi(ten, ds)

    if not a.ghi:
        print("\n(chua ghi - them --ghi de ghi file)")


if __name__ == "__main__":
    main()
