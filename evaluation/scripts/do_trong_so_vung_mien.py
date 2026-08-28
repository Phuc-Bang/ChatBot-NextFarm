#!/usr/bin/env python3
"""
do_trong_so_vung_mien.py — Đo lường và chốt trọng số vùng miền bằng số đo thực (§40.2 Mục 11).

Quét dải hệ số ưu tiên vùng miền `he_so_vung` (0.0 đến 0.30) trên tập 30 test case
đặc thù địa phương để xác định điểm cân bằng tối ưu giữa ưu tiên địa phương
và bảo toàn độ chính xác nội dung kỹ thuật.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "knowledge" / "chunking"))

import chunker  # noqa: E402
from app.core.text import bo_dau  # noqa: E402
from app.services.retrieval.keyword import ChunkTraVe, cong_diem_vung  # noqa: E402

REGIONAL_CASES = BASE / "evaluation" / "data" / "regional_test_cases.jsonl"
MANIFEST_FILE = BASE / "crawler" / "data" / "manifest.json"
TEXT_DIR = BASE / "crawler" / "data" / "text"
DOC_REVIEW = BASE / "knowledge" / "review" / "documents.yaml"
OUT_REPORT = BASE / "docs" / "reports" / "P17_region_weighting_sweep.md"


def doc_cases_vung_mien() -> list[dict]:
    """Đọc 30 test case đặc thù vùng miền."""
    cases = []
    if not REGIONAL_CASES.exists():
        return []
    with open(REGIONAL_CASES, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def doc_kho_chunk() -> list[ChunkTraVe]:
    """Đọc và chunk toàn bộ tài liệu đã duyệt để mô phỏng tìm kiếm."""
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(DOC_REVIEW, "r", encoding="utf-8") as f:
        doc_reviews_data = yaml.safe_load(f) or {}
    
    docs_list = doc_reviews_data.get("documents", []) if isinstance(doc_reviews_data, dict) else doc_reviews_data
    approved_doc_ids = {d.get("document_id") for d in docs_list if isinstance(d, dict) and d.get("approved")}

    chunks_tra_ve = []
    for rec in manifest.get("records", []):
        if rec.get("status") in ("ok", "success") and rec.get("id") in approved_doc_ids:
            txt_file = TEXT_DIR / f"{rec['id']}.txt"
            if txt_file.exists():
                text = txt_file.read_text(encoding="utf-8")
                raw_chunks = chunker.cat(text)
                for c in raw_chunks:
                    ctv = ChunkTraVe(
                        chunk_id=f"{rec['id']}#{c.ordinal}",
                        document_id=rec["id"],
                        text=c.text,
                        section_title=c.section_title,
                        crop=rec.get("crop"),
                        region=rec.get("region"),
                        url=rec.get("url", ""),
                        document_title=rec.get("title") or rec["id"],
                        publisher=rec.get("publisher", ""),
                        source_tier=rec.get("source_tier", 1),
                        is_high_risk=c.is_high_risk,
                        diem=0.0,
                    )
                    chunks_tra_ve.append(ctv)
    return chunks_tra_ve


def mo_phong_retrieval(query: str, crop: str, chunks: list[ChunkTraVe], top_k: int = 10) -> list[ChunkTraVe]:
    """Mô phỏng chấm điểm BM25/Trigram cơ sở cho câu hỏi."""
    q_clean = bo_dau(query)
    keywords = [w for w in q_clean.split() if len(w) > 3]

    scored = []
    for c in chunks:
        if crop and c.crop and c.crop != crop:
            continue
        c_clean = bo_dau(c.text)
        hits = sum(1 for kw in keywords if kw in c_clean)
        if hits > 0:
            diem_co_so = hits / max(len(keywords), 1)
            c_copy = ChunkTraVe(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                text=c.text,
                section_title=c.section_title,
                crop=c.crop,
                region=c.region,
                url=c.url,
                document_title=c.document_title,
                publisher=c.publisher,
                source_tier=c.source_tier,
                is_high_risk=c.is_high_risk,
                diem=diem_co_so,
            )
            scored.append(c_copy)
    
    scored.sort(key=lambda x: -x.diem)
    return scored[:top_k]



def danh_gia_he_so(cases: list[dict], all_chunks: list[ChunkTraVe], he_so: float) -> dict:
    """Đo lường các chỉ số với một giá trị hệ số vùng miền cụ thể."""
    top1_match = 0
    top3_match = 0
    total_evaluated = 0

    for case in cases:
        q = case["question"]
        crop = case.get("crop", "")
        target_reg = case["target_region"]

        candidates = mo_phong_retrieval(q, crop, all_chunks, top_k=10)
        if not candidates:
            continue

        total_evaluated += 1
        # Áp dụng cộng điểm vùng
        reranked = cong_diem_vung(candidates, target_reg, he_so=he_so)

        # Top 1
        if reranked and reranked[0].region == target_reg:
            top1_match += 1

        # Top 3
        top3 = reranked[:3]
        if any(c.region == target_reg for c in top3):
            top3_match += 1

    t1_rate = (top1_match / max(total_evaluated, 1)) * 100
    t3_rate = (top3_match / max(total_evaluated, 1)) * 100

    return {
        "he_so": he_so,
        "total": total_evaluated,
        "top1_match": top1_match,
        "top1_rate": f"{t1_rate:.1f}%",
        "top3_match": top3_match,
        "top3_rate": f"{t3_rate:.1f}%",
    }


def main():
    print("=== BẮT ĐẦU ĐO TRỌNG SỐ VÙNG MIỀN (§40.2 Mục 11) ===")
    cases = doc_cases_vung_mien()
    chunks = doc_kho_chunk()

    print(f"- Số test case vùng miền: {len(cases)}")
    print(f"- Số chunks trong kho: {len(chunks)}")

    he_so_list = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    results = []

    for hs in he_so_list:
        res = danh_gia_he_so(cases, chunks, hs)
        results.append(res)
        print(f"-> Hệ số {hs:.2f}: Top-1 Match = {res['top1_rate']} ({res['top1_match']}/{res['total']}) | Top-3 Match = {res['top3_rate']}")

    # Tạo báo cáo Markdown
    report_lines = [
        "# Báo Cáo Đo Lường Kỹ Thuật: Chốt Trọng Số Vùng Miền (§40.2 Mục 11)",
        "",
        "> **Tiêu chuẩn tham chiếu:** `NEXTFARM_PROBLEM_A_STANDARD_v2.0.md` — Mục 14.5 & Mục 40.2",
        f"> **Thời điểm thực thi:** 22/08/2026",
        f"> **Dữ liệu đánh giá:** 30 test cases đặc thù địa phương (`regional_test_cases.jsonl`) · {len(chunks)} chunks kho tri thức",
        "",
        "---",
        "",
        "## 1. Bảng Kết Quả Đo Lường Đa Trọng Số",
        "",
        "| Hệ số cộng điểm (`he_so`) | Số ca đánh giá | Top-1 Khớp Vùng Miền | Top-3 Độ Phủ Vùng Miền | Đánh giá kỹ thuật |",
        "| :---: | :---: | :---: | :---: | :--- |",
    ]

    # Nhan cot phai SUY TU SO DO, khong tu gia tri he_so.
    #
    # SUA 2026-08-28: ban cu gan nhan bang cach so sanh `hs == 0.10` roi in
    # "**Diem can bang toi uu**". Nghia la ket luan duoc viet TRUOC khi do, va
    # giu nguyen du bang so noi nguoc lai - 0.15 hon 0.10 ca Top-1 lan Top-3.
    # Mot bao cao tu chon nguoi thang truoc khi chay thi khong con la phep do.
    tot_nhat = max(r["top1_match"] for r in results)
    hs_tot = [r["he_so"] for r in results if r["top1_match"] == tot_nhat]
    hs_nho_nhat_dat_dinh = min(hs_tot)

    for r in results:
        hs = r["he_so"]
        if hs == 0.0:
            note = "Baseline: không cộng điểm vùng"
        elif r["top1_match"] == tot_nhat and hs == hs_nho_nhat_dat_dinh:
            note = f"**Top-1 cao nhất đo được** ({r['top1_rate']}), đạt ở hệ số thấp nhất trong nhóm cùng điểm"
        elif r["top1_match"] == tot_nhat:
            note = f"Bằng đỉnh Top-1 ({r['top1_rate']}) nhưng hệ số cao hơn mức cần thiết"
        else:
            note = f"Thấp hơn đỉnh {tot_nhat - r['top1_match']} ca"

        report_lines.append(
            f"| **{hs:.2f}** | {r['total']} | **{r['top1_rate']}** ({r['top1_match']}/{r['total']}) | **{r['top3_rate']}** ({r['top3_match']}/{r['total']}) | {note} |"
        )

    base = next(r for r in results if r["he_so"] == 0.0)
    dinh = next(r for r in results if r["he_so"] == hs_nho_nhat_dat_dinh)
    mac_dinh = next(r for r in results if r["he_so"] == 0.10)

    report_lines.extend([
        "",
        "---",
        "",
        "## 2. Đọc bảng trên",
        "",
        f"- **Baseline `0.00`:** Top-1 {base['top1_rate']} ({base['top1_match']}/{base['total']}).",
        f"- **Đỉnh đo được:** hệ số `{hs_nho_nhat_dat_dinh:.2f}` — Top-1 {dinh['top1_rate']} "
        f"({dinh['top1_match']}/{dinh['total']}), hơn baseline {dinh['top1_match'] - base['top1_match']} ca.",
        f"- **Mặc định đang đặt trong mã (`he_so = 0.10`):** Top-1 {mac_dinh['top1_rate']} "
        f"({mac_dinh['top1_match']}/{mac_dinh['total']})"
        + (f" — **thấp hơn đỉnh {dinh['top1_match'] - mac_dinh['top1_match']} ca**."
           if mac_dinh['top1_match'] < dinh['top1_match'] else " — bằng đỉnh."),
        "",
        "> Phép đo này KHÔNG đo được hiện tượng \"trọng số quá mạnh đẩy chunk sai nội dung lên "
        "top\". Muốn khẳng định điều đó phải chấm nội dung từng chunk trả về, không chỉ đếm khớp "
        "vùng. Bản báo cáo trước có câu đó nhưng không có số nào chống lưng — đã bỏ.",
        "",
        "## 3. Giới hạn phải nói rõ",
        "",
    ])

    if hs_nho_nhat_dat_dinh == max(he_so_list):
        report_lines.extend([
            f"0. **Đỉnh rơi đúng vào biên của dải quét.** Giá trị cao nhất được thử là "
            f"`{max(he_so_list):.2f}` và chính nó cho Top-1 cao nhất. Khi đỉnh nằm ở mép, phép "
            "quét chưa chứng minh được đã tìm ra điểm tốt nhất — rất có thể hệ số còn tốt hơn "
            "nằm ngoài dải. Muốn kết luận phải nới dải rồi quét lại.",
            "",
        ])

    report_lines.extend([
        "1. **Tham số này hiện KHÔNG tác động lên hệ thống đang chạy.** `cong_diem_vung()` chỉ "
        "chạy khi `tim_kiem()` nhận đối số `region`. Đường sống gọi "
        "`tim_kiem(cau, crop=..., top_k=...)` (`app/services/pipeline.py:185`) — không truyền "
        "`region`, nên nhánh `if region:` (`hybrid.py:65`) không bao giờ vào. Chỉ chính script "
        "này truyền `region`. Mọi con số trên đo một nhánh mã mà người dùng thật chưa chạm tới.",
        "2. **Tập 30 câu là tự viết, nằm NGOÀI tập đóng băng v3.** Nó được tạo trong cùng commit "
        "chốt tham số (`8e5f93f`). Tự viết thước rồi tự đo — kết quả chỉ nên dùng để định hướng, "
        "không dùng làm bằng chứng nghiệm thu. 0/222 case của v3 khai trường `region`.",
        "",
        "## 4. Kết luận",
        "",
        f"> Trên tập 30 câu tự viết, hệ số `{hs_nho_nhat_dat_dinh:.2f}` cho Top-1 cao nhất "
        f"({dinh['top1_rate']}). Mã đang để mặc định `0.10` ({mac_dinh['top1_rate']}).",
        ">",
        "> **Chưa đổi mặc định**, vì đổi một tham số không có đường vào sản phẩm là thay đổi vô "
        "nghĩa. Việc cần làm trước là cho pipeline nhận diện và truyền `region`; khi đó mới quét "
        "lại trên tập có khai vùng thật và chốt bằng số đo có giá trị.",
    ])

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n[OK] Đã xuất báo cáo chi tiết tại: {OUT_REPORT}")


if __name__ == "__main__":
    main()
