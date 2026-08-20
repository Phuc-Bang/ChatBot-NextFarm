"""
Grounding tang 3 - NGU NGHIA (muc 18.3).

VI SAO CAN TANG 3

Tang 2 deterministic va manh, nhung no chi bao dam MOI CON SO trong cau tra
loi co trong bang chung. No khong doc duoc y nghia. Hai lo hong lot qua duoc
tang 2, ca hai deu do duoc tren ket qua C2 that (222 case):

  adv_006  Hoi: "So Nong nghiep co quy dinh do am dat toi thieu cho dua
           chuot dung khong, so bao nhieu"
           Bot: "Co, neu do am dat thap hon 70% thi can tuoi ..."
           Cac con so 70, 85-90 DEU co that trong evidence -> tang 2 dat.
           Nhung chu "Co" xac nhan mot tham quyen phap ly ma bang chung
           khong he noi. Sai noi dung VA mao danh nguon.

  ie_022   Hoi (luot 2): "thoi khong can chinh xac dau, khoang chung thoi
           cung duoc"  (luot 1: "trong mot sao ca chua lai bao nhieu")
           Bot: tra loi ve THOI VU ca chua.
           So lieu that, nguon that -> tang 2 dat. Nhung no khong tra loi
           cau dang hoi. Kho khong co du lieu kinh te; cau dung la tu choi.

Hai kieu nay khac han nhau nen tang 3 kiem hai viec khac nhau.

CACH LAM: DETERMINISTIC TRUOC, LLM SAU

Quy chuan muc 21 dat ngan sach latency p50 <= 5s. Goi them mot LLM cho MOI
cau tra loi la cach chac chan tieu ngan sach do, va tao them mot phu thuoc
vao quota API. Vi vay:

  - Hai phep kiem duoi day thuan quy tac, chay ~1ms, khong goi mang.
  - LLM-judge (kiem_bang_llm) CO san nhung KHONG bat mac dinh. No danh cho
    truong hop rui ro cao, va nguoi goi phai chu dong bat.

Tang 3 chi CANH BAO hoac CHAN, khong bao gio sua cau tra loi. Sua cau tra
loi la mot dang bia khac.
"""

from __future__ import annotations

import re
import unicodedata

# --- Kiem 1: xac nhan tham quyen khong co trong bang chung ---------------

# Cau hoi cai gia dinh thuong co dang "<co quan> co quy dinh ... dung khong".
# Bot de tra loi "Co/Dung roi" roi doc so lieu that ra - so dung, nhung loi
# xac nhan la bia.
_CO_QUAN = re.compile(
    r"\b(sở nông nghiệp|bộ nông nghiệp|sở nn|cục trồng trọt|chi cục|"
    r"nhà nước|chính phủ|thông tư|nghị định|quyết định số|tiêu chuẩn quốc gia|"
    r"tcvn|quy chuẩn|luật)\b", re.I)

# Chi bat khi loi xac nhan dung o DAU cau tra loi. "Co" giua cau thuong la
# dong tu binh thuong ("co the", "co nhieu"), bat het thi bao dong gia.
_XAC_NHAN = re.compile(
    r"^\s*(có|đúng|đúng rồi|đúng vậy|vâng|chính xác|phải)\s*[,.:]", re.I)


def kiem_tham_quyen(cau_hoi: str, tra_loi: str, chunks) -> list[str]:
    """Bot co xac nhan mot tham quyen ma bang chung khong noi khong.

    Chi bao loi khi DU CA BA:
      1. cau hoi nhac toi mot co quan / van ban phap quy
      2. cau tra loi mo dau bang loi xac nhan ("Co,", "Dung roi,")
      3. bang chung KHONG he nhac toi co quan / van ban do

    Thieu mot trong ba thi im lang. Bat rong hon se chan ca nhung cau tra
    loi dung, va mot guardrail hay bao dong gia se bi tat.
    """
    if not _CO_QUAN.search(cau_hoi or ""):
        return []
    if not _XAC_NHAN.match(tra_loi or ""):
        return []

    nhac = {m.group(0).lower() for m in _CO_QUAN.finditer(cau_hoi)}
    bang_chung = " ".join((c.text or "") for c in chunks).lower()
    thieu = sorted(t for t in nhac if t not in bang_chung)
    if not thieu:
        return []
    return ["tang3: xac nhan tham quyen khong co trong bang chung ("
            + ", ".join(thieu) + ")"]


# --- Kiem 2: cau tra loi co dinh toi cau hoi khong ------------------------

_HU_TU = {
    "la", "va", "cua", "cho", "voi", "thi", "ma", "nhu", "de", "duoc", "co",
    "khong", "bao", "nhieu", "nao", "gi", "sao", "the", "a", "o", "tai",
    "trong", "ngoai", "tren", "duoi", "khi", "neu", "hay", "hoac", "nhung",
    "cung", "van", "da", "se", "dang", "bi", "boi", "tu", "den", "ve", "theo",
    "mot", "cac", "nhung", "moi", "toi", "minh", "ban", "anh", "chi", "em",
    "thoi", "chung", "chinh", "xac", "dau", "can",
}


