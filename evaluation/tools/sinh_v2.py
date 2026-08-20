#!/usr/bin/env python3
"""
sinh_v2.py - Dung tap kiem thu v2 tu bang fact DA DUYET.

    python evaluation/tools/sinh_v2.py            # in ra, khong ghi
    python evaluation/tools/sinh_v2.py --ghi

VI SAO PHAI CO v2

v1 co 30 case known_answer, trong do CHIN case chua con so KHONG co trong van
ban goc. Vi du ka_008 ghi dap an "pH 5,5 - 6,5; EC 1,5 - 2,5 mS/cm" trong khi
tai lieu hcm_dost_ca_chua_bi khong chua mot con so nao trong so do.

Do la loi nghiem trong hon no ve ngoai: neu thuoc do co san so bia thi moi
phep do "ty le bia" deu vo nghia. He thong tra loi DUNG theo tai lieu se bi
cham la SAI, con he thong bia trung dap an bia se duoc cham la DUNG.

Quy chuan muc 24.5 va muc 29 da noi truoc dieu nay: dap an chuan phai do
NGUOI xac nhan, va cam dung LLM sinh ca cau hoi lan dap an roi dua thang vao
eval set. v1 vi pham dung dieu do.

CACH v2 KHAC v1

v1: dap an viet tay, tro toi tai lieu bang mot chuoi khong ai kiem
v2: dap an SINH THANG TU BANG fact, moi case truy nguoc duoc ve mot cau
    nguyen van ma nguoi duyet da xac nhan

Nghia la khong the bia duoc nua: neu bang fact khong co, case khong sinh ra.

DEC-023 VA VIEC GIU v1

Khong sua v1 tai cho. v1 duoc giu nguyen ven lam BANG CHUNG - no la vi du cu
the cho NextFarm thay vi sao quy chuan cam LLM sinh dap an, dung thu ma muc 6
cua de bai hoi. v1 cung chua tung dung de chay C0/C1/C2 nen khong co ket qua
do nao bi anh huong.
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

from app.core.db import ket_noi  # noqa: E402

V1 = BASE / "evaluation" / "datasets" / "v1"
V2 = BASE / "evaluation" / "datasets" / "v2"   # gan lai theo --version trong main()
PHIEN_BAN = "v2"

# Muoi nhom nay khong co van de gi - be nguyen tu v1 sang.
BE_NGUYEN = [
    "garden_data", "product_feature", "device_control", "out_of_scope",
    "adversarial", "no_diacritic", "typo", "local_terms", "high_risk",
    "insufficient_evidence",
]

# Ba nhom nay dung lai tu bang fact.
DUNG_LAI = ["known_answer", "paraphrase", "contradictory"]

TEN_CAY = {"lua": "lúa", "ca_chua": "cà chua", "dua_chuot": "dưa chuột"}

# Mau cau hoi theo chi so. Chi la CACH HOI - moi con so trong dap an deu den
# tu bang fact, khong co con so nao viet tay o day.
#
# KHONG CO MAU CHO thoi_vu, va do la co y. Moi cay co nhieu vu, moi vu mot
# khoang thang khac nhau, nhung truong `stage` ghi "thoi vu gieo trong" cho
# tat ca - khong tach duoc vu dong xuan voi vu he thu bang may. Sinh cau hoi
# "thoi vu trong dua chuot vao thang nao" se co hai dap an dung khac nhau
# (thang 4-7 va thang 8-11), tuc la mot cau hoi khong tra loi duoc.
#
# Nhom thoi_vu se co khi bang fact ghi duoc TEN VU vao `stage`.
MAU_HOI = {
    "ph": ["đất trồng {cay} cần độ pH bao nhiêu",
           "{cay} thích hợp với đất có pH khoảng bao nhiêu"],
    "do_am": ["độ ẩm đất cho {cay} nên duy trì bao nhiêu",
              "{cay} cần độ ẩm đất khoảng bao nhiêu là phù hợp"],
    "nhiet_do": ["nhiệt độ thích hợp cho {cay} là bao nhiêu",
                 "{cay} sinh trưởng tốt ở nhiệt độ nào"],
    "mat_do_gieo": ["mật độ gieo trồng {cay} là bao nhiêu",
                    "gieo {cay} với mật độ bao nhiêu là hợp lý"],
    "khoang_cach": ["khoảng cách trồng {cay} là bao nhiêu",
                    "{cay} nên trồng cách nhau bao nhiêu"],
    "luong_phan": ["bón phân cho {cay} với lượng bao nhiêu",
                   "lượng phân bón cho {cay} là bao nhiêu"],
    "nang_suat": ["năng suất {cay} đạt khoảng bao nhiêu",
                  "{cay} cho năng suất bao nhiêu"],
    "ec": ["EC phù hợp cho {cay} là bao nhiêu"],
}


def nap_fact() -> list[dict]:
    """Chi lay fact DA XAC NHAN va CO GIA TRI SO.

    Fact khong co gia tri so (vi du cau tieu de "Bon thuc lan 1" bi extract.py
    bat nham) khong dung lam dap an duoc - khong co gi de doi chieu.
    """
    with ket_noi() as c, c.cursor() as cur:
        cur.execute("""
            SELECT f.document_id, f.sentence_index, f.sentence, f.crop, f.metric,
                   f.value_min, f.value_max, f.unit, f.stage, f.high_risk,
                   d.url, s.publisher
            FROM fact f
            JOIN document d ON d.document_id = f.document_id
            LEFT JOIN source s ON s.source_id = d.source_id
            WHERE f.verified
              AND (f.value_min IS NOT NULL OR f.value_max IS NOT NULL)
            ORDER BY f.crop, f.metric, f.document_id, f.sentence_index
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def _so(v) -> str:
    """In so theo dung cach nguoi Viet doc, khong them bot chu so nao."""
    if v is None:
        return ""
    s = str(v)
    if s.endswith(".00"):
        s = s[:-3]
    elif "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def dap_an(f: dict) -> str:
    """Dap an chuan, ghep tu value_min / value_max / unit cua bang fact.

    Khong dien gia, khong lam tron, khong quy doi don vi (muc 27.3).
    """
    a, b, u = _so(f["value_min"]), _so(f["value_max"]), f["unit"] or ""
    if a and b and a != b:
        gt = a + " - " + b
    else:
        gt = a or b
    return (gt + " " + u).strip()


