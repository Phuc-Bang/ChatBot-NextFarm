# -*- coding: utf-8 -*-
"""
Doc docs/PHIEU_CHAM_CHUYEN_GIA.md thanh du lieu co cau truc cho trang /expert.

HAI DANG BAN GHI TRONG PHIEU - va do la cho da tung tach sai

    **Hỏi:** ...
    **Trả lời:**                                     <- ca CO tra loi
    > noi dung

    **Hỏi:** ...
    **Hệ thống TỪ CHỐI** (lý do máy ghi: `...`)      <- ca TU CHOI
    > ly do noi voi nguoi dung

LOI DA CO 2026-08-22: ban dau chi biet dau moc "**Trả lời:**". Hau qua tren
50 cau that:

  - 21 ca tu choi bi nuot ca khoi "TỪ CHỐI" vao truong `cau_hoi`, con
    `tra_loi` thi RONG;
  - phan loai suy ra tu choi bang `len(nguon)==0` cong vai cum tu trong
    `tra_loi` - ca hai deu truot, vi ca tu choi VAN dan nguon va `tra_loi`
    luc do dang rong. 21 ca tu choi that chi nhan ra 7.

Sai lech nay khong chi lam xau giao dien: mot script cham diem tu dong da
cho 4/5 diem kem ghi chu "trich dan chuan" cho nhung o tra loi TRONG, vi no
tuong chung la cau tra loi co nguon.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[3]
MD_PATH = BASE / "docs" / "PHIEU_CHAM_CHUYEN_GIA.md"

# Dau moc TU CHOI, kem ly do may ghi trong dau backtick.
RE_TU_CHOI = re.compile(
    r"\*\*Hệ thống TỪ CHỐI\*\*\s*\(lý do máy ghi:\s*`([^`]*)`\)")

# Cau hoi dung lai o BAT KY dau moc nao phia sau.
RE_HOI = re.compile(
    r"\*\*Hỏi:\*\*\s*(.*?)"
    r"(?=\n\n\*\*Trả lời:\*\*|\n\n\*\*Hệ thống TỪ CHỐI\*\*|\n\n\*\*Nguồn|\n\n\|)",
    re.DOTALL)

# Noi dung nam sau ca hai dang dau moc.
RE_NOI_DUNG = re.compile(
    r"(?:\*\*Trả lời:\*\*|\*\*Hệ thống TỪ CHỐI\*\*[^\n]*)\s*\n\n(.*?)"
    r"(?=\n\n\*\*Nguồn|\n\n\||\n\n\*\*Nhận xét)",
    re.DOTALL)

RE_NGUON = re.compile(
    r"\*\*Nguồn hệ thống đã dẫn:\*\*\s*\n\n(.*?)(?=\n\n\||\n\n\*\*Nhận xét)",
    re.DOTALL)

RE_MUC_NGUON = re.compile(
    r"^(.*?)\*\*\s*—\s*(.*?)\n\s*(https?://[^\s]+)\n\s*>\s*(.*)$", re.DOTALL)


def _tach_nguon(khoi: str) -> list[dict[str, str]]:
    ra: list[dict[str, str]] = []
    if not khoi or khoi.startswith("(không có"):
        return ra
    for muc in re.split(r"\n-\s+\*\*", "\n" + khoi):
        muc = muc.strip()
        if not muc:
            continue
        m = RE_MUC_NGUON.search(muc)
        if m:
            ra.append({"tieu_de": m.group(1).strip(),
                       "co_quan": m.group(2).strip(),
                       "url": m.group(3).strip(),
                       "trich_doan": m.group(4).strip()})
        else:
            dong = muc.split("\n")
            ra.append({"tieu_de": dong[0].replace("**", "").strip("* -"),
                       "co_quan": "", "url": "",
                       "trich_doan": "\n".join(dong[1:]).strip("> ")})
    return ra


def _gan_nhan(cau_hoi: str, la_tu_choi: bool) -> list[str]:
    t: list[str] = []
    h = cau_hoi.lower()
    if "lúa" in h or "lua" in h:
        t.append("Lúa")
    if "cà chua" in h or "ca chua" in h:
        t.append("Cà chua")
    if "dưa chuột" in h or "dua chuột" in h or "dưa leo" in h:
        t.append("Dưa chuột")
    if "cà phê" in h or "ca phe" in h:
        t.append("Ngoài phạm vi (Cà phê)")
    if ("thuốc" in h or "phun" in h or "đạo ôn" in h
            or "héo xanh" in h or "phấn trắng" in h):
        t.append("Sâu bệnh / BVTV")
    if "bơm" in h or "van" in h:
        t.append("Điều khiển thiết bị")
    if ("vườn" in h or "độ ẩm" in h) and la_tu_choi:
        t.append("Dữ liệu cảm biến")
    return t or ["Kỹ thuật canh tác"]


def doc_phieu_cham() -> list[dict[str, Any]]:
    if not MD_PATH.exists():
        return []

    phan = re.split(r"\n##\s+Câu\s+(\d+)\s*\n",
                    MD_PATH.read_text(encoding="utf-8"))

    ra: list[dict[str, Any]] = []
    for i in range(1, len(phan), 2):
        so = int(phan[i])
        khoi = phan[i + 1]

        m_tc = RE_TU_CHOI.search(khoi)
        la_tu_choi = bool(m_tc)          # dua vao DAU MOC, khong doan qua cum tu
        ly_do = m_tc.group(1).strip() if m_tc else ""

        m_hoi = RE_HOI.search(khoi)
        cau_hoi = re.sub(r"\s+", " ",
                         m_hoi.group(1).strip() if m_hoi else "").strip()

        m_nd = RE_NOI_DUNG.search(khoi)
        noi_dung = m_nd.group(1).strip() if m_nd else ""
        noi_dung = re.sub(r"^>\s*", "", noi_dung, flags=re.MULTILINE).strip()

        m_ng = RE_NGUON.search(khoi)
        nguon = _tach_nguon(m_ng.group(1).strip() if m_ng else "")

        ra.append({
            "id": "cau_" + str(so),
            "so": so,
            "cau_hoi": cau_hoi,
            "tra_loi": noi_dung,
            "da_tu_choi": la_tu_choi,
            "ly_do_tu_choi": ly_do,
            "nguon": nguon,
            "loai": "tu_choi" if la_tu_choi else "tra_loi",
            "tags": _gan_nhan(cau_hoi, la_tu_choi),
        })

    return ra
