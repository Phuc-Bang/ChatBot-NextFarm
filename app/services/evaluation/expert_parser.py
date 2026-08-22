# -*- coding: utf-8 -*-
"""
Robust parser for docs/PHIEU_CHAM_CHUYEN_GIA.md into structured JSON.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[3]
MD_PATH = BASE / "docs" / "PHIEU_CHAM_CHUYEN_GIA.md"


def doc_phieu_cham() -> list[dict[str, Any]]:
    if not MD_PATH.exists():
        return []

    text = MD_PATH.read_text(encoding="utf-8")
    
    # Split by ## Câu <n>
    pattern = r"\n##\s+Câu\s+(\d+)\s*\n"
    parts = re.split(pattern, text)
    
    cases = []
    for i in range(1, len(parts), 2):
        so = int(parts[i])
        block = parts[i + 1]

        # Extract Cau hoi
        m_hoi = re.search(r"\*\*Hỏi:\*\*\s*(.*?)(?=\n\n\*\*Trả lời:\*\*|\n\n\*\*Nguồn|\n\n\|)", block, re.DOTALL)
        raw_hoi = m_hoi.group(1).strip() if m_hoi else ""
        cau_hoi = re.sub(r"\s+", " ", raw_hoi).strip()

        # Extract Tra loi
        m_tl = re.search(r"\*\*Trả lời:\*\*\s*\n\n(.*?)(?=\n\n\*\*Nguồn|\n\n\||\n\n\*\*Nhận xét)", block, re.DOTALL)
        tra_loi = m_tl.group(1).strip() if m_tl else ""
        tra_loi = re.sub(r"^>\s*", "", tra_loi, flags=re.MULTILINE).strip()

        # Extract Nguon
        m_nguon = re.search(r"\*\*Nguồn hệ thống đã dẫn:\*\*\s*\n\n(.*?)(?=\n\n\||\n\n\*\*Nhận xét)", block, re.DOTALL)
        nguon_block = m_nguon.group(1).strip() if m_nguon else ""

        nguon_list = []
        if nguon_block and not nguon_block.startswith("(không có"):
            items = re.split(r"\n-\s+\*\*", "\n" + nguon_block)
            for it in items:
                it = it.strip()
                if not it:
                    continue
                m_it = re.search(r"^(.*?)\*\*\s*—\s*(.*?)\n\s*(https?://[^\s]+)\n\s*>\s*(.*)$", it, re.DOTALL)
                if m_it:
                    nguon_list.append({
                        "tieu_de": m_it.group(1).strip(),
                        "co_quan": m_it.group(2).strip(),
                        "url": m_it.group(3).strip(),
                        "trich_doan": m_it.group(4).strip()
                    })
                else:
                    lines = it.split("\n")
                    tieu_de = lines[0].replace("**", "").strip("* -")
                    nguon_list.append({
                        "tieu_de": tieu_de,
                        "co_quan": "",
                        "url": "",
                        "trich_doan": "\n".join(lines[1:]).strip("> ")
                    })

        # Phan loai loai cau hoi & chu de
        is_refusal = (
            len(nguon_list) == 0 or
            "chưa được kết nối" in tra_loi.lower() or
            "không đoán" in tra_loi.lower() or
            "không có căn cứ" in tra_loi.lower() or
            "chưa có tài liệu" in tra_loi.lower() or
            "chưa tìm thấy" in tra_loi.lower() or
            "bạn đang hỏi về cây trồng nào" in tra_loi.lower()
        )

        loai = "tu_choi" if is_refusal else "tra_loi"
        
        # Tag chu de
        tags = []
        h_lower = cau_hoi.lower()
        if "lúa" in h_lower or "lua" in h_lower: tags.append("Lúa")
        if "cà chua" in h_lower or "ca chua" in h_lower: tags.append("Cà chua")
        if "dưa chuột" in h_lower or "dua chuột" in h_lower or "dưa leo" in h_lower: tags.append("Dưa chuột")
        if "cà phê" in h_lower or "ca phe" in h_lower: tags.append("Ngoài phạm vi (Cà phê)")
        if "thuốc" in h_lower or "phun" in h_lower or "đạo ôn" in h_lower or "héo xanh" in h_lower or "phấn trắng" in h_lower: tags.append("Sâu bệnh / BVTV")
        if "bơm" in h_lower or "van" in h_lower: tags.append("Điều khiển thiết bị")
        if "vườn" in h_lower or "độ ẩm" in h_lower and is_refusal: tags.append("Dữ liệu cảm biến")
        if not tags: tags.append("Kỹ thuật canh tác")

        cases.append({
            "id": f"cau_{so}",
            "so": so,
            "cau_hoi": cau_hoi,
            "tra_loi": tra_loi,
            "da_tu_choi": is_refusal,
            "nguon": nguon_list,
            "loai": loai,
            "tags": tags
        })

    return cases