# Don vi hop le cho tung chi so. Dung de bat fact bi extract.py gan NHAN SAI.
#
# Nguoi duyet kiem so lieu co dung nguyen van khong - do la viec cua ho va ho
# lam dung. Nhung ho khong sua NHAN chi so, nen mot cau "duong kinh lo mang
# phu 12-15 cm" van mang nhan mat_do_gieo tu luc extract.py chay.
#
# Fact do KHONG sai: so dung, don vi dung, cau nguyen van dung. Chi co nhan
# la sai. Van de la sinh cau hoi TU NHAN se ra "mat do gieo trong dua chuot
# la bao nhieu" voi dap an "12-15 cm" - mot cau hoi vo nghia.
#
# Don vi la cach kiem nhan re nhat: mat do khong bao gio tinh bang cm, nang
# suat khong bao gio tinh bang %.
DON_VI_HOP_LE = {
    "ph": ["ph"],
    "do_am": ["%"],
    "nhiet_do": ["độ c", "oc", "°c"],
    "mat_do_gieo": ["cây", "kg", "hạt"],
    "khoang_cach": ["cm", "m"],
    "luong_phan": ["kg", "tấn", "g"],
    "nang_suat": ["tấn", "tạ", "kg"],
    "ec": ["ms"],
}

# Giai doan cho thay fact noi ve mot thu KHAC voi ten chi so, du don vi hop le.
# "nhiet do 30 do C" trong cau ve phan giai phan bon khong phai nhiet do sinh
# truong cua cay lua.
STAGE_LAC_DE = [
    "phân giải phân bón", "phát sinh bệnh", "phun thuốc", "ngưỡng mật độ",
    "thiệt hại", "chuẩn bị màng phủ", "làm đất", "xử lý đất chua",
]


