"""
Sinh cau tra loi tu Evidence Pack, roi KIEM TRUOC KHI TRA VE (muc 16-18).

NGUYEN TAC SO MOT: LLM KHONG PHAI NGUON SU THAT

Model chi duoc doc Evidence Pack va viet lai. Moi cau co so lieu phai gan
[chunk_id]. Sau khi model tra ve, Grounding Validator kiem lai - va day moi
la thu chan bia, khong phai prompt.

Ly do: prompt la LOI DE NGHI, model co the khong nghe. Validator la CO CHE,
model khong vuot qua duoc. Mot he thong chi dua vao prompt de chong bia thi
khong co gi bao dam ca.

BA TANG KIEM (muc 18)

  tang 1 cau truc  - chunk_id co that khong, cau co so co kem nguon khong
  tang 2 so lieu   - MOI con so trong cau tra loi phai co trong evidence
  tang 3 ngu nghia - xem app/services/grounding/ngu_nghia.py

Tang 2 la tang quan trong nhat va no DETERMINISTIC: trich so tu cau tra loi,
doi chieu voi so trong chunk duoc trich dan. Khong dua vao model nao.

Tang 3 cung deterministic o hai phep kiem mac dinh (khong goi mang). LLM-judge
co san nhung phai bat bang tay - no ton them mot luot goi va nam tren duong
latency, xem muc 21.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

MAU_PROMPT = """Bạn là trợ lý nông nghiệp. Trả lời câu hỏi CHỈ dựa vào BẰNG CHỨNG dưới đây.

QUY TẮC BẮT BUỘC:
1. Chỉ dùng thông tin có trong BẰNG CHỨNG. Không thêm kiến thức bên ngoài.
2. Mỗi câu có số liệu phải kèm mã nguồn dạng [chunk_id].
3. Nếu BẰNG CHỨNG không đủ để trả lời, phải nói rõ là không đủ. Không đoán.
4. Trả lời bằng tiếng Việt, ngắn gọn.

BẰNG CHỨNG:
{bang_chung}

CÂU HỎI: {cau_hoi}

