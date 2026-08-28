#!/usr/bin/env python3
"""
sweep_chunk_size.py — Quét và đánh giá tối ưu kích thước chunk (§40.2 Mục 4).

Thử nghiệm các dải kích thước (800, 1000, 1200, 1500 ký tự) trên kho tri thức
Nextfarm để xác định điểm cân bằng tối ưu giữa độ mịn ngữ nghĩa và bảo toàn ngữ cảnh.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "knowledge" / "chunking"))
sys.path.insert(0, str(BASE / "evaluation"))

import chunker  # noqa: E402
from app.core.text import bo_dau  # noqa: E402
import freeze  # noqa: E402

MANIFEST_FILE = BASE / "crawler" / "data" / "manifest.json"
TEXT_DIR = BASE / "crawler" / "data" / "text"
DOC_REVIEW = BASE / "knowledge" / "review" / "documents.yaml"
FACT_REVIEW = BASE / "knowledge" / "review" / "facts.yaml"
OUT_REPORT = BASE / "docs" / "reports" / "P16_chunk_size_sweep.md"


def doc_tai_lieu_da_duyet() -> list[dict]:
    """Đọc các tài liệu thành công và đã được duyệt."""
    if not MANIFEST_FILE.exists() or not DOC_REVIEW.exists():
        return []
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(DOC_REVIEW, "r", encoding="utf-8") as f:
        doc_reviews_data = yaml.safe_load(f) or {}
    
    docs_list = doc_reviews_data.get("documents", []) if isinstance(doc_reviews_data, dict) else doc_reviews_data
    approved_doc_ids = {d.get("document_id") for d in docs_list if isinstance(d, dict) and d.get("approved")}

    tai_lieu = []
    for rec in manifest.get("records", []):
        if rec.get("status") in ("ok", "success") and rec.get("id") in approved_doc_ids:
            txt_file = TEXT_DIR / f"{rec['id']}.txt"
            if txt_file.exists():
                tai_lieu.append({
                    "id": rec["id"],
                    "crop": rec.get("crop", ""),
                    "region": rec.get("region", ""),
                    "publisher": rec.get("publisher", ""),
                    "url": rec.get("url", ""),
                    "title": rec.get("title") or rec["id"],
                    "content": txt_file.read_text(encoding="utf-8")
                })
    return tai_lieu




def doc_facts() -> list[dict]:
    """Đọc danh sách facts đã xác nhận từ facts.yaml."""
    if not FACT_REVIEW.exists():
        return []
    with open(FACT_REVIEW, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    facts = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                v["fact_id"] = k
                facts.append(v)
            elif isinstance(v, list):
                for item in v:
                    facts.append(item)
    return facts


def doc_cases() -> list[dict]:
    """Đọc 222 test cases v3 đã đóng băng."""
    v3_dir = BASE / "evaluation" / "datasets" / "v3"
    cases = []
    for yaml_file in v3_dir.glob("*.yaml"):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            for c in data.get("cases", []):
                c["group"] = data.get("group")
                cases.append(c)
    return cases



def chay_chunking(tai_lieu_list: list[dict], target_size: int, max_size: int) -> list[dict]:
    """Chạy chunker với kích thước tùy biến."""
    chunker.KICH_THUOC_MUC_TIEU = target_size
    chunker.KICH_THUOC_TOI_DA = max_size
    
    all_chunks = []
    for doc in tai_lieu_list:
        chunks = chunker.cat(doc["content"])
        for c in chunks:
            all_chunks.append({
                "ordinal": c.ordinal,
                "content": c.text,
                "content_unaccent": c.text_unaccent,
                "section_title": c.section_title,
                "is_high_risk": c.is_high_risk,
                "needs_caution": c.needs_caution,
                "doc_id": doc["id"],
            })
    return all_chunks



def danh_gia_cau_hinh(all_chunks: list[dict], facts: list[dict], cases: list[dict], target_size: int) -> dict:
    """Tính toán các chỉ số thống kê & độ bao phủ cho cấu hình chunk size."""
    if not all_chunks:
        return {
            "target_size": target_size,
            "so_chunk": 0,
            "do_dai_tb": 0,
            "do_dai_min": 0,
            "do_dai_max": 0,
            "ty_le_rui_ro_cao": "0%",
            "fact_coverage": "0%",
            "retrieval_hit_rate": "0%",
        }

    lengths = [len(c.get("content", "")) for c in all_chunks]
    high_risk_count = sum(1 for c in all_chunks if c.get("is_high_risk"))
    
    # Đo Fact Coverage
    fact_hits = 0
    for fact in facts:
        fact_text = fact.get("sentence", "") or fact.get("fact_text", "") or fact.get("statement", "")
        if not fact_text:
            continue
        fact_clean = bo_dau(fact_text)
        keywords = [w for w in fact_clean.split() if len(w) > 3]
        if not keywords:
            continue
        found = False
        for c in all_chunks:
            c_clean = c.get("content_unaccent") or bo_dau(c.get("content", ""))
            if fact_clean in c_clean or sum(1 for kw in keywords if kw in c_clean) >= min(len(keywords), 3):
                found = True
                break
        if found:
            fact_hits += 1
    fact_coverage = (fact_hits / max(len(facts), 1)) * 100

    # Đo Retrieval Hit Rate trên 222 test cases (nhóm expected_behavior == answer)
    case_hits = 0
    in_scope_cases = [c for c in cases if c.get("expected_behavior") == "answer"]
    for case in in_scope_cases:
        q = bo_dau(case.get("question", "") or case.get("cau_hoi", ""))
        keywords = [w for w in q.split() if len(w) > 3]
        if not keywords:
            continue
        found = False
        for c in all_chunks:
            c_clean = c.get("content_unaccent") or bo_dau(c.get("content", ""))
            if sum(1 for kw in keywords if kw in c_clean) >= min(len(keywords), 2):
                found = True
                break
        if found:
            case_hits += 1
    hit_rate = (case_hits / max(len(in_scope_cases), 1)) * 100


    return {
        "target_size": target_size,
        "so_chunk": len(all_chunks),
        "do_dai_tb": round(sum(lengths) / len(lengths), 1),
        "do_dai_min": min(lengths),
        "do_dai_max": max(lengths),
        "ty_le_rui_ro_cao": f"{(high_risk_count / len(all_chunks)) * 100:.1f}% ({high_risk_count}/{len(all_chunks)})",
        "fact_coverage": f"{fact_coverage:.1f}% ({fact_hits}/{len(facts)})",
        "retrieval_hit_rate": f"{hit_rate:.1f}% ({case_hits}/{len(in_scope_cases)})",
    }


def main():
    print("=== BẮT ĐẦU QUÉT KÍCH THƯỚC CHUNK (§40.2 Mục 4) ===")
    tai_lieu = doc_tai_lieu_da_duyet()
    facts = doc_facts()
    cases = doc_cases()

    print(f"- Số tài liệu đã duyệt: {len(tai_lieu)}")
    print(f"- Số facts kiểm định: {len(facts)}")
    print(f"- Số test cases kiểm thử: {len(cases)}")

    configs = [
        (800, 1500),
        (1000, 1800),
        (1200, 2200),  # Cấu hình chuẩn của Nextfarm
        (1500, 2800),
    ]

    results = []
    for target_size, max_size in configs:
        print(f"\n-> Đang chạy cấu hình target_size = {target_size} (max = {max_size})...")
        t0 = time.time()
        chunks = chay_chunking(tai_lieu, target_size, max_size)
        res = danh_gia_cau_hinh(chunks, facts, cases, target_size)
        res["thoi_gian_ms"] = round((time.time() - t0) * 1000, 1)
        results.append(res)
        print(f"   Kết quả: {res['so_chunk']} chunks | Độ dài TB: {res['do_dai_tb']} | Fact Coverage: {res['fact_coverage']} | Hit Rate: {res['retrieval_hit_rate']}")

    # Tạo báo cáo Markdown
    report_lines = [
        "# Báo Cáo Đo Lường Kỹ Thuật: Quét Tối Ưu Kích Thước Chunk (§40.2 Mục 4)",
        "",
        "> **Tiêu chuẩn tham chiếu:** `NEXTFARM_PROBLEM_A_STANDARD_v2.0.md` — Mục 26 & Mục 40.2",
        f"> **Thời điểm thực thi:** 22/08/2026",
        f"> **Dữ liệu đánh giá:** {len(tai_lieu)} tài liệu crawl đã duyệt · {len(facts)} facts xác nhận · {len(cases)} test cases đóng băng",
        "",
        "---",
        "",
        "## 1. Bảng Kết Quả So Sánh Đa Cấu Hình",
        "",
        "| Kích thước mục tiêu | Tổng Chunk | Độ dài TB (min–max) | Tỷ lệ Rủi ro cao | Fact Coverage | Hit Rate (In-scope) | Thời gian xử lý |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for r in results:
        report_lines.append(
            f"| **{r['target_size']} ký tự** | {r['so_chunk']} | {r['do_dai_tb']} ({r['do_dai_min']}–{r['do_dai_max']}) | {r['ty_le_rui_ro_cao']} | **{r['fact_coverage']}** | **{r['retrieval_hit_rate']}** | {r['thoi_gian_ms']} ms |"
        )

    # Ket luan phai SUY TU BANG, khong viet san.
    #
    # SUA 2026-08-28: ban cu in "Cau hinh 1.200 ky tu (Diem toi uu da chot)" va
    # "da duoc chung minh thuc nghiem" duoi dang chuoi hang - bat ke bang so noi
    # gi. Bang so that su noi: ca bon cau hinh deu 100% Fact Coverage va 100%
    # Hit Rate. Phep do KHONG PHAN BIET duoc chung. Mot ket qua dong nhat tuyet
    # doi tren moi cau hinh gan nhu luon la gioi han cua phep do, khong phai
    # phat hien - va tuyet doi khong phai bang chung cho mot lua chon.
    fc = {r["fact_coverage"] for r in results}
    hr = {r["retrieval_hit_rate"] for r in results}
    khong_phan_biet = len(fc) == 1 and len(hr) == 1

    report_lines.extend([
        "",
        "---",
        "",
        "## 2. Bảng trên nói được gì",
        "",
    ])

    if khong_phan_biet:
        report_lines.extend([
            f"**Không phân biệt được cấu hình nào.** Cả {len(results)} cấu hình đều cho "
            f"Fact Coverage {fc.pop()} và Hit Rate {hr.pop()}. Hai chỉ số chất lượng duy nhất "
            "trong bảng đứng yên trên toàn dải 800–1500 ký tự.",
            "",
            "Nghĩa là phép đo này **không đủ độ phân giải để chọn kích thước chunk**. Nó chứng "
            "minh được một điều hẹp hơn nhưng có thật: trong dải đã thử, không kích thước nào "
            "làm mất fact hay trượt câu hỏi in-scope.",
            "",
            "Những chỉ số CÓ khác nhau giữa các cấu hình — tổng số chunk, độ dài trung bình, "
            "tỷ lệ chunk rủi ro cao — là đặc tính của phép cắt, không phải thước đo chất lượng "
            "trả lời. Không thể chốt tham số bằng chúng.",
            "",
            "> Bản báo cáo trước kết luận 1.200 ký tự là *\"cấu hình tối ưu kỹ thuật đã được "
            "chứng minh thực nghiệm\"*, kèm nhận định 800 ký tự *\"cắt ngang bảng định lượng "
            "phân bón\"* và 1.500 ký tự *\"tăng nhiễu từ khóa\"*. Không có số nào trong bảng "
            "đo hai điều đó. Đã bỏ.",
        ])
    else:
        report_lines.extend([
            "Các cấu hình cho kết quả khác nhau — xem bảng. Fact Coverage: "
            + ", ".join(sorted(fc)) + "; Hit Rate: " + ", ".join(sorted(hr)) + ".",
        ])

    report_lines.extend([
        "",
        "## 3. Vì sao vẫn giữ 1.200",
        "",
        "Không phải vì phép đo chọn nó. Vì **đổi kích thước chunk sẽ vô hiệu hoá toàn bộ quyết "
        "định duyệt lẻ đang có**.",
        "",
        "`chunk_id` dựng theo thứ tự trong tài liệu (`knowledge/ingestion/load.py:153`):",
        "",
        "```python",
        'cid = rec["id"] + "#" + str(c.ordinal)',
        "```",
        "",
        "Đổi hằng số cắt → mọi `ordinal` xê dịch → một `chunk_id` cũ trỏ sang đoạn văn khác. "
        "Khoá duyệt đã chuyển sang sha256 nội dung nên hỏng theo hướng an toàn (không khớp = "
        "chưa duyệt = bị chặn), nhưng hậu quả vận hành vẫn là **31 chunk rủi ro cao phải duyệt "
        "lại từ đầu**.",
        "",
        "Đo thực nghiệm 2026-08-22 khi hạ 1200 → 700: 292 chunk thành 440, 31 chunk rủi ro cao "
        "thành 41. Nếu còn khoá theo `chunk_id`, 10 quyết định duyệt cũ sẽ đè lên văn bản khác — "
        "một trong số đó mang `approved=True`.",
        "",
        "## 4. Kết luận §40.2 Mục 4",
        "",
        "> **Giữ `KICH_THUOC_MUC_TIEU = 1200`, `KICH_THUOC_TOI_DA = 2200`, `CHONG_LAN = 150`.**",
        ">",
        "> Lý do là **chi phí duyệt lại**, không phải ưu thế đo được. Trên dải 800–1500, phép đo "
        "hiện có không phân biệt được cấu hình nào tốt hơn. Muốn chốt bằng số đo thật thì cần "
        "một thước phân biệt được — ví dụ Recall@K theo từng cấu hình trên tập v3, hoặc chấm "
        "tay chất lượng trích dẫn — và cần chấp nhận ngân sách duyệt lại 31 chunk.",
    ])

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n[OK] Đã xuất báo cáo chi tiết tại: {OUT_REPORT}")


if __name__ == "__main__":
    main()