def nhan_dung_khong(f: dict) -> bool:
    """Nhan chi so cua fact nay co dung voi noi dung cau khong."""
    u = (f.get("unit") or "").lower()
    if not any(h in u for h in DON_VI_HOP_LE.get(f["metric"], [])):
        return False
    st = (f.get("stage") or "").lower()
    return not any(x in st for x in STAGE_LAC_DE)


def _con_so(s) -> set[str]:
    """Moi con so trong chuoi, chuan hoa dau phan cach.

    30.000 va 30000 la MOT so; 6.5 va 6,5 la MOT so; nhung 6 va 6.0 cung
    phai coi la mot, neu khong thi kiem tra se bao dong gia.
    """
    ra: set[str] = set()
    for x in re.findall(r"\d[\d.,]*", str(s or "")):
        x = x.rstrip(".,")
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", x):      # 30.000 -> 30000
            x = re.sub(r"[.,]", "", x)
        else:
            x = x.replace(",", ".")
        try:
            ra.add(("%g" % float(x)))                        # 6.0 -> 6
        except ValueError:
            ra.add(x)
    return ra


def so_khong_truy_duoc(f: dict, dap_an_str: str) -> set[str]:
    """Con so xuat hien trong dap an nhung KHONG co trong nguon.

    VI SAO CAN HAM NAY

    Sinh case tu bang fact chan duoc viec BIA CA CAU TRA LOI, nhung khong tu
    dong chan duoc viec mot con so len tren dap an qua truong `unit` ma nguoi
    duyet go tay. Do la ca that:

        cau goc : "... lieu luong cho 1 lan bon: 4 kg Better NPK ... pha
                   loang vao nuoc de tuoi."
        unit go : "kg NPK/1000m2/10 ngay"

    Cau goc khong he neu dien tich. Chuoi "/1000m2" duoc suy tu cau LIEN KE
    noi ve san pham KHAC (Better KNO3 200g/16 lit nuoc/1000 m2) o giai doan
    KHAC. Suy dien nhu vay la dung mot phep noi suy de tao ra con so moi -
    dung thu ma quy chuan cam (muc 23.1, DEC-020).

    Neu de lot, dap an "4 kg NPK/1000m2/10 ngay" tro thanh GROUND TRUTH. Luc
    do he thong tra loi DUNG theo tai lieu se bi cham la SAI, va con so bao
    cao cho NextFarm se do nham chieu.

    Nguon hop le gom cau nguyen van VA truong value_min/value_max - hai
    truong do nguoi duyet chep tu chinh cau do nen van la trich dan.
    """
    nguon = _con_so(f["sentence"]) | _con_so(f.get("value_min"))         | _con_so(f.get("value_max"))
    return _con_so(dap_an_str) - nguon