Trả về JSON đúng dạng:
{{"du_can_cu": true/false, "tra_loi": "...", "chunk_da_dung": ["..."]}}"""


@dataclass
class KetQuaSinh:
    tra_loi: str
    da_tu_choi: bool
    ly_do: str | None = None
    chunk_da_dung: list[str] = field(default_factory=list)
    token_vao: int = 0
    token_ra: int = 0
    canh_bao_grounding: list[str] = field(default_factory=list)
    raw: str = ""


_SO = re.compile(r"\d+(?:[.,]\d+)*")
_MA = re.compile(r"\[([^\]]+)\]")


def _cac_so(text: str) -> set[str]:
    """Moi con so, chuan hoa dau phan cach.

    30.000 va 30000 la MOT so; 6,5 va 6.5 la MOT so; 6 va 6.0 la MOT so.
    Khong chuan hoa thi tang 2 bao dong gia lien tuc va se bi tat di - luc
    do mat han tang chan quan trong nhat.
    """
    ra: set[str] = set()
    for x in _SO.findall(_MA.sub(" ", text or "")):
        x = x.rstrip(".,")
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", x):
            x = re.sub(r"[.,]", "", x)
        else:
            x = x.replace(",", ".")
        try:
            ra.add("%g" % float(x))
        except ValueError:
            ra.add(x)
    return ra


def dung_evidence_pack(chunks) -> str:
    """Evidence Pack - nguyen van, khong tom tat (muc 16).

    Tom tat truoc khi dua cho model la lam mat thong tin ma tang kiem so
    lieu can den, va tao them mot cho co the bia.
    """
    phan = []
    for c in chunks:
        dau = "[" + c.chunk_id + "]"
        if c.document_title:
            dau += " " + c.document_title
        if c.publisher:
            dau += " (" + c.publisher + ")"
        phan.append(dau + "\n" + " ".join(c.text.split()))
    return "\n\n".join(phan)


def kiem_grounding(tra_loi: str, chunks, chunk_da_dung: list[str]) -> list[str]:
    """Tang 1 + tang 2. Tra ve danh sach loi; rong = dat.

    Tang 3 (ngu nghia) CHUA LAM - ghi ro o day thay vi de nguoi doc tuong
    da du ba tang.
    """
    loi: list[str] = []
    hop_le = {c.chunk_id for c in chunks}

    # --- Tang 1: chunk_id phai co that ---
    for ma in set(_MA.findall(tra_loi)):
        if ma not in hop_le:
            loi.append("trich dan chunk khong co trong Evidence Pack: " + ma)
    for ma in chunk_da_dung:
        if ma not in hop_le:
            loi.append("chunk_da_dung khai bao ma khong co: " + ma)

    # --- Tang 2: moi con so phai co trong evidence ---
    #
    # Doi chieu voi TOAN BO evidence chu khong chi chunk duoc trich dan:
    # model co the ghi nhan sai nguon nhung con so van dung. Bat loi ghi
    # nguon sai la viec cua tang 1; tang 2 chi hoi "so nay co that khong".
    so_evidence: set[str] = set()
    for c in chunks:
        so_evidence |= _cac_so(c.text)

    la = _cac_so(tra_loi) - so_evidence
    if la:
        loi.append("so khong co trong bang chung: " + ", ".join(sorted(la)))
    return loi


def sinh_va_kiem(cau_hoi: str, chunks, client=None,
                 context_turns: list[str] | None = None,
                 tang3_llm: bool = False) -> KetQuaSinh:
    """Goi model roi kiem. Khong dat thi TU CHOI, khong tra ve cau nghi ngo.

    `tang3_llm=True` bat them LLM-judge - TON MOT LUOT GOI NUA, chi dung
    cho cau rui ro cao. Hai phep kiem quy tac cua tang 3 luon chay vi
    chung khong goi mang.
    """
    from app.services.llm import tao_client

    client = client or tao_client()
    prompt = MAU_PROMPT.format(bang_chung=dung_evidence_pack(chunks),
                               cau_hoi=cau_hoi)
    r = client.sinh(prompt, json_mode=True, max_token_ra=800)

    if not r.thanh_cong:
        return KetQuaSinh(
            tra_loi="Hệ thống đang bận, bạn thử lại sau ít phút nhé.",
            da_tu_choi=True, ly_do="loi_he_thong",
            token_vao=r.token_vao, token_ra=r.token_ra_tinh_tien,
            raw=r.loi or "")

    try:
        d = json.loads(r.text)
    except json.JSONDecodeError:
        # Model khong tra ve JSON dung dang -> KHONG doan y no. Coi la khong
        # dat va tu choi: mot cau tra loi khong phan tich duoc thi cung khong
        # kiem duoc, ma khong kiem duoc thi khong duoc phep hien ra.
        return KetQuaSinh(
            tra_loi="Tôi chưa tạo được câu trả lời đủ căn cứ cho câu hỏi này.",
            da_tu_choi=True, ly_do="loi_dinh_dang",
            token_vao=r.token_vao, token_ra=r.token_ra_tinh_tien, raw=r.text)

    if not d.get("du_can_cu", False):
        return KetQuaSinh(
            tra_loi=d.get("tra_loi") or (
                "Kho tri thức hiện chưa có đủ căn cứ để trả lời câu hỏi này. "
                "Tôi không đoán khi không có tài liệu."),
            da_tu_choi=True, ly_do="insufficient_evidence",
            token_vao=r.token_vao, token_ra=r.token_ra_tinh_tien, raw=r.text)

    tl = (d.get("tra_loi") or "").strip()
    dung = [str(x) for x in (d.get("chunk_da_dung") or [])]
    loi = kiem_grounding(tl, chunks, dung)

    # --- Tang 3: ngu nghia (muc 18.3) ---
    # Tang 2 bao dam moi CON SO co that. No khong doc duoc y nghia, nen hai
    # thu lot qua duoc: loi xac nhan tham quyen khong co trong bang chung
    # (adv_006), va cau tra loi khong dinh toi cau dang hoi (ie_022).
    from app.services.grounding.ngu_nghia import kiem_ngu_nghia
    loi = loi + kiem_ngu_nghia(cau_hoi, tl, chunks, context_turns,
                               dung_llm=tang3_llm, client=client)

    if loi:
        # CHAN. Day la con so cho cau "he thong da chan N ca bia" (muc 18).
        return KetQuaSinh(
            tra_loi="Tôi chưa đủ căn cứ chắc chắn để trả lời câu hỏi này.",
            da_tu_choi=True, ly_do="grounding_khong_dat",
            canh_bao_grounding=loi, chunk_da_dung=dung,
            token_vao=r.token_vao, token_ra=r.token_ra_tinh_tien, raw=r.text)

    return KetQuaSinh(tra_loi=tl, da_tu_choi=False, chunk_da_dung=dung,
                      token_vao=r.token_vao, token_ra=r.token_ra_tinh_tien,
                      raw=r.text)