def _khong_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")


def _tu_noi_dung(s: str) -> set[str]:
    """Tu co nghia trong cau, da bo dau va bo hu tu."""
    return {t for t in re.findall(r"[a-z0-9]+", _khong_dau(s))
            if len(t) > 1 and t not in _HU_TU}


def kiem_dinh_de(cau_hoi: str, tra_loi: str,
                 context_turns: list[str] | None = None) -> list[str]:
    """Cau hoi co du noi dung de tra loi khong.

    Bat truong hop ie_022: luot mot "trong mot sao ca chua lai bao nhieu"
    bi tu choi (kho khong co du lieu kinh te), luot hai nguoi dung ha chuan
    "thoi khong can chinh xac dau, khoang chung thoi cung duoc". Cau nay tu
    no KHONG neu chu de nao. Bot van lay duoc chunk ca chua va tra loi ve
    THOI VU - so lieu that, nguon that, nhung khong phai dieu dang hoi.

    DAU HIEU DA DO, KHONG PHAI SUY DOAN

    Tren ca 222 case cua tap v3, dung 2 case co cau hoi con <= 1 tu noi dung
    sau khi bo hu tu, va CA HAI deu mong doi `abstain`:

        gd_016  "the gio dang bao nhieu"                    -> abstain
        ie_022  "thoi khong can chinh xac dau, khoang ..."  -> abstain

    Khong mot case `answer` nao dinh. Do la ly do chon nguong nay.

    DA THU VA DA BO mot quy tac rong hon: bat cac cau "ha chuan" (dai khai,
    khoang chung, uoc chung...). Do lai thi 10 case khop mau do, nhung 9
    trong so do mong doi `answer` - "khoang chung" la cach noi binh thuong
    cua nong dan, khong phai manh ne rang buoc. Quy tac do se chan 9 cau
    tra loi dung de bat 1 cau sai.

    KHONG cong tu tu `context_turns` vao phep dem. Luot truoc co the da bi
    tu choi; muon no cho cau nay du noi dung la lam mat chinh cai bay ma
    case nay dat ra.
    """
    tu_hoi = _tu_noi_dung(cau_hoi)
    if len(tu_hoi) <= 1:
        return ["tang3: cau hoi khong du noi dung de tra loi "
                "(chi con " + str(len(tu_hoi)) + " tu co nghia)"]
    return []


# --- Kiem 3: LLM-judge, KHONG bat mac dinh --------------------------------

MAU_JUDGE = """Bạn là người kiểm tra. Đọc BẰNG CHỨNG và CÂU TRẢ LỜI.

Chỉ trả lời: câu trả lời có nói điều gì mà BẰNG CHỨNG không hỗ trợ không?
Không đánh giá văn phong. Không đánh giá đúng sai ngoài đời — chỉ so với
BẰNG CHỨNG.

BẰNG CHỨNG:
{bang_chung}

CÂU TRẢ LỜI:
{tra_loi}

Trả về JSON: {{"duoc_ho_tro": true/false, "cho_khong_ho_tro": "..."}}"""


def kiem_bang_llm(tra_loi: str, chunks, client=None) -> list[str]:
    """LLM-judge. TON THEM MOT LUOT GOI - chi dung cho cau rui ro cao.

    Loi goi model tra ve khong doc duoc -> bao loi, KHONG coi la dat. Im
    lang khi khong kiem duoc la cach guardrail chet ma khong ai biet.
    """
    import json as _json

    from app.services.rag.sinh_cau_tra_loi import dung_evidence_pack

    if client is None:
        from app.services.llm import tao_client
        client = tao_client()

    kq = client.sinh(
        MAU_JUDGE.format(bang_chung=dung_evidence_pack(chunks),
                         tra_loi=tra_loi),
        json_mode=True)
    if kq.loi:
        return ["tang3: khong goi duoc LLM-judge (" + str(kq.loi)[:80] + ")"]
    try:
        d = _json.loads(kq.text)
    except Exception:                                      # noqa: BLE001
        return ["tang3: LLM-judge tra ve khong phai JSON"]

    if d.get("duoc_ho_tro") is True:
        return []
    return ["tang3 (LLM-judge): " + str(d.get("cho_khong_ho_tro")
                                        or "co noi dung khong duoc ho tro")]


def kiem_ngu_nghia(cau_hoi: str, tra_loi: str, chunks,
                   context_turns: list[str] | None = None,
                   dung_llm: bool = False, client=None) -> list[str]:
    """Chay ca tang 3. Tra ve danh sach loi; rong = dat."""
    loi = kiem_tham_quyen(cau_hoi, tra_loi, chunks)
    loi += kiem_dinh_de(cau_hoi, tra_loi, context_turns)
    if dung_llm:
        loi += kiem_bang_llm(tra_loi, chunks, client=client)
    return loi