def _lam_ro(f: dict) -> str:
    """Phan lam cho cau hoi tro nen DUY NHAT.

    Mot cay co nhieu fact cung chi so: ca chua co bon muc luong_phan khac
    nhau cho bon lan bon thuc. Neu bon case cung hoi "bon phan cho ca chua
    voi luong bao nhieu" ma bon dap an khac nhau thi de thi tu mau thuan -
    khong he thong nao tra loi dung duoc, va con so do duoc se la con so vo
    nghia.

    Phan lam ro lay tu `stage` cua chinh dong fact do, tuc van la thu nguoi
    duyet da ghi, khong phai thu sinh them.
    """
    st = (f.get("stage") or "").strip()
    if not st:
        return ""

    # stage chi noi lai chinh chi so thi khong lam ro them duoc gi:
    # "mat do gieo trong ca chua la bao nhieu MAT DO TRONG" chi dai ra.
    if st in ("bón phân", "thời vụ gieo trồng", "mật độ trồng", "trồng cây",
              "thời điểm và phương pháp bón", "bón lót và bón thúc"):
        return ""

    # stage la CUM DANH TU, khong noi thang vao cuoi cau duoc. Phai co tu noi,
    # va tu noi khac nhau tuy loai giai doan.
    if st.startswith(("trước khi", "sau khi", "khi ")):
        noi = ", "                       # "..., truoc khi ra hoa"
    elif st.startswith(("trồng ", "thu hoạch", "chăm sóc", "làm đất",
                        "chuẩn bị", "ngâm ủ", "xử lý", "phun ")):
        noi = " khi "                    # "... khi trong nha mang"
    else:
        noi = " ở giai đoạn "            # "... o giai doan bon thuc lan 1"
    return noi + st


def _cau_hoi_goc(f: dict, cay: str, mau: list[str]) -> str:
    """Cau hoi thanh pham. Deterministic theo chinh fact, khong theo thu tu."""
    i = (f["sentence_index"] + len(f["document_id"])) % len(mau)
    return mau[i].format(cay=cay) + _lam_ro(f)


def sinh_known_answer(facts: list[dict]) -> list[dict]:
    """Chi sinh case cho fact PHAN BIET DUOC voi cac fact khac cung nhom.

    Fact nao khong phan biet duoc (cung cay + chi so + stage voi mot fact
    khac nhung gia tri khac) thi BO QUA. Tha it case ma moi case tra loi
    duoc, con hon nhieu case ma mot nua khong the dung.
    """
    # Gom theo CAU HOI SE SINH RA, khong theo stage.
    #
    # stage la chu nguoi duyet go tay nen cung mot y co nhieu cach viet:
    # "trong cay" va "mat do trong" deu la khoang cach giua cac cay. Gom theo
    # stage thi hai fact do lot vao hai nhom khac nhau, roi ca hai cung sinh
    # ra cau hoi "khoang cach trong dua chuot la bao nhieu" voi hai dap an
    # khac nhau - de thi tu mau thuan voi chinh no.
    #
    # Gom theo cau hoi thanh pham la cach duy nhat chac chan: hai case khong
    # bao gio co the trung cau hoi ma khac dap an.
    nhom = defaultdict(list)
    for f in facts:
        mau = MAU_HOI.get(f["metric"])
        cay = TEN_CAY.get(f["crop"])
        if not mau or not cay or not nhan_dung_khong(f):
            continue
        nhom[_cau_hoi_goc(f, cay, mau)].append(f)

    ra: list[dict] = []
    bo_vi_so: list[tuple] = []
    da_sinh: set[str] = set()
    da_nguon: set[str] = set()
    i = 0
    for f in facts:
        mau = MAU_HOI.get(f["metric"])
        cay = TEN_CAY.get(f["crop"])
        if not mau or not cay:
            continue
        if not nhan_dung_khong(f):
            continue          # nhan chi so sai -> cau hoi sinh ra se vo nghia
        q = _cau_hoi_goc(f, cay, mau)
        cung = nhom[q]
        if len(cung) > 1 and len({dap_an(x) for x in cung}) > 1:
            continue          # trung cau hoi, khac dap an -> khong sinh case
        if q in da_sinh:
            continue          # da sinh case cho cau hoi nay roi
        nguon = f["document_id"] + "#" + str(f["sentence_index"])
        if nguon in da_nguon:
            continue          # cung mot fact hoi hai kieu -> do la paraphrase
        da = dap_an(f)
        lac = so_khong_truy_duoc(f, da)
        if lac:
            # Con so trong dap an khong co trong nguon -> khong sinh case.
            # Thua mot case con hon co mot dap an chuan bi sai.
            bo_vi_so.append((f["document_id"] + "#" + str(f["sentence_index"]),
                             da, sorted(lac)))
            continue
        da_sinh.add(q)
        da_nguon.add(nguon)
        i += 1
        c = {
            "case_id": "ka_" + str(len(ra) + 1).zfill(3),
            "question": q,
            "crop": f["crop"],
            "expected_behavior": "answer",
            "expected_facts": da,
            "source_of_truth": f["document_id"] + "#" + str(f["sentence_index"]),
        }
        if f["high_risk"]:
            c["must_have_caution"] = True
        c["note"] = ("Sinh tu fact da duyet. Nguyen van: "
                     + " ".join(f["sentence"].split())[:180])
        ra.append(c)

    if bo_vi_so:
        print()
        print("BO " + str(len(bo_vi_so)) + " case: dap an chua con so KHONG "
              "co trong nguon")
        for k, d, s in bo_vi_so:
            print("  " + k + "  dap an '" + d + "'  so la: " + ", ".join(s))
    return ra


# Cach dien dat lai - chi doi HINH THUC cau hoi, khong doi noi dung hoi.
DIEN_DAT_LAI = [
    ("bao nhiêu", "khoảng chừng nào"),
    ("thích hợp", "phù hợp"),
    ("nên", "cần"),
    ("là bao nhiêu", "ở mức nào"),
]


def sinh_paraphrase(ka: list[dict], moi_n: int = 3) -> list[dict]:
    """Dien dat lai cau hoi cua known_answer, GIU NGUYEN source_of_truth.

    Ky vong phai giong het case goc: nhom nay do "hoi cach khac co ra cung
    dap an khong", khong do kien thuc moi.
    """
    ra = []
    for i, c in enumerate(ka):
        if i % moi_n:
            continue
        q = c["question"]
        for tim, thay in DIEN_DAT_LAI:
            if tim in q:
                q = q.replace(tim, thay)
                break
        else:
            q = "cho hỏi " + q
        if q == c["question"]:
            continue
        ra.append({
            "case_id": "pa_" + str(len(ra) + 1).zfill(3),
            "derived_from": c["case_id"],
            "question": q,
            "crop": c["crop"],
            "expected_behavior": c["expected_behavior"],
            "expected_facts": c["expected_facts"],
            "source_of_truth": c["source_of_truth"],
            "note": ("Dien dat lai cua " + c["case_id"]
                     + ". Ky vong phai GIONG HET case goc."),
        })
    return ra


def tim_mau_thuan(facts: list[dict]) -> list[tuple[dict, dict]]:
    """Cap fact THAT SU mau thuan nhau.

    Bon dieu kien, va ca bon deu can:
      1. cung cay, cung chi so, CUNG DON VI
         (100 kg NPK/ha va 4 kg dam/sao khong so duoc voi nhau)
      2. ca hai co DU value_min va value_max
         (mot khoang mo "tu 25cm tro len" khong ket luan duoc gi)
      3. khac tai lieu
      4. cung GIAI DOAN - stage phai giong nhau
         (thoi vu dong xuan thang 10-11 va he thu thang 6-7 KHONG mau thuan,
          chung la hai vu khac nhau)

    Dieu kien 4 la thu de bo sot nhat, va bo sot no thi sinh ra mot nhom
    "mau thuan" toan mau thuan gia - tuc la lai bia, chi la bia mot kieu khac.
    """
    g = defaultdict(list)
    for f in facts:
        if f["value_min"] is None or f["value_max"] is None:
            continue
        g[(f["crop"], f["metric"], f["unit"], f["stage"])].append(f)

    ra = []
    for ds in g.values():
        for a, b in itertools.combinations(ds, 2):
            if a["document_id"] == b["document_id"]:
                continue
            if a["value_max"] < b["value_min"] or b["value_max"] < a["value_min"]:
                ra.append((a, b))
    return ra


def sinh_contradictory(facts: list[dict]) -> list[dict]:
    ra = []
    for a, b in tim_mau_thuan(facts):
        cay = TEN_CAY.get(a["crop"], a["crop"])
        mau = MAU_HOI.get(a["metric"], ["{cay} chỉ số này bao nhiêu"])[0]
        ra.append({
            "case_id": "ct_" + str(len(ra) + 1).zfill(3),
            "question": mau.format(cay=cay),
            "crop": a["crop"],
            "expected_behavior": "answer",
            "expected_facts": dap_an(a) + " HOẶC " + dap_an(b),
            "source_of_truth": a["document_id"] + "#" + str(a["sentence_index"]),
            "note": ("Hai nguon lech nhau, cung giai doan. Tra loi dung phai "
                     "neu CA HAI kem nguon, hoac ha muc tu tin - khong duoc "
                     "chon mot ben roi im lang. "
                     + a["document_id"] + ": " + dap_an(a) + " | "
                     + b["document_id"] + ": " + dap_an(b)),
        })
    return ra


DAU = {
    "known_answer": """# Nhóm known_answer — câu hỏi có đáp án đã được người xác nhận
#
# SINH THẲNG TỪ BẢNG fact, KHÔNG VIẾT TAY
#
# Mỗi case ở đây tương ứng đúng một dòng `fact` có `verified = true`. Đáp án
# (`expected_facts`) ghép từ `value_min` / `value_max` / `unit` của chính dòng
# đó, và `source_of_truth` trỏ tới `document_id#sentence_index` — truy ngược
# được về một câu nguyên văn mà người duyệt đã đọc và xác nhận.
#
# VÌ SAO PHẢI SINH CHỨ KHÔNG VIẾT
#
# Nhóm known_answer của v1 viết tay, và 9/30 case chứa con số KHÔNG có trong
# văn bản gốc. Ví dụ ka_008 của v1 ghi "pH 5,5 - 6,5; EC 1,5 - 2,5 mS/cm"
# trong khi tài liệu nguồn không chứa một con số nào trong số đó.
#
# Thước đo có sẵn số bịa thì mọi phép đo "tỷ lệ bịa" đều vô nghĩa: hệ thống
# trả lời đúng theo tài liệu bị chấm là SAI, hệ thống bịa trúng đáp án bịa
# được chấm là ĐÚNG.
#
# Sinh từ bảng fact làm việc bịa trở thành bất khả: không có fact thì không
# có case. Muốn thêm case thì phải duyệt thêm số liệu.
#
# Câu hỏi lấy từ mẫu cố định trong evaluation/tools/sinh_v2.py — mẫu chỉ quy
# định CÁCH HỎI, không chứa một con số nào.
""",
    "paraphrase": """# Nhóm paraphrase — cùng câu hỏi, cách diễn đạt khác
#
# Đo đúng một thứ: hỏi cách khác có ra cùng đáp án không. Kỳ vọng của mỗi
# case BẰNG ĐÚNG kỳ vọng của case known_answer gốc, và `source_of_truth`
# giữ nguyên — trường `derived_from` cho phép đối chiếu tự động.
#
# Phép diễn đạt lại chỉ đổi HÌNH THỨC câu hỏi ("bao nhiêu" → "khoảng chừng
# nào"), không đổi nội dung hỏi. Đổi nội dung thì không còn là paraphrase.
""",
    "contradictory": """# Nhóm contradictory — hai nguồn nói hai khoảng khác nhau
#
# ĐÁP ÁN ĐÚNG KHÔNG PHẢI LÀ CHỌN MỘT BÊN
#
# Khi hai Sở nói hai khoảng khác nhau cho cùng cây, cùng chỉ số, cùng giai
# đoạn, câu trả lời đúng là nêu CẢ HAI kèm nguồn, hoặc hạ mức tự tin. Chọn
# một bên rồi im lặng về bên kia là giấu thông tin người dùng cần biết.
#
# BỐN ĐIỀU KIỆN ĐỂ TÍNH LÀ MÂU THUẪN THẬT
#
#   1. cùng cây, cùng chỉ số, CÙNG ĐƠN VỊ
#   2. cả hai có đủ value_min và value_max
#   3. khác tài liệu
#   4. CÙNG GIAI ĐOẠN (stage)
#
# Điều kiện 4 dễ bỏ sót nhất. Bỏ nó thì "gieo tháng 10-11" (vụ đông xuân) và
# "gieo tháng 6-7" (vụ hè thu) bị tính là mâu thuẫn, trong khi hai tài liệu
# hoàn toàn đồng ý với nhau — chỉ là nói về hai vụ khác nhau.
#
# Sinh ra một nhóm "mâu thuẫn" toàn mâu thuẫn giả cũng là bịa, chỉ là bịa
# một kiểu khác.
""",
}


def ghi(ten: str, cases: list[dict]) -> None:
    V2.mkdir(parents=True, exist_ok=True)
    noi_dung = DAU.get(ten, "") + "\n" + yaml.safe_dump(
        {"group": ten, "version": PHIEN_BAN, "cases": cases},
        allow_unicode=True, sort_keys=False, width=100)
    (V2 / (ten + ".yaml")).write_text(noi_dung, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ghi", action="store_true")
    ap.add_argument("--version", default="v2",
                    help="Thu muc phien ban se ghi ra (DEC-023: khong sua "
                         "tai cho, tao phien ban moi)")
    a = ap.parse_args()

    global V2, PHIEN_BAN
    PHIEN_BAN = a.version
    V2 = BASE / "evaluation" / "datasets" / PHIEN_BAN
    print("Ghi ra phien ban:", PHIEN_BAN)

    facts = nap_fact()
    print("Fact da xac nhan, co gia tri so:", len(facts))

    ka = sinh_known_answer(facts)
    pa = sinh_paraphrase(ka)
    ct = sinh_contradictory(facts)

    print("\nSinh tu bang fact:")
    print("  known_answer  :", len(ka))
    print("  paraphrase    :", len(pa))
    print("  contradictory :", len(ct), "-> KHONG GHI")
    print()
    print("  Ba cap duoc danh dau mau thuan deu la MAU THUAN GIA: chung so")
    print("  thoi vu vu dong xuan (thang 10-11) voi vu he thu (thang 6-7).")
    print("  Hai tai lieu hoan toan dong y voi nhau, chi la noi ve hai vu")
    print("  khac nhau - truong `stage` ghi 'thoi vu gieo trong' cho ca hai")
    print("  nen khong tach duoc bang may.")
    print()
    print("  Sinh mot nhom 'mau thuan' toan mau thuan gia cung la bia, chi la")
    print("  bia mot kieu khac. Nhom nay se co khi bang fact ghi duoc TEN VU.")
    ct = []

    if a.ghi:
        for ten, ds in (("known_answer", ka), ("paraphrase", pa),
                        ("contradictory", ct)):
            if ds:
                ghi(ten, ds)
                print("  da ghi", ten + ".yaml")
        V2.mkdir(parents=True, exist_ok=True)
        for ten in BE_NGUYEN:
            src = V1 / (ten + ".yaml")
            t = src.read_text(encoding="utf-8").replace(
                "version: v1", "version: " + PHIEN_BAN)
            (V2 / (ten + ".yaml")).write_text(t, encoding="utf-8")
        print("  da be nguyen", len(BE_NGUYEN), "nhom tu v1")
    else:
        print("\n(chua ghi - them --ghi)")
        for c in ka[:5]:
            print("   " + c["case_id"] + ": " + c["question"])
            print("      -> " + c["expected_facts"] + "   [" + c["source_of_truth"] + "]")


if __name__ == "__main__":
    main()
